# Next Task
**Last updated:** 2026-03-23
**Owner:** Joe

## Task summary

Implement the 2PC voting phase (Q1): create `server/2pc.proto`, generate Python stubs, add coordinator `VoteRequest` logic, add participant `VoteResponse` logic, wire intra-node gRPC, update Docker environment variables, and print required RPC log messages.

**Task queue reference:** q1-2pc-voting (see `docs/handoff/TASK_QUEUE.md`)

## Why this task is next

- Seed bootstrap is complete — all planning docs, specs, and baseline code are in place.
- No implementation has started. Q1 is the first implementation milestone.
- All decisions are locked (scope, proto organization, node topology).

Long-horizon references:
- `docs/handoff/OVERVIEW_CHECKLIST.md` (phase A–G status)
- `docs/handoff/TASK_QUEUE.md` (full milestone queue Q1→Q5→delivery)

## Recommended task order

1. **Create `server/2pc.proto`** — define `TwoPhaseCommitService` (VoteRequest, GlobalDecision) and `IntraNodePhaseService` (ReportVote, NotifyDecision) with all messages from spec.
2. **Generate Python stubs** — run `make proto` (or `cd server && python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. 2pc.proto`). Verify `2pc_pb2.py` and `2pc_pb2_grpc.py` are produced.
3. **Update `server/dockerfile`** — ensure `grpcio-tools` is installed so stubs can be regenerated in-container if needed (or pre-generate and COPY them in).
4. **Update `server/docker-compose.yml`** — add `NODE_ID`, `PEERS`, and `IS_COORDINATOR` env vars to each service. `fishing1` is the permanent coordinator.
5. **Implement coordinator voting logic in `server/server.py`** — when `UpdateLocation` arrives at the coordinator, create a transaction ID, send `VoteRequest` to all peers via gRPC, collect `VoteResponse` replies.
6. **Implement participant voting logic in `server/server.py`** — handle incoming `VoteRequest`, apply voting rule (vote-commit unless coordinates are negative), return `VoteResponse`.
7. **Implement intra-node gRPC** — register `IntraNodePhaseService` on the same server; coordinator's voting phase calls `ReportVote` on localhost to pass its vote to the decision phase handler.
8. **Add required RPC log messages** — both client-side (sender) and server-side (receiver) formats exactly as specified in the spec.
9. **Write/extend unit tests** — add tests in `tests/unit/` covering coordinator vote collection, participant vote logic, and log format. No Docker required.
10. **Run `make check`** — lint + unit tests must pass before proceeding to validation.
11. **Validate with Docker** — run `docker compose -f server/docker-compose.yml up --build`, confirm 5+ containers start and coordinator runs VoteRequest flow on an UpdateLocation call.
12. **Mandatory final subtask** — see below.

Steps 5 and 6 can be developed in parallel once the proto stubs exist.

## Scope (in)

- `server/2pc.proto` with `TwoPhaseCommitService` and `IntraNodePhaseService`
- Generated stubs (`2pc_pb2.py`, `2pc_pb2_grpc.py`) committed to repo
- Coordinator: sends `VoteRequest` to all participants, collects `VoteResponse`
- Participants: receive `VoteRequest`, return `VoteResponse` (vote-commit or vote-abort)
- Intra-node gRPC: `IntraNodePhaseService.ReportVote` wired on localhost
- Docker env vars: `NODE_ID`, `PEERS`, `IS_COORDINATOR` on all services
- Required RPC log messages in assignment format (both sender and receiver sides)
- Unit tests for coordinator logic, participant logic, and log format
- `make proto` target regenerates stubs cleanly

## Scope (out)

- **Decision phase (Q2)**: `GlobalDecision` RPC, apply/discard logic, `IntraNodePhaseService.NotifyDecision` — that is Q2's work.
- Raft (Q3, Q4) — not this milestone.
- Failure tests (Q5) — not this milestone.
- Smoke/integration tests requiring a live Docker cluster — useful but not blocking for Q1 acceptance.

## Dependencies / prerequisites

- Quick orientation: `AGENTS.md` (read first), `docs/handoff/CURRENT_STATUS.md`
- Environment setup: `requirements-dev.txt`, `Makefile`
- Specs (read only what's needed):
  - `docs/spec/03_2pc_contract.md` — complete 2PC spec including proto sketch, log formats, voting rules, intra-node approach
  - `docs/spec/02_extension_scope.md` — locked scope (UpdateLocation as integration surface)
- Baseline code to modify: `server/server.py`, `server/docker-compose.yml`, `server/dockerfile`
- No outputs required from a prior phase — this is the first implementation task.

## Implementation notes

- **Node 1 (`fishing1`, port 50051) is the permanent coordinator.** Set `IS_COORDINATOR=true` only on `fishing1`.
- **PEERS format**: Pass comma-separated host:port strings, e.g. `PEERS=fishing2:50051,fishing3:50051,fishing4:50051,fishing5:50051,fishing6:50051`. The coordinator reads this list to know which peers to contact.
- **Stub naming**: `grpc_tools.protoc` on a file named `2pc.proto` may produce stubs with the module name `twopc` (from the `package` declaration) or a prefix derived from the filename. Check the generated file and adjust imports accordingly.
- **Intra-node gRPC**: Register `IntraNodePhaseService` on the same gRPC server as `TwoPhaseCommitService`. Call it via `localhost:<port>` to satisfy the assignment's requirement for gRPC between phases.
- **Log format** (must match exactly — see `docs/spec/03_2pc_contract.md`):
  - Sender: `Phase voting of Node 1 sends RPC VoteRequest to Phase voting of Node 2`
  - Receiver: `Phase voting of Node 2 sends RPC VoteRequest to Phase voting of Node 1`
- **Voting rule**: Participants vote-commit by default; vote-abort if `x < 0 or y < 0` (demonstrates abort path).
- Run `make check` (lint + unit tests) after every significant code change.
- The decision phase (`GlobalDecision`) is intentionally deferred to Q2 — do not implement it here.

## Acceptance criteria (definition of done)

- [ ] `server/2pc.proto` exists with `TwoPhaseCommitService` and `IntraNodePhaseService` and all required messages
- [ ] Generated stubs (`2pc_pb2.py`, `2pc_pb2_grpc.py`) committed and importable
- [ ] Coordinator sends `VoteRequest` to all participants and collects responses
- [ ] Participants receive `VoteRequest` and return `VoteResponse` with correct vote logic
- [ ] Intra-node gRPC (`IntraNodePhaseService.ReportVote`) works on localhost
- [ ] RPC log messages match required format (both sender and receiver sides)
- [ ] `NODE_ID`, `PEERS`, `IS_COORDINATOR` env vars present in `docker-compose.yml`
- [ ] All unit tests pass (`make test`)
- [ ] `make check` passes (lint + unit tests)
- [ ] 5+ Docker containers start and coordinator runs VoteRequest flow on `UpdateLocation`
- [ ] Handoff docs updated (see mandatory final subtask below)

## Verification checklist

- [ ] `make proto` completes without errors
- [ ] `make check` passes
- [ ] `docker compose -f server/docker-compose.yml config` validates
- [ ] `docker compose -f server/docker-compose.yml up --build` starts 5+ containers
- [ ] Sending an `UpdateLocation` RPC to Node 1 produces VoteRequest log lines for Nodes 2–6
- [ ] Sending an `UpdateLocation` with negative coordinates produces vote-abort in participant logs
- [ ] No unresolved placeholder text in new code or docs

## Mandatory final subtask: Update handoff documentation

**Complete this last, after all code is written and all tests pass.**

Using `docs/handoff/NEXT_TASK_TEMPLATE.md` as a guide, update the following before closing this batch:

- [ ] Mark `q1-2pc-voting` as `done` in `docs/handoff/TASK_QUEUE.md`
- [ ] Update Phase B status to `DONE` in `docs/handoff/OVERVIEW_CHECKLIST.md` and tick exit criteria
- [ ] Rewrite `docs/handoff/CURRENT_STATUS.md`:
  - What was completed (concrete, verifiable — list files created/modified)
  - Checks run and their outcomes (`make check`, docker validation)
  - Any remaining blockers or caveats
- [ ] Update `docs/handoff/BLOCKERS.md`: mark any blockers resolved this session; add any new unresolved blockers that need Joe's input
- [ ] Rewrite `docs/handoff/NEXT_TASK.md` to brief the next agent on **Q2 (2PC decision phase)**, following `docs/handoff/NEXT_TASK_TEMPLATE.md`
  - Q2 subtasks: implement `GlobalDecision` coordinator logic, implement participant apply/discard, implement `IntraNodePhaseService.NotifyDecision`, add Q2 log messages, extend unit tests, end-to-end 2PC flow validation
  - Reference `docs/spec/03_2pc_contract.md` (same spec, decision-phase sections)

The next `NEXT_TASK.md` must itself include this same "Mandatory final subtask" section so the pattern propagates to every future agent.

## Risks / rollback notes

- **Stub naming collision**: `2pc.proto` filename may conflict with Python import rules (leading digit). If `import 2pc_pb2` fails, rename the generated files to `twopc_pb2.py` / `twopc_pb2_grpc.py` and update imports accordingly.
- **Intra-node port conflict**: If you run `IntraNodePhaseService` on a separate port within the container, ensure it doesn't clash with the main gRPC port (50051) or Docker host mappings. Recommended: use a single server hosting both services.
- **Docker networking**: Peer addresses use Docker service names (e.g., `fishing2:50051`), not `localhost`. Verify the compose network allows inter-service gRPC.
