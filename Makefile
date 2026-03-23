.PHONY: install lint format test test-smoke proto up down logs check

COMPOSE_FILE := server/docker-compose.yml
PYTHON       := python3

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

# Lint only files we own. The forked server/server.py and client/client.py are
# excluded to avoid modifying baseline code. As new implementation files are
# added (server/2pc.py, server/raft.py, etc.), append them here.
lint:
	ruff check tests/

format:
	ruff format tests/

test:
	$(PYTHON) -m pytest -m "not smoke"

test-smoke:
	$(PYTHON) -m pytest -m smoke

# proto: regenerate stubs after adding new .proto files (2pc.proto, raft.proto)
# Will fail until those files exist in Q1/Q3 -- that is expected.
proto:
	$(PYTHON) -m grpc_tools.protoc -I server --python_out=server --grpc_python_out=server server/2pc.proto
	$(PYTHON) -m grpc_tools.protoc -I server --python_out=server --grpc_python_out=server server/raft.proto

up:
	docker compose -f $(COMPOSE_FILE) up --build -d

down:
	docker compose -f $(COMPOSE_FILE) down

logs:
	docker compose -f $(COMPOSE_FILE) logs -f

# Quality gate: run before marking any task complete
# typecheck will be added here in Q1 once typed implementation files exist
check: lint test
