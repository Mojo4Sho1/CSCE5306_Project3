# Overview Checklist

LAST_UPDATED: 2026-03-25
PROJECT_PHASE: final-deliverables

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
- STATUS: DONE
- SPEC: `docs/spec/05_raft_log_replication_contract.md`
- EXIT_CRITERIA:
  - [x] Leader appends client requests to log as `<operation, term, index>`
  - [x] Leader sends entire log + commit_index on each heartbeat (AppendEntries)
  - [x] Followers replace entire log and execute committed entries via apply_fn callback
  - [x] Leader commits after receiving ACKs from majority (ack_tracker set per entry)
  - [x] commit_index increments correctly after majority ACK; pending client event set
  - [x] Non-leader nodes forward UpdateLocation to leader via ForwardRequest RPC
  - [x] All RPC calls produce required log format (sender + receiver)
  - [x] 55/55 unit tests pass; `make check` clean (2026-03-24)
- EVIDENCE: `server/raft_node.py` (LogEntry, append_log_entry, _record_ack, wait_for_commit, get_leader_address, ForwardRequest handler), `server/raft.proto` (sender_id added to ForwardRequestMessage), `server/server.py` (_raft_update_location, UpdateLocation routing, raft_node global), `tests/unit/test_raft_replication.py` (15 tests)

## F. Q5 — Failure Tests
- STATUS: DONE
- SPEC: `docs/spec/06_failure_test_matrix.md`
- EXIT_CRITERIA:
  - [x] TC1: Leader crash and re-election — Node 2 killed; Node 6 elected leader (term 2) in ~2-3 s
  - [x] TC2: Follower crash and recovery — Node 1 stopped; cluster continued; Node 1 synced on restart via AppendEntries
  - [x] TC3: Network partition (pause/unpause) — Node 5 (leader) paused; Node 6 elected (term 2); Node 5 stepped down on unpause after seeing higher term
  - [x] TC4: New node joining — 5-node cluster (Node 4 leader); fishing6 added; received AppendEntries within 1 heartbeat cycle and synced
  - [x] TC5: Split vote and retry — Nodes 2 + 3 killed; Nodes 5 and 6 both started term-2 elections (split); Node 5 won term 3 on retry
  - [x] 5 raw log files in `docs/report/logs/tc{1-5}_raw.txt`
  - [x] 5 PNG screenshots in `docs/report/screenshots/tc{1-5}_*.png`
  - [x] Observed behaviour filled in `docs/report/report.tex` (all TC `\todo{}` replaced)
  - [x] Bug fixed: `PEERS: ""` for nodes 2-6 in docker-compose.yml — each node now has its full peer list
  - [x] `make check` still passes (55/55 tests, lint clean) after docker-compose.yml fix
- EVIDENCE: `docs/report/logs/`, `docs/report/screenshots/`, `docs/report/report.tex`, `server/docker-compose.yml`

## G. Final Deliverables
- STATUS: NOT_STARTED
- EXIT_CRITERIA: README complete (build/run, unusual notes, sources, GitHub link), report complete (team members, IDs, work division, AI lessons-learned section), PDF compiled (Overleaf or TeX Live), zip submitted

## Update Rules
- Only set `DONE` when exit criteria and evidence are both present.
