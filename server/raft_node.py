#!/usr/bin/env python3
# raft_node.py — Raft leader election (Q3) + log replication (Q4)
#
# Implements the follower/candidate/leader state machine with:
#   - Randomized election timeout [1.5s, 3.0s]
#   - RequestVote RPC (voting phase)
#   - AppendEntries RPC (heartbeat Q3; log replication Q4)
#   - ForwardRequest RPC (Q4: non-leader forwards client requests to leader)
#
# Thread model:
#   - Timer thread: monitors election timeout (runs always)
#   - Heartbeat thread: sends periodic AppendEntries (leader only, one per term)
#   - gRPC main thread: handles incoming RPCs via RaftServicer
#
# All shared state is protected by self._lock.

import dataclasses
import random
import threading
import time
from typing import Callable, Optional

import grpc
import raft_pb2
import raft_pb2_grpc


def peer_node_id(peer_addr: str) -> int:
    """Extract numeric node ID from address like 'fishing3:50053'."""
    hostname = peer_addr.split(":")[0]
    return int(hostname.replace("fishing", ""))


@dataclasses.dataclass
class LogEntry:
    """In-memory log entry representation."""

    operation: str  # "UpdateLocation:jwt:x:y"
    term: int
    index: int  # 1-based; 0 means "nothing committed"


def _parse_operation(operation: str):
    """Parse 'UpdateLocation:jwt:x:y' → (jwt, x, y). Returns None on parse error."""
    parts = operation.split(":", 3)
    if len(parts) != 4 or parts[0] != "UpdateLocation":
        return None
    try:
        return parts[1], float(parts[2]), float(parts[3])
    except ValueError:
        return None


def _execute_operation(operation: str, apply_fn: Callable) -> None:
    """Execute a committed log entry by calling apply_fn(jwt, x, y)."""
    parsed = _parse_operation(operation)
    if parsed is not None:
        apply_fn(*parsed)


class RaftNode:
    def __init__(self, node_id: int, peers: list, _start_threads: bool = True):
        """
        Args:
            node_id: integer ID for this node
            peers: list of "host:port" strings for all other nodes
            _start_threads: set False in unit tests to suppress background threads
        """
        self.node_id = node_id
        self.peers = peers  # list of "host:port" strings

        # Persistent state
        self.current_term = 0
        self.voted_for = None  # candidate_id voted for in current term
        self.log = []  # list of LogEntry

        # Volatile state
        self.role = "follower"  # "follower", "candidate", "leader"
        self.leader_id = None
        self.commit_index = 0  # index of highest committed entry (0 = none)
        self.last_applied = 0  # index of highest entry applied to state machine

        # Q4: client commit tracking
        self.pending_clients = {}  # index -> threading.Event
        self.ack_tracker = {}  # index -> set of follower_ids that have ACKed

        # Q4: apply_fn set by RaftServicer; called to execute committed operations
        self._apply_fn: Optional[Callable] = None

        # Timers
        self.election_timeout = random.uniform(1.5, 3.0)
        self.heartbeat_interval = 1.0
        self.last_heartbeat_time = time.time()

        self._lock = threading.Lock()
        self._start_threads = _start_threads

        if _start_threads:
            t = threading.Thread(target=self._election_timer_loop, daemon=True)
            t.start()

    # ------------------------------------------------------------------
    # Q4 public API (call under self._lock unless noted)
    # ------------------------------------------------------------------

    def append_log_entry(self, operation: str) -> int:
        """Append a new entry to the leader's log. Returns the new entry index.

        Must be called while holding self._lock.
        """
        next_index = len(self.log) + 1
        entry = LogEntry(operation=operation, term=self.current_term, index=next_index)
        self.log.append(entry)
        self.ack_tracker[next_index] = {self.node_id}  # self-ACK
        self.pending_clients[next_index] = threading.Event()
        return next_index

    def wait_for_commit(self, index: int, timeout: float = 5.0) -> bool:
        """Block until entry at *index* is committed or timeout expires.

        Safe to call without holding the lock.
        Returns True if committed, False on timeout (e.g., leader stepped down).
        """
        event = self.pending_clients.get(index)
        if event is None:
            # Already committed and cleaned up, or never existed
            return index <= self.commit_index
        return event.wait(timeout=timeout)

    def get_leader_address(self) -> Optional[str]:
        """Return the peer address for the current leader, or None.

        Must be called while holding self._lock.
        """
        if self.leader_id is None:
            return None
        for peer in self.peers:
            if peer_node_id(peer) == self.leader_id:
                return peer
        return None

    def _record_ack(self, follower_id: int) -> None:
        """Record that follower_id has ACKed; commit any newly-majority entries.

        Must be called while holding self._lock.
        """
        total_nodes = len(self.peers) + 1
        # Credit the ACK to every uncommitted entry (follower confirmed entire log)
        for entry in self.log:
            if entry.index > self.commit_index:
                tracker = self.ack_tracker.setdefault(entry.index, {self.node_id})
                tracker.add(follower_id)

        # Commit entries that have reached majority, in index order
        for entry in sorted(self.log, key=lambda e: e.index):
            if entry.index <= self.commit_index:
                continue
            acks = self.ack_tracker.get(entry.index, set())
            if len(acks) > total_nodes / 2:
                if self._apply_fn is not None:
                    _execute_operation(entry.operation, self._apply_fn)
                self.commit_index = entry.index
                self.last_applied = entry.index
                event = self.pending_clients.pop(entry.index, None)
                if event is not None:
                    event.set()
                self.ack_tracker.pop(entry.index, None)

    # ------------------------------------------------------------------
    # Election timer
    # ------------------------------------------------------------------

    def _election_timer_loop(self) -> None:
        """Background thread: trigger election when heartbeat times out."""
        while True:
            time.sleep(0.1)
            with self._lock:
                if self.role != "leader":
                    elapsed = time.time() - self.last_heartbeat_time
                    if elapsed > self.election_timeout:
                        self._start_election()

    # ------------------------------------------------------------------
    # Election
    # ------------------------------------------------------------------

    def _start_election(self) -> None:
        """Start a new election. Must be called under self._lock."""
        self.role = "candidate"
        self.current_term += 1
        self.voted_for = self.node_id
        self.election_timeout = random.uniform(1.5, 3.0)  # re-randomize
        self.last_heartbeat_time = time.time()  # reset timer

        term = self.current_term
        node_id = self.node_id
        peers = list(self.peers)

        # Spawn thread so we don't hold the lock during RPC calls
        t = threading.Thread(
            target=self._send_vote_requests, args=(term, node_id, peers), daemon=True
        )
        t.start()

    def _send_vote_requests(self, term: int, candidate_id: int, peers: list) -> None:
        """Send RequestVote to all peers; runs outside the lock."""
        votes = 1  # self-vote already counted
        total_nodes = len(peers) + 1

        for peer in peers:
            pid = peer_node_id(peer)
            print(f"Node {candidate_id} sends RPC RequestVote to Node {pid}")
            try:
                channel = grpc.insecure_channel(peer)
                stub = raft_pb2_grpc.RaftServiceStub(channel)
                resp = stub.RequestVote(
                    raft_pb2.RequestVoteRequest(
                        term=term,
                        candidate_id=candidate_id,
                        last_log_index=0,
                        last_log_term=0,
                    ),
                    timeout=1.0,
                )
                with self._lock:
                    if resp.term > self.current_term:
                        self.current_term = resp.term
                        self.role = "follower"
                        self.voted_for = None
                        return
                if resp.vote_granted:
                    votes += 1
            except grpc.RpcError:
                pass

        with self._lock:
            if self.role == "candidate" and self.current_term == term:
                if votes > total_nodes / 2:
                    self._become_leader()

    def _become_leader(self) -> None:
        """Transition to leader. Must be called under self._lock."""
        self.role = "leader"
        self.leader_id = self.node_id
        print(f"[RAFT] Node {self.node_id} became leader for term {self.current_term}")

        if self._start_threads:
            t = threading.Thread(target=self._heartbeat_loop, daemon=True)
            t.start()

    # ------------------------------------------------------------------
    # Heartbeat sender (leader only) — Q4: sends full log + commit_index
    # ------------------------------------------------------------------

    def _heartbeat_loop(self) -> None:
        """Background thread: send AppendEntries to all peers every heartbeat_interval."""
        while True:
            time.sleep(self.heartbeat_interval)
            with self._lock:
                if self.role != "leader":
                    return
                term = self.current_term
                node_id = self.node_id
                peers = list(self.peers)
                # Snapshot the full log as proto entries
                proto_entries = [
                    raft_pb2.LogEntry(
                        operation=e.operation, term=e.term, index=e.index
                    )
                    for e in self.log
                ]
                commit_index = self.commit_index

            for peer in peers:
                pid = peer_node_id(peer)
                print(f"Node {node_id} sends RPC AppendEntries to Node {pid}")
                try:
                    channel = grpc.insecure_channel(peer)
                    stub = raft_pb2_grpc.RaftServiceStub(channel)
                    resp = stub.AppendEntries(
                        raft_pb2.AppendEntriesRequest(
                            term=term,
                            leader_id=node_id,
                            entries=proto_entries,
                            commit_index=commit_index,
                        ),
                        timeout=1.0,
                    )
                    with self._lock:
                        if resp.term > self.current_term:
                            self.current_term = resp.term
                            self.role = "follower"
                            self.voted_for = None
                            return
                        if resp.success and self.role == "leader":
                            self._record_ack(resp.follower_id)
                except grpc.RpcError:
                    pass


# ------------------------------------------------------------------
# gRPC servicer
# ------------------------------------------------------------------


class RaftServicer(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self, raft_node: RaftNode, apply_fn: Optional[Callable] = None):
        """
        Args:
            raft_node: the RaftNode instance for this server
            apply_fn: callable(jwt, x, y) invoked when a committed entry is executed.
                      Used by both the follower's AppendEntries handler and the leader's
                      _record_ack path (stored on the node for heartbeat thread access).
        """
        self._node = raft_node
        self._node._apply_fn = apply_fn

    def RequestVote(self, request, context):
        node = self._node
        print(
            f"Node {node.node_id} runs RPC RequestVote called by Node {request.candidate_id}"
        )
        with node._lock:
            # Stale term: reject immediately
            if request.term < node.current_term:
                return raft_pb2.RequestVoteResponse(
                    term=node.current_term,
                    vote_granted=False,
                    voter_id=node.node_id,
                )

            # Higher term: step down unconditionally
            if request.term > node.current_term:
                node.current_term = request.term
                node.role = "follower"
                node.voted_for = None

            # Grant vote if we haven't voted or already voted for this candidate
            if node.voted_for is None or node.voted_for == request.candidate_id:
                node.voted_for = request.candidate_id
                node.last_heartbeat_time = time.time()
                return raft_pb2.RequestVoteResponse(
                    term=node.current_term,
                    vote_granted=True,
                    voter_id=node.node_id,
                )

            return raft_pb2.RequestVoteResponse(
                term=node.current_term,
                vote_granted=False,
                voter_id=node.node_id,
            )

    def AppendEntries(self, request, context):
        node = self._node
        print(
            f"Node {node.node_id} runs RPC AppendEntries called by Node {request.leader_id}"
        )
        with node._lock:
            # Stale leader: reject
            if request.term < node.current_term:
                return raft_pb2.AppendEntriesResponse(
                    term=node.current_term,
                    success=False,
                    follower_id=node.node_id,
                )

            # Valid leader: update term if needed, step down, reset timer
            if request.term > node.current_term:
                node.current_term = request.term
                node.voted_for = None

            node.role = "follower"
            node.leader_id = request.leader_id
            node.last_heartbeat_time = time.time()

            # Q4: replace entire log with leader's log
            node.log = [
                LogEntry(operation=e.operation, term=e.term, index=e.index)
                for e in request.entries
            ]

            # Q4: execute all committed entries not yet applied
            new_commit = request.commit_index
            apply_fn = node._apply_fn
            for entry in node.log:
                if entry.index <= new_commit and entry.index > node.last_applied:
                    if apply_fn is not None:
                        _execute_operation(entry.operation, apply_fn)
                    node.last_applied = entry.index

            node.commit_index = new_commit

            return raft_pb2.AppendEntriesResponse(
                term=node.current_term,
                success=True,
                follower_id=node.node_id,
            )

    def ForwardRequest(self, request, context):
        node = self._node
        sender_id = request.sender_id

        with node._lock:
            is_leader = node.role == "leader"
            node_id = node.node_id
            leader_addr = node.get_leader_address() if not is_leader else None
            leader_id = node.leader_id

        print(
            f"Node {node_id} runs RPC ForwardRequest called by Node {sender_id}"
        )

        if is_leader:
            # This node is the leader — append to log and wait for commit
            operation = f"UpdateLocation:{request.user_jwt}:{request.x}:{request.y}"
            with node._lock:
                index = node.append_log_entry(operation)
            committed = node.wait_for_commit(index)
            if committed:
                return raft_pb2.ForwardRequestResponse(success=True, message="")
            return raft_pb2.ForwardRequestResponse(
                success=False, message="Commit timeout: leader may have stepped down"
            )

        # Not the leader — forward to the known leader
        if leader_addr is None:
            return raft_pb2.ForwardRequestResponse(
                success=False, message="No leader known; election may be in progress"
            )

        print(f"Node {node_id} sends RPC ForwardRequest to Node {leader_id}")
        try:
            channel = grpc.insecure_channel(leader_addr)
            stub = raft_pb2_grpc.RaftServiceStub(channel)
            resp = stub.ForwardRequest(
                raft_pb2.ForwardRequestMessage(
                    user_jwt=request.user_jwt,
                    x=request.x,
                    y=request.y,
                    sender_id=node_id,
                ),
                timeout=6.0,
            )
            return resp
        except grpc.RpcError as exc:
            return raft_pb2.ForwardRequestResponse(
                success=False, message=f"ForwardRequest to leader failed: {exc}"
            )
