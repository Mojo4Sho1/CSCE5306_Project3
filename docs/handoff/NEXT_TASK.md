# Next Task
**Last updated:** 2026-03-24
**Owner:** Joe

## Task summary

Implement Q3 (Raft leader election): create `raft.proto`, generate stubs, implement the follower/candidate/leader state machine in a new `raft_node.py` module, handle `RequestVote` and heartbeat `AppendEntries` RPCs, and register `RaftService` on the existing gRPC server.

**Task queue reference:** q3-raft-election (see `docs/handoff/TASK_QUEUE.md`)

## Why this task is next

- Q1 (2PC voting) and Q2 (2PC decision) are both COMPLETE — `twopc.proto`, all servicers, log formats, 26 unit tests, `make check` clean.
- Q3 builds on the existing Docker/env-var setup (NODE_ID, PEERS) from 2PC — no compose changes needed.

Long-horizon references:
- `docs/handoff/OVERVIEW_CHECKLIST.md` (phase A–G status)
- `docs/handoff/TASK_QUEUE.md` (full milestone queue)

## Recommended task order

1. **Create `server/raft.proto`** — copy the proto definition from `docs/spec/04_raft_election_contract.md` exactly (do not modify it).
2. **Generate stubs** — `cd server && python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto` → produces `raft_pb2.py` / `raft_pb2_grpc.py`. Add a `proto-raft` target to `Makefile`.
3. **Create `server/raft_node.py`** — implement `RaftNode` class (state machine) and `RaftServicer` (gRPC handler). Use the spec's `RaftNode.__init__` skeleton as the starting point.
4. **Implement election timeout monitor** — background thread that promotes follower → candidate when no heartbeat received within `election_timeout` seconds (random [1.5, 3.0]).
5. **Implement RequestVote handler** — vote logic per spec (term comparison, voted_for check). Log required format on both sender and receiver sides.
6. **Implement AppendEntries handler (heartbeat)** — accept/reset timer on valid leader; entries is empty in Q3 (log replication is Q4). Log required format.
7. **Implement heartbeat sender** — leader background thread sends AppendEntries to all peers every 1 second.
8. **Wire into `server/server.py`** — import `raft_node`, instantiate `RaftNode`, register `RaftService`, start timer and heartbeat threads in `serve()`.
9. **Add unit tests** — in `tests/unit/test_raft.py`: follower initial state, election timeout triggers candidacy, vote-grant/reject logic, majority-vote → leader, heartbeat resets timer, higher-term causes step-down. Minimum 8 tests.
10. **Run `make check`** — lint + all tests must pass.
11. **Validate with Docker** — `docker compose up --build`; confirm leader elected and heartbeat log lines appear.
12. **Mandatory final subtask** — update handoff docs (see below).

Steps 3–7 can be developed mostly in parallel; step 8 depends on 3–7.

## Scope (in)

- `server/raft.proto` with `RequestVote` and `AppendEntries` RPCs
- Generated stubs `raft_pb2.py` / `raft_pb2_grpc.py`
- `server/raft_node.py` — `RaftNode` class and `RaftServicer`
- Follower/candidate/leader state machine with election timeout [1.5s, 3.0s] and heartbeat interval 1s
- `RequestVote` RPC (election flow) and `AppendEntries` RPC (heartbeat only — no log entries)
- RPC log messages in required format (sender and receiver)
- `Makefile` `proto-raft` target
- Unit tests (`tests/unit/test_raft.py`) — minimum 8 tests, no Docker required
- `make check` passes

## Scope (out)

- Log replication (Q4) — `AppendEntries` carries no entries in Q3
- Client forwarding to leader (Q4)
- Failure tests (Q5)
- Re-implementing 2PC — all Q1+Q2 code stays; Raft runs alongside it

## Dependencies / prerequisites

- Quick orientation: `AGENTS.md` (read first), `docs/handoff/CURRENT_STATUS.md`
- Environment setup: `requirements-dev.txt`, `Makefile`
- Specs (read only what's needed):
  - `docs/spec/04_raft_election_contract.md` — full Q3 spec (proto, state machine, timeouts, log format)
- Inputs from prior phase: `server/server.py` (existing `serve()` function and env config), `server/docker-compose.yml` (NODE_ID, PEERS already set)

## Implementation notes

- **New module `raft_node.py`**: keep Raft logic out of `server.py`. Import and wire in `serve()`.
- **Thread safety**: use `threading.Lock` on all shared Raft state (term, role, voted_for, last_heartbeat_time).
- **Election timer thread**: check `time.time() - self.last_heartbeat_time > self.election_timeout` in a loop with small sleep (0.1s). On timeout, call `self.start_election()`.
- **Heartbeat thread**: only runs when `self.role == "leader"`. Sleep 1s between rounds.
- **Log format** (must match exactly):
  - Sender: `Node <sender_id> sends RPC RequestVote to Node <receiver_id>`
  - Receiver: `Node <receiver_id> runs RPC RequestVote called by Node <sender_id>`
  - Same pattern for AppendEntries.
- **PEERS env var format**: same `fishing2:50052,...` as 2PC. Reuse `peer_node_id()` helper from `server.py`.
- Run `make check` after every significant code change.

## Acceptance criteria (definition of done)

- [ ] `server/raft.proto` exists with RequestVote and AppendEntries RPCs
- [ ] Generated stubs compile without errors
- [ ] All nodes start as followers
- [ ] Election timeout triggers candidate transition
- [ ] Candidate sends RequestVote and counts majority → becomes leader
- [ ] Leader sends heartbeats every 1 second
- [ ] Followers reset election timer on heartbeat receipt
- [ ] Higher-term messages cause step-down to follower
- [ ] All RPC calls produce the required log format
- [ ] All unit tests pass (`make test`)
- [ ] `make check` passes (lint + unit tests)
- [ ] 5+ containerized nodes elect a leader (Docker validation)
- [ ] Handoff docs updated (see mandatory final subtask below)

## Verification checklist

- [ ] `make check` passes
- [ ] `docker compose -f server/docker-compose.yml up --build` starts 5+ containers
- [ ] Leader election log lines appear within 3 seconds of cluster start
- [ ] Heartbeat `AppendEntries` log lines appear every ~1 second from leader
- [ ] No unresolved placeholder text in new code or docs

## Mandatory final subtask: Update handoff documentation

**Complete this last, after all code is written and all tests pass.**

Using `docs/handoff/NEXT_TASK_TEMPLATE.md` as a guide, update the following before closing this batch:

- [ ] Mark `q3-raft-election` as `done` in `docs/handoff/TASK_QUEUE.md`
- [ ] Update Phase D status to `DONE` in `docs/handoff/OVERVIEW_CHECKLIST.md` and tick exit criteria
- [ ] Rewrite `docs/handoff/CURRENT_STATUS.md`:
  - What was completed (concrete, verifiable — list files created/modified)
  - Checks run and their outcomes (`make check`, docker validation)
  - Any remaining blockers or caveats
- [ ] Update `docs/handoff/BLOCKERS.md`: mark any blockers resolved this session; add any new unresolved blockers that need Joe's input
- [ ] Rewrite `docs/handoff/NEXT_TASK.md` to brief the next agent on **Q4 (Raft log replication)**, following `docs/handoff/NEXT_TASK_TEMPLATE.md`
  - Q4 subtasks: extend AppendEntries with log entries, majority-ACK commit, client forwarding to leader
  - Reference `docs/spec/05_raft_log_replication_contract.md`

The next `NEXT_TASK.md` must itself include this same "Mandatory final subtask" section so the pattern propagates to every future agent.

## Risks / rollback notes

- **Election storm on startup**: all nodes start simultaneously with overlapping timeouts. The [1.5s, 3.0s] range should stagger elections enough, but if all pick similar timeouts a split vote can repeat. Re-randomize timeout on each new election to resolve.
- **gRPC channel reuse**: creating a new channel per RPC (as done in 2PC) is fine for correctness but slow. For Q3 heartbeats at 1s intervals it is acceptable — do not optimize unless timeouts occur.
- **Thread lifecycle**: the heartbeat thread must check `self.role == "leader"` on each iteration and exit (or idle) if the node steps down. A stale heartbeat sender running on a follower will cause term confusion.
