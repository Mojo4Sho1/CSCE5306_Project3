# Next Task
**Last updated:** 2026-03-24
**Owner:** Joe

## Task summary

Implement Q4 (Raft log replication): extend the existing Raft implementation from Q3 to replicate `UpdateLocation` operations via the log. The leader appends entries to its log, sends the full log on each heartbeat, followers copy and execute committed entries, and non-leader nodes forward client requests to the leader.

**Task queue reference:** q4-raft-log-replication (see `docs/handoff/TASK_QUEUE.md`)

## Why this task is next

- Q3 (Raft leader election) is COMPLETE — `raft.proto`, `raft_node.py`, `RaftServicer`, all wired in `server.py`, 40 unit tests passing, `make check` clean.
- Q4 extends the existing `AppendEntries` handler and `RaftNode` with log state; no new proto file needed (messages already defined in Q3).

Long-horizon references:
- `docs/handoff/OVERVIEW_CHECKLIST.md` (phase A–G status)
- `docs/handoff/TASK_QUEUE.md` (full milestone queue)

## Recommended task order

1. **Extend `RaftNode` state** — add `last_applied` and `pending_clients` dict to `__init__`. `log` and `commit_index` are already present from Q3.
2. **Add `append_log_entry(operation)` method** — creates a `LogEntry`, appends to `self.log`, returns the new entry index.
3. **Extend heartbeat sender** — populate `entries` (full log) and `commit_index` in `AppendEntriesRequest`.
4. **Extend `AppendEntries` handler (follower side)** — replace log with received entries; execute all entries with `index <= commit_index` that have not yet been applied.
5. **Track majority ACKs in leader** — after receiving `AppendEntriesResponse(success=True)`, increment ACK count for pending entries; commit when majority reached.
6. **Implement `ForwardRequest` handler** — non-leader forwards to current `leader_id`'s address; logs required format.
7. **Modify `FishingService.UpdateLocation`** — route through Raft log: if leader, call `append_log_entry` and wait for commit; if follower, call `ForwardRequest` to leader.
8. **Add `get_leader_address()` helper** — maps `leader_id` to peer address using PEERS env var.
9. **Add unit tests** — `tests/unit/test_raft_replication.py`: log append, follower copy, majority ACK commit, client forwarding stub. Minimum 8 tests.
10. **Run `make check`** — lint + all tests must pass.
11. **Validate with Docker** — `make up`; issue UpdateLocation from client; confirm operation appears in all node logs.
12. **Mandatory final subtask** — update handoff docs (see below).

Steps 3–5 can be developed mostly in parallel; steps 6–7 depend on 3–5.

## Scope (in)

- Extended `server/raft_node.py`: `append_log_entry`, ACK tracking, `ForwardRequest` implementation
- Extended `AppendEntries` handler: full log copy + execute committed entries
- Modified heartbeat sender: send full log + commit_index
- `FishingService.UpdateLocation` routed through Raft log
- `get_leader_address()` helper
- Unit tests (`tests/unit/test_raft_replication.py`) — minimum 8 tests, no Docker required
- `make check` passes

## Scope (out)

- New proto file — all messages already defined in `raft.proto` from Q3
- Failure tests (Q5)
- Conflict resolution in log — spec says send full log, so follower simply replaces its log

## Dependencies / prerequisites

- Quick orientation: `AGENTS.md` (read first), `docs/handoff/CURRENT_STATUS.md`
- Environment setup: `requirements-dev.txt`, `Makefile`
- Specs (read only what's needed):
  - `docs/spec/05_raft_log_replication_contract.md` — full Q4 spec (log structure, heartbeat extension, client forwarding, commit protocol)
- Inputs from prior phase: `server/raft_node.py` (RaftNode + RaftServicer), `server/raft_pb2.py` / `server/raft_pb2_grpc.py`, `server/server.py` (RaftNode wired in serve())

## Implementation notes

- **No new proto file**: `LogEntry`, `AppendEntriesRequest.entries`, `AppendEntriesRequest.commit_index`, and `ForwardRequest` messages are already defined in Q3's `raft.proto`.
- **Full log on heartbeat**: the spec explicitly says send the entire log, not incremental entries. Followers replace their log wholesale.
- **Majority definition**: `votes > total_nodes / 2` (same as election). For 6 nodes, need 4 ACKs (including leader).
- **Blocking commit**: use `threading.Event` per pending entry index in `pending_clients`. Client blocks until event is set when entry is committed.
- **ForwardRequest log format**:
  - Sender: `Node <sender_id> sends RPC ForwardRequest to Node <leader_id>`
  - Receiver: `Node <receiver_id> runs RPC ForwardRequest called by Node <sender_id>`
- **AppendEntries ACK tracking**: the leader needs to count ACKs per log index across heartbeat rounds. A simple `dict[int, int]` of `{entry_index: ack_count}` works. Set `ack_count = 1` on entry creation (leader's self-ACK).
- **`_start_threads=False`** in unit tests — same as Q3. Test log append, ACK counting, and commit logic directly without threads.
- Run `make check` after every significant code change.

## Acceptance criteria (definition of done)

- [ ] Leader appends client requests to log as `<operation, term, index>`
- [ ] Leader sends entire log + `commit_index` on each heartbeat
- [ ] Followers copy entire log and execute all entries with `index <= commit_index`
- [ ] Leader commits after receiving ACKs from majority (including self)
- [ ] `commit_index` increments correctly after majority ACK
- [ ] Non-leader nodes forward `UpdateLocation` to leader via `ForwardRequest`
- [ ] All RPC calls produce the required log format
- [ ] All unit tests pass (`make test`)
- [ ] `make check` passes (lint + unit tests)
- [ ] Handoff docs updated (see mandatory final subtask below)

## Verification checklist

- [ ] `make check` passes
- [ ] `docker compose -f server/docker-compose.yml up --build` starts 5+ containers
- [ ] UpdateLocation from client propagates to all nodes (visible in docker logs)
- [ ] Non-leader node correctly forwards location update to leader
- [ ] No unresolved placeholder text in new code or docs

## Mandatory final subtask: Update handoff documentation

**Complete this last, after all code is written and all tests pass.**

Using `docs/handoff/NEXT_TASK_TEMPLATE.md` as a guide, update the following before closing this batch:

- [ ] Mark `q4-raft-log-replication` as `done` in `docs/handoff/TASK_QUEUE.md`
- [ ] Update Phase E status to `DONE` in `docs/handoff/OVERVIEW_CHECKLIST.md` and tick exit criteria
- [ ] Rewrite `docs/handoff/CURRENT_STATUS.md`:
  - What was completed (concrete, verifiable — list files created/modified)
  - Checks run and their outcomes (`make check`, docker validation)
  - Any remaining blockers or caveats
- [ ] Update `docs/handoff/BLOCKERS.md`: mark any blockers resolved this session; add any new unresolved blockers that need Joe's input
- [ ] Rewrite `docs/handoff/NEXT_TASK.md` to brief the next agent on **Q5 (failure tests)**, following `docs/handoff/NEXT_TASK_TEMPLATE.md`
  - Q5 subtasks: 5 failure scenarios from `docs/spec/06_failure_test_matrix.md`, Docker setup, screenshot capture
  - Reference `docs/spec/06_failure_test_matrix.md`

The next `NEXT_TASK.md` must itself include this same "Mandatory final subtask" section so the pattern propagates to every future agent.

## Risks / rollback notes

- **Blocking client on commit**: if leader steps down before committing, waiting clients will hang. Add a timeout to `threading.Event.wait()` (e.g., 5 seconds) and return an error if the event is not set.
- **ACK counting across heartbeats**: leader may receive ACKs for the same entry across multiple heartbeat rounds. The `ack_count` dict must deduplicate by `follower_id`, not just increment on every response.
- **ForwardRequest races**: if leader steps down between when a follower identifies it and when it sends `ForwardRequest`, the RPC will fail. Handle `grpc.RpcError` and return an error to the client.
