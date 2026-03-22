# Raft Log Replication Contract (Q4)

## Overview

Extend the Raft implementation from Q3 with log replication. The leader accepts client requests (location updates), appends them to its log, and replicates the entire log to followers via heartbeat AppendEntries RPCs. Once a majority acknowledge, the leader commits and executes the operation.

**Traceability**: S00-M13, S00-M14, S00-M15

## Proto Additions

No new proto file — extend the existing `raft.proto` from Q3. The `LogEntry`, `AppendEntriesRequest` (with entries + commit_index), and `ForwardRequest` messages are already defined in the Q3 proto sketch.

## Log Entry Structure

Each log entry is a tuple `<operation, term, index>`:

```python
# In-memory log representation
class LogEntry:
    def __init__(self, operation: str, term: int, index: int):
        self.operation = operation  # e.g., "UpdateLocation:user1:pass1:10.5:20.3"
        self.term = term
        self.index = index
```

- **operation**: string encoding of the UpdateLocation command (jwt + coordinates)
- **term**: the leader's current term when the entry was created
- **index**: sequential, starting at 1 (k+1 where k is the last index)

## Leader Receives Client Request

1. Client sends an UpdateLocation request (via the existing `FishingService.UpdateLocation` or a new dedicated RPC).
2. If this node is the leader:
   a. Create a new `LogEntry`: `<operation=UpdateLocation(jwt,x,y), term=current_term, index=last_index+1>`
   b. Append to the leader's local log.
   c. The entry is **pending** (not yet committed).
   d. On the **next heartbeat** (within 1 second), the leader sends its **entire log** plus the current **commit_index `c`** to all followers via `AppendEntries`.
3. If this node is NOT the leader:
   a. Forward the request to the current leader via `ForwardRequest` RPC.
   b. Return the leader's response to the client.

## Heartbeat with Log Replication

The leader's periodic heartbeat (every 1 second) now includes:
- `entries`: the **entire log** (all entries, committed and pending)
- `commit_index`: the index of the most recently committed entry (`c`)

This is a simplified version of Raft — the assignment explicitly says to send the entire log, not incremental entries.

## Follower Receives AppendEntries

1. Follower receives `AppendEntries` with `entries` and `commit_index`.
2. Follower **replaces its entire log** with the received entries (simplified — no conflict resolution needed since we send the full log).
3. Follower checks: for all entries with `index <= commit_index`, execute the operation if not already executed.
   - "Execute" means: apply the location update to local state (`state.update_user(jwt, x, y)`).
4. Follower returns `AppendEntriesResponse` with `success = true` (ACK).

## Leader Commits

1. Leader waits for ACKs from followers.
2. When the leader has received ACKs from a **majority** (including itself):
   - Execute all pending operations (entries with `index > commit_index` up to the latest).
   - Increment `commit_index` (`c`) to the latest executed entry's index.
   - Return results to the client.
3. "Majority" = more than half of total nodes. For 5 nodes, need 3 (including leader).

## Client Forwarding

Assignment requirement: a client can connect to ANY node. Non-leader nodes must forward to the leader.

```python
# In the FishingService or a wrapper
def handle_client_update(self, jwt, x, y):
    if self.raft_node.role == "leader":
        # Append to log, will be replicated on next heartbeat
        self.raft_node.append_log_entry(f"UpdateLocation:{jwt}:{x}:{y}")
        # Wait for commit (blocking or callback-based)
        result = self.raft_node.wait_for_commit(entry_index)
        return result
    else:
        # Forward to leader
        leader_address = self.raft_node.get_leader_address()
        if leader_address:
            # Call ForwardRequest RPC on leader
            response = forward_to_leader(leader_address, jwt, x, y)
            return response
        else:
            return error("No leader available")
```

## State Variables (extending Q3)

```python
# Add to RaftNode from Q3:
self.log = []                    # list of LogEntry
self.commit_index = 0            # index of highest committed entry (c)
self.last_applied = 0            # index of highest applied entry
self.pending_clients = {}        # index -> callback for waiting clients
```

## RPC Logging

Same format as Q3:

**Client side** (sender):
```
Node <sender_id> sends RPC AppendEntries to Node <receiver_id>
Node <sender_id> sends RPC ForwardRequest to Node <receiver_id>
```

**Server side** (receiver):
```
Node <receiver_id> runs RPC AppendEntries called by Node <sender_id>
Node <receiver_id> runs RPC ForwardRequest called by Node <sender_id>
```

## Integration Notes

- The `AppendEntries` RPC handler from Q3 needs to be extended to process log entries (not just heartbeat).
- The leader's heartbeat thread now populates `entries` and `commit_index` in every `AppendEntriesRequest`.
- The existing `UpdateLocation` handler in `FishingService` should be modified to route through the Raft log instead of directly updating state.
- Consider adding a simple blocking mechanism for the client to wait until its entry is committed (e.g., `threading.Event` per pending entry).

## Acceptance Criteria

- [ ] Leader appends client requests to log as `<operation, term, index>`
- [ ] Leader sends entire log + commit_index on each heartbeat
- [ ] Followers copy entire log and execute committed entries
- [ ] Leader commits after receiving majority ACKs
- [ ] Non-leader nodes forward client requests to leader
- [ ] Commit index `c` is correctly tracked and incremented
- [ ] All RPC calls produce the required log format
- [ ] State is consistent across all nodes after committed operations
