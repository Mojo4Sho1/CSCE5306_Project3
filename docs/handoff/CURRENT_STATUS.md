# Current Status

LAST_UPDATED: 2026-03-24
PROJECT_PHASE: implementation-in-progress
REPO_BASELINE: forked upstream Python gRPC fishing prototype — preserved, now extended with 2PC Q1+Q2 and Raft Q3+Q4
ACTIVE_PRIMARY_OBJECTIVE: implement Q5 (failure tests)
STATUS_SUMMARY:
- Q1 (2PC voting phase) is COMPLETE.
- Q2 (2PC decision phase) is COMPLETE.
- Q3 (Raft leader election) is COMPLETE.
- Q4 (Raft log replication) is COMPLETE.
- Files created/modified this session (Q4):
  - MODIFIED: server/raft.proto (added sender_id field to ForwardRequestMessage)
  - REGENERATED: server/raft_pb2.py (regenerated after proto change)
  - REGENERATED: server/raft_pb2_grpc.py (regenerated after proto change)
  - MODIFIED: server/raft_node.py (LogEntry dataclass, append_log_entry, wait_for_commit, get_leader_address, _record_ack, _heartbeat_loop extended, AppendEntries extended, ForwardRequest fully implemented, RaftServicer accepts apply_fn)
  - MODIFIED: server/server.py (raft_node module-level global, _raft_update_location helper, UpdateLocation routed through Raft, apply_fn=state.update_user wired to RaftServicer, raft_pb2 imported)
  - CREATED: tests/unit/test_raft_replication.py (15 unit tests for Q4: log append, ACK tracking, commit, follower log replace, apply_fn, ForwardRequest, parse helpers)
QUALITY_GATES:
- make check: PASS — 55/55 unit tests pass (15 Raft-replication + 14 Raft-election + 20 2PC + 6 baseline), ruff clean (2026-03-24)
- Docker validation: not run this session (no docker-compose.yml changes; existing config sufficient)
BLOCKERS: NONE
DECISIONS_LOCKED:
- Proto file named twopc.proto (not 2pc.proto) — Python cannot import module names starting with a digit.
- Proto file named raft.proto (kept consistent).
- sender_id added to ForwardRequestMessage in raft.proto for required log format (receiver side needs Node ID of sender).
- apply_fn callback pattern: RaftServicer accepts apply_fn; stored on node so heartbeat thread (_record_ack) can call it without importing server.py.
- ACK deduplication via set(follower_ids) per entry index — prevents double-counting across heartbeat rounds.
- Full log sent every heartbeat; followers replace entire log (no incremental/conflict resolution).
- wait_for_commit timeout = 5 seconds; falls back to direct apply with warning if leader steps down.
- Project 3 scope locked to replicated player state updates via UpdateLocation.
- Non-coordinator nodes previously accepted UpdateLocation directly; Q4 routes via Raft.
DECISIONS_PENDING: NONE
RISKS_ACTIVE: NONE
NEXT_TASK_ID: q5-failure-tests
ACTIVE_QUEUE_TASK_ID: q5-failure-tests
OPEN_DECISIONS_COUNT: 0
NEXT_TASK_READY: YES
REQUIRED_REFERENCES:
1. `AGENTS.md` (primary agent guide)
2. `docs/spec/06_failure_test_matrix.md` (Q5 spec — 5 failure scenarios)
3. `docs/handoff/NEXT_TASK.md`
4. `docs/handoff/TASK_QUEUE.md`
HANDOFF_INSTRUCTIONS:
- Read `AGENTS.md` first.
- Check this file for current phase and next task.
- Read the spec doc for your assigned task.
- Implement, test, update handoff docs when done.
