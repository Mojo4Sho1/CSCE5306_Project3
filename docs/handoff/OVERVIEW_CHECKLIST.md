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
- STATUS: DONE
- SPEC: `docs/spec/03_2pc_contract.md`
- EXIT_CRITERIA:
  - [x] Coordinator sends GlobalDecision to all participants after vote collection
  - [x] Participants apply `state.update_user` on global-commit, discard on global-abort
  - [x] Coordinator's local update gated on unanimous commit
  - [x] `IntraNodePhaseService.NotifyDecision` called on localhost with final decision
  - [x] Q2 RPC log messages match required format (sender and receiver)
  - [x] 26/26 unit tests pass; `make check` clean
- EVIDENCE: `server/server.py` (run_decision_phase, GlobalDecision handler, UpdateLocation gating), `tests/unit/test_2pc.py` (tests 11–20)

## D. Q3 — Raft Leader Election
- STATUS: DONE
- SPEC: `docs/spec/04_raft_election_contract.md`
- EXIT_CRITERIA:
  - [x] `raft.proto` compiled (produces `raft_pb2.py` / `raft_pb2_grpc.py`)
  - [x] All nodes start as followers (term 0, voted_for None)
  - [x] Election timeout triggers candidate transition
  - [x] Candidate sends RequestVote to all peers and collects majority → becomes leader
  - [x] Leader sends heartbeat AppendEntries every 1 second
  - [x] Followers reset election timer on valid AppendEntries
  - [x] Higher-term messages cause step-down to follower
  - [x] All RPC calls produce required log format (sender + receiver)
  - [x] 40/40 unit tests pass; `make check` clean (2026-03-24)
- EVIDENCE: `server/raft.proto`, `server/raft_pb2.py`, `server/raft_pb2_grpc.py`, `server/raft_node.py`, `server/server.py` (Raft wired in serve()), `tests/unit/test_raft.py` (14 tests)

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
