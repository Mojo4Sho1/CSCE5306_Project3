# Decision Log

LAST_UPDATED: 2026-03-21
OPEN_DECISIONS_COUNT: 0

## Status Legend
- `OPEN`: unresolved question
- `LOCKED`: resolved with evidence

## Decisions
DECISION_ID: DEC-0001
STATUS: LOCKED
SOURCE_DOC: `docs/spec/02_extension_scope.md`
QUESTION: Which single functionality in the MMO fishing baseline will be extended with 2PC and Raft for Project 3?
DECISION: Project 3 is locked to replicated player state updates via location-update commands, using the existing `UpdateLocation` RPC as the baseline integration surface.
OWNER_TASK_ID: seed-review-requirements
EVIDENCE: User-directed scope lock recorded in `docs/spec/02_extension_scope.md` and aligned with the audited `UpdateLocation` mutation path in `server/server.py`.
ACTIVE_LOOP_IMPACT: RESOLVED

DECISION_ID: DEC-0002
STATUS: LOCKED
SOURCE_DOC: `docs/spec/03_2pc_contract.md`, `docs/spec/04_raft_election_contract.md`
QUESTION: Should Project 3 introduce new proto files for 2PC and Raft, or extend the current baseline proto layout?
DECISION: Create separate `2pc.proto` and `raft.proto` files. Do NOT modify the existing `fishing.proto`. The assignment requires a new proto file for Raft; a separate 2PC proto keeps concerns clean and avoids touching baseline artifacts.
OWNER_TASK_ID: seed-pass2-decomposition
EVIDENCE: Assignment Q3 explicitly requires a new proto file for Raft. Proto sketches documented in `docs/spec/03_2pc_contract.md` and `docs/spec/04_raft_election_contract.md`.
ACTIVE_LOOP_IMPACT: RESOLVED

## Update Rules
- `OPEN_DECISIONS_COUNT` must equal number of `STATUS: OPEN` entries.
- Escalate only when active task is blocked.
