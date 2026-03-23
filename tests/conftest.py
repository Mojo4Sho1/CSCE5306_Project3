"""
Shared pytest fixtures for CSCE5306 Project 3.

sys.path note: server/server.py uses bare imports (import fishing_pb2) with no
package prefix — they work when running from inside server/ but fail from repo
root. We insert server/ at the front of sys.path here, before any test module
is collected, so all bare imports resolve correctly throughout the test suite.
"""
import os
import sys
from unittest.mock import MagicMock

import pytest

# Make server/ importable with bare names (fishing_pb2, fishing_pb2_grpc)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))


@pytest.fixture()
def fresh_state():
    """
    Return a clean, isolated ServerState instance.

    Imports are deferred into the fixture body so that the grpcio version check
    in fishing_pb2_grpc.py fires at test execution time (not collection time),
    giving a cleaner error message when grpcio < 1.76.0 is installed.
    """
    from server import ServerState  # noqa: PLC0415

    return ServerState()


@pytest.fixture()
def servicer(fresh_state, monkeypatch):
    """
    Return a FishingService instance backed by an isolated ServerState.

    monkeypatch replaces the module-level `state` singleton in server.py with
    `fresh_state` for the duration of this test, then restores it automatically.

    When a test requests both `servicer` and `fresh_state`, pytest injects the
    same fresh_state object into both (function-scope deduplication), so the
    test's reference and the patched module attribute point to the same object.
    """
    import server as server_module  # noqa: PLC0415
    from server import FishingService  # noqa: PLC0415

    monkeypatch.setattr(server_module, "state", fresh_state)
    return FishingService()


def mock_context() -> MagicMock:
    """Return a minimal mock gRPC ServicerContext."""
    ctx = MagicMock()
    ctx.add_callback = MagicMock()
    return ctx
