# Spec Conformance Checklist

LAST_UPDATED: 2026-04-08

## Status Legend
- `SATISFIED`
- `IN_PROGRESS`
- `NOT_STARTED`

SPEC_MUST_ID: S00-M01
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: The project MUST extend one selected existing distributed system.
STATUS: SATISFIED
OWNER_TASK_ID: seed-review-requirements
EVIDENCE: `docs/spec/01_repo_baseline_audit.md`, `docs/spec/02_extension_scope.md`, `server/server.py`

SPEC_MUST_ID: S00-M02
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: The implementation MUST use gRPC for node/process communication.
STATUS: SATISFIED
OWNER_TASK_ID: q1-2pc-voting, q3-raft-election
EVIDENCE: `server/twopc.proto`, `server/raft.proto`, `server/server.py`, `server/raft_node.py`

SPEC_MUST_ID: S00-M03
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: The implementation MUST use Docker for containerization.
STATUS: SATISFIED
OWNER_TASK_ID: q1-2pc-voting
EVIDENCE: `server/docker-compose.yml`, `server/dockerfile`, `Makefile`

SPEC_MUST_ID: S00-M04
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: At least 5 containerized nodes MUST communicate successfully.
STATUS: SATISFIED
OWNER_TASK_ID: q1-2pc-voting, q5-failure-tests
EVIDENCE: `server/docker-compose.yml`, `docs/spec/06_failure_test_matrix.md`, `docs/handoff/CURRENT_STATUS.md`

SPEC_MUST_ID: S00-M05
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: 2PC voting MUST implement vote-request, vote-commit, and vote-abort behavior.
STATUS: SATISFIED
OWNER_TASK_ID: q1-2pc-voting
EVIDENCE: `server/twopc.proto`, `server/server.py`, `tests/unit/test_2pc.py`

SPEC_MUST_ID: S00-M06
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: 2PC decision MUST implement global-commit and global-abort behavior.
STATUS: SATISFIED
OWNER_TASK_ID: q2-2pc-decision
EVIDENCE: `server/server.py`, `tests/unit/test_2pc.py`

SPEC_MUST_ID: S00-M07
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: Intra-node communication between 2PC phases MUST use gRPC.
STATUS: SATISFIED
OWNER_TASK_ID: q2-2pc-decision
EVIDENCE: `server/twopc.proto`, `server/server.py`, `docs/spec/03_2pc_contract.md`

SPEC_MUST_ID: S00-M08
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: 2PC RPC logging MUST follow the required assignment format.
STATUS: SATISFIED
OWNER_TASK_ID: q1-2pc-voting, q2-2pc-decision, compliance-2pc-logging-audit-patch
EVIDENCE: `server/server.py` (`run_voting_phase`, `run_decision_phase`, `TwoPhaseCommitServicer`, `IntraNodePhaseServicer`), `tests/unit/test_2pc.py`, `README.md`

SPEC_MUST_ID: S00-M09
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: Raft leader election MUST implement follower, candidate, and leader state transitions.
STATUS: SATISFIED
OWNER_TASK_ID: q3-raft-election, compliance-raft-election-state-audit-patch
EVIDENCE: `server/raft.proto`, `server/raft_node.py`, `tests/unit/test_raft.py`

SPEC_MUST_ID: S00-M10
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: Heartbeat timeout MUST be 1 second.
STATUS: SATISFIED
OWNER_TASK_ID: q3-raft-election
EVIDENCE: `server/raft_node.py`, `docs/spec/04_raft_election_contract.md`

SPEC_MUST_ID: S00-M11
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: Election timeout MUST be randomized in `[1.5s, 3s]`.
STATUS: SATISFIED
OWNER_TASK_ID: q3-raft-election
EVIDENCE: `server/raft_node.py`, `tests/unit/test_raft.py`, `docs/spec/04_raft_election_contract.md`

SPEC_MUST_ID: S00-M12
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: Raft RPC logging MUST follow the required assignment format.
STATUS: SATISFIED
OWNER_TASK_ID: q3-raft-election, q4-raft-log-replication
EVIDENCE: `server/raft_node.py`, `server/server.py`, `README.md`

SPEC_MUST_ID: S00-M13
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: Raft log replication MUST maintain committed and pending operations.
STATUS: SATISFIED
OWNER_TASK_ID: q4-raft-log-replication
EVIDENCE: `server/raft_node.py`, `tests/unit/test_raft_replication.py`

SPEC_MUST_ID: S00-M14
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: The leader MUST send the entire log plus commit index `c` on the next heartbeat.
STATUS: SATISFIED
OWNER_TASK_ID: q4-raft-log-replication
EVIDENCE: `server/raft_node.py`, `server/raft.proto`, `tests/unit/test_raft_replication.py`

SPEC_MUST_ID: S00-M15
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: Non-leader nodes MUST forward client requests to the leader.
STATUS: SATISFIED
OWNER_TASK_ID: q4-raft-log-replication
EVIDENCE: `server/raft.proto`, `server/server.py`, `server/raft_node.py`, `tests/unit/test_raft_replication.py`

SPEC_MUST_ID: S00-M16
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: The project MUST include 5 failure-related Raft test cases.
STATUS: SATISFIED
OWNER_TASK_ID: q5-failure-tests, compliance-new-node-audit-wording-patch
EVIDENCE: `docs/spec/06_failure_test_matrix.md`, `docs/handoff/CURRENT_STATUS.md` (evidence captured during execution and moved to the final report workflow; TC4 wording narrowed to late startup of a preconfigured node)

SPEC_MUST_ID: S00-M17
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: The final submission MUST include source code, README, and report.
STATUS: SATISFIED
OWNER_TASK_ID: final-deliverables
EVIDENCE: Source code and README are present in the repo; the final report is maintained externally in Overleaf per the final project workflow.

SPEC_MUST_ID: S00-M18
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: The README MUST include build/run instructions, unusual solution notes, external sources, and the GitHub link.
STATUS: SATISFIED
OWNER_TASK_ID: final-deliverables
EVIDENCE: `README.md`

SPEC_MUST_ID: S00-M19
SOURCE_SPEC: `docs/spec/00_assignment_project3.md`
MUST_TEXT: The report MUST include team identities, work division, failure evidence, and the GitHub link.
STATUS: SATISFIED
OWNER_TASK_ID: final-deliverables
EVIDENCE: Final report content is maintained externally in Overleaf per the final project workflow.
