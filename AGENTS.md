# AGENTS.md — Project Guide for AI Agents

## Project Summary

**Course**: CSCE 5306 Distributed Systems — Project 3
**Baseline**: Forked MMO fishing game — Python gRPC prototype with 6-node Docker cluster
**Goal**: Extend the baseline with simplified **Two-Phase Commit (2PC)** and **Raft** consensus algorithms

The assignment has 5 implementation questions (Q1-Q5). All use gRPC for communication and Docker for containerization. At least 5 containerized nodes must communicate.

## Architecture Overview

### Baseline (DO NOT MODIFY unless implementing a task that requires it)
- **Proto**: `fishing.proto` — defines `FishingService` with 7 RPCs (Login, UpdateLocation, ListUsers, StartFishing, CurrentUsers, Inventory, GetImage)
- **Server**: `server/server.py` — Python gRPC server with in-memory state (users dict, inventory). Each of 6 instances runs on ports 50051-50056
- **Client**: `client/client.py` — interactive Python gRPC client
- **Docker**: `server/docker-compose.yml` — 6 services (fishing1-fishing6), Python 3.11-slim
- **Generated stubs**: `*_pb2.py` and `*_pb2_grpc.py` in client/ and server/ — preserved from baseline
- **Alternate variant**: `servermono/` — single-container variant (6 processes via entrypoint.sh). Reference only; primary work uses `server/`

### Extension Surface
- **Chosen functionality**: Replicated player state updates via `UpdateLocation` RPC
- **Scope**: All 2PC and Raft consensus logic applies to location-update commands only
- **Rationale**: UpdateLocation is an existing mutation with visible state effects and natural commit/abort semantics

### New Components to Build
- **`2pc.proto`** — new proto file for 2PC service definitions (Q1, Q2)
- **`raft.proto`** — new proto file for Raft service definitions (Q3, Q4)
- **2PC coordinator/participant logic** — integrated into server nodes
- **Raft state machine** — follower/candidate/leader roles with election and log replication
- **Failure test harness** — 5 test cases exercising Raft fault tolerance (Q5)

## Key Locked Decisions

1. **Scope**: Replicated player state updates via UpdateLocation. No full game redesign.
2. **Proto organization**: Separate `2pc.proto` and `raft.proto` files. Do NOT modify existing `fishing.proto`.
3. **Intra-node gRPC for 2PC**: Voting phase and decision phase communicate via gRPC even within the same container (assignment requirement).
4. **Node count**: Use existing 6-node cluster topology (exceeds minimum 5).
5. **Language**: Python (same as baseline). Assignment allows any language but Python is simplest for extending the existing code.

## Implementation Task Order

| Task | Assignment Q | Description | Status |
|------|-------------|-------------|--------|
| Q1 | 2PC Voting Phase | Proto + coordinator sends vote-request, participants respond vote-commit/vote-abort | NOT STARTED |
| Q2 | 2PC Decision Phase | Coordinator sends global-commit/global-abort based on votes, intra-node gRPC between phases | NOT STARTED |
| Q3 | Raft Leader Election | Proto + follower/candidate/leader state machine, RequestVote RPC, heartbeat via AppendEntries | NOT STARTED |
| Q4 | Raft Log Replication | Log entries, full log sent on heartbeat, ACK majority, client forwarding to leader | NOT STARTED |
| Q5 | Failure Tests | 5 failure-related test cases with screenshots for report | NOT STARTED |

**Execute in order**: Q1 → Q2 → Q3 → Q4 → Q5. Each builds on the previous.

## File Layout

```
.
├── CLAUDE.md              # Claude Code auto-load pointer → this file
├── AGENTS.md              # THIS FILE — primary agent guide
├── SEED.md                # Bootstrap contract (COMPLETE — reference only)
├── README.md              # Project README (update at end with build/run instructions)
├── fishing.proto           # Baseline proto (DO NOT MODIFY)
├── fishing_test.js         # k6 load test (baseline reference)
├── client/                 # Python gRPC client (baseline)
│   ├── client.py
│   ├── fishing.proto       # Copy of baseline proto
│   ├── fishing_pb2.py      # Generated (preserved)
│   └── fishing_pb2_grpc.py # Generated (preserved)
├── server/                 # PRIMARY working directory for implementation
│   ├── server.py           # Main server — extend this with 2PC/Raft
│   ├── fishing.proto       # Copy of baseline proto
│   ├── fishing_pb2.py      # Generated (preserved)
│   ├── fishing_pb2_grpc.py # Generated (preserved)
│   ├── docker-compose.yml  # 6-node cluster — extend for 2PC/Raft
│   ├── dockerfile          # Container image — may need proto generation added
│   └── *.JPG               # Image assets per node
├── servermono/             # Alternate variant (reference only, don't extend)
└── docs/
    ├── _INDEX.md           # Documentation topic index
    ├── spec/
    │   ├── 00_assignment_project3.md   # Full assignment requirements (authoritative)
    │   ├── 01_repo_baseline_audit.md   # Audited baseline state
    │   ├── 02_extension_scope.md       # Locked scope definition
    │   ├── 03_2pc_contract.md          # 2PC implementation contract (Q1+Q2)
    │   ├── 04_raft_election_contract.md # Raft election contract (Q3)
    │   ├── 05_raft_log_replication_contract.md # Raft log replication contract (Q4)
    │   └── 06_failure_test_matrix.md   # 5 failure test cases (Q5)
    └── handoff/
        ├── CURRENT_STATUS.md
        ├── NEXT_TASK.md
        ├── TASK_QUEUE.md
        ├── DECISION_LOG.md
        ├── SPEC_CONFORMANCE_CHECKLIST.md
        └── OVERVIEW_CHECKLIST.md
```

## Build & Run Commands

```bash
# Start 6-node cluster
cd server && docker compose up --build

# Run client (from host, requires grpcio + protobuf)
cd client && python3 client.py

# Validate Docker config
docker compose -f server/docker-compose.yml config

# Compile-check Python
python -m py_compile server/server.py client/client.py

# Generate proto stubs (when adding new protos)
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. 2pc.proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto
```

## RPC Logging Formats (Assignment-Required)

### 2PC (Q1, Q2) — both client and server side print:
```
Phase <phase_name> of Node <node_id> sends RPC <rpc_name> to Phase <phase_name> of Node <node_id>
```
Where `phase_name` is `voting` or `decision`.

**Note**: The assignment uses the same "sends RPC" wording for both client and server side. This appears to be a typo in the server-side format, but we follow the assignment text literally.

### Raft (Q3, Q4) — client side:
```
Node <node_id> sends RPC <rpc_name> to Node <node_id>
```

### Raft (Q3, Q4) — server side:
```
Node <node_id> runs RPC <rpc_name> called by Node <node_id>
```

## Detailed Implementation Specs

For each task, read the corresponding spec doc before implementing:
- **Q1+Q2**: `docs/spec/03_2pc_contract.md` — proto sketches, coordinator/participant flows, intra-node gRPC
- **Q3**: `docs/spec/04_raft_election_contract.md` — state machine, timeouts, RequestVote flow
- **Q4**: `docs/spec/05_raft_log_replication_contract.md` — log structure, AppendEntries, client forwarding
- **Q5**: `docs/spec/06_failure_test_matrix.md` — 5 test scenarios with setup and expected behavior

## Deliverables Checklist

- [ ] Source code for 2PC (Q1+Q2)
- [ ] Source code for Raft (Q3+Q4)
- [ ] 5 failure test cases with screenshots (Q5)
- [ ] README with: build/run instructions, unusual notes, external sources, GitHub link
- [ ] Report with: team members, student IDs, work division, test screenshots, GitHub link

## Agent Session Startup

1. Read this file (AGENTS.md)
2. Check `docs/handoff/CURRENT_STATUS.md` for current phase and next task
3. Read the spec doc for your assigned task
4. Implement, test, update handoff docs when done
