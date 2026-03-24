"""
Unit tests for Q1 — 2PC voting phase.

Tests cover:
- Participant vote logic (commit / abort)
- Log format strings (assignment-required format)
- Transaction ID monotonicity
- Coordinator peer list iteration (mocked gRPC)
- Intra-node ReportVote servicer
- Helper: peer_node_id extraction

No Docker required. All tests run via: make test
"""

from unittest.mock import MagicMock, patch

import pytest

# server/ is already on sys.path via conftest.py
import twopc_pb2
import twopc_pb2_grpc as twopc_grpc

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_2pc_state(monkeypatch):
    """Reset module-level 2PC state before each test to avoid ordering issues."""
    import server as srv

    monkeypatch.setattr(srv, "_tx_counter", 0)
    monkeypatch.setattr(srv, "NODE_ID", 1)
    monkeypatch.setattr(srv, "PEERS_STR", "fishing2:50052,fishing3:50053")
    monkeypatch.setattr(srv, "IS_COORDINATOR", True)
    monkeypatch.setattr(srv, "PORT", 50051)


@pytest.fixture()
def participant_servicer(monkeypatch):
    """TwoPhaseCommitServicer with NODE_ID=2 (participant perspective)."""
    import server as srv

    monkeypatch.setattr(srv, "NODE_ID", 2)
    from server import TwoPhaseCommitServicer

    return TwoPhaseCommitServicer()


@pytest.fixture()
def intra_servicer():
    from server import IntraNodePhaseServicer

    return IntraNodePhaseServicer()


def _mock_ctx():
    return MagicMock()


# ---------------------------------------------------------------------------
# Test 1: vote-commit for positive coordinates
# ---------------------------------------------------------------------------


def test_vote_commit_positive_coords(participant_servicer):
    """Participant votes commit when both coordinates are positive."""
    req = twopc_pb2.VoteRequestMessage(
        coordinator_id=1,
        transaction_id=42,
        proposed_update=twopc_pb2.LocationUpdate(user_jwt="alice:pw", x=5.0, y=3.0),
    )
    resp = participant_servicer.VoteRequest(req, _mock_ctx())
    assert resp.vote_commit is True
    assert resp.transaction_id == 42
    assert resp.participant_id == 2


# ---------------------------------------------------------------------------
# Test 2: vote-abort for negative x
# ---------------------------------------------------------------------------


def test_vote_abort_negative_x(participant_servicer):
    """Participant votes abort when x is negative."""
    req = twopc_pb2.VoteRequestMessage(
        coordinator_id=1,
        transaction_id=7,
        proposed_update=twopc_pb2.LocationUpdate(user_jwt="alice:pw", x=-1.0, y=3.0),
    )
    resp = participant_servicer.VoteRequest(req, _mock_ctx())
    assert resp.vote_commit is False
    assert resp.reason != ""


# ---------------------------------------------------------------------------
# Test 3: vote-abort for negative y
# ---------------------------------------------------------------------------


def test_vote_abort_negative_y(participant_servicer):
    """Participant votes abort when y is negative."""
    req = twopc_pb2.VoteRequestMessage(
        coordinator_id=1,
        transaction_id=8,
        proposed_update=twopc_pb2.LocationUpdate(user_jwt="alice:pw", x=1.0, y=-0.5),
    )
    resp = participant_servicer.VoteRequest(req, _mock_ctx())
    assert resp.vote_commit is False


# ---------------------------------------------------------------------------
# Test 4: boundary — zero coordinates vote commit (only negative aborts)
# ---------------------------------------------------------------------------


def test_vote_commit_zero_coords(participant_servicer):
    """Coordinates of exactly (0, 0) should vote commit — only negative triggers abort."""
    req = twopc_pb2.VoteRequestMessage(
        coordinator_id=1,
        transaction_id=9,
        proposed_update=twopc_pb2.LocationUpdate(user_jwt="alice:pw", x=0.0, y=0.0),
    )
    resp = participant_servicer.VoteRequest(req, _mock_ctx())
    assert resp.vote_commit is True


# ---------------------------------------------------------------------------
# Test 5: participant log format (receiver side)
# ---------------------------------------------------------------------------


def test_participant_log_format(participant_servicer, capsys):
    """Participant prints the assignment-required log line on VoteRequest receive."""
    req = twopc_pb2.VoteRequestMessage(
        coordinator_id=1,
        transaction_id=1,
        proposed_update=twopc_pb2.LocationUpdate(user_jwt="alice:pw", x=1.0, y=1.0),
    )
    participant_servicer.VoteRequest(req, _mock_ctx())
    captured = capsys.readouterr()
    expected = "Phase voting of Node 2 sends RPC VoteRequest to Phase voting of Node 1"
    assert expected in captured.out


# ---------------------------------------------------------------------------
# Test 6: coordinator log format (sender side) — one line per peer
# ---------------------------------------------------------------------------


def test_coordinator_log_format(monkeypatch, capsys):
    """Coordinator prints one sender log line per peer before calling VoteRequest."""
    import server as srv

    mock_vote_resp = twopc_pb2.VoteResponse(participant_id=2, transaction_id=1, vote_commit=True)
    mock_stub = MagicMock()
    mock_stub.VoteRequest.return_value = mock_vote_resp

    mock_intra_stub = MagicMock()
    mock_intra_stub.ReportVote.return_value = twopc_pb2.IntraVoteAck(acknowledged=True)

    def fake_channel(addr):
        ch = MagicMock()
        return ch

    with patch("grpc.insecure_channel") as mock_chan:
        mock_chan.return_value = MagicMock()
        with patch.object(twopc_grpc, "TwoPhaseCommitServiceStub", return_value=mock_stub):
            with patch.object(
                twopc_grpc, "IntraNodePhaseServiceStub", return_value=mock_intra_stub
            ):
                srv.run_voting_phase("alice:pw", 3.0, 4.0, 1)

    captured = capsys.readouterr()
    assert "Phase voting of Node 1 sends RPC VoteRequest to Phase voting of Node 2" in captured.out
    assert "Phase voting of Node 1 sends RPC VoteRequest to Phase voting of Node 3" in captured.out


# ---------------------------------------------------------------------------
# Test 7: transaction ID increments monotonically
# ---------------------------------------------------------------------------


def test_transaction_id_increments():
    """next_transaction_id returns distinct, increasing IDs on each call."""
    from server import next_transaction_id

    ids = [next_transaction_id() for _ in range(5)]
    assert ids == sorted(ids)
    assert len(set(ids)) == 5


# ---------------------------------------------------------------------------
# Test 8: intra-node ReportVote returns acknowledged=True
# ---------------------------------------------------------------------------


def test_intra_node_report_vote_ack(intra_servicer):
    """IntraNodePhaseServicer.ReportVote acknowledges the call."""
    req = twopc_pb2.IntraVoteReport(transaction_id=1, vote_commit=True)
    resp = intra_servicer.ReportVote(req, _mock_ctx())
    assert resp.acknowledged is True


# ---------------------------------------------------------------------------
# Test 9: coordinator calls VoteRequest on every peer
# ---------------------------------------------------------------------------


def test_coordinator_calls_all_peers(monkeypatch):
    """run_voting_phase issues exactly one VoteRequest call per peer."""
    import server as srv

    mock_vote_resp = twopc_pb2.VoteResponse(participant_id=2, transaction_id=1, vote_commit=True)
    mock_stub = MagicMock()
    mock_stub.VoteRequest.return_value = mock_vote_resp

    mock_intra_stub = MagicMock()
    mock_intra_stub.ReportVote.return_value = twopc_pb2.IntraVoteAck(acknowledged=True)

    with patch("grpc.insecure_channel"):
        with patch.object(twopc_grpc, "TwoPhaseCommitServiceStub", return_value=mock_stub):
            with patch.object(
                twopc_grpc, "IntraNodePhaseServiceStub", return_value=mock_intra_stub
            ):
                votes = srv.run_voting_phase("alice:pw", 1.0, 2.0, 1)

    # PEERS_STR is set to "fishing2:50052,fishing3:50053" in the fixture → 2 peers
    assert mock_stub.VoteRequest.call_count == 2
    assert len(votes) == 2


# ---------------------------------------------------------------------------
# Test 10: peer_node_id extraction
# ---------------------------------------------------------------------------


def test_peer_node_id_extraction():
    """peer_node_id correctly extracts numeric ID from 'fishingN:PORT' addresses."""
    from server import peer_node_id

    assert peer_node_id("fishing1:50051") == 1
    assert peer_node_id("fishing3:50053") == 3
    assert peer_node_id("fishing6:50056") == 6
