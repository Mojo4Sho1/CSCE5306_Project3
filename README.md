# CSCE 5306 Project 3 — Distributed Consensus (2PC + Raft)

**GitHub:** <https://github.com/Mojo4Sho1/CSCE5306_Project3>

This project extends a baseline multiplayer fishing game (Python gRPC, 6-node
Docker cluster) with two distributed consensus algorithms:

- **Two-Phase Commit (2PC)** — coordinator-driven voting and decision phases
  for atomic location updates (Q1 + Q2).
- **Raft** — leader election with randomised timeouts and log replication with
  majority commit (Q3 + Q4).
- **Failure Tests** — five fault-tolerance scenarios exercising leader crash,
  follower crash, network partition, late startup of a preconfigured sixth
  node, and split-vote re-election (Q5).

The final written report is maintained separately in Overleaf and is
intentionally not versioned in this repository.

---

## Project Structure

```
.
├── client/                  # Interactive Python client
│   └── client.py
├── server/                  # 6-node cluster implementation
│   ├── server.py            # Main server (2PC + Raft + fishing service)
│   ├── raft_node.py         # Raft state machine and gRPC servicer
│   ├── fishing.proto        # Baseline fishing service (unmodified)
│   ├── twopc.proto          # 2PC gRPC service definitions
│   ├── raft.proto           # Raft gRPC service definitions
│   ├── docker-compose.yml   # 6-node Docker Compose cluster
│   └── Dockerfile
├── tests/
│   ├── unit/                # 55 unit tests (no Docker required)
│   └── smoke/               # Docker integration tests
├── Makefile                 # Build, test, and cluster management
└── AGENTS.md                # Full project context and architecture
```

---

## How to Compile and Run

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- GNU Make

### Quick Start

```bash
# Install Python dependencies
make install

# (Optional) Regenerate gRPC stubs from proto files
make proto

# Run unit tests (no Docker required) — 55 tests
make test

# Run the full quality gate
make check

# Start the 6-node Docker cluster
make up

# Run the interactive client (cluster must be running)
cd client && python3 client.py

# Stream logs from all nodes
make logs

# Tear down the cluster
make down
```

### Other Make Targets

| Target          | Description                              |
|-----------------|------------------------------------------|
| `make lint`     | Run ruff linter                          |
| `make format`   | Auto-format with ruff                    |
| `make check`    | Quality gate (lint + unit tests)         |
| `make proto-2pc`| Regenerate only 2PC stubs                |
| `make proto-raft`| Regenerate only Raft stubs              |
| `make test-smoke`| Run Docker integration tests            |

---

## Where To Look In The Demo

- `server/server.py`: main gRPC server, baseline `FishingService`, 2PC servicers,
  cluster wiring, and the `UpdateLocation` integration point.
- `server/raft_node.py`: Raft state machine, leader election, heartbeat loop,
  log replication, commit tracking, and the `RaftService` gRPC handlers.
- `server/twopc.proto`: 2PC RPC/message contract (`VoteRequest`,
  `GlobalDecision`, intra-node `ReportVote` / `NotifyDecision`).
- `server/raft.proto`: Raft RPC/message contract (`RequestVote`,
  `AppendEntries`, `ForwardRequest`, `LogEntry`).
- `tests/unit/test_2pc.py`: 2PC voting/decision behavior and abort-path tests.
- `tests/unit/test_raft.py`: election and timeout behavior tests.
- `tests/unit/test_raft_replication.py`: log replication, majority ACK, commit,
  and forwarding tests.

## What Changed From The Baseline

- Added `server/twopc.proto` plus generated 2PC stubs.
- Added `server/raft.proto` plus generated Raft stubs.
- Added `server/raft_node.py` for the Raft state machine and gRPC servicer.
- Extended `server/server.py` to host 2PC services, wire in Raft, and route
  `UpdateLocation` through the new consensus logic.
- Extended `server/docker-compose.yml` so all six nodes have explicit `NODE_ID`,
  `PEERS`, and unbuffered logging configuration.
- Added unit tests for 2PC, Raft election, and Raft replication behavior.

## Unusual Notes

- **Proto file naming:** The 2PC proto file is named `twopc.proto` (not
  `2pc.proto`). Python cannot import a module whose name starts with a digit;
  `grpc_tools.protoc` would generate `2pc_pb2.py`, which is an invalid Python
  identifier.

- **Docker log buffering:** All containers set `PYTHONUNBUFFERED=1` to prevent
  Python's default stdout buffering from suppressing log output in
  `docker logs`.

- **PEERS environment variable:** The `PEERS` variable must be set for *every*
  node, not only the coordinator. An initial misconfiguration left `PEERS=""`
  for nodes 2–6, causing each node to treat itself as a single-node cluster.

- **Simplified Raft log replication:** The Raft implementation sends the entire
  log on every heartbeat rather than incremental entries. Followers replace
  their log wholesale. This is a simplification from the full Raft protocol.

- **Unit test threading:** Tests pass `_start_threads=False` to `RaftNode` to
  suppress background election-timer and heartbeat threads; without this flag
  tests are flaky.

- **Report location:** The final report is maintained in Overleaf and is not
  included in this repository.

---

## External Sources

- Ongaro, D. and Ousterhout, J. (2014). *In Search of an Understandable
  Consensus Algorithm (Extended Version)*. USENIX ATC.
  <https://raft.github.io/raft.pdf>
- Gray, J. and Lamport, L. (2006). Consensus on Transaction Commit. *ACM
  Transactions on Database Systems*, 31(1):133–160.
- gRPC Python documentation: <https://grpc.io/docs/languages/python/>
- Protocol Buffers language guide (proto3):
  <https://protobuf.dev/programming-guides/proto3/>
