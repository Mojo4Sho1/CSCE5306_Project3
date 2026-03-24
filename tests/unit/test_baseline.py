"""
Baseline unit tests for server/server.py (forked code verification).

These 6 tests confirm the forked baseline works correctly at the exact points
that 2PC and Raft will build on top of. They are intentionally narrow — we are
not exhaustively auditing someone else's code, just gaining confidence in the
foundation before we extend it.

No Docker required. All tests run via: make test

Import note: conftest.py inserts server/ into sys.path, so fishing_pb2 and
other server/ modules are importable directly (not via `from server import ...`).
"""

import fishing_pb2 as pb
import pytest
from google.protobuf import empty_pb2

from tests.conftest import mock_context

# ---------------------------------------------------------------------------
# Test 1: Login token format
# The jwt produced by Login is used as the key in ALL state dicts.
# If the format is wrong, every downstream RPC breaks.
# ---------------------------------------------------------------------------


def test_login_token_format(servicer):
    """Login returns 'username:password' — the jwt format all other RPCs depend on."""
    resp = servicer.Login(pb.LoginRequest(username="alice", password="secret"), mock_context())
    assert resp.token == "alice:secret"


# ---------------------------------------------------------------------------
# Test 2: add_user and current_user_count
# The 2PC coordinator needs to know the cluster's live user count (it drives
# fish-catch probability and will be part of the replicated state).
# ---------------------------------------------------------------------------


def test_add_user_and_count(fresh_state):
    """add_user stores a user; current_user_count reflects it correctly."""
    assert fresh_state.current_user_count() == 0

    added = fresh_state.add_user("alice:secret")
    assert added is True
    assert fresh_state.current_user_count() == 1

    # Duplicate jwt should be rejected
    added_again = fresh_state.add_user("alice:secret")
    assert added_again is False
    assert fresh_state.current_user_count() == 1


# ---------------------------------------------------------------------------
# Test 3: UpdateLocation stores coordinates
# UpdateLocation is the RPC that 2PC will be replicating.
# Verifying the state is actually mutated correctly is the core foundation check.
# ---------------------------------------------------------------------------


def test_update_location_stores_coords(servicer, fresh_state):
    """UpdateLocation stream persists x/y coordinates into ServerState."""
    requests = iter(
        [
            pb.UpdateLocationRequest(jwt="alice:secret", x=3.5, y=7.2),
            pb.UpdateLocationRequest(jwt="alice:secret", x=10.0, y=20.0),
        ]
    )
    resp = servicer.UpdateLocation(requests, mock_context())

    assert resp.success is True
    users = fresh_state.get_user_snapshot()
    assert len(users) == 1
    assert users[0].x == pytest.approx(10.0)  # last update wins
    assert users[0].y == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# Test 4: remove_user clears both users and inventory
# 2PC abort path must be able to roll back a committed UpdateLocation —
# confirming remove_user is a clean teardown is a prerequisite.
# ---------------------------------------------------------------------------


def test_remove_user_clears_state(fresh_state):
    """Removing a user clears both the user record and their inventory slot."""
    fresh_state.add_user("bob:pw")
    fish = pb.Fish(fish_id=42, fish_dna="DNA42", fish_level=3)
    fresh_state.add_fish_to_user("bob:pw", fish)

    assert fresh_state.current_user_count() == 1

    fresh_state.remove_user("bob:pw")

    assert fresh_state.current_user_count() == 0
    assert fresh_state.get_user_snapshot() == []
    assert fresh_state.get_all_fishes() == []


# ---------------------------------------------------------------------------
# Test 5: ListUsers returns the current snapshot
# Raft log replication will need to verify that all nodes converge on the
# same user list; confirming ListUsers works correctly is part of that foundation.
# ---------------------------------------------------------------------------


def test_list_users_returns_snapshot(servicer, fresh_state):
    """ListUsers yields all registered users without error."""
    # Empty cluster
    results = list(servicer.ListUsers(empty_pb2.Empty(), mock_context()))
    assert results == []

    # Add two users directly to state (bypassing Login/UpdateLocation stream)
    fresh_state.add_user("alice:secret")
    fresh_state.add_user("bob:pw")

    results = list(servicer.ListUsers(empty_pb2.Empty(), mock_context()))
    assert len(results) == 2


# ---------------------------------------------------------------------------
# Test 6: Inventory returns fish across all users
# The Inventory RPC aggregates state from all users — a simple but important
# read path that future Raft reads will need to be consistent with.
# ---------------------------------------------------------------------------


def test_inventory_returns_all_fish(servicer, fresh_state):
    """Fish added to state are returned by the Inventory RPC."""
    fresh_state.add_user("alice:secret")
    fresh_state.add_user("bob:pw")
    fresh_state.add_fish_to_user("alice:secret", pb.Fish(fish_id=1, fish_dna="A", fish_level=1))
    fresh_state.add_fish_to_user("bob:pw", pb.Fish(fish_id=2, fish_dna="B", fish_level=2))

    resp = servicer.Inventory(pb.InventoryRequest(), mock_context())
    fish_ids = {f.fish_id for f in resp.fish}
    assert fish_ids == {1, 2}
