# CSCE 5306 Project 3 — Distributed Consensus (2PC + Raft)

**GitHub:** <https://github.com/Mojo4Sho1/CSCE5306_Project3>

This project extends a baseline multiplayer fishing game (Python gRPC, 6-node
Docker cluster) with two distributed consensus algorithms:

- **Two-Phase Commit (2PC)** — coordinator-driven voting and decision phases
  for atomic location updates (Q1 + Q2).
- **Raft** — leader election with randomised timeouts and log replication with
  majority commit (Q3 + Q4).
- **Failure Tests** — five fault-tolerance scenarios exercising leader crash,
  follower crash, network partition, late startup of a preconfigured sixth
  node, and split-vote re-election (Q5).

The final written report is maintained separately in Overleaf and is
intentionally not versioned in this repository.

---

## Project Structure

```
.
├── client/                  # Interactive Python client
│   └── client.py
├── server/                  # 6-node cluster implementation
│   ├── server.py            # Main server (2PC + Raft + fishing service)
│   ├── raft_node.py         # Raft state machine and gRPC servicer
│   ├── fishing.proto        # Baseline fishing service (unmodified)
│   ├── twopc.proto          # 2PC gRPC service definitions
│   ├── raft.proto           # Raft gRPC service definitions
│   ├── docker-compose.yml   # 6-node Docker Compose cluster
│   └── Dockerfile
├── tests/
│   ├── unit/                # 55 unit tests (no Docker required)
│   └── smoke/               # Docker integration tests
├── Makefile                 # Build, test, and cluster management
└── AGENTS.md                # Full project context and architecture
```

---

## How to Compile and Run

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- GNU Make

### Quick Start

```bash
# Install Python dependencies
make install

# (Optional) Regenerate gRPC stubs from proto files
make proto

# Run unit tests (no Docker required) — 55 tests
make test

# Run the full quality gate
make check

# Start the 6-node Docker cluster
make up

# Run the interactive client (cluster must be running)
cd client && python3 client.py

# Stream logs from all nodes
make logs

# Tear down the cluster
make down
```

### Other Make Targets

| Target          | Description                              |
|-----------------|------------------------------------------|
| `make lint`     | Run ruff linter                          |
| `make format`   | Auto-format with ruff                    |
| `make check`    | Quality gate (lint + unit tests)         |
| `make proto-2pc`| Regenerate only 2PC stubs                |
| `make proto-raft`| Regenerate only Raft stubs              |
| `make test-smoke`| Run Docker integration tests            |

## Running the 5 Raft Failure Tests

This section is the operator runbook for the Q5 manual Raft tests. Follow it
as written and use the log output plus screenshots as the evidence for the
final report.

### Shared Setup

Use three terminals for all five tests unless a test case says to restart from
scratch.

**Terminal 1 — start the cluster**

```bash
make up
```

**Terminal 2 — watch cluster logs**

```bash
docker compose -f server/docker-compose.yml logs -f
```

**Terminal 3 — open the client against a Raft path**

```bash
cd client
python3 -c "from client import FishingClient; FishingClient('localhost:50052').run()"
```

Then type these client commands to confirm the cluster is alive before you
start a failure scenario:

```text
login joe pw
update_location 1 1
update_location 2 2
list_users
```

### Known Practical Notes

- Node 1 (`50051`) is still configured as the 2PC coordinator in
  `server/docker-compose.yml`. For Raft manual testing, use a non-Node-1 port
  such as `50052` unless you are intentionally testing the coordinator path.
- Compose service names are `fishing1` through `fishing6`. Use those names with
  `docker compose ... stop` and `docker compose ... start`.
- Runtime container names are `server-fishing1-1` through `server-fishing6-1`.
  Use those names with `docker pause` and `docker unpause`.
- The sixth-node scenario is late startup of a preconfigured node, not dynamic
  membership. `fishing6` is already present in the compose file and peer lists.
- The split-vote test is the least deterministic case. If it resolves too
  quickly into a leader election, repeat the scenario and capture the run that
  shows multiple rounds.

### How To Identify the Current Leader

Watch Terminal 2 for the line:

```text
[RAFT] Node X became leader for term Y
```

That node is the current leader. When a test says "stop the leader" or "pause
the leader", substitute the node number you saw in that message.

### Common Commands

```bash
# Stop or restart a node by compose service name
docker compose -f server/docker-compose.yml stop fishingN
docker compose -f server/docker-compose.yml start fishingN

# Pause or unpause a running container by container name
docker pause server-fishingN-1
docker unpause server-fishingN-1

# Start only the sixth node after the other nodes are already running
docker compose -f server/docker-compose.yml up -d fishing6
```

### Log Lines To Watch For

- Leader election: `"[RAFT] Node X became leader for term Y"`
- Vote requests: `"Node X sends RPC RequestVote to Node Y"`
- Heartbeats and replication: `"Node X sends RPC AppendEntries to Node Y"`
- Follower receives heartbeat or catch-up log: `"Node Y runs RPC AppendEntries called by Node X"`
- Client forwarding: `"Node X sends RPC ForwardRequest to Node Y"`

### TC1 — Leader Crash and Re-Election

**What this test proves:**  
The cluster can survive loss of the current leader and elect a replacement.

**Setup:**
1. Start the cluster and open the client using the shared setup above.
2. Identify the current leader from the `became leader` log line.
3. Send at least two location updates from the client before crashing the
   leader.

**Action:**
1. In Terminal 1, stop the leader:

```bash
docker compose -f server/docker-compose.yml stop fishing<leader_id>
```

Example if Node 3 is leader:

```bash
docker compose -f server/docker-compose.yml stop fishing3
```

2. Wait about 3-6 seconds.
3. In the client, send another update to a surviving node:

```text
update_location 3 3
list_users
```

**What success looks like:**
- Logs show `RequestVote` traffic after the old leader stops.
- A new `"[RAFT] Node X became leader for term Y"` line appears.
- The cluster resumes `AppendEntries` from the new leader.
- The client still accepts updates after re-election.

**Screenshot to capture:**  
Capture the old leader stop command, the election logs, the new leader log line,
and a successful client update after failover.

### TC2 — Follower Crash and Recovery

**What this test proves:**  
The cluster continues operating with one follower down, and the restarted
follower catches up from the leader.

**Setup:**
1. Start from a healthy cluster with an identified leader.
2. Use the client to send several updates first so the leader has entries to
   replicate.
3. Choose a follower that is not the current leader.

**Action:**
1. Stop the follower:

```bash
docker compose -f server/docker-compose.yml stop fishing<follower_id>
```

Example:

```bash
docker compose -f server/docker-compose.yml stop fishing4
```

2. While that follower is down, send more client updates:

```text
update_location 4 4
update_location 5 5
list_users
```

3. Restart the stopped follower:

```bash
docker compose -f server/docker-compose.yml start fishing<follower_id>
```

Example:

```bash
docker compose -f server/docker-compose.yml start fishing4
```

**What success looks like:**
- The leader continues sending `AppendEntries` to the remaining nodes.
- Client updates still succeed while the follower is down.
- After restart, the follower resumes receiving `AppendEntries` and catches up.

**Screenshot to capture:**  
Capture the follower stop, successful updates while it is down, and the
restarted follower receiving `AppendEntries` again.

### TC3 — Temporary Network Partition

**What this test proves:**  
The cluster handles a temporarily unreachable node and the old leader steps down
if it returns stale.

**Primary documented path:** pause the current leader, because it shows both
partition handling and re-election clearly.

**Setup:**
1. Start from a healthy cluster and identify the current leader.
2. Send a few client updates first.

**Action:**
1. Pause the leader container:

```bash
docker pause server-fishing<leader_id>-1
```

Example if Node 5 is leader:

```bash
docker pause server-fishing5-1
```

2. Wait about 5-10 seconds and watch the logs for re-election.
3. While the old leader is paused, send another client update to a surviving
   node:

```text
update_location 6 6
list_users
```

4. Unpause the old leader:

```bash
docker unpause server-fishing<leader_id>-1
```

Example:

```bash
docker unpause server-fishing5-1
```

**What success looks like:**
- The paused leader stops participating.
- The remaining nodes elect a new leader.
- After unpause, the old leader no longer behaves as leader and instead resumes
  receiving `AppendEntries` from the new leader.
- Only one leader remains active.

**Screenshot to capture:**  
Capture the pause command, the re-election logs, the unpause command, and the
old leader rejoining as a follower.

### TC4 — Late Startup of a Preconfigured Sixth Node

**What this test proves:**  
`fishing6` can join an already-running preconfigured cluster and catch up via
heartbeats and log replication.

**Setup:**
1. Start clean:

```bash
make down
docker compose -f server/docker-compose.yml up --build -d fishing1 fishing2 fishing3 fishing4 fishing5
```

2. Open logs and the client as usual.
3. Wait for leader election among nodes 1-5.
4. Send a few updates from the client before starting Node 6.

**Action:**
1. Start only the sixth node:

```bash
docker compose -f server/docker-compose.yml up -d fishing6
```

**What success looks like:**
- `fishing6` starts successfully.
- Within about one heartbeat interval, logs show `fishing6` receiving
  `AppendEntries` from the current leader.
- `fishing6` catches up to the cluster state as a follower.

**Screenshot to capture:**  
Capture the startup of `fishing6`, the first `AppendEntries` it receives, and
evidence that it joined as a follower rather than becoming leader.

### TC5 — Split Vote and Election Retry

**What this test proves:**  
The cluster can go through multiple election rounds before a leader is finally
chosen.

**Setup:**
1. Start clean with a healthy cluster.
2. Identify the current leader.
3. Pick one additional follower to stop at the same time as the leader.

**Action:**
1. Stop the leader and one follower together:

```bash
docker compose -f server/docker-compose.yml stop fishing<leader_id> fishing<follower_id>
```

Example if Node 1 is leader and Node 5 is the extra follower:

```bash
docker compose -f server/docker-compose.yml stop fishing1 fishing5
```

2. Watch the logs for competing `RequestVote` rounds.
3. Wait for the cluster to resolve to a final leader.

**What success looks like:**
- More than one node starts an election.
- Logs show multiple rounds or terms before one node wins.
- Eventually a final `became leader` line appears and heartbeats resume from
  that leader.
- If the election resolves too quickly and you do not capture multiple rounds,
  restart the cluster and repeat the scenario.

**Screenshot to capture:**  
Capture the simultaneous stop command, multiple `RequestVote` rounds or terms,
and the final leader selection.

---

## Where To Look In The Demo

- `server/server.py`: main gRPC server, baseline `FishingService`, 2PC servicers,
  cluster wiring, and the `UpdateLocation` integration point.
- `server/raft_node.py`: Raft state machine, leader election, heartbeat loop,
  log replication, commit tracking, and the `RaftService` gRPC handlers.
- `server/twopc.proto`: 2PC RPC/message contract (`VoteRequest`,
  `GlobalDecision`, intra-node `ReportVote` / `NotifyDecision`).
- `server/raft.proto`: Raft RPC/message contract (`RequestVote`,
  `AppendEntries`, `ForwardRequest`, `LogEntry`).
- `tests/unit/test_2pc.py`: 2PC voting/decision behavior and abort-path tests.
- `tests/unit/test_raft.py`: election and timeout behavior tests.
- `tests/unit/test_raft_replication.py`: log replication, majority ACK, commit,
  and forwarding tests.

## What Changed From The Baseline

- Added `server/twopc.proto` plus generated 2PC stubs.
- Added `server/raft.proto` plus generated Raft stubs.
- Added `server/raft_node.py` for the Raft state machine and gRPC servicer.
- Extended `server/server.py` to host 2PC services, wire in Raft, and route
  `UpdateLocation` through the new consensus logic.
- Extended `server/docker-compose.yml` so all six nodes have explicit `NODE_ID`,
  `PEERS`, and unbuffered logging configuration.
- Added unit tests for 2PC, Raft election, and Raft replication behavior.

## Unusual Notes

- **Proto file naming:** The 2PC proto file is named `twopc.proto` (not
  `2pc.proto`). Python cannot import a module whose name starts with a digit;
  `grpc_tools.protoc` would generate `2pc_pb2.py`, which is an invalid Python
  identifier.

- **Docker log buffering:** All containers set `PYTHONUNBUFFERED=1` to prevent
  Python's default stdout buffering from suppressing log output in
  `docker logs`.

- **PEERS environment variable:** The `PEERS` variable must be set for *every*
  node, not only the coordinator. An initial misconfiguration left `PEERS=""`
  for nodes 2–6, causing each node to treat itself as a single-node cluster.

- **Simplified Raft log replication:** The Raft implementation sends the entire
  log on every heartbeat rather than incremental entries. Followers replace
  their log wholesale. This is a simplification from the full Raft protocol.

- **Unit test threading:** Tests pass `_start_threads=False` to `RaftNode` to
  suppress background election-timer and heartbeat threads; without this flag
  tests are flaky.

- **Report location:** The final report is maintained in Overleaf and is not
  included in this repository.

---

## External Sources

- Ongaro, D. and Ousterhout, J. (2014). *In Search of an Understandable
  Consensus Algorithm (Extended Version)*. USENIX ATC.
  <https://raft.github.io/raft.pdf>
- Gray, J. and Lamport, L. (2006). Consensus on Transaction Commit. *ACM
  Transactions on Database Systems*, 31(1):133–160.
- gRPC Python documentation: <https://grpc.io/docs/languages/python/>
- Protocol Buffers language guide (proto3):
  <https://protobuf.dev/programming-guides/proto3/>
