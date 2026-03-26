# Task Queue

LAST_UPDATED: 2026-03-26
QUEUE_PHASE: complete
QUEUE_POLICY: Execute tasks in order Q1 → Q2 → Q3 → Q4 → Q5 → final-deliverables. When the repo is finalized, all queue entries should be `READY: DONE`.

## Queue Entry 1
TASK_ID: q1-2pc-voting
MILESTONE: Q1
OBJECTIVE: Implement 2PC voting phase — proto, coordinator vote-request, participant vote-commit/abort, Docker 5+ nodes.
SPEC_DOC: docs/spec/03_2pc_contract.md
READY: DONE
COMPLETED: 2026-03-24

## Queue Entry 2
TASK_ID: q2-2pc-decision
MILESTONE: Q2
OBJECTIVE: Implement 2PC decision phase — global-commit/abort, intra-node gRPC between phases, RPC logging.
SPEC_DOC: docs/spec/03_2pc_contract.md
PREREQUISITES: q1-2pc-voting
READY: DONE
COMPLETED: 2026-03-24

## Queue Entry 3
TASK_ID: q3-raft-election
MILESTONE: Q3
OBJECTIVE: Implement Raft leader election — raft.proto, follower/candidate/leader state machine, RequestVote, heartbeat AppendEntries.
SPEC_DOC: docs/spec/04_raft_election_contract.md
PREREQUISITES: q2-2pc-decision
READY: DONE
COMPLETED: 2026-03-24

## Queue Entry 4
TASK_ID: q4-raft-log-replication
MILESTONE: Q4
OBJECTIVE: Implement Raft log replication — log entries, full log on heartbeat, majority ACK commit, client forwarding.
SPEC_DOC: docs/spec/05_raft_log_replication_contract.md
PREREQUISITES: q3-raft-election
READY: DONE
COMPLETED: 2026-03-24

## Queue Entry 5
TASK_ID: q5-failure-tests
MILESTONE: Q5
OBJECTIVE: Design and execute 5 failure-related Raft test cases with screenshot evidence.
SPEC_DOC: docs/spec/06_failure_test_matrix.md
PREREQUISITES: q4-raft-log-replication
READY: DONE
COMPLETED: 2026-03-25

## Queue Entry 6
TASK_ID: final-deliverables
MILESTONE: DELIVERY
OBJECTIVE: Finalize the repository for push: README polished, report workflow moved to Overleaf, repo-local report assets removed, and handoff/docs closed out.
PREREQUISITES: q5-failure-tests
READY: DONE
COMPLETED: 2026-03-26

## Queue Update Rules
- During active implementation, keep one and only one queue entry with `READY: YES`.
- When the project is fully finalized, all queue entries should be `READY: DONE`.
