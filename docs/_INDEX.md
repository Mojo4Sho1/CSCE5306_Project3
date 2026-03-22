# Documentation Index (Agent-First)

## How To Use
- Read `docs/handoff/CURRENT_STATUS.md` first.
- Search `KEYWORDS` blocks and open `PRIMARY_DOC` first.
- When runtime behavior is in scope, cross-check with `docs/spec/01_repo_baseline_audit.md`.

KEYWORDS: current state, blockers, ready flag, next task id
CANONICAL_TOPIC: handoff_current_status
PRIMARY_DOC: docs/handoff/CURRENT_STATUS.md
RELATED_DOCS: docs/handoff/NEXT_TASK.md, docs/handoff/TASK_QUEUE.md

KEYWORDS: next task, single primary task, quality gates
CANONICAL_TOPIC: handoff_next_task
PRIMARY_DOC: docs/handoff/NEXT_TASK.md
RELATED_DOCS: docs/handoff/CURRENT_STATUS.md, docs/handoff/OVERVIEW_CHECKLIST.md

KEYWORDS: task queue, ready task, dependency order
CANONICAL_TOPIC: handoff_task_queue
PRIMARY_DOC: docs/handoff/TASK_QUEUE.md
RELATED_DOCS: docs/handoff/CURRENT_STATUS.md, docs/handoff/NEXT_TASK.md

KEYWORDS: decision log, open questions, locked decisions
CANONICAL_TOPIC: handoff_decision_log
PRIMARY_DOC: docs/handoff/DECISION_LOG.md
RELATED_DOCS: docs/handoff/NEXT_TASK.md

KEYWORDS: spec conformance, must requirements, gate 4
CANONICAL_TOPIC: handoff_spec_conformance
PRIMARY_DOC: docs/handoff/SPEC_CONFORMANCE_CHECKLIST.md
RELATED_DOCS: docs/handoff/NEXT_TASK.md

KEYWORDS: overview checklist, milestones, definition of done
CANONICAL_TOPIC: handoff_overview_checklist
PRIMARY_DOC: docs/handoff/OVERVIEW_CHECKLIST.md
RELATED_DOCS: docs/handoff/CURRENT_STATUS.md, docs/handoff/NEXT_TASK.md

KEYWORDS: assignment, project 3, 2pc, raft, deliverables
CANONICAL_TOPIC: assignment_project3
PRIMARY_DOC: docs/spec/00_assignment_project3.md
RELATED_DOCS: docs/spec/02_extension_scope.md

KEYWORDS: upstream repo, baseline, audit, preserve, generated files, docker compose
CANONICAL_TOPIC: repo_baseline_audit
PRIMARY_DOC: docs/spec/01_repo_baseline_audit.md
RELATED_DOCS: docs/spec/02_extension_scope.md

KEYWORDS: chosen functionality, replicated player state updates, location-update commands, single extension surface, non goals
CANONICAL_TOPIC: extension_scope
PRIMARY_DOC: docs/spec/02_extension_scope.md
RELATED_DOCS: docs/spec/00_assignment_project3.md, docs/handoff/DECISION_LOG.md

KEYWORDS: agent startup, loop workflow, continuity rules
CANONICAL_TOPIC: agent_runtime_workflow
PRIMARY_DOC: AGENTS.md
RELATED_DOCS: docs/handoff/CURRENT_STATUS.md, docs/handoff/NEXT_TASK.md

KEYWORDS: 2pc, two phase commit, voting, decision, coordinator, participant, proto
CANONICAL_TOPIC: 2pc_implementation
PRIMARY_DOC: docs/spec/03_2pc_contract.md
RELATED_DOCS: docs/spec/00_assignment_project3.md, docs/spec/02_extension_scope.md

KEYWORDS: raft, leader election, candidate, follower, requestvote, heartbeat, timeout
CANONICAL_TOPIC: raft_election
PRIMARY_DOC: docs/spec/04_raft_election_contract.md
RELATED_DOCS: docs/spec/00_assignment_project3.md

KEYWORDS: raft, log replication, appendentries, commit index, client forwarding
CANONICAL_TOPIC: raft_log_replication
PRIMARY_DOC: docs/spec/05_raft_log_replication_contract.md
RELATED_DOCS: docs/spec/04_raft_election_contract.md

KEYWORDS: failure tests, test cases, leader crash, network partition, split vote
CANONICAL_TOPIC: failure_tests
PRIMARY_DOC: docs/spec/06_failure_test_matrix.md
RELATED_DOCS: docs/spec/04_raft_election_contract.md, docs/spec/05_raft_log_replication_contract.md
