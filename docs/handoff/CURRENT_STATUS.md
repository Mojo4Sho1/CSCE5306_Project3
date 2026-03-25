# Current Status

LAST_UPDATED: 2026-03-25
PROJECT_PHASE: final-deliverables
REPO_BASELINE: forked upstream Python gRPC fishing prototype — extended with 2PC Q1+Q2 and Raft Q3+Q4+Q5
ACTIVE_PRIMARY_OBJECTIVE: final deliverables (G) — README, report PDF, submission
STATUS_SUMMARY:
- Q1 (2PC voting phase) is COMPLETE.
- Q2 (2PC decision phase) is COMPLETE.
- Q3 (Raft leader election) is COMPLETE.
- Q4 (Raft log replication) is COMPLETE.
- Q5 (failure tests) is COMPLETE.
- Files created/modified this session (Q5):
  - FIXED: server/docker-compose.yml — added PEERS env var for nodes 2-6 (was "" causing single-node election bug)
  - CREATED: docs/report/logs/tc1_raw.txt through tc5_raw.txt (5 raw log captures)
  - CREATED: docs/report/screenshots/tc1_*.png through tc5_*.png (5 terminal-styled PNG screenshots)
  - MODIFIED: docs/report/report.tex — all TC \todo{} observed-behaviour placeholders filled; screenshot \includegraphics paths corrected to match actual filenames; PEERS bug noted in Unusual Notes section
  - MODIFIED: docs/report/q5_failure_tests.ipynb — fixed render_screenshot slug generation to use re.sub (handles "/" in titles like "pause/unpause")
  - MODIFIED: Makefile — pdf target now prints helpful error when pdflatex not found
QUALITY_GATES:
- make check: PASS — 55/55 unit tests pass, ruff clean (verified 2026-03-25 before Q5 run)
- Docker validation: ALL 5 TCs executed successfully against live 6-node cluster
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
- PEERS must be set for ALL nodes, not only the coordinator — original config had PEERS="" for nodes 2-6.
DECISIONS_PENDING: NONE
RISKS_ACTIVE: NONE
NEXT_TASK_ID: final-deliverables
ACTIVE_QUEUE_TASK_ID: final-deliverables
OPEN_DECISIONS_COUNT: 0
NEXT_TASK_READY: YES
REQUIRED_REFERENCES:
1. `AGENTS.md` (primary agent guide)
2. `docs/spec/00_assignment_project3.md` (deliverable requirements)
3. `docs/handoff/NEXT_TASK.md`
4. `docs/handoff/TASK_QUEUE.md`
HANDOFF_INSTRUCTIONS:
- Read `AGENTS.md` first.
- Check this file for current phase and next task.
- Read the spec doc for your assigned task.
- Implement, update handoff docs when done.
