# Failure Test Matrix (Q5)

## Overview

Design and implement 5 failure-related test cases for the Raft implementation. Each test must demonstrate fault tolerance behavior. Results must be documented with screenshots for the final report.

**Traceability**: S00-M16

## Test Case 1: Leader Crash and Re-Election

**Description**: Kill the current leader node and verify that a new leader is elected within the election timeout window.

**Setup**:
1. Start 5-node cluster, wait for initial leader election.
2. Identify which node is the current leader (from logs).
3. Send a few location updates to verify the cluster is working.

**Action**:
```bash
docker stop fishing<leader_id>
```

**Expected Behavior**:
- Remaining followers detect missing heartbeat (election timeout: 1.5-3s).
- One follower transitions to candidate, starts election.
- New leader is elected within ~3-6 seconds.
- Client can resume sending updates to a non-stopped node (which forwards to new leader).

**What to Verify**:
- Logs show election timeout triggered on at least one follower.
- Logs show RequestVote RPCs sent and votes granted.
- Logs show new leader sending heartbeats.
- Client operations succeed after re-election.

**Screenshot**: Capture terminal output showing the leader crash, election process, and resumed operations.

## Test Case 2: Follower Crash and Recovery

**Description**: Kill a follower node, verify the cluster continues operating, then restart the follower and verify it catches up.

**Setup**:
1. Start 5-node cluster, wait for leader election.
2. Send several location updates (so the log has entries).

**Action**:
```bash
docker stop fishing<follower_id>
# Wait, send more updates
docker start fishing<follower_id>
```

**Expected Behavior**:
- Cluster continues with 4 nodes (majority still available).
- New updates are committed (leader gets 3/4 remaining ACKs = majority of 5).
- When follower restarts, it receives the full log on next heartbeat.
- Restarted follower catches up to current commit index.

**What to Verify**:
- Leader logs show it continues sending heartbeats to remaining nodes.
- New commits succeed while follower is down.
- Restarted follower's log matches leader's log after recovery.

**Screenshot**: Capture logs showing continued operation during failure and log catch-up after recovery.

## Test Case 3: Network Partition (Temporary)

**Description**: Simulate a network partition by pausing a container, then unpause it to simulate recovery.

**Setup**:
1. Start 5-node cluster with an established leader and some log entries.

**Action**:
```bash
docker pause fishing<node_id>
# Wait 5-10 seconds, send updates
docker unpause fishing<node_id>
```

**Expected Behavior**:
- Paused node stops responding to heartbeats and RPCs.
- If the paused node is the leader: re-election occurs among remaining nodes.
- If the paused node is a follower: cluster continues (majority intact).
- On unpause: node receives heartbeat, discovers current term, syncs log.
- If it was a stale leader: it steps down upon seeing higher term.

**What to Verify**:
- Cluster correctly handles the "disappeared" node.
- Unpaused node rejoins as follower with correct term and log.
- No split-brain: only one leader exists at any time.

**Screenshot**: Capture the pause, cluster reaction, unpause, and resynchronization.

## Test Case 4: New Node Joining the Cluster

**Description**: Start a 6th node after the cluster is already running and verify it integrates as a follower.

**Setup**:
1. Start 5-node cluster, wait for leader election, send some updates.

**Action**:
```bash
docker compose up -d fishing6
```

(Requires fishing6 to be defined in docker-compose.yml but not started initially, e.g., with `profiles` or manual start.)

**Expected Behavior**:
- New node starts as a follower.
- New node receives heartbeat from the leader within 1 second.
- New node accepts the leader's full log via AppendEntries.
- New node executes all committed entries to catch up.

**What to Verify**:
- New node logs show it received AppendEntries and synced log.
- New node's state matches other nodes after sync.
- Cluster now has 6 nodes; leader adjusts majority calculation if needed.

**Screenshot**: Capture the new node startup, log sync, and cluster membership.

## Test Case 5: Split Vote and Election Retry

**Description**: Demonstrate that when no candidate gets a majority in an election, a new election starts with re-randomized timeouts.

**Setup**:
1. Start 5-node cluster.
2. Kill the current leader to trigger an election.
3. To increase the chance of a split vote: kill 2 nodes (so only 3 remain), or manipulate timing.

**Action**:
```bash
# Kill leader and one follower simultaneously to create tight race
docker stop fishing<leader_id> fishing<follower_id>
```

Alternatively, if split votes are hard to reliably trigger, demonstrate the *mechanism*:
- Show in logs that election timeouts are randomized (different values per node).
- Show that if a candidate doesn't get majority within its timeout, it starts a new term.

**Expected Behavior**:
- Multiple candidates may start elections in the same term.
- If no candidate gets majority, the term ends without a leader.
- New election starts with incremented term and fresh random timeouts.
- Eventually one candidate wins.

**What to Verify**:
- Logs show multiple RequestVote rounds (different terms).
- Logs show randomized election timeouts (different per node).
- A leader is eventually elected.

**Screenshot**: Capture the election attempts, term increments, and final leader selection.

## Docker Commands Reference

```bash
# Stop a specific node
docker stop fishing<N>

# Start a stopped node
docker start fishing<N>

# Pause (simulate network partition)
docker pause fishing<N>

# Unpause
docker unpause fishing<N>

# View logs for a specific node
docker logs -f fishing<N>

# Start a new node (if defined in compose)
docker compose up -d fishing6
```

## Evidence Collection

For each test case:
1. Run the test scenario.
2. Capture terminal screenshots showing the relevant log output.
3. Annotate screenshots with test case number and key observations.
4. Include all 5 test screenshots in the final report.
