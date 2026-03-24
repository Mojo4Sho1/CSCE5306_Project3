#!/usr/bin/env python3
# raft_node.py — Raft leader election (Q3)
#
# Implements the follower/candidate/leader state machine with:
#   - Randomized election timeout [1.5s, 3.0s]
#   - RequestVote RPC (voting phase)
#   - AppendEntries RPC (heartbeat in Q3; log replication in Q4)
#   - ForwardRequest RPC stub (Q4)
#
# Thread model:
#   - Timer thread: monitors election timeout (runs always)
#   - Heartbeat thread: sends periodic AppendEntries (leader only, one per term)
#   - gRPC main thread: handles incoming RPCs via RaftServicer
#
# All shared state is protected by self._lock.

import random
import threading
import time

import grpc
import raft_pb2
import raft_pb2_grpc


def peer_node_id(peer_addr: str) -> int:
    """Extract numeric node ID from address like 'fishing3:50053'."""
    hostname = peer_addr.split(":")[0]
    return int(hostname.replace("fishing", ""))


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
        self.log = []  # list of LogEntry (Q4)

        # Volatile state
        self.role = "follower"  # "follower", "candidate", "leader"
        self.leader_id = None
        self.commit_index = 0  # Q4

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
    # Heartbeat sender (leader only)
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
                            entries=[],
                            commit_index=0,
                        ),
                        timeout=1.0,
                    )
                    with self._lock:
                        if resp.term > self.current_term:
                            self.current_term = resp.term
                            self.role = "follower"
                            self.voted_for = None
                            return
                except grpc.RpcError:
                    pass


# ------------------------------------------------------------------
# gRPC servicer
# ------------------------------------------------------------------


class RaftServicer(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self, raft_node: RaftNode):
        self._node = raft_node

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

            return raft_pb2.AppendEntriesResponse(
                term=node.current_term,
                success=True,
                follower_id=node.node_id,
            )

    def ForwardRequest(self, request, context):
        # Q4 stub: non-leader forwarding to leader not implemented in Q3
        return raft_pb2.ForwardRequestResponse(
            success=False, message="Not implemented in Q3"
        )
