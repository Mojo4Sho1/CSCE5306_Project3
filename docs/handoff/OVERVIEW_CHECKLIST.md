# Overview Checklist

LAST_UPDATED: 2026-03-24
PROJECT_PHASE: implementation-in-progress

## A. Seed and Planning
- STATUS: DONE
- EXIT_CRITERIA: baseline audit, scope lock, implementation specs (03-06), all decisions locked
- EVIDENCE: `docs/spec/00-06`, `docs/handoff/DECISION_LOG.md`, `AGENTS.md`

## B. Q1 — 2PC Voting Phase
- STATUS: DONE
- SPEC: `docs/spec/03_2pc_contract.md`
- EXIT_CRITERIA:
  - [x] `twopc.proto` compiled (renamed from 2pc.proto — Python import constraint)
  - [x] Coordinator sends VoteRequest to all 5 participants and collects responses
  - [x] Participants respond vote-commit/vote-abort (abort on negative coordinates)
  - [x] Intra-node gRPC ReportVote works (voting → decision on localhost)
  - [x] 6 Docker nodes communicate; RPC log lines in required format verified
  - [x] 16/16 unit tests pass; `make check` clean
- EVIDENCE: `server/twopc.proto`, `server/twopc_pb2.py`, `server/twopc_pb2_grpc.py`, `server/server.py`, `tests/unit/test_2pc.py`

## C. Q2 — 2PC Decision Phase
- STATUS: NOT_STARTED
- SPEC: `docs/spec/03_2pc_contract.md`
- EXIT_CRITERIA: coordinator sends GlobalDecision, participants apply/discard, intra-node gRPC works, RPC logs in required format

## D. Q3 — Raft Leader Election
- STATUS: NOT_STARTED
- SPEC: `docs/spec/04_raft_election_contract.md`
- EXIT_CRITERIA: `raft.proto` compiled, all nodes start as followers, leader elected via RequestVote majority, heartbeat every 1s, election timeout [1.5s, 3s]

## E. Q4 — Raft Log Replication
- STATUS: NOT_STARTED
- SPEC: `docs/spec/05_raft_log_replication_contract.md`
- EXIT_CRITERIA: log entries replicated on heartbeat, majority ACK commits, client forwarding to leader, state consistent across nodes

## F. Q5 — Failure Tests
- STATUS: NOT_STARTED
- SPEC: `docs/spec/06_failure_test_matrix.md`
- EXIT_CRITERIA: 5 failure test cases executed, screenshots captured, documented for report

## G. Final Deliverables
- STATUS: NOT_STARTED
- EXIT_CRITERIA: README complete (build/run, unusual notes, sources, GitHub link), report complete (team members, IDs, work division, screenshots, GitHub link), zip submitted

## Update Rules
- Only set `DONE` when exit criteria and evidence are both present.
