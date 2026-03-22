# Next Task

TASK_ID: q1-2pc-voting
TASK_TITLE: Implement 2PC voting phase (Q1)
OBJECTIVE: Create `2pc.proto`, generate stubs, implement coordinator vote-request and participant vote-commit/vote-abort logic, containerize with 5+ nodes.
SPEC_DOC: docs/spec/03_2pc_contract.md
IN_SCOPE:
- Create `server/2pc.proto` with TwoPhaseCommitService and messages
- Generate Python gRPC stubs from `2pc.proto`
- Implement coordinator logic: send VoteRequest to all participants
- Implement participant logic: receive VoteRequest, return VoteResponse (commit or abort)
- Add NODE_ID and PEERS environment variables to docker-compose.yml
- Print required RPC log messages in assignment format
- Ensure 5+ containerized nodes communicate
OUT_OF_SCOPE:
- Decision phase (Q2)
- Intra-node gRPC between phases (Q2)
- Raft (Q3, Q4)
- Failure tests (Q5)
TARGET_FILES:
- `server/2pc.proto` (CREATE)
- `server/2pc_pb2.py` (GENERATE)
- `server/2pc_pb2_grpc.py` (GENERATE)
- `server/server.py` (MODIFY — add 2PC voting logic)
- `server/docker-compose.yml` (MODIFY — add env vars)
- `server/dockerfile` (MODIFY — add grpcio-tools if needed)
ACCEPTANCE_CRITERIA:
- [ ] `2pc.proto` compiles without errors
- [ ] Coordinator sends VoteRequest to all participants
- [ ] Participants respond with vote-commit or vote-abort
- [ ] RPC log messages match required format
- [ ] 5+ Docker containers communicate successfully
VALIDATION_COMMANDS:
- `python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. 2pc.proto`
- `docker compose -f server/docker-compose.yml config`
- `docker compose -f server/docker-compose.yml up --build`
READY: YES
