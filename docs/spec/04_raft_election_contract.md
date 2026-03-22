# Raft Leader Election Contract (Q3)

## Overview

Implement simplified Raft leader election. All nodes start as followers. When a follower's election timeout expires without receiving a heartbeat, it becomes a candidate and initiates an election. The winner becomes leader and sends periodic heartbeats.

**Traceability**: S00-M09, S00-M10, S00-M11, S00-M12

## Proto Definition: `raft.proto`

Create a new file `server/raft.proto`:

```protobuf
syntax = "proto3";

package raft;

service RaftService {
  // Leader election
  rpc RequestVote (RequestVoteRequest) returns (RequestVoteResponse);

  // Heartbeat + log replication (Q4 extends this for log entries)
  rpc AppendEntries (AppendEntriesRequest) returns (AppendEntriesResponse);

  // Client request forwarding (Q4: non-leader forwards to leader)
  rpc ForwardRequest (ForwardRequestMessage) returns (ForwardRequestResponse);
}

// ============================================================
// Leader Election Messages
// ============================================================

message RequestVoteRequest {
  int32 term = 1;              // candidate's term
  int32 candidate_id = 2;      // candidate requesting vote
  int32 last_log_index = 3;    // index of candidate's last log entry (Q4)
  int32 last_log_term = 4;     // term of candidate's last log entry (Q4)
}

message RequestVoteResponse {
  int32 term = 1;              // current term of the voter (for candidate to update itself)
  bool vote_granted = 2;       // true = vote granted
  int32 voter_id = 3;          // ID of the responding node
}

// ============================================================
// AppendEntries (heartbeat in Q3, log replication in Q4)
// ============================================================

message LogEntry {
  string operation = 1;        // the operation (e.g., "UpdateLocation:jwt:x:y")
  int32 term = 2;              // term when entry was created
  int32 index = 3;             // log index
}

message AppendEntriesRequest {
  int32 term = 1;              // leader's term
  int32 leader_id = 2;         // so followers know who the leader is
  repeated LogEntry entries = 3; // empty for heartbeat (Q3), populated for replication (Q4)
  int32 commit_index = 4;      // index of highest committed entry (Q4)
}

message AppendEntriesResponse {
  int32 term = 1;              // current term of the responder
  bool success = 2;            // true if follower accepted
  int32 follower_id = 3;       // ID of the responding node
}

// ============================================================
// Client Forwarding (Q4)
// ============================================================

message ForwardRequestMessage {
  string user_jwt = 1;
  double x = 2;
  double y = 3;
}

message ForwardRequestResponse {
  bool success = 1;
  string message = 2;
}
```

## Generate stubs

```bash
cd server
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto
```

## State Machine

Each node maintains:

```python
class RaftNode:
    def __init__(self, node_id, peers):
        self.node_id = node_id
        self.peers = peers                    # list of (peer_id, address) tuples

        # Persistent state
        self.current_term = 0
        self.voted_for = None                 # candidate_id voted for in current term
        self.log = []                         # list of LogEntry (Q4)

        # Volatile state
        self.role = "follower"                # "follower", "candidate", "leader"
        self.leader_id = None                 # known leader
        self.commit_index = 0                 # highest committed log index (Q4)

        # Timers
        self.election_timeout = random.uniform(1.5, 3.0)  # seconds
        self.heartbeat_interval = 1.0                       # seconds
        self.last_heartbeat_time = time.time()
```

### State Transitions

```
FOLLOWER:
  - Receives AppendEntries (heartbeat) → reset election timer, stay follower
  - Election timeout expires → become CANDIDATE

CANDIDATE:
  - Increment term, vote for self, send RequestVote to all peers
  - Receives majority votes → become LEADER
  - Receives AppendEntries from valid leader (term >= current) → become FOLLOWER
  - Receives RequestVote with higher term → become FOLLOWER, grant vote
  - Election timeout expires without majority → start new election (increment term, retry)

LEADER:
  - Send AppendEntries (heartbeat) every 1 second to all peers
  - Receives AppendEntries or RequestVote with higher term → become FOLLOWER
```

## Timeout Configuration

- **Heartbeat interval**: exactly 1 second (all nodes)
- **Election timeout**: random in [1.5s, 3.0s] per node, re-randomized on each new election
- The election timeout should be significantly larger than heartbeat interval to avoid unnecessary elections

## RequestVote Flow

1. Candidate increments `current_term`, sets `voted_for = self.node_id`.
2. Candidate sends `RequestVote` RPC to all peers in parallel.
3. Each peer receiving `RequestVote`:
   - If `request.term < self.current_term` → reject (vote_granted = false)
   - If `request.term > self.current_term` → update term, become follower, grant vote
   - If `request.term == self.current_term` and (`voted_for is None` or `voted_for == candidate_id`) → grant vote
   - Otherwise → reject
   - Return current term in response (so candidate can step down if stale)
4. Candidate counts votes (including self-vote):
   - If votes > len(peers) / 2 → become leader, start sending heartbeats
   - If receives AppendEntries from node with term >= current → step down to follower
   - If election timeout expires → start new election

## Heartbeat Flow

1. Leader sends `AppendEntries` RPC to all peers every 1 second.
2. For Q3, `entries` is empty (heartbeat only). Q4 adds log entries.
3. Each follower receiving AppendEntries:
   - If `request.term < self.current_term` → reject
   - Otherwise → accept, reset election timer, update `leader_id`
   - Return current term in response

## RPC Logging

**Client side** (node sending the RPC):
```
Node <sender_id> sends RPC RequestVote to Node <receiver_id>
Node <sender_id> sends RPC AppendEntries to Node <receiver_id>
```

**Server side** (node receiving the RPC):
```
Node <receiver_id> runs RPC RequestVote called by Node <sender_id>
Node <receiver_id> runs RPC AppendEntries called by Node <sender_id>
```

## Integration with Existing Server

- Create a `raft_node.py` module in `server/` that implements the `RaftNode` class and `RaftService` servicer.
- Modify `server/server.py` to:
  - Import and instantiate `RaftNode`
  - Register `RaftService` on the same gRPC server alongside `FishingService`
  - Start the election timeout monitor in a background thread
  - Start the heartbeat sender in a background thread (when leader)
- Node ID and peer addresses passed via environment variables (same as 2PC setup).

## Docker Integration

Same compose environment as 2PC. Each node needs:
- `NODE_ID` — integer identifier
- `PEERS` — comma-separated list of `host:port` for all other nodes

## Threading Model

- **Main thread**: gRPC server (handles incoming RPCs)
- **Timer thread**: monitors election timeout, triggers candidate transition
- **Heartbeat thread** (leader only): sends periodic AppendEntries to all peers
- Use `threading.Lock` to protect shared state (term, role, voted_for, etc.)

## Acceptance Criteria

- [ ] `raft.proto` exists with RequestVote and AppendEntries RPCs
- [ ] All nodes start as followers
- [ ] Election timeout triggers candidate transition
- [ ] Candidate sends RequestVote and collects votes
- [ ] Majority vote makes candidate the leader
- [ ] Leader sends heartbeats every 1 second
- [ ] Followers reset election timer on heartbeat receipt
- [ ] Higher-term messages cause step-down
- [ ] Split votes resolve via randomized timeout
- [ ] All RPC calls produce the required log format
- [ ] 5+ containerized nodes elect a leader successfully
