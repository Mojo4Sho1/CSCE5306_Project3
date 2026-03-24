.PHONY: install lint format test test-smoke proto proto-2pc proto-raft up down logs check pdf

COMPOSE_FILE := server/docker-compose.yml
PYTHON       := python3

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

# Lint owned source files. server/server.py and server/raft_node.py are included.
# client/client.py remains excluded (unmodified baseline).
lint:
	ruff check tests/ server/server.py server/raft_node.py

format:
	ruff format tests/ server/server.py server/raft_node.py

test:
	$(PYTHON) -m pytest -m "not smoke"

test-smoke:
	$(PYTHON) -m pytest -m smoke

# proto-2pc: regenerate stubs from twopc.proto only (Q1+).
# Note: file is named twopc.proto (not 2pc.proto) — Python cannot import a
# module whose name starts with a digit, so twopc avoids that issue.
proto-2pc:
	$(PYTHON) -m grpc_tools.protoc -I server --python_out=server --grpc_python_out=server server/twopc.proto

# proto-raft: regenerate stubs from raft.proto (Q3+).
proto-raft:
	$(PYTHON) -m grpc_tools.protoc -I server --python_out=server --grpc_python_out=server server/raft.proto

# proto: regenerate all stubs (twopc + raft).
proto: proto-2pc proto-raft

up:
	docker compose -f $(COMPOSE_FILE) up --build -d

down:
	docker compose -f $(COMPOSE_FILE) down

logs:
	docker compose -f $(COMPOSE_FILE) logs -f

# Quality gate: run before marking any task complete
check: lint test

# Build the PDF report (requires pdflatex on PATH).
# Screenshots must be placed in docs/report/screenshots/ before building.
pdf:
	cd docs/report && pdflatex -interaction=nonstopmode report.tex && pdflatex -interaction=nonstopmode report.tex
