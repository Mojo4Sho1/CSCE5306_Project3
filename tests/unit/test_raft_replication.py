"""
Unit tests for Q4 — Raft log replication.

Tests cover:
- append_log_entry: index assignment, ack_tracker initialisation, Event creation
- _record_ack: majority commit, event signalling, apply_fn invocation
- wait_for_commit: returns True on commit, False on timeout
- get_leader_address: maps leader_id to peer address
- AppendEntries handler (follower): log replacement, committed entry execution
- ForwardRequest handler: log format, leader processes directly, non-leader forwards
- _parse_operation / _execute_operation helpers

No Docker required. All tests run via: make test
"""

import threading
from unittest.mock import MagicMock

# server/ is on sys.path via conftest.py
import raft_pb2
from raft_node import LogEntry, RaftNode, RaftServicer, _parse_operation


def _mock_ctx():
    return MagicMock()


def _node(node_id=1, peers=None):
    """Create a RaftNode with background threads disabled."""
    if peers is None:
        peers = ["fishing2:50052", "fishing3:50053", "fishing4:50054",
                 "fishing5:50055", "fishing6:50056"]
    return RaftNode(node_id, peers, _start_threads=False)


def _leader_node(node_id=1, peers=None):
    """Create a RaftNode in leader role."""
    node = _node(node_id, peers)
    node.role = "leader"
    node.leader_id = node_id
    node.current_term = 1
    return node


# ---------------------------------------------------------------------------
# Test 1: append_log_entry increments index correctly
# ---------------------------------------------------------------------------


def test_append_log_entry_increments_index():
    """Two successive appends produce indices 1 and 2."""
    node = _leader_node()
    with node._lock:
        idx1 = node.append_log_entry("UpdateLocation:user1:1.0:2.0")
        idx2 = node.append_log_entry("UpdateLocation:user2:3.0:4.0")
    assert idx1 == 1
    assert idx2 == 2
    assert len(node.log) == 2
    assert node.log[0].index == 1
    assert node.log[1].index == 2


# ---------------------------------------------------------------------------
# Test 2: append_log_entry sets ack_tracker with self-ACK
# ---------------------------------------------------------------------------


def test_append_log_entry_initialises_ack_tracker():
    """New log entry's ack_tracker starts with just the leader's own node_id."""
    node = _leader_node(node_id=1)
    with node._lock:
        idx = node.append_log_entry("UpdateLocation:u:0.0:0.0")
    assert idx in node.ack_tracker
    assert node.ack_tracker[idx] == {1}


# ---------------------------------------------------------------------------
# Test 3: append_log_entry creates a threading.Event
# ---------------------------------------------------------------------------


def test_append_log_entry_creates_pending_event():
    """append_log_entry creates a threading.Event in pending_clients."""
    node = _leader_node()
    with node._lock:
        idx = node.append_log_entry("UpdateLocation:u:0.0:0.0")
    assert idx in node.pending_clients
    assert isinstance(node.pending_clients[idx], threading.Event)


# ---------------------------------------------------------------------------
# Test 4: wait_for_commit returns True when event is already set
# ---------------------------------------------------------------------------


def test_wait_for_commit_true_when_committed():
    """wait_for_commit returns True immediately when the entry's event is set."""
    node = _leader_node()
    with node._lock:
        idx = node.append_log_entry("UpdateLocation:u:1.0:2.0")
    node.pending_clients[idx].set()  # simulate commit
    assert node.wait_for_commit(idx) is True


# ---------------------------------------------------------------------------
# Test 5: wait_for_commit returns False on timeout
# ---------------------------------------------------------------------------


def test_wait_for_commit_false_on_timeout():
    """wait_for_commit returns False when event is never set within timeout."""
    node = _leader_node()
    with node._lock:
        idx = node.append_log_entry("UpdateLocation:u:1.0:2.0")
    result = node.wait_for_commit(idx, timeout=0.05)
    assert result is False


# ---------------------------------------------------------------------------
# Test 6: _record_ack commits entry when majority reached
# ---------------------------------------------------------------------------


def test_record_ack_commits_on_majority():
    """_record_ack commits and signals the event when majority ACKs received."""
    # 6 nodes total (1 leader + 5 peers) → majority = 4
    node = _leader_node(node_id=1)
    apply_calls = []
    node._apply_fn = lambda jwt, x, y: apply_calls.append((jwt, x, y))

    with node._lock:
        idx = node.append_log_entry("UpdateLocation:alice:10.0:20.0")
        # Add ACKs from 3 more followers → total 4 (majority of 6)
        node._record_ack(2)
        node._record_ack(3)
        node._record_ack(4)

    assert node.commit_index == idx
    assert node.last_applied == idx
    assert node.pending_clients.get(idx) is None  # cleaned up
    assert apply_calls == [("alice", 10.0, 20.0)]


# ---------------------------------------------------------------------------
# Test 7: _record_ack does not commit before majority
# ---------------------------------------------------------------------------


def test_record_ack_no_commit_before_majority():
    """_record_ack does not commit an entry until majority is reached."""
    # 6 nodes total → need 4 ACKs (leader + 3 followers)
    node = _leader_node(node_id=1)
    apply_calls = []
    node._apply_fn = lambda jwt, x, y: apply_calls.append((jwt, x, y))

    with node._lock:
        node.append_log_entry("UpdateLocation:bob:5.0:6.0")
        node._record_ack(2)  # only 2 ACKs total (leader + follower 2)
        node._record_ack(3)  # only 3 ACKs total

    assert node.commit_index == 0  # not committed yet
    assert apply_calls == []


# ---------------------------------------------------------------------------
# Test 8: AppendEntries follower replaces its log
# ---------------------------------------------------------------------------


def test_follower_replaces_log_on_append_entries():
    """Follower's AppendEntries handler replaces its entire log with received entries."""
    node = _node(node_id=2)
    node.current_term = 1
    node.log = [LogEntry("UpdateLocation:old:0.0:0.0", term=0, index=1)]
    servicer = RaftServicer(node)

    new_entries = [
        raft_pb2.LogEntry(operation="UpdateLocation:new1:1.0:2.0", term=1, index=1),
        raft_pb2.LogEntry(operation="UpdateLocation:new2:3.0:4.0", term=1, index=2),
    ]
    req = raft_pb2.AppendEntriesRequest(
        term=1, leader_id=1, entries=new_entries, commit_index=0
    )
    resp = servicer.AppendEntries(req, _mock_ctx())

    assert resp.success is True
    assert len(node.log) == 2
    assert node.log[0].operation == "UpdateLocation:new1:1.0:2.0"
    assert node.log[1].operation == "UpdateLocation:new2:3.0:4.0"


# ---------------------------------------------------------------------------
# Test 9: AppendEntries follower executes committed entries via apply_fn
# ---------------------------------------------------------------------------


def test_follower_applies_committed_entries():
    """Follower applies entries with index <= commit_index via apply_fn."""
    node = _node(node_id=3)
    node.current_term = 1
    apply_calls = []

    servicer = RaftServicer(node, apply_fn=lambda jwt, x, y: apply_calls.append((jwt, x, y)))

    entries = [
        raft_pb2.LogEntry(operation="UpdateLocation:user1:1.0:2.0", term=1, index=1),
        raft_pb2.LogEntry(operation="UpdateLocation:user2:3.0:4.0", term=1, index=2),
        raft_pb2.LogEntry(operation="UpdateLocation:user3:5.0:6.0", term=1, index=3),
    ]
    # commit_index=2 → entries 1 and 2 should be executed; entry 3 should not
    req = raft_pb2.AppendEntriesRequest(
        term=1, leader_id=1, entries=entries, commit_index=2
    )
    servicer.AppendEntries(req, _mock_ctx())

    assert ("user1", 1.0, 2.0) in apply_calls
    assert ("user2", 3.0, 4.0) in apply_calls
    assert ("user3", 5.0, 6.0) not in apply_calls
    assert node.last_applied == 2
    assert node.commit_index == 2


# ---------------------------------------------------------------------------
# Test 10: get_leader_address returns correct peer address
# ---------------------------------------------------------------------------


def test_get_leader_address_returns_peer_for_leader_id():
    """get_leader_address returns the peer address matching the current leader_id."""
    peers = ["fishing2:50052", "fishing3:50053"]
    node = _node(node_id=1, peers=peers)
    with node._lock:
        node.leader_id = 3
        addr = node.get_leader_address()
    assert addr == "fishing3:50053"


def test_get_leader_address_returns_none_when_no_leader():
    """get_leader_address returns None when leader_id is None."""
    node = _node()
    with node._lock:
        addr = node.get_leader_address()
    assert addr is None


# ---------------------------------------------------------------------------
# Test 11: ForwardRequest receiver log format on leader
# ---------------------------------------------------------------------------


def test_forward_request_receiver_log_format_on_leader(capsys):
    """RaftServicer.ForwardRequest logs required receiver-side format when called on leader."""
    node = _leader_node(node_id=1)
    servicer = RaftServicer(node)

    req = raft_pb2.ForwardRequestMessage(user_jwt="tok", x=1.0, y=2.0, sender_id=3)
    servicer.ForwardRequest(req, _mock_ctx())

    captured = capsys.readouterr()
    assert "Node 1 runs RPC ForwardRequest called by Node 3" in captured.out


# ---------------------------------------------------------------------------
# Test 12: ForwardRequest on leader appends log entry and waits for commit
# ---------------------------------------------------------------------------


def test_forward_request_on_leader_appends_and_commits(capsys):
    """ForwardRequest on a leader node appends the entry and returns success after commit."""
    node = _leader_node(node_id=1)
    apply_calls = []
    node._apply_fn = lambda jwt, x, y: apply_calls.append((jwt, x, y))

    # Pre-set the event so wait_for_commit returns immediately
    _events = {}
    original_append = node.append_log_entry

    def patched_append(op):
        idx = original_append(op)
        node.pending_clients[idx].set()  # simulate instant commit
        return idx

    node.append_log_entry = patched_append

    servicer = RaftServicer(node)
    req = raft_pb2.ForwardRequestMessage(user_jwt="alice", x=5.0, y=7.0, sender_id=2)
    resp = servicer.ForwardRequest(req, _mock_ctx())

    assert resp.success is True
    assert len(node.log) == 1
    assert "UpdateLocation:alice:5.0:7.0" in node.log[0].operation


# ---------------------------------------------------------------------------
# Test 13: _parse_operation parses valid operation string
# ---------------------------------------------------------------------------


def test_parse_operation_valid():
    """_parse_operation correctly parses a valid UpdateLocation string."""
    result = _parse_operation("UpdateLocation:myuser:3.5:7.2")
    assert result == ("myuser", 3.5, 7.2)


def test_parse_operation_invalid_returns_none():
    """_parse_operation returns None for malformed operation strings."""
    assert _parse_operation("InvalidOp:x:1:2") is None
    assert _parse_operation("UpdateLocation:only_three") is None
    assert _parse_operation("UpdateLocation:user:notfloat:1.0") is None
