# Next Task
**Last updated:** 2026-03-24
**Owner:** Joe

## Task summary

Execute Q5 (failure tests): run 5 failure-related Raft test scenarios against the live 6-node Docker cluster, capture screenshots of terminal/log output for each, and document the results. No new code is required — this task is about operating the cluster and collecting evidence.

**Task queue reference:** q5-failure-tests (see `docs/handoff/TASK_QUEUE.md`)

## Why this task is next

- Q4 (Raft log replication) is COMPLETE — `append_log_entry`, `_record_ack`, `ForwardRequest`, full log on heartbeat, client routing all done. 55/55 unit tests pass, `make check` clean.
- Q5 only requires Docker and the existing cluster; no new proto file or Python code is needed.

Long-horizon references:
- `docs/handoff/OVERVIEW_CHECKLIST.md` (phase A–G status)
- `docs/handoff/TASK_QUEUE.md` (full milestone queue)

## Recommended task order

1. **Build and start the cluster:** `make up` — verify 6 containers are running.
2. **Connect a client and send UpdateLocation** to confirm Raft replication works (find leader in logs, confirm heartbeats and commits).
3. **Test Case 1 — Leader Crash and Re-Election:** kill leader container, confirm new leader elected, client resumes.
4. **Test Case 2 — Follower Crash and Recovery:** kill one follower, send updates, restart follower, verify log catch-up.
5. **Test Case 3 — Network Partition (pause/unpause):** `docker pause` a node, send updates, `docker unpause`, verify resync.
6. **Test Case 4 — New Node Joining:** stop fishing6 beforehand, start it after other 5 have log entries, verify it syncs.
7. **Test Case 5 — Split Vote / Election Retry:** kill leader + one follower simultaneously, observe multiple election rounds in logs, confirm a leader is eventually elected.
8. **Capture screenshots** for each test case (terminal or log output — annotate with TC number).
9. **Mandatory final subtask** — update handoff docs (see below).

Steps 3–7 must be run sequentially (each changes cluster state). Steps 3–7 each require `make down && make up` between tests to reset cluster state.

## Scope (in)

- 5 test cases executed against live Docker cluster
- Screenshots captured for each test case (for the final report)
- Brief written observation per test (1-2 sentences: what was observed vs. expected)
- `make check` still passes after this task (no code changes should break it)

## Scope (out)

- New Python code / new proto file — not needed
- Automated test scripts for failure scenarios (manual Docker commands are sufficient)
- Performance benchmarking

## Dependencies / prerequisites

- Quick orientation: `AGENTS.md` (read first), `docs/handoff/CURRENT_STATUS.md`
- Environment setup: Docker + `make up` / `make down` / `make logs`
- Specs (read only what's needed):
  - `docs/spec/06_failure_test_matrix.md` — full Q5 spec with exact Docker commands, expected behavior, and what to screenshot per test case
- Inputs from prior phase: `server/raft_node.py`, `server/server.py`, `server/docker-compose.yml` (all from Q3+Q4)

## Implementation notes

- **Docker commands** for each test case are in `docs/spec/06_failure_test_matrix.md` — use them verbatim.
- **Finding the leader**: run `docker compose -f server/docker-compose.yml logs | grep "became leader"` after startup.
- **Test Case 4 (new node joining)**: fishing6 is already defined in `server/docker-compose.yml`. Start cluster with `make up`, then stop fishing6 immediately (`docker stop fishing6`), run TC1-3, then re-run `docker compose -f server/docker-compose.yml up -d fishing6` for TC4.
- **Test Case 5 (split vote)**: reliably triggering a split vote is hard — if you can't reproduce one, demonstrate the *mechanism* by showing in logs that election timeouts differ per node and that a new term starts when no majority is reached. The assignment alternative is acceptable.
- **Screenshots**: capture `docker logs -f fishing<N>` output in a terminal window. Annotate the screenshot filename or caption with the test case number.
- Run `make check` after any accidental code changes.

## Acceptance criteria (definition of done)

- [ ] All 5 test cases executed (or attempted with documented rationale if not reproducible)
- [ ] Screenshot evidence collected for each test case
- [ ] Brief observation written per test case (what happened, does it match expected behavior)
- [ ] `make check` still passes (55/55 tests, lint clean)
- [ ] Handoff docs updated (see mandatory final subtask below)

## Verification checklist

- [ ] `make check` passes
- [ ] `docker compose -f server/docker-compose.yml up --build` starts 6 containers
- [ ] `docker compose -f server/docker-compose.yml logs | grep "became leader"` shows a leader
- [ ] Client can connect and send UpdateLocation; logs show AppendEntries on leader
- [ ] Each of the 5 test cases produces observable log output matching the spec's expected behavior
- [ ] No unresolved placeholder text in new docs

## Mandatory final subtask: Update handoff documentation

**Complete this last, after all tests are run and screenshots captured.**

Using `docs/handoff/NEXT_TASK_TEMPLATE.md` as a guide, update the following before closing this batch:

- [ ] Mark `q5-failure-tests` as `done` in `docs/handoff/TASK_QUEUE.md`
- [ ] Update Phase F status to `DONE` in `docs/handoff/OVERVIEW_CHECKLIST.md` and tick exit criteria
- [ ] Rewrite `docs/handoff/CURRENT_STATUS.md`:
  - What was completed (test cases run, screenshots collected, files created)
  - Checks run and their outcomes (`make check`, Docker validation)
  - Any remaining blockers or caveats
- [ ] Update `docs/handoff/BLOCKERS.md`: mark any blockers resolved this session; add any new unresolved blockers
- [ ] Rewrite `docs/handoff/NEXT_TASK.md` to brief the next agent on **final deliverables (G)**: update README with build/run instructions, unusual notes, external sources, GitHub link; create report (team members, IDs, work division, test screenshots, GitHub link)
  - Reference `docs/spec/00_assignment_project3.md` for deliverable requirements
  - Reference `docs/handoff/OVERVIEW_CHECKLIST.md` Phase G exit criteria

The next `NEXT_TASK.md` must itself include this same "Mandatory final subtask" section so the pattern propagates to every future agent.

## Risks / rollback notes

- **Test Case 5 split vote**: may be non-deterministic. If you cannot reproduce a genuine split vote within a few attempts, document the mechanism from logs and move on — the assignment provides an acceptable alternative.
- **Cluster state contamination**: each test case can leave the cluster in an unusual state (missing nodes, stale terms). Always `make down && make up` to reset between test cases.
- **Client streaming RPC**: `UpdateLocation` is a client-streaming RPC. Ensure the client keeps the stream open long enough to see commits in logs. Use the interactive client (`cd client && python3 client.py`).
