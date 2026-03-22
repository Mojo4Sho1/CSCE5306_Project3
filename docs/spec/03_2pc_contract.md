# 2PC Implementation Contract (Q1 + Q2)

## Overview

Implement Two-Phase Commit (2PC) for replicated player location updates. When a client sends an `UpdateLocation` command, the coordinator node runs 2PC across all participant nodes to decide whether to commit or abort the state change.

**Traceability**: S00-M05, S00-M06, S00-M07, S00-M08

## Proto Definition: `2pc.proto`

Create a new file `server/2pc.proto`:

```protobuf
syntax = "proto3";

package twopc;

// ============================================================
// Inter-node 2PC RPCs (coordinator <-> participants)
// ============================================================

service TwoPhaseCommitService {
  // Q1: Voting Phase
  rpc VoteRequest (VoteRequestMessage) returns (VoteResponse);

  // Q2: Decision Phase
  rpc GlobalDecision (DecisionMessage) returns (DecisionAck);
}

// ============================================================
// Intra-node RPCs (voting phase <-> decision phase on same node)
// Assignment requires gRPC between phases even within one container.
// ============================================================

service IntraNodePhaseService {
  // Decision phase notifies voting phase of the final outcome
  rpc NotifyDecision (IntraDecisionNotification) returns (IntraDecisionAck);

  // Voting phase reports its vote to the decision phase
  rpc ReportVote (IntraVoteReport) returns (IntraVoteAck);
}

// ============================================================
// Messages
// ============================================================

message LocationUpdate {
  string user_jwt = 1;
  double x = 2;
  double y = 3;
}

message VoteRequestMessage {
  int32 coordinator_id = 1;
  int32 transaction_id = 2;
  LocationUpdate proposed_update = 3;
}

message VoteResponse {
  int32 participant_id = 1;
  int32 transaction_id = 2;
  bool vote_commit = 3;       // true = vote-commit, false = vote-abort
  string reason = 4;           // reason for abort, if any
}

message DecisionMessage {
  int32 coordinator_id = 1;
  int32 transaction_id = 2;
  bool global_commit = 3;      // true = global-commit, false = global-abort
  LocationUpdate update = 4;   // the update to apply (if committing)
}

message DecisionAck {
  int32 participant_id = 1;
  int32 transaction_id = 2;
  bool applied = 3;
}

// Intra-node messages
message IntraDecisionNotification {
  int32 transaction_id = 1;
  bool global_commit = 2;
}

message IntraDecisionAck {
  bool acknowledged = 1;
}

message IntraVoteReport {
  int32 transaction_id = 1;
  bool vote_commit = 2;
}

message IntraVoteAck {
  bool acknowledged = 1;
}
```

## Generate stubs

After creating `2pc.proto`, generate Python stubs:

```bash
cd server
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. 2pc.proto
```

This produces `twopc_pb2.py` and `twopc_pb2_grpc.py` (or `2pc_pb2.py` / `2pc_pb2_grpc.py` depending on protoc naming — adjust imports accordingly).

**Dockerfile update**: Add `grpcio-tools` to pip install, or pre-generate stubs and copy them in.

## Coordinator Flow (Q1 + Q2)

One node acts as the 2PC coordinator for each transaction. For simplicity, designate **Node 1** (fishing1, port 50051) as the permanent coordinator. All other nodes are participants.

### Q1 — Voting Phase

1. Client sends `UpdateLocation` to the coordinator (Node 1).
2. Coordinator creates a transaction ID and packages the proposed location update.
3. Coordinator sends `VoteRequest` RPC to every participant node (Nodes 2-5+).
4. Each participant checks a precondition:
   - **Vote-commit**: The user exists (has logged in) OR the update is valid (coordinates within bounds, no conflicting lock, etc.). For simplicity, participants can always vote-commit unless they want to demonstrate abort behavior.
   - **Vote-abort**: A configurable condition to test abort paths (e.g., reject if x < 0 or y < 0).
5. Each participant returns `VoteResponse` with `vote_commit = true/false`.

**Logging** (client-side, i.e., the coordinator sending the RPC):
```
Phase voting of Node 1 sends RPC VoteRequest to Phase voting of Node 2
```

**Logging** (server-side, i.e., the participant receiving the RPC):
```
Phase voting of Node 2 sends RPC VoteRequest to Phase voting of Node 1
```

### Q2 — Decision Phase

1. Coordinator collects all `VoteResponse` messages.
2. If ALL votes are `vote_commit = true` → coordinator decides **global-commit**.
3. If ANY vote is `vote_commit = false` → coordinator decides **global-abort**.
4. Coordinator sends `GlobalDecision` RPC to every participant.
5. Each participant:
   - On `global_commit = true`: applies the location update to local state (`state.update_user(jwt, x, y)`).
   - On `global_commit = false`: discards the proposed update.

**Logging** (client-side, coordinator sending decision):
```
Phase decision of Node 1 sends RPC GlobalDecision to Phase decision of Node 2
```

**Logging** (server-side, participant receiving decision):
```
Phase decision of Node 2 sends RPC GlobalDecision to Phase decision of Node 1
```

### Intra-Node Communication

Within each container, the voting-phase handler and decision-phase handler must communicate via gRPC (not direct function calls). Implementation options:

- Run two gRPC servers on different ports within the same container (e.g., main server on 50051, intra-node on 60051).
- OR run them as separate services in the same gRPC server but use the `IntraNodePhaseService` RPCs for cross-phase communication.

**Recommended approach**: Run a single gRPC server per container that hosts both `TwoPhaseCommitService` and `IntraNodePhaseService`. The voting handler calls `IntraNodePhaseService.ReportVote` on localhost to pass its vote to the decision handler, and the decision handler calls `IntraNodePhaseService.NotifyDecision` to inform the voting handler of the outcome.

**Logging for intra-node RPCs** follows the same format:
```
Phase voting of Node 2 sends RPC ReportVote to Phase decision of Node 2
Phase decision of Node 2 sends RPC NotifyDecision to Phase voting of Node 2
```

## Integration with Existing Server

- Modify `server/server.py` to import 2PC stubs and register `TwoPhaseCommitService` + `IntraNodePhaseService` on the gRPC server.
- The `UpdateLocation` handler should trigger the 2PC coordinator flow (if this node is the coordinator) or participate in voting (if this node is a participant).
- Each node needs to know the addresses of all other nodes. Use environment variables or a config list (e.g., `PEERS=fishing2:50051,fishing3:50051,...`).
- Update `server/docker-compose.yml` to pass peer addresses as environment variables.

## Docker Integration

Update `server/docker-compose.yml`:
- Add environment variable for node ID (e.g., `NODE_ID=1`)
- Add environment variable for peer list (e.g., `PEERS=fishing2:50051,fishing3:50051,...`)
- Add environment variable for coordinator designation (e.g., `IS_COORDINATOR=true` on fishing1)
- Ensure at least 5 nodes are defined

## Acceptance Criteria

- [ ] `2pc.proto` exists with all required messages and services
- [ ] Generated stubs compile without errors
- [ ] Coordinator sends VoteRequest to all participants and collects responses
- [ ] Coordinator sends GlobalDecision based on unanimous vote
- [ ] Participants apply or discard updates based on decision
- [ ] Intra-node gRPC communication between voting and decision phases works
- [ ] All RPC calls produce the required log format
- [ ] 5+ containerized nodes communicate successfully
