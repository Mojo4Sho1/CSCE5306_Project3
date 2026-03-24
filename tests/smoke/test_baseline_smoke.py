"""
Baseline smoke tests — require Docker.

These 4 tests confirm the 6-node cluster starts correctly and the core RPCs
work end-to-end over a live gRPC connection. Run with: make test-smoke

All tests are tagged @pytest.mark.smoke and are excluded from make test / make check.
"""

import os
import subprocess
import sys
import time

import grpc
import pytest

pytestmark = pytest.mark.smoke

COMPOSE_FILE = "server/docker-compose.yml"
PRIMARY_ADDR = "localhost:50051"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wait_for_grpc(address: str, timeout: int = 30) -> None:
    """Poll until a gRPC channel is ready or timeout expires."""
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            ch = grpc.insecure_channel(address)
            grpc.channel_ready_future(ch).result(timeout=2)
            ch.close()
            return
        except Exception as exc:
            last_exc = exc
            time.sleep(1)
    raise TimeoutError(f"{address} not reachable after {timeout}s. Last: {last_exc}")


# ---------------------------------------------------------------------------
# Session-scoped cluster fixture
# Starts Docker cluster once for all smoke tests; tears it down after.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=False)
def docker_cluster():
    result = subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "up", "--build", "-d"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        pytest.fail(f"docker compose up failed:\n{result.stderr}")

    _wait_for_grpc(PRIMARY_ADDR, timeout=30)
    yield

    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "down"],
        capture_output=True,
        timeout=60,
    )


@pytest.fixture(scope="session")
def stub(docker_cluster):
    """FishingServiceStub connected to the primary node (port 50051)."""
    # server/ must be on sys.path for fishing_pb2_grpc to import
    server_dir = os.path.join(os.path.dirname(__file__), "..", "..", "server")
    if server_dir not in sys.path:
        sys.path.insert(0, server_dir)

    import fishing_pb2_grpc as pb_grpc  # noqa: PLC0415

    channel = grpc.insecure_channel(PRIMARY_ADDR)
    s = pb_grpc.FishingServiceStub(channel)
    yield s
    channel.close()


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


def test_cluster_is_up(docker_cluster):
    """Primary port (50051) is reachable after docker compose up."""
    _wait_for_grpc(PRIMARY_ADDR, timeout=5)  # already up; just a quick confirm


def test_login_rpc_works(stub):
    """Login RPC returns the expected token format end-to-end over gRPC."""
    import fishing_pb2 as pb  # noqa: PLC0415

    resp = stub.Login(pb.LoginRequest(username="smokeuser", password="smokepass"))
    assert resp.token == "smokeuser:smokepass"


def test_update_location_rpc_works(stub):
    """UpdateLocation client-streaming RPC completes with success=True."""
    import fishing_pb2 as pb  # noqa: PLC0415

    jwt = "smokeuser:smokepass"
    requests = iter(
        [
            pb.UpdateLocationRequest(jwt=jwt, x=1.0, y=2.0),
            pb.UpdateLocationRequest(jwt=jwt, x=3.0, y=4.0),
        ]
    )
    resp = stub.UpdateLocation(requests)
    assert resp.success is True


def test_all_six_nodes_reachable(docker_cluster):
    """All 6 cluster nodes accept gRPC connections on ports 50051-50056."""
    for offset in range(6):
        addr = f"localhost:{50051 + offset}"
        try:
            _wait_for_grpc(addr, timeout=10)
        except TimeoutError:
            pytest.fail(f"Node at {addr} not reachable")
