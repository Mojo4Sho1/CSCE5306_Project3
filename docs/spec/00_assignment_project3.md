# Project 3 Assignment Requirements

## Purpose

This document stores the authoritative assignment requirements for Project 3 in a
single repo-local specification so planning and implementation do not depend on
chat history alone.

This project requires the team to extend one selected Project 2 distributed
system with simplified implementations of:

- Two-Phase Commit (2PC)
- Raft leader election
- Raft log replication

The implementation MUST use gRPC for node-to-node communication and Docker for
containerization. The final solution MUST include source code, a README, and a
report.

## Assignment Scope

### Summary

The project goal is to implement simplified consensus behavior on top of one
selected existing distributed system. The assignment is divided into:

1. repository selection by bidding,
2. 2PC voting phase,
3. 2PC decision phase,
4. simplified Raft leader election,
5. simplified Raft log replication,
6. five Raft-related failure test cases,
7. final deliverables.

### Required Background Reading

Before implementation begins, the assignment states that the team SHOULD read:

- Section 2: Consensus Algorithms
- Section 3: 2PC
- Section 4: Raft

### Technology Constraints

The implementation MUST satisfy all of the following:

- use gRPC for communication between nodes/processes,
- use Docker for containerization,
- support communication among at least 5 containerized nodes,
- define the required RPCs and data structures in `.proto` files,
- print required RPC activity logs in the specified formats.

### Q0. Bidding / Upstream Selection Context

Each group MUST select three distinct Project 2 implementations created by other
groups. A group MUST NOT select its own implementation. Each implementation may
be capped in how many groups can select it.

For this repo, Q0 is already resolved operationally because the team has chosen
and forked one candidate implementation. The remaining project work extends that
chosen baseline.

### Single-Functionality Extension Constraint

For implementation planning in this repo, the extension MUST remain bounded to a
single chosen functionality on top of the selected upstream system. The team
does **not** need to redesign or fully re-implement the entire original system.
The team needs one workable extension surface that supports all required Project
3 features.

## 2PC Requirements

## Q1. 2PC Voting Phase

The team MUST implement the voting phase of 2PC on the same selected
implementation.

### Required Behavior

The implementation MUST support the following voting-phase steps:

1. A coordinator sends a `vote-request` message to all participants.
2. When a participant receives a `vote-request`, it returns either:
   - `vote-commit`, indicating it is prepared to locally commit its part of the
     transaction, or
   - `vote-abort`, indicating it cannot commit.

### Proto / RPC Requirements

The team MUST define its own gRPC data structures and service methods in a
`.proto` file for this phase.

### Deployment Requirement

The implementation MUST be containerized for each node, and at least 5
containerized nodes MUST be able to communicate with each other.

### Simplification Boundary

The assignment explicitly allows 2PC to support only a single functionality.
Therefore, the implementation MAY restrict 2PC to one chosen operation in the
selected system.

## Q2. 2PC Decision Phase

The team MUST implement the decision phase of 2PC on the same selected
implementation used in Q1.

### Required Behavior

The implementation MUST support the following decision-phase steps:

1. The coordinator collects all participant votes.
2. If all participants vote to commit, the coordinator decides to commit and
   sends `global-commit` to all participants.
3. If any participant votes to abort, the coordinator decides to abort and sends
   `global-abort` to all participants.
4. Each participant that voted to commit waits for the coordinator’s final
   decision.
5. If a participant receives `global-commit`, it locally commits.
6. If a participant receives `global-abort`, it locally aborts.

### Same-Node Inter-Phase Communication

The assignment states that to allow voting and decision phases implemented in
different languages to operate on the same node, the team MUST use gRPC for
communication between these two phases **within the same node/container**.

Therefore, the implementation MUST include intra-node gRPC communication between
the two 2PC phases, and the necessary messages / RPC methods MUST be defined in
the same `.proto` file created for Q1.

### RPC Logging Requirement for 2PC

For **each** RPC method call in both voting and decision phases, the
implementation MUST print a client-side log message in the following format:

`Phase <phase_name> of Node <node_id> sends RPC <rpc_name> to Phase <phase_name> of Node <node_id>`

The assignment also states that the server side should print a message in the
format:

`Phase <phase_name> of Node <node_id> sends RPC <rpc_name> to Phase <phase_name> of Node <node_id>`

This wording appears to contain a likely typo because it repeats “sends RPC” for
the server side. Until clarified, the team MUST treat the exact assignment text
as authoritative, but SHOULD record this ambiguity in the project decision log.

### Deployment Requirement

The implementation MUST be containerized for each node, and at least 5
containerized nodes MUST be able to communicate with each other.

## Raft Requirements

## Q3. Simplified Raft Leader Election

The team MUST implement the leader election portion of a simplified Raft system
on one selected implementation.

### Proto / RPC Requirements

The team MUST define the necessary gRPC data structures and service methods in a
**new** `.proto` file for Raft.

### Initial State Requirement

At program start, all processes/nodes MUST begin in the `follower` state.

### Timeout Requirements

The implementation MUST use both of the following timeout settings:

- Heartbeat timeout: exactly 1 second for all processes
- Election timeout: randomly chosen from the fixed interval `[1.5 seconds, 3 seconds]`
  for each process/node

### Required Leader Election Behavior

If a follower does not receive a heartbeat from a leader within its randomized
election timeout, it MUST assume no leader currently exists and transition to
the `candidate` state.

As a candidate, a node MUST:

1. increment its term,
2. vote for itself,
3. send `RequestVote` RPCs to the other processes in the cluster.

If a candidate receives a majority of votes, it MUST become the leader and
begin sending periodic `AppendEntries` RPCs as heartbeats to all other
processes.

If another candidate wins first, or if the node fails to gather a majority, it
MUST revert to the follower state and wait for further heartbeats.

### RPC Logging Requirement for Raft

For **each** RPC method being called, the implementation MUST print:

Client side:

`Node <node_id> sends RPC <rpc_name> to Node <node_id>`

Server side:

`Node <node_id> runs RPC <rpc_name> called by Node <node_id>`

### Deployment Requirement

The implementation MUST be containerized for each node, and at least 5
containerized nodes MUST be able to communicate with each other.

## Q4. Simplified Raft Log Replication

The team MUST implement simplified Raft log replication on top of the same
selected implementation used in Q3.

### Proto / RPC Requirements

The team MUST define the necessary gRPC data structures and service methods in
the **same** `.proto` file created in Q3.

### Log Requirements

Each process/node MUST maintain a log of operations. The log MUST contain:

1. operations that have already been committed,
2. operations that are pending.

### Required Behavior for Client Requests

For each client request to execute operation `o`, the implementation MUST
support the following behavior:

1. The current leader receives the request.
2. The leader appends `<o, t, k+1>` to its log, where:
   - `o` is the operation,
   - `t` is the current term,
   - `k+1` is the next log index.
3. On the next heartbeat, the leader sends its **entire log** to all other
   servers, along with the current value of `c`, where `c` is the index of the
   most recently committed operation.
4. Each follower copies the entire log and returns an ACK to the leader.
5. Each follower checks and executes operations so that all operations up to and
   including index `c` have been executed.
6. When the leader receives a majority of ACKs, the leader executes all pending
   operations, returns the results to the client, and increments `c`.

### Client Forwarding Requirement

A client may connect to **any** process, not necessarily the leader. Therefore,
the implementation MUST support request forwarding from a non-leader receiver to
the current leader.

### RPC Logging Requirement for Raft

For **each** RPC method being called, the implementation MUST print:

Client side:

`Node <node_id> sends RPC <rpc_name> to Node <node_id>`

Server side:

`Node <node_id> runs RPC <rpc_name> called by Node <node_id>`

### Deployment Requirement

The implementation MUST be containerized for each node, and at least 5
containerized nodes MUST be able to communicate with each other.

## Testing Requirements

## Q5. Failure-Oriented Test Cases

The team MUST design and implement 5 different test cases for the Raft
implementation, and these test cases MUST relate to failures.

The assignment gives “a new node entering the system” as an example of one such
test case.

### Documentation / Evidence Requirement

The team MUST document the 5 test cases and MUST include captured screenshots of
their execution in the final report.

### Practical Interpretation

The test matrix SHOULD cover fault or disruption scenarios that exercise the
simplified Raft design, such as:

- leader failure,
- follower failure,
- split vote / election retry,
- node restart or new node entry,
- temporary communication loss or delayed heartbeat behavior.

The exact five tests MAY vary, but the final set MUST be failure-related.

## Deliverables

The final submission MUST include all required project artifacts in a zipped
folder uploaded to Canvas.

### Required Submission Contents

The zipped deliverable MUST include:

- source code for the 2PC implementation,
- source code for the Raft implementation,
- a `README` file,
- a report.

### README Requirements

The README MUST explain:

1. how to compile and run the program,
2. anything unusual about the solution that the TA should know,
3. any external sources referenced while working on the solution.

The README MUST also include the team’s GitHub link.

### Report Requirements

The report MUST:

1. clearly list the team members’ names,
2. clearly list the team members’ student IDs,
3. clearly state which student worked on which part of the project,
4. include captured screenshots of the required failure-oriented Raft tests,
5. include the GitHub link.

### Penalty Note

The assignment states that the late penalty is 20 points per day.

## Open Questions

The following items are ambiguous or need explicit handling during planning:

1. **2PC server-side log format typo**
   - The Q2 instructions appear to repeat the client-side “sends RPC” format for
     the server side.
   - The team should record whether it follows the text literally or uses a more
     natural server-side wording while documenting the reason.

2. **Exact single functionality to extend**
   - The assignment allows 2PC to support a single functionality.
   - The repo-local planning docs must explicitly define which functionality the
     team chooses to extend.

3. **Whether voting phase and decision phase actually need different languages**
   - The assignment mentions different languages, but it does not require them.
   - The safe interpretation is that intra-node communication between the phases
     MUST still use gRPC even if both phases use the same language.

4. **Meaning of “new node entering the system” in simplified Raft**
   - The example appears in Q5, but the simplified Raft requirements do not
     fully define membership change semantics.
   - The team should interpret such a test in a bounded way that fits the
     simplified implementation.

5. **Selection cap in Q0**
   - The assignment mentions “up to three groups (or another cap defined by the
     instructor).”
   - This is administratively relevant but should not affect implementation now
     that the forked baseline is chosen.

## Traceability Notes

This document should act as the top-level requirement source for repo-local
planning. Derived planning and implementation documents should trace back here.

Recommended downstream traceability surfaces:

- `docs/spec/01_repo_baseline_audit.md`
- `docs/spec/02_extension_scope.md`
- `docs/spec/03_2pc_contract.md`
- `docs/spec/04_raft_election_contract.md`
- `docs/spec/05_raft_log_replication_contract.md`
- `docs/spec/06_failure_test_matrix.md`

### Suggested Normative Requirement IDs

The following IDs are recommended for downstream traceability:

- `S00-M01` — The project MUST extend one selected existing distributed system.
- `S00-M02` — The implementation MUST use gRPC for node/process communication.
- `S00-M03` — The implementation MUST use Docker for containerization.
- `S00-M04` — At least 5 containerized nodes MUST communicate successfully.
- `S00-M05` — 2PC voting MUST implement vote-request / vote-commit /
  vote-abort behavior.
- `S00-M06` — 2PC decision MUST implement global-commit / global-abort behavior.
- `S00-M07` — Intra-node communication between 2PC phases MUST use gRPC.
- `S00-M08` — 2PC RPC logging MUST follow the required assignment format.
- `S00-M09` — Raft leader election MUST implement follower / candidate / leader
  roles with the required timeout behavior.
- `S00-M10` — Heartbeat timeout MUST be 1 second.
- `S00-M11` — Election timeout MUST be randomized in `[1.5s, 3s]`.
- `S00-M12` — Raft RPC logging MUST follow the required assignment format.
- `S00-M13` — Raft log replication MUST maintain committed and pending
  operations.
- `S00-M14` — The leader MUST send the entire log plus commit index `c` on the
  next heartbeat.
- `S00-M15` — Non-leader nodes MUST forward client requests to the leader.
- `S00-M16` — The project MUST include 5 failure-related Raft test cases.
- `S00-M17` — The final submission MUST include source code, README, and report.
- `S00-M18` — The README MUST include build/run instructions, unusual solution
  notes, referenced external sources, and the GitHub link.
- `S00-M19` — The report MUST include team identities, work division, failure
  test screenshots, and the GitHub link.
```