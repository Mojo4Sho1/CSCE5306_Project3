"""
Unit tests for Q3 — Raft leader election.

Tests cover:
- Initial node state (follower, term 0)
- Election start transitions (candidate, term increment, self-vote)
- RequestVote handler: grant, reject stale term, reject already-voted, step-down on higher term
- AppendEntries handler: timer reset, reject stale, step-down on higher term
- Majority vote → leader promotion (via _send_vote_requests with mocked gRPC)
- RPC log format strings (sender and receiver side)

No Docker required. All tests run via: make test
"""

import time
from unittest.mock import MagicMock, patch

# server/ is on sys.path via conftest.py
import raft_pb2
import raft_pb2_grpc
from raft_node import RaftNode, RaftServicer


def _mock_ctx():
    return MagicMock()


# ---------------------------------------------------------------------------
# Helper: build a node without background threads
# ---------------------------------------------------------------------------


def _node(node_id=1, peers=None):
    if peers is None:
        peers = ["fishing2:50052", "fishing3:50053"]
    return RaftNode(node_id, peers, _start_threads=False)


# ---------------------------------------------------------------------------
# Test 1: initial state is follower
# ---------------------------------------------------------------------------


def test_initial_state_is_follower():
    """All nodes start as followers with term 0 and no vote."""
    node = _node()
    assert node.role == "follower"
    assert node.current_term == 0
    assert node.voted_for is None
    assert node.leader_id is None


# ---------------------------------------------------------------------------
# Test 2: _start_election increments term and becomes candidate
# ---------------------------------------------------------------------------


def test_start_election_increments_term_and_sets_candidate():
    """_start_election promotes to candidate, increments term, votes for self."""
    node = _node()
    with node._lock:
        node._start_election()
    assert node.role == "candidate"
    assert node.current_term == 1
    assert node.voted_for == node.node_id


# ---------------------------------------------------------------------------
# Test 3: RequestVote grants vote when voted_for is None
# ---------------------------------------------------------------------------


def test_request_vote_grants_vote_to_first_candidate():
    """RequestVote is granted when the node has not yet voted this term."""
    node = _node(node_id=2)
    node.current_term = 1
    servicer = RaftServicer(node)

    req = raft_pb2.RequestVoteRequest(term=1, candidate_id=1, last_log_index=0, last_log_term=0)
    resp = servicer.RequestVote(req, _mock_ctx())

    assert resp.vote_granted is True
    assert resp.voter_id == 2
    assert node.voted_for == 1


# ---------------------------------------------------------------------------
# Test 4: RequestVote rejects stale term
# ---------------------------------------------------------------------------


def test_request_vote_rejects_stale_term():
    """RequestVote is rejected when the request term is less than current_term."""
    node = _node(node_id=2)
    node.current_term = 5
    servicer = RaftServicer(node)

    req = raft_pb2.RequestVoteRequest(term=3, candidate_id=1, last_log_index=0, last_log_term=0)
    resp = servicer.RequestVote(req, _mock_ctx())

    assert resp.vote_granted is False
    assert resp.term == 5


# ---------------------------------------------------------------------------
# Test 5: RequestVote rejects when already voted for a different candidate
# ---------------------------------------------------------------------------


def test_request_vote_rejects_already_voted_for_other():
    """RequestVote is rejected when node already voted for a different candidate this term."""
    node = _node(node_id=2)
    node.current_term = 2
    node.voted_for = 3  # already voted for node 3
    servicer = RaftServicer(node)

    req = raft_pb2.RequestVoteRequest(term=2, candidate_id=1, last_log_index=0, last_log_term=0)
    resp = servicer.RequestVote(req, _mock_ctx())

    assert resp.vote_granted is False
    assert node.voted_for == 3  # unchanged


# ---------------------------------------------------------------------------
# Test 6: RequestVote with higher term causes step-down and grants vote
# ---------------------------------------------------------------------------


def test_request_vote_higher_term_causes_step_down():
    """Higher term in RequestVote causes follower step-down and vote grant."""
    node = _node(node_id=2)
    node.current_term = 2
    node.role = "leader"
    servicer = RaftServicer(node)

    req = raft_pb2.RequestVoteRequest(term=5, candidate_id=1, last_log_index=0, last_log_term=0)
    resp = servicer.RequestVote(req, _mock_ctx())

    assert resp.vote_granted is True
    assert node.role == "follower"
    assert node.current_term == 5
    assert node.voted_for == 1


# ---------------------------------------------------------------------------
# Test 7: AppendEntries resets election timer
# ---------------------------------------------------------------------------


def test_append_entries_resets_election_timer():
    """Valid AppendEntries from current-term leader resets last_heartbeat_time."""
    node = _node(node_id=2)
    node.current_term = 1
    # Push last_heartbeat_time far into the past to verify it gets updated
    node.last_heartbeat_time = time.time() - 10.0
    servicer = RaftServicer(node)

    req = raft_pb2.AppendEntriesRequest(term=1, leader_id=1, entries=[], commit_index=0)
    resp = servicer.AppendEntries(req, _mock_ctx())

    assert resp.success is True
    assert node.leader_id == 1
    assert (time.time() - node.last_heartbeat_time) < 1.0  # reset to ~now


# ---------------------------------------------------------------------------
# Test 8: AppendEntries rejects stale term
# ---------------------------------------------------------------------------


def test_append_entries_rejects_stale_term():
    """AppendEntries is rejected when request term is less than current_term."""
    node = _node(node_id=2)
    node.current_term = 5
    servicer = RaftServicer(node)

    req = raft_pb2.AppendEntriesRequest(term=3, leader_id=1, entries=[], commit_index=0)
    resp = servicer.AppendEntries(req, _mock_ctx())

    assert resp.success is False
    assert resp.term == 5


# ---------------------------------------------------------------------------
# Test 9: AppendEntries with higher term causes leader to step down
# ---------------------------------------------------------------------------


def test_append_entries_higher_term_causes_step_down():
    """A leader receiving AppendEntries with a higher term steps down to follower."""
    node = _node(node_id=1)
    node.current_term = 3
    node.role = "leader"
    servicer = RaftServicer(node)

    req = raft_pb2.AppendEntriesRequest(term=7, leader_id=2, entries=[], commit_index=0)
    resp = servicer.AppendEntries(req, _mock_ctx())

    assert resp.success is True
    assert node.role == "follower"
    assert node.current_term == 7
    assert node.leader_id == 2


# ---------------------------------------------------------------------------
# Test 10: majority vote makes candidate the leader
# ---------------------------------------------------------------------------


def test_majority_vote_makes_leader():
    """Candidate becomes leader when it receives a majority of votes."""
    # 3 peers → total 4 nodes → majority = 3 votes needed
    node = _node(node_id=1, peers=["fishing2:50052", "fishing3:50053", "fishing4:50054"])
    node.role = "candidate"
    node.current_term = 1
    node.voted_for = 1  # self-vote

    mock_stub = MagicMock()
    mock_stub.RequestVote.return_value = raft_pb2.RequestVoteResponse(
        term=1, vote_granted=True, voter_id=2
    )

    with patch("grpc.insecure_channel"), patch.object(
        raft_pb2_grpc, "RaftServiceStub", return_value=mock_stub
    ):
        node._send_vote_requests(1, 1, node.peers)

    assert node.role == "leader"


# ---------------------------------------------------------------------------
# Test 11: split vote — no majority, node reverts to follower
# ---------------------------------------------------------------------------


def test_split_vote_reverts_to_follower():
    """Candidate reverts to follower when it does not receive a majority of votes."""
    # 4 peers → total 5 nodes → need 3 votes. self-vote=1, only 1 peer grants → total 2.
    node = _node(node_id=1, peers=["fishing2:50052", "fishing3:50053", "fishing4:50054", "fishing5:50055"])
    node.role = "candidate"
    node.current_term = 1
    node.voted_for = 1

    call_count = 0

    def mock_request_vote(request, timeout=None):
        nonlocal call_count
        call_count += 1
        granted = call_count == 1  # only first peer grants
        return raft_pb2.RequestVoteResponse(term=1, vote_granted=granted, voter_id=call_count + 1)

    mock_stub = MagicMock()
    mock_stub.RequestVote.side_effect = mock_request_vote

    with patch("grpc.insecure_channel"), patch.object(
        raft_pb2_grpc, "RaftServiceStub", return_value=mock_stub
    ):
        node._send_vote_requests(1, 1, node.peers)

    # self(1) + 1 peer grant = 2 out of 5 → not majority
    assert node.role == "follower"
    assert node.leader_id is None
    assert node.current_term == 1


# ---------------------------------------------------------------------------
# Test 12: RequestVote sender log format
# ---------------------------------------------------------------------------


def test_request_vote_sender_log_format(capsys):
    """Candidate prints required log line when sending RequestVote."""
    node = _node(node_id=1, peers=["fishing2:50052"])
    node.role = "candidate"
    node.current_term = 1
    node.voted_for = 1

    mock_stub = MagicMock()
    mock_stub.RequestVote.return_value = raft_pb2.RequestVoteResponse(
        term=1, vote_granted=True, voter_id=2
    )

    with patch("grpc.insecure_channel"), patch.object(
        raft_pb2_grpc, "RaftServiceStub", return_value=mock_stub
    ):
        node._send_vote_requests(1, 1, ["fishing2:50052"])

    captured = capsys.readouterr()
    assert "Node 1 sends RPC RequestVote to Node 2" in captured.out


# ---------------------------------------------------------------------------
# Test 13: RequestVote receiver log format
# ---------------------------------------------------------------------------


def test_request_vote_receiver_log_format(capsys):
    """RaftServicer.RequestVote prints required receiver-side log line."""
    node = _node(node_id=2)
    node.current_term = 1
    servicer = RaftServicer(node)

    req = raft_pb2.RequestVoteRequest(term=1, candidate_id=1, last_log_index=0, last_log_term=0)
    servicer.RequestVote(req, _mock_ctx())

    captured = capsys.readouterr()
    assert "Node 2 runs RPC RequestVote called by Node 1" in captured.out


# ---------------------------------------------------------------------------
# Test 14: AppendEntries receiver log format
# ---------------------------------------------------------------------------


def test_append_entries_receiver_log_format(capsys):
    """RaftServicer.AppendEntries prints required receiver-side log line."""
    node = _node(node_id=3)
    node.current_term = 2
    servicer = RaftServicer(node)

    req = raft_pb2.AppendEntriesRequest(term=2, leader_id=1, entries=[], commit_index=0)
    servicer.AppendEntries(req, _mock_ctx())

    captured = capsys.readouterr()
    assert "Node 3 runs RPC AppendEntries called by Node 1" in captured.out
