# Blocker Log

**Last updated:** 2026-03-24

This file is the running record of blockers encountered during implementation. Agents update it in real-time — do not wait until the end of a session.

See `AGENTS.md` § "Blocker Handling Protocol" for the full protocol on when and how to log entries here.

---

## Unresolved Blockers

*None currently. Joe's guidance is needed to unblock any entry that appears here.*

---

## Resolved Blockers

### BLOCKER-R001 — Proto filename 2pc.proto causes Python import error
**Date discovered:** 2026-03-24
**Date resolved:** 2026-03-24
**Task:** q1-2pc-voting
**Description:** The spec instructed creating `server/2pc.proto`. `grpc_tools.protoc` generates `2pc_pb2.py` from that filename. Python cannot import a module whose name starts with a digit — `import 2pc_pb2` is a syntax error.
**Root cause:** Python identifier rules prohibit names starting with digits. The spec did not account for this.
**Solution:** Named the file `twopc.proto` instead. Updated the spec (`docs/spec/03_2pc_contract.md`), Makefile, and all imports accordingly. Generated files are `twopc_pb2.py` / `twopc_pb2_grpc.py`.
**Prevention:** Any proto file whose name starts with a digit will hit this in Python. Always use alphanumeric-starting filenames for proto files targeting Python.
**Broadly applicable:** Yes — applies to any Python project using grpc_tools.protoc where the proto file name would produce an invalid Python module name.
**Written to auto-memory:** No (project-specific, low reuse value outside this project type)

### BLOCKER-R002 — Docker logs empty due to Python stdout buffering
**Date discovered:** 2026-03-24
**Date resolved:** 2026-03-24
**Task:** q1-2pc-voting
**Description:** After starting the Docker cluster, `docker logs` returned empty output even though containers were running and serving RPCs correctly.
**Root cause:** Python buffers stdout by default. In a Docker container with no TTY, print() output is held in the buffer and not flushed to the container's stdout stream until the process exits.
**Solution:** Added `PYTHONUNBUFFERED: "1"` to the environment section of all services in `server/docker-compose.yml`. This forces Python to use unbuffered stdout so logs appear immediately.
**Prevention:** Always add `PYTHONUNBUFFERED: "1"` (or `PYTHONUNBUFFERED=1`) to Docker environments running Python servers. Without it, `docker logs` will appear empty until container exit.
**Broadly applicable:** Yes — affects all Python gRPC (and any Python) Docker services. Standard gotcha.
**Written to auto-memory:** No
