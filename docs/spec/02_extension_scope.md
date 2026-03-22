# Extension Scope

## Purpose
Define the single-functionality extension boundary for Project 3 and make
non-goals explicit.

## 1. Chosen Functionality
- Locked scope: replicated player state updates via location-update commands, using the existing `UpdateLocation` RPC as the baseline integration surface.
- Logical operation: a client submits a player state update command containing location coordinates, one coordinator/leader path decides whether that command commits, and the cluster replicates the committed player-state change.
- Scope note: the bounded functionality is the player state/location update command flow, not the entire MMO gameplay surface.
- Status: locked for Project 3 requirements review.

## 2. In-Scope Runtime Surfaces
- The existing `UpdateLocation` client-to-server mutation path in `client/client.py` and `server/server.py`.
- The server-side `users` state mutated by location-update commands.
- New Project 3-specific gRPC RPCs and messages needed for 2PC voting, 2PC decision, Raft leader election, and Raft log replication.
- Dockerized multi-node deployment based on the existing `server/` cluster topology.
- Failure-oriented test planning and evidence capture for replicated player state updates only.

## 3. Out-of-Scope Runtime Surfaces
- Full redesign of the MMO fishing game.
- `StartFishing`, `Inventory`, `GetImage`, and other gameplay flows beyond what is needed to preserve baseline behavior while extending location-update commands.
- Performance tuning, persistence-layer redesign, and generalized service discovery.
- Cross-cutting repo reorganization during this seed stage.
- Any attempt to turn Project 3 into an open-ended redesign of the whole game architecture.

## 4. Why This Boundary Fits the Assignment
- The assignment explicitly allows a single functionality for 2PC.
- The existing `UpdateLocation` flow already represents a mutating operation with visible player-state effects and a natural commit/abort outcome.
- The existing six-service cluster provides a nearby path to the assignment’s minimum five-container requirement.
- Treating the logical operation as replicated player state updates via location-update commands keeps the work concrete while remaining broader than a single function name.
- Keeping consensus logic attached to one bounded command flow avoids widening scope into a full game rewrite.

## 5. Preserve Rules for Unchanged Surfaces
- Baseline fishing gameplay APIs remain informational context, not immediate refactor targets.
- Existing generated protobuf files remain preserved until a later approved implementation task introduces a regeneration workflow.
- Existing compose files, images, and server variants remain audit references even if later cleanup consolidates them.
- Any repo normalization after seed completion must be documented first in a dedicated reorganization plan.

## 6. Open Questions
- Should 2PC RPCs be added in a dedicated Project 3 proto file, while Raft gets its own required new proto file?
- Will the six-node cluster be used directly, or narrowed to five active nodes plus one spare/test node?

## 7. Traceability to `docs/spec/00_assignment_project3.md`
- Assignment scope: one selected existing distributed system with one bounded functionality.
- 2PC requirements: map vote-request, vote-commit, vote-abort, global-commit, and global-abort to replicated player state updates via location-update commands.
- Raft requirements: leader election and log replication apply only to the replicated log of player state/location update commands.
- Testing and deliverables: failure tests, README updates, and report evidence should center on the same bounded functionality.
