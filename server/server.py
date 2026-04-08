#!/usr/bin/env python3
# server.py

import os
import random
import threading
import time
from concurrent import futures

import fishing_pb2 as pb
import fishing_pb2_grpc as grpc_stub
import grpc
import raft_node as raft_mod
import raft_pb2
import raft_pb2_grpc as raft_grpc
import twopc_pb2
import twopc_pb2_grpc as twopc_grpc

# ----------------------------------------------------------------------
# 2PC environment configuration
# ----------------------------------------------------------------------
NODE_ID = int(os.environ.get("NODE_ID", "1"))
PEERS_STR = os.environ.get("PEERS", "")
IS_COORDINATOR = os.environ.get("IS_COORDINATOR", "false").lower() == "true"
PORT = 50051  # updated by serve() at startup

# Q4: module-level reference to the RaftNode, set in serve()
raft_node: raft_mod.RaftNode = None  # type: ignore[assignment]

# Transaction ID counter (coordinator only)
_tx_counter = 0
_tx_lock = threading.Lock()


# ----------------------------------------------------------------------
# In‑memory state (protected by a lock)
# ----------------------------------------------------------------------
class ServerState:
    def __init__(self):
        self.users = {}  # jwt -> pb.User
        self.inventory = {}  # jwt -> list[Fish]
        self.user_id_seq = 1
        self.lock = threading.Lock()

    def add_user(self, jwt):
        with self.lock:
            if jwt not in self.users:
                uid = self.user_id_seq
                self.user_id_seq += 1
                user = pb.User(id=uid, x=0.0, y=0.0, is_fishing=False)
                self.users[jwt] = user
                self.inventory.setdefault(jwt, [])
                return True
            return False

    def update_user(self, jwt, x, y):
        with self.lock:
            if jwt in self.users:
                u = self.users[jwt]
                u.x = x
                u.y = y

    def remove_user(self, jwt):
        with self.lock:
            self.users.pop(jwt, None)
            self.inventory.pop(jwt, None)

    def get_user_snapshot(self):
        with self.lock:
            return list(self.users.values())

    def current_user_count(self):
        with self.lock:
            return len(self.users)

    def add_fish_to_user(self, jwt, fish):
        with self.lock:
            if jwt in self.inventory:
                self.inventory[jwt].append(fish)

    def get_all_fishes(self):
        with self.lock:
            all_fishes = []
            for fishes in self.inventory.values():
                all_fishes.extend(fishes)
            return all_fishes


state = ServerState()

# ----------------------------------------------------------------------
# 2PC helpers (module-level so unit tests can import them directly)
# ----------------------------------------------------------------------


def next_transaction_id() -> int:
    """Return a monotonically increasing transaction ID (thread-safe)."""
    global _tx_counter
    with _tx_lock:
        _tx_counter += 1
        return _tx_counter


def peer_node_id(peer_addr: str) -> int:
    """Extract numeric node ID from a peer address like 'fishing3:50053'."""
    hostname = peer_addr.split(":")[0]  # e.g. 'fishing3'
    return int(hostname.replace("fishing", ""))


def run_voting_phase(jwt: str, x: float, y: float, transaction_id: int) -> list:
    """Coordinator: send VoteRequest to all peers, then call intra-node ReportVote.

    Returns the list of VoteResponse messages collected from participants.
    """
    peers = [p.strip() for p in PEERS_STR.split(",") if p.strip()]
    proposed = twopc_pb2.LocationUpdate(user_jwt=jwt, x=x, y=y)
    votes = []

    for peer in peers:
        pid = peer_node_id(peer)
        # Sender-side log (assignment-required format)
        print(f"Phase voting of Node {NODE_ID} sends RPC VoteRequest to Phase voting of Node {pid}")
        try:
            channel = grpc.insecure_channel(peer)
            stub = twopc_grpc.TwoPhaseCommitServiceStub(channel)
            resp = stub.VoteRequest(
                twopc_pb2.VoteRequestMessage(
                    coordinator_id=NODE_ID,
                    transaction_id=transaction_id,
                    proposed_update=proposed,
                )
            )
            votes.append(resp)
        except grpc.RpcError as exc:
            print(f"[2PC] VoteRequest to {peer} failed: {exc}")

    # Intra-node gRPC: voting phase → decision phase (same container, localhost)
    all_commit = all(v.vote_commit for v in votes) if votes else True
    print(
        f"Phase voting of Node {NODE_ID} sends RPC ReportVote to Phase decision of Node {NODE_ID}"
    )
    try:
        channel = grpc.insecure_channel(f"localhost:{PORT}")
        intra_stub = twopc_grpc.IntraNodePhaseServiceStub(channel)
        intra_stub.ReportVote(
            twopc_pb2.IntraVoteReport(
                transaction_id=transaction_id,
                vote_commit=all_commit,
            )
        )
    except grpc.RpcError as exc:
        print(f"[2PC] Intra-node ReportVote failed: {exc}")

    return votes


def run_decision_phase(jwt: str, x: float, y: float, transaction_id: int, votes: list) -> bool:
    """Coordinator: send GlobalDecision to all peers, then call intra-node NotifyDecision.

    Returns True if global-commit, False if global-abort.
    """
    global_commit = all(v.vote_commit for v in votes) if votes else True
    peers = [p.strip() for p in PEERS_STR.split(",") if p.strip()]
    update = twopc_pb2.LocationUpdate(user_jwt=jwt, x=x, y=y)

    for peer in peers:
        pid = peer_node_id(peer)
        print(
            f"Phase decision of Node {NODE_ID} sends RPC GlobalDecision"
            f" to Phase decision of Node {pid}"
        )
        try:
            channel = grpc.insecure_channel(peer)
            stub = twopc_grpc.TwoPhaseCommitServiceStub(channel)
            stub.GlobalDecision(
                twopc_pb2.DecisionMessage(
                    coordinator_id=NODE_ID,
                    transaction_id=transaction_id,
                    global_commit=global_commit,
                    update=update,
                )
            )
        except grpc.RpcError as exc:
            print(f"[2PC] GlobalDecision to {peer} failed: {exc}")

    # Intra-node gRPC: decision phase → voting phase (same container, localhost)
    print(
        f"Phase decision of Node {NODE_ID} sends RPC NotifyDecision"
        f" to Phase voting of Node {NODE_ID}"
    )
    try:
        channel = grpc.insecure_channel(f"localhost:{PORT}")
        intra_stub = twopc_grpc.IntraNodePhaseServiceStub(channel)
        intra_stub.NotifyDecision(
            twopc_pb2.IntraDecisionNotification(
                transaction_id=transaction_id,
                global_commit=global_commit,
            )
        )
    except grpc.RpcError as exc:
        print(f"[2PC] Intra-node NotifyDecision failed: {exc}")

    return global_commit


# ----------------------------------------------------------------------
# 2PC servicers
# ----------------------------------------------------------------------


class TwoPhaseCommitServicer(twopc_grpc.TwoPhaseCommitServiceServicer):
    """Handles inter-node 2PC RPCs. All nodes register this (participant role)."""

    def VoteRequest(self, request, context):
        # Receiver-side log (assignment uses same "sends RPC" wording as sender)
        print(
            f"Phase voting of Node {NODE_ID} sends RPC VoteRequest"
            f" to Phase voting of Node {request.coordinator_id}"
        )
        update = request.proposed_update
        if update.x < 0 or update.y < 0:
            return twopc_pb2.VoteResponse(
                participant_id=NODE_ID,
                transaction_id=request.transaction_id,
                vote_commit=False,
                reason=f"Negative coordinates: x={update.x}, y={update.y}",
            )
        return twopc_pb2.VoteResponse(
            participant_id=NODE_ID,
            transaction_id=request.transaction_id,
            vote_commit=True,
            reason="",
        )

    def GlobalDecision(self, request, context):
        # Receiver-side log (assignment-required format)
        print(
            f"Phase decision of Node {NODE_ID} sends RPC GlobalDecision"
            f" to Phase decision of Node {request.coordinator_id}"
        )
        if request.global_commit:
            upd = request.update
            state.update_user(upd.user_jwt, upd.x, upd.y)
            applied = True
        else:
            applied = False
        return twopc_pb2.DecisionAck(
            participant_id=NODE_ID,
            transaction_id=request.transaction_id,
            applied=applied,
        )


class IntraNodePhaseServicer(twopc_grpc.IntraNodePhaseServiceServicer):
    """Handles intra-node gRPC between voting and decision phases."""

    def ReportVote(self, request, context):
        print(
            f"Phase decision of Node {NODE_ID} sends RPC ReportVote"
            f" to Phase voting of Node {NODE_ID}"
        )
        # Q1: decision phase receives aggregated vote; Q2 will act on it
        return twopc_pb2.IntraVoteAck(acknowledged=True)

    def NotifyDecision(self, request, context):
        print(
            f"Phase voting of Node {NODE_ID} sends RPC NotifyDecision"
            f" to Phase decision of Node {NODE_ID}"
        )
        # Voting phase receives notification of final decision from decision phase
        return twopc_pb2.IntraDecisionAck(acknowledged=True)


# ----------------------------------------------------------------------
# Q4 Raft helper
# ----------------------------------------------------------------------


def _raft_update_location(jwt: str, x: float, y: float) -> None:
    """Route an UpdateLocation through the Raft log.

    If this node is the leader: append to log, wait for commit (majority ACK).
    If this node is a follower: forward to the current leader via ForwardRequest RPC.
    Falls back to a direct state update with a warning if Raft is unavailable.
    """
    with raft_node._lock:
        role = raft_node.role
        leader_addr = raft_node.get_leader_address()
        leader_id = raft_node.leader_id
        node_id = raft_node.node_id

    if role == "leader":
        with raft_node._lock:
            index = raft_node.append_log_entry(f"UpdateLocation:{jwt}:{x}:{y}")
        committed = raft_node.wait_for_commit(index)
        if not committed:
            print(f"[RAFT] Commit timeout for index {index}; applying locally as fallback")
            state.update_user(jwt, x, y)
    elif leader_addr is not None:
        print(f"Node {node_id} sends RPC ForwardRequest to Node {leader_id}")
        try:
            channel = grpc.insecure_channel(leader_addr)
            stub = raft_grpc.RaftServiceStub(channel)
            stub.ForwardRequest(
                raft_pb2.ForwardRequestMessage(
                    user_jwt=jwt,
                    x=x,
                    y=y,
                    sender_id=NODE_ID,
                ),
                timeout=6.0,
            )
        except grpc.RpcError as exc:
            print(f"[RAFT] ForwardRequest to leader failed: {exc}; applying locally")
            state.update_user(jwt, x, y)
    else:
        # No leader known (election in progress); apply directly with a warning
        print(f"[RAFT] No leader known on Node {node_id}; applying locally as fallback")
        state.update_user(jwt, x, y)


# ----------------------------------------------------------------------
# Service implementation
# ----------------------------------------------------------------------
class FishingService(grpc_stub.FishingServiceServicer):
    # ---------- Login ----------
    def Login(self, request, context):
        # Dummy auth – always accept
        token = f"{request.username}:{request.password}"
        print(f"[LOGIN] User '{token}' logged in.")
        return pb.LoginResponse(token=token)

    # ---------- UpdateLocation (client‑stream) ----------
    def UpdateLocation(self, request_iterator, context):
        jwt = None

        # This function will be executed when the RPC ends
        def cleanup():
            if jwt:
                state.remove_user(jwt)
                print(f"[UPDATE] User stream closed: {jwt}")

        # Register the cleanup callback
        context.add_callback(cleanup)

        for req in request_iterator:
            if not jwt:  # first message establishes the user
                jwt = req.jwt
                added = state.add_user(jwt)
                if added:
                    print(f"[UPDATE] New user stream opened: {jwt}")

            if IS_COORDINATOR:
                # 2PC path: coordinator drives voting + decision phases
                tx_id = next_transaction_id()
                votes = run_voting_phase(req.jwt, req.x, req.y, tx_id)
                global_commit = run_decision_phase(req.jwt, req.x, req.y, tx_id, votes)
                if global_commit:
                    state.update_user(jwt, req.x, req.y)
            elif raft_node is not None:
                # Q4 Raft path: route through log replication
                _raft_update_location(req.jwt, req.x, req.y)
            else:
                # Fallback (raft not yet initialised — shouldn't happen in prod)
                state.update_user(jwt, req.x, req.y)

        # No explicit call to cleanup() is needed – it will run automatically.
        return pb.UpdateLocationResponse(success=True)

    # ---------- ListUsers (server‑stream) ----------
    def ListUsers(self, request, context):
        for user in state.get_user_snapshot():
            yield user

    # ---------- StartFishing (server‑stream) ----------
    def StartFishing(self, request, context):
        jwt = request.jwt
        # Random chance increases with number of users
        base_chance = 0.1
        extra_per_user = 0.05
        chance = base_chance + state.current_user_count() * extra_per_user

        print(f"[FISH] User {jwt} started fishing. Chance={chance:.2f}")
        while True:
            # Simulate a short delay
            time.sleep(random.uniform(1, 3))
            if random.random() < chance:
                fish = pb.Fish(
                    fish_id=random.randint(1000, 9999),
                    fish_dna=f"DNA{random.randint(100000, 999999)}",
                    fish_level=random.randint(1, 10),
                )
                state.add_fish_to_user(jwt, fish)
                print(f"[FISH] User {jwt} caught fish {fish.fish_id}")
                yield fish
                break
            else:
                print(f"[FISH] User {jwt} did not catch a fish.")
                # Nothing to yield – stream will close

    # ---------- CurrentUsers (server‑stream) ----------
    def CurrentUsers(self, request, context):
        previouscount = state.current_user_count()
        yield pb.CurrentUsersResponse(count=previouscount)
        while True:
            count = state.current_user_count()
            if previouscount != count:
                previouscount = count
                yield pb.CurrentUsersResponse(count=count)
            time.sleep(1.0)  # update every second

    # ---------- Inventory ----------
    def Inventory(self, request, context):
        fishes = state.get_all_fishes()
        return pb.InventoryResponse(fish=fishes)

    def GetImage(self, request, context):
        # Read the image file from the path stored in IMAGE_PATH
        with open(IMAGE_PATH, "rb") as f:
            image_bytes = f.read()
        return pb.ImageResponse(image_data=image_bytes)


# ----------------------------------------------------------------------
# Server bootstrap
# ----------------------------------------------------------------------
def serve(port=50051, image_path="image.jpg"):  # <- accept an image path
    global IMAGE_PATH, PORT
    IMAGE_PATH = image_path  # set the global to the provided argument
    PORT = port  # expose port for intra-node gRPC calls

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grpc_stub.add_FishingServiceServicer_to_server(FishingService(), server)
    twopc_grpc.add_TwoPhaseCommitServiceServicer_to_server(TwoPhaseCommitServicer(), server)
    twopc_grpc.add_IntraNodePhaseServiceServicer_to_server(IntraNodePhaseServicer(), server)

    # Q4: Raft — instantiate node (module-level so UpdateLocation can access it)
    global raft_node
    peers = [p.strip() for p in PEERS_STR.split(",") if p.strip()]
    raft_node = raft_mod.RaftNode(node_id=NODE_ID, peers=peers)
    raft_grpc.add_RaftServiceServicer_to_server(
        raft_mod.RaftServicer(raft_node, apply_fn=state.update_user), server
    )

    # Use the supplied port instead of hard‑coding it
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Server listening on port {port} (NODE_ID={NODE_ID}, IS_COORDINATOR={IS_COORDINATOR})")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print("Shutting down server…")
        server.stop(0)


if __name__ == "__main__":
    import sys

    # Read optional port and image path from command‑line; default to 50051 and "image.jpg" if omitted
    try:
        cmd_port = int(sys.argv[1])
    except (IndexError, ValueError):
        cmd_port = 50051
    try:
        cmd_image_path = sys.argv[2]
    except IndexError:
        cmd_image_path = "image.jpg"
    serve(cmd_port, cmd_image_path)
