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

### Added Components
- **`twopc.proto`** — new proto file for 2PC service definitions (Q1, Q2)
- **`raft.proto`** — new proto file for Raft service definitions (Q3, Q4)
- **2PC coordinator/participant logic** — integrated into server nodes
- **Raft state machine** — follower/candidate/leader roles with election and log replication
- **Failure test harness** — 5 test cases exercising Raft fault tolerance (Q5)

## Key Locked Decisions

1. **Scope**: Replicated player state updates via UpdateLocation. No full game redesign.
2. **Proto organization**: Separate `twopc.proto` and `raft.proto` files. Do NOT modify existing `fishing.proto`.
3. **Intra-node gRPC for 2PC**: Voting phase and decision phase communicate via gRPC even within the same container (assignment requirement).
4. **Node count**: Use existing 6-node cluster topology (exceeds minimum 5).
5. **Language**: Python (same as baseline). Assignment allows any language but Python is simplest for extending the existing code.

## Implementation Task Order

| Task | Assignment Q | Description | Status |
|------|-------------|-------------|--------|
| Q1 | 2PC Voting Phase | Proto + coordinator sends vote-request, participants respond vote-commit/vote-abort | COMPLETE |
| Q2 | 2PC Decision Phase | Coordinator sends global-commit/global-abort based on votes, intra-node gRPC between phases | COMPLETE |
| Q3 | Raft Leader Election | Proto + follower/candidate/leader state machine, RequestVote RPC, heartbeat via AppendEntries | COMPLETE |
| Q4 | Raft Log Replication | Log entries, full log sent on heartbeat, ACK majority, client forwarding to leader | COMPLETE |
| Q5 | Failure Tests | 5 failure-related test cases with screenshots for report | COMPLETE |

**Execute in order**: Q1 → Q2 → Q3 → Q4 → Q5 → final deliverables. Each builds on the previous.

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
        ├── NEXT_TASK_TEMPLATE.md   # Template — use when rewriting NEXT_TASK.md
        ├── TASK_QUEUE.md
        ├── DECISION_LOG.md
        ├── SPEC_CONFORMANCE_CHECKLIST.md
        ├── OVERVIEW_CHECKLIST.md
        └── BLOCKERS.md             # Running log of open and resolved blockers
```

## Build & Run Commands

A `Makefile` at the repo root provides all common operations. **Always use `make` targets instead of typing raw commands.**

```bash
make install      # install dev dependencies (grpcio, pytest, ruff, etc.)
make check        # QUALITY GATE: lint + unit tests — run before marking any task complete
make test         # run unit tests only (no Docker needed)
make test-smoke   # run smoke tests (requires Docker cluster to be running)
make lint         # ruff linter on owned source files
make format       # ruff auto-formatter
make proto        # regenerate stubs from twopc.proto and raft.proto (Q1/Q3+)
make up           # docker compose up --build -d (6-node cluster)
make down         # docker compose down
make logs         # docker compose logs -f

# Run client interactively (requires cluster to be up)
cd client && python3 client.py
```

**Note on `make proto`:** Regenerates Python stubs from the checked-in `server/twopc.proto` and `server/raft.proto` files.

**Note on the report:** The final report is maintained in Overleaf and is intentionally not versioned in this repo.

**Note on `make typecheck`:** Not configured in this repo. `ruff` linting plus `pytest` are the active quality gates via `make check`.

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

- [x] Source code for 2PC (Q1+Q2)
- [x] Source code for Raft (Q3+Q4)
- [x] 5 failure test cases with screenshot evidence (maintained in the final report / Overleaf workflow)
- [x] README with: build/run instructions, unusual notes, external sources, GitHub link
- [x] Report with: team members, student IDs, work division, test screenshots, GitHub link (maintained outside the repo)

## Agent Working Rules

### Automation & Token Efficiency
- A `Makefile` already exists at the repo root. **Extend it** for new tasks rather than creating separate scripts.
- Never run long multi-step commands manually — add a `make` target and use it. Future agents (and you on the next run) will thank you.
- The common targets are already defined: `make test`, `make proto`, `make up`, `make down`, `make logs`, `make check`.

### Testing Requirements
- **`make check` is the quality gate.** Run it before marking any task complete. It runs lint + unit tests.
- **Write tests for every new module** — use `pytest`. Unit tests go in `tests/unit/`, smoke tests in `tests/smoke/`.
- After any Docker/compose change, also run `make test-smoke` to verify the live cluster still works.
- Unit tests should cover: state transitions, edge cases (vote-abort path, split vote, majority calculation, log index arithmetic).
- Smoke tests should verify: containers start, nodes communicate over gRPC, RPC log output matches the required format.
- If a test fails, fix the issue before moving on. Do not leave broken tests behind.
- **`make typecheck`** is not configured in this repo. Do not block on it; `make check` remains the active quality gate.

### Code Quality
- `make lint` (ruff) catches import errors, unused variables, and style issues — run it early and often.
- Validate Docker config with `docker compose config` after any compose file changes (or rely on `make up` which will surface errors).
- Keep the test/build infrastructure working at all times — a broken `make check` blocks all future agents.

## Known Gotchas (discovered during implementation — read before starting)

These were found the hard way. Do not repeat them.

**Agent responsibility:** If you discover a new gotcha while implementing your task, add it here before closing your session — same format as below. Future agents read this file first, so this is the highest-visibility place to leave a warning. Also log it in `docs/handoff/BLOCKERS.md` per the Blocker Handling Protocol below.

### Proto file cannot be named `2pc.proto`
Python cannot import a module whose name starts with a digit (`import 2pc_pb2` is a syntax error). The proto file is named **`twopc.proto`** and generates **`twopc_pb2.py`** / **`twopc_pb2_grpc.py`**. The spec originally said `2pc.proto` — that spec has been corrected. Do not rename the file.

### Docker logs empty without `PYTHONUNBUFFERED=1`
Python buffers stdout by default. In Docker without a TTY, `docker logs` will show nothing until the process exits. All services in `docker-compose.yml` set `PYTHONUNBUFFERED: "1"`. If you add a new service, include this env var or you will see no log output.

### RaftNode background threads must be suppressed in unit tests
`RaftNode.__init__` starts a daemon timer thread (and heartbeat thread when leader) that acquire the lock and fire RPCs. In unit tests, always pass `_start_threads=False` or tests will be flaky and `_become_leader` will spawn a live heartbeat thread. Example: `RaftNode(1, peers, _start_threads=False)`. This flag is already supported in `server/raft_node.py`.

---

## Blocker Handling Protocol

When you hit a blocker during implementation, follow the path below. All entries go in `docs/handoff/BLOCKERS.md` using the template format in that file.

### Blocker you CANNOT resolve on your own

1. Log it in `docs/handoff/BLOCKERS.md` under **Unresolved Blockers** — describe what went wrong, what you tried, and what guidance Joe needs to provide.
2. Continue with any remaining subtasks that do NOT depend on the blocked one.
3. At the **top of your response** (before any other output), flag it clearly:
   `BLOCKER (unresolved): <title> — details in docs/handoff/BLOCKERS.md`
4. When rewriting NEXT_TASK.md for the next agent, reference the open blocker so it isn't forgotten.

### Blocker you CAN resolve on your own

1. Fix it.
2. Log it in `docs/handoff/BLOCKERS.md` under **Resolved Blockers** — include root cause, exact solution, and a prevention tip for future agents.
3. If the fix is likely to apply in other projects (library quirk, Docker behavior, gRPC/protoc gotcha, Python packaging edge case, etc.), save it to this project's auto-memory as a `feedback`-type entry so it's loaded in future sessions.
4. At the **top of your response**, flag it:
   `BLOCKER RESOLVED: <title> — logged to BLOCKERS.md` (+ `+ auto-memory` if you wrote a memory entry)

### Cross-project propagation

This project's auto-memory is session-local to this repo. For knowledge to reach Joe's other projects, he needs to see it and decide whether to propagate it. **Flag anything broadly useful** — Joe will push relevant findings to `~/.claude/memory/` for other projects to pick up.

---

## Agent Session Startup

1. Read this file (AGENTS.md)
2. Check `docs/handoff/CURRENT_STATUS.md` for current phase and next task
3. Check `docs/handoff/BLOCKERS.md` for any open unresolved blockers — do not start work that depends on an open blocker without first notifying Joe
4. Read the spec doc for your assigned task
5. Implement, test (run full suite), update handoff docs when done
