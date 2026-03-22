# Task Queue

LAST_UPDATED: 2026-03-21
QUEUE_PHASE: implementation-ready
QUEUE_POLICY: Execute tasks in order Q1 → Q2 → Q3 → Q4 → Q5. Keep one `READY: YES` task at a time.

## Queue Entry 1
TASK_ID: q1-2pc-voting
MILESTONE: Q1
OBJECTIVE: Implement 2PC voting phase — proto, coordinator vote-request, participant vote-commit/abort, Docker 5+ nodes.
SPEC_DOC: docs/spec/03_2pc_contract.md
READY: YES

## Queue Entry 2
TASK_ID: q2-2pc-decision
MILESTONE: Q2
OBJECTIVE: Implement 2PC decision phase — global-commit/abort, intra-node gRPC between phases, RPC logging.
SPEC_DOC: docs/spec/03_2pc_contract.md
PREREQUISITES: q1-2pc-voting
READY: NO

## Queue Entry 3
TASK_ID: q3-raft-election
MILESTONE: Q3
OBJECTIVE: Implement Raft leader election — raft.proto, follower/candidate/leader state machine, RequestVote, heartbeat AppendEntries.
SPEC_DOC: docs/spec/04_raft_election_contract.md
PREREQUISITES: q2-2pc-decision
READY: NO

## Queue Entry 4
TASK_ID: q4-raft-log-replication
MILESTONE: Q4
OBJECTIVE: Implement Raft log replication — log entries, full log on heartbeat, majority ACK commit, client forwarding.
SPEC_DOC: docs/spec/05_raft_log_replication_contract.md
PREREQUISITES: q3-raft-election
READY: NO

## Queue Entry 5
TASK_ID: q5-failure-tests
MILESTONE: Q5
OBJECTIVE: Design and execute 5 failure-related Raft test cases with screenshot evidence.
SPEC_DOC: docs/spec/06_failure_test_matrix.md
PREREQUISITES: q4-raft-log-replication
READY: NO

## Queue Entry 6
TASK_ID: final-deliverables
MILESTONE: DELIVERY
OBJECTIVE: Update README with build/run instructions, create final report, zip and submit.
PREREQUISITES: q5-failure-tests
READY: NO

## Queue Update Rules
- Keep one and only one queue entry with `READY: YES`.
- When a task completes, mark next entry as `READY: YES`.
- `CURRENT_STATUS:ACTIVE_QUEUE_TASK_ID` must equal queue `READY: YES` `TASK_ID`.
