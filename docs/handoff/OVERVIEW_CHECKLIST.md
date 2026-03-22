# Overview Checklist

LAST_UPDATED: 2026-03-21
PROJECT_PHASE: implementation-ready

## A. Seed and Planning
- STATUS: DONE
- EXIT_CRITERIA: baseline audit, scope lock, implementation specs (03-06), all decisions locked
- EVIDENCE: `docs/spec/00-06`, `docs/handoff/DECISION_LOG.md`, `AGENTS.md`

## B. Q1 — 2PC Voting Phase
- STATUS: NOT_STARTED
- SPEC: `docs/spec/03_2pc_contract.md`
- EXIT_CRITERIA: `2pc.proto` compiled, coordinator sends VoteRequest, participants respond, 5+ Docker nodes communicate, RPC logs in required format

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
