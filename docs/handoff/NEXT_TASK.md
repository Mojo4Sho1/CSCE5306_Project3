# Next Task
**Last updated:** 2026-03-24
**Owner:** Joe

## Task summary

Implement the 2PC decision phase (Q2): coordinator collects votes and sends `GlobalDecision`, participants apply or discard the location update, `IntraNodePhaseService.NotifyDecision` wires decision → voting phase, and all required RPC log messages are printed.

**Task queue reference:** q2-2pc-decision (see `docs/handoff/TASK_QUEUE.md`)

## Why this task is next

- Q1 is complete — `twopc.proto`, stubs, coordinator `VoteRequest`, participant `VoteResponse`, intra-node `ReportVote`, and Docker env vars are all in place.
- Q2 builds directly on Q1's scaffolding: `GlobalDecision` RPC and `NotifyDecision` are already stub-declared in `twopc.proto`, just not implemented.
- `make check` passes (16/16 tests) and Docker cluster is validated.

Long-horizon references:
- `docs/handoff/OVERVIEW_CHECKLIST.md` (phase A–G status)
- `docs/handoff/TASK_QUEUE.md` (full milestone queue)

## Recommended task order

1. **Implement coordinator `GlobalDecision` logic in `server/server.py`** — after collecting votes in `run_voting_phase`, decide global-commit (all true) or global-abort (any false), then send `GlobalDecision` RPC to all peers with the decision and the proposed update.
2. **Implement participant `GlobalDecision` handler** — fill in `TwoPhaseCommitServicer.GlobalDecision`: on `global_commit=true`, apply `state.update_user(jwt, x, y)`; on false, discard. Return `DecisionAck`.
3. **Implement `IntraNodePhaseService.NotifyDecision`** — after the coordinator sends GlobalDecision to all peers, call `NotifyDecision` on localhost (intra-node gRPC) to inform the voting phase of the final outcome. The voting phase handler receives this and can log/record the outcome.
4. **Gate the coordinator's local state update** — in Q1, the coordinator applied the update locally unconditionally. In Q2, only apply if all votes were commit (mirrors the participant behavior).
5. **Add required Q2 RPC log messages** — both client-side (coordinator sending) and server-side (participant receiving), using the decision-phase format.
6. **Extend unit tests** — add tests for coordinator decision logic, participant apply/discard behavior, intra-node NotifyDecision, and Q2 log format in `tests/unit/test_2pc.py`.
7. **Run `make check`** — lint + unit tests must pass.
8. **Validate with Docker** — `docker compose up --build`, send `UpdateLocation` to Node 1, confirm GlobalDecision log lines appear for Nodes 2–6.
9. **Mandatory final subtask** — see below.

Steps 1 and 2 can be developed in parallel.

## Scope (in)

- Coordinator: after vote collection, sends `GlobalDecision` RPC to all participants
- Participants: receive `GlobalDecision`, apply or discard location update via `state.update_user`
- Coordinator: gates local state update on unanimous commit
- `IntraNodePhaseService.NotifyDecision` intra-node gRPC call (coordinator → localhost)
- Q2 RPC log messages in required format (both sender and receiver sides)
- Unit tests for decision logic, apply/discard, NotifyDecision, log format
- `make check` passes

## Scope (out)

- Raft (Q3, Q4) — not this milestone
- Failure tests (Q5) — not this milestone
- Re-implementing Q1 — all Q1 code is already in place; extend it, don't replace it

## Dependencies / prerequisites

- Quick orientation: `AGENTS.md` (read first), `docs/handoff/CURRENT_STATUS.md`
- Environment setup: `requirements-dev.txt`, `Makefile`
- Specs (read only what's needed):
  - `docs/spec/03_2pc_contract.md` — same spec, Q2 decision-phase sections
- Inputs from Q1: `server/twopc.proto`, `server/twopc_pb2.py`, `server/twopc_pb2_grpc.py`, `server/server.py` (with Q1 voting logic), `server/docker-compose.yml`

## Implementation notes

- **Proto stubs already exist** — `GlobalDecision` and `NotifyDecision` are already declared in `twopc.proto` and have stub implementations in `server.py`. Fill them in.
- **`run_voting_phase` already returns the vote list** — extend it to call `GlobalDecision` on peers after collecting votes, then call `NotifyDecision` on localhost.
- **Coordinator local update gating** — in Q1, `UpdateLocation` calls `state.update_user` unconditionally. In Q2, only call it if the decision is global-commit. For participants, `state.update_user` is called inside `GlobalDecision` handler.
- **PEERS format** — coordinator's `PEERS` env var is `fishing2:50052,...`. Re-use the same `peers` list and `peer_node_id()` helper from Q1.
- **Log format** (must match exactly):
  - Sender (coordinator): `Phase decision of Node 1 sends RPC GlobalDecision to Phase decision of Node 2`
  - Receiver (participant): `Phase decision of Node 2 sends RPC GlobalDecision to Phase decision of Node 1`
  - Intra-node (coordinator): `Phase decision of Node 1 sends RPC NotifyDecision to Phase voting of Node 1`
- Run `make check` after every significant code change.

## Acceptance criteria (definition of done)

- [ ] Coordinator sends `GlobalDecision` to all participants after vote collection
- [ ] Participants apply `state.update_user` on global-commit, discard on global-abort
- [ ] Coordinator's local update gated on unanimous commit
- [ ] `IntraNodePhaseService.NotifyDecision` called on localhost with final decision
- [ ] Q2 RPC log messages match required format (both sender and receiver)
- [ ] All unit tests pass (`make test`)
- [ ] `make check` passes (lint + unit tests)
- [ ] 5+ Docker containers start and full 2PC flow (vote + decision) completes on `UpdateLocation`
- [ ] Handoff docs updated (see mandatory final subtask below)

## Verification checklist

- [ ] `make check` passes
- [ ] `docker compose -f server/docker-compose.yml up --build` starts 5+ containers
- [ ] `UpdateLocation` to Node 1 produces both VoteRequest AND GlobalDecision log lines
- [ ] `UpdateLocation` with negative coordinates produces vote-abort AND global-abort log lines (no state update)
- [ ] `NotifyDecision` intra-node log appears on Node 1
- [ ] No unresolved placeholder text in new code or docs

## Mandatory final subtask: Update handoff documentation

**Complete this last, after all code is written and all tests pass.**

Using `docs/handoff/NEXT_TASK_TEMPLATE.md` as a guide, update the following before closing this batch:

- [ ] Mark `q2-2pc-decision` as `done` in `docs/handoff/TASK_QUEUE.md`
- [ ] Update Phase C status to `DONE` in `docs/handoff/OVERVIEW_CHECKLIST.md` and tick exit criteria
- [ ] Rewrite `docs/handoff/CURRENT_STATUS.md`:
  - What was completed (concrete, verifiable — list files created/modified)
  - Checks run and their outcomes (`make check`, docker validation)
  - Any remaining blockers or caveats
- [ ] Update `docs/handoff/BLOCKERS.md`: mark any blockers resolved this session; add any new unresolved blockers that need Joe's input
- [ ] Rewrite `docs/handoff/NEXT_TASK.md` to brief the next agent on **Q3 (Raft leader election)**, following `docs/handoff/NEXT_TASK_TEMPLATE.md`
  - Q3 subtasks: create `raft.proto`, generate stubs, implement follower/candidate/leader state machine, RequestVote RPC, heartbeat AppendEntries, election timeout [1.5s, 3s]
  - Reference `docs/spec/04_raft_election_contract.md`

The next `NEXT_TASK.md` must itself include this same "Mandatory final subtask" section so the pattern propagates to every future agent.

## Risks / rollback notes

- **Coordinator local update race** — in `UpdateLocation` (client-streaming), the coordinator now must NOT call `state.update_user` before the decision comes back. The voting-phase call is synchronous (blocking), so this is straightforward — just move the `state.update_user` call to after `run_voting_phase` returns, conditioned on the commit decision.
- **Participant state consistency** — participants now get their state update from `GlobalDecision`, not from `UpdateLocation`. Since participants are NOT coordinators, their `UpdateLocation` handler will not trigger any 2PC flow (IS_COORDINATOR=false). If a non-coordinator receives an `UpdateLocation` directly from a client, it should either reject it or forward it (forwarding is a Q4/Raft concern — for now, participants can still accept it directly for testing convenience).
