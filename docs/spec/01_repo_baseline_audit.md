# Repo Baseline Audit

## Purpose
Capture the actual current state of the forked repo before any reorganization or
implementation work begins.

## 1. Top-Level Structure
- `client/`: Python gRPC client plus generated protobuf stubs and a local copy of `fishing.proto`.
- `server/`: multi-container Python gRPC server variant with six JPG assets, Dockerfile, compose file, generated protobuf stubs, and `server.py`.
- `servermono/`: alternate single-service variant with parallel copies of the server runtime, proto, generated stubs, Dockerfile, compose file, and JPG assets.
- `docs/spec/00_assignment_project3.md`: local Project 3 requirements summary already present.
- `README.md`, root `fishing.proto`, and `fishing_test.js`: baseline documentation, shared proto surface, and a k6 load-test script.

## 2. Runtime Entry Points
- Primary clustered runtime entrypoint: `server/server.py`, started by `server/docker-compose.yml` as six separate services on ports `50051` through `50056`.
- Alternate mono runtime entrypoint: `servermono/server.py`, with `servermono/docker-compose.yml` describing a single service.
- Interactive client entrypoint: `client/client.py`, defaulting to `localhost:50051`.
- No repo-level package manager or task runner is present; runtime is command-oriented.

## 3. Proto / Generated Artifact Inventory
- Root `fishing.proto` declares package `fishingapp` and the `FishingService` RPC surface.
- `client/fishing.proto`, `server/fishing.proto`, and `servermono/fishing.proto` duplicate the baseline proto, creating drift risk.
- Generated protobuf outputs exist in both `client/`, `server/`, and `servermono/` as `fishing_pb2.py` and `fishing_pb2_grpc.py`.
- Generated artifacts are treated as preserve/no-touch during seed execution; no regeneration was performed.

## 4. Docker / Compose Inventory
- `server/docker-compose.yml` defines six services (`fishing1` through `fishing6`) that all build the same local Docker context and pass unique port/image arguments.
- `server/dockerfile` is the actual build file name used by Compose; Docker normalizes it as `Dockerfile` in `docker compose config`.
- `servermono/docker-compose.yml` defines one service `fishing-cluster` and exposes the port range `50051-50056`, which does not match the file’s “single-node” description cleanly.
- Baseline compose syntax validated successfully with `docker compose -f server/docker-compose.yml config` on 2026-03-20.

## 5. Client / Server Interaction Surfaces
- `Login`: unary RPC returning a token composed from username and password.
- `UpdateLocation`: client-streaming RPC used to register a user and mutate server-side `(x, y)` state.
- `ListUsers`: server-streaming RPC returning a snapshot of current users.
- `StartFishing`: server-streaming RPC simulating a probabilistic fish catch and appending to in-memory inventory.
- `CurrentUsers`, `Inventory`, and `GetImage`: additional read-oriented surfaces.
- The locked extension surface is replicated player state updates via location-update commands, using `UpdateLocation` as the baseline integration surface.

## 6. Preserve / No-Touch List
- Preserve existing Python runtime files in `client/`, `server/`, and `servermono/` during seed work.
- Preserve all generated protobuf artifacts (`*_pb2.py`, `*_pb2_grpc.py`) until a later approved task explicitly introduces regeneration.
- Preserve baseline compose files and image assets.
- Preserve root and duplicated proto files as audit evidence even though they may later be normalized.
- Avoid moving or renaming runtime files before a dedicated reorganization plan is approved.

## 7. Documentation Inconsistencies
- `README.md` RPC naming, streaming descriptions, and prerequisites were normalized on 2026-03-20 to match the audited baseline.
- `servermono/` remains an alternate baseline variant whose compose file exposes the port range `50051-50056`; it should not be read as a fully normalized deployment target.
- The repository still contains three copies of `fishing.proto`, increasing the chance that docs and generated stubs drift apart.

## 8. Likely Extension Surfaces
- Locked functionality: replicated player state updates via location-update commands, using `UpdateLocation` as the baseline integration surface.
- The chosen operation mutates the in-memory `users` map and gives Project 3 one bounded place to apply 2PC and Raft later.
- Any extension should likely add new Project 3-specific RPC surfaces rather than overload baseline gameplay RPCs during the early implementation phase.

## 9. Open Questions
- Should the six `server/` instances become the five-node minimum cluster for Project 3, or should one node be reserved for testing/coordination?
- Should new 2PC and Raft proto definitions live in separate files to satisfy the assignment’s Raft proto requirement cleanly?

## 10. Evidence References
- Files inspected: `README.md`, root `fishing.proto`, `client/client.py`, `server/server.py`, `server/docker-compose.yml`, `server/dockerfile`, `servermono/server.py`, `servermono/docker-compose.yml`.
- Validation commands:
  - `docker compose -f server/docker-compose.yml config`
  - `python -m py_compile server/server.py client/client.py`
