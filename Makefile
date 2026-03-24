.PHONY: install lint format test test-smoke proto proto-2pc up down logs check

COMPOSE_FILE := server/docker-compose.yml
PYTHON       := python3

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

# Lint owned source files. server/server.py is included now that we extend it
# with 2PC logic. client/client.py remains excluded (unmodified baseline).
# Append new implementation files (server/raft.py, etc.) here as they are added.
lint:
	ruff check tests/ server/server.py

format:
	ruff format tests/ server/server.py

test:
	$(PYTHON) -m pytest -m "not smoke"

test-smoke:
	$(PYTHON) -m pytest -m smoke

# proto-2pc: regenerate stubs from twopc.proto only (Q1+).
# Note: file is named twopc.proto (not 2pc.proto) — Python cannot import a
# module whose name starts with a digit, so twopc avoids that issue.
proto-2pc:
	$(PYTHON) -m grpc_tools.protoc -I server --python_out=server --grpc_python_out=server server/twopc.proto

# proto: regenerate all stubs (twopc + raft). raft.proto is added in Q3.
proto: proto-2pc
	$(PYTHON) -m grpc_tools.protoc -I server --python_out=server --grpc_python_out=server server/raft.proto

up:
	docker compose -f $(COMPOSE_FILE) up --build -d

down:
	docker compose -f $(COMPOSE_FILE) down

logs:
	docker compose -f $(COMPOSE_FILE) logs -f

# Quality gate: run before marking any task complete
check: lint test
