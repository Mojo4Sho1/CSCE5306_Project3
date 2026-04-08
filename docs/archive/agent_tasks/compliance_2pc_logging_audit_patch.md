# Compliance Task A — 2PC Logging Audit + Patch

LAST_UPDATED: 2026-04-08
TASK_ID: compliance-2pc-logging-audit-patch
STATUS: DONE
PRIORITY: HIGH
DEPENDENCY_STATUS: Independent task; scheduled first in the compliance follow-up queue.
COMPLETED: 2026-04-08

## Objective

Audit every 2PC RPC path for assignment-compliant sender-side and receiver-side log messages, including the intra-node gRPC communication between the voting and decision phases within the same container. Patch only missing logging and the smallest supporting tests/docs needed to defend compliance.

## Why This Matters

The assignment requires 2PC RPC logging on both sides of the call. The compliance scope specifically flags intra-node gRPC as an area that may have been missed, so this task is the highest-priority conformance check.

## Source Traceability

- Primary source: `docs/archive/agent_tasks/compliance_patch_scope.md` ("2PC RPC logging completeness")
- Assignment source: `docs/spec/00_assignment_project3.md`
- Implementation contract: `docs/spec/03_2pc_contract.md`
- Active workflow context: `AGENTS.md`, `docs/handoff/CURRENT_STATUS.md`, `docs/handoff/TASK_QUEUE.md`

## Likely Files Involved

- `server/server.py`
- `tests/unit/test_2pc.py`
- `README.md` only if logging claims or examples need correction
- `docs/handoff/SPEC_CONFORMANCE_CHECKLIST.md` only if the compliance evidence or wording needs to be tightened

## Scope (In)

- Enumerate all 2PC RPCs currently used by the implementation
- Verify each RPC has both caller-side and callee-side logging
- Verify the required assignment wording is used for 2PC logs
- Pay special attention to voting-to-decision localhost/intra-node gRPC
- Add the smallest code patch needed if any logging path is missing
- Add or update targeted tests only where needed to lock the behavior down

## Scope (Out)

- No 2PC protocol redesign
- No Raft changes
- No broad refactors or cleanup
- No changes to `fishing.proto` or unrelated generated stubs
- No behavior changes except the minimum logging/test/doc patch needed for compliance

## Expected Deliverables

- Audit findings that map each 2PC RPC to current sender-side and receiver-side log coverage
- Minimal code patch if a logging gap exists
- Minimal test/doc patch if needed to validate or accurately describe the behavior
- Clear validation steps and outcomes
- Remaining limitations, if any

## Validation Expectations

- Add or update targeted unit tests if code changes are made
- Run `make check`
- If unit tests alone cannot demonstrate the runtime logging path, provide explicit manual verification steps and outcomes for a live run

## Recommended Agent Instructions

1. Read `AGENTS.md`, `docs/handoff/CURRENT_STATUS.md`, `docs/archive/agent_tasks/compliance_patch_scope.md`, `docs/spec/00_assignment_project3.md`, and `docs/spec/03_2pc_contract.md`.
2. Enumerate the concrete 2PC RPC paths before editing anything.
3. Compare the current sender-side and receiver-side log lines against the assignment-required 2PC format in `AGENTS.md`.
4. Inspect intra-node gRPC calls separately; do not assume localhost calls are already covered.
5. Patch only missing logging and the closest supporting tests/docs.
6. When done, update `docs/handoff/TASK_QUEUE.md`, `docs/handoff/CURRENT_STATUS.md`, `docs/handoff/NEXT_TASK.md`, and `docs/handoff/BLOCKERS.md` as needed.

## Success Criteria

- Every implemented 2PC RPC path is accounted for in the audit
- Any missing 2PC log line is patched with the assignment-required wording
- Validation is concrete enough for a fresh reviewer to defend compliance
- The handoff docs clearly record what was changed and what remains, if anything

## Completion Notes

- Audit result: inter-node `VoteRequest` and `GlobalDecision` already had sender-side and receiver-side logging, but intra-node `ReportVote` and `NotifyDecision` were missing receiver-side logs in `IntraNodePhaseServicer`.
- Patch applied: added assignment-format receiver logs for both intra-node RPC handlers in `server/server.py`.
- Validation: added targeted unit tests in `tests/unit/test_2pc.py` for both intra-node receiver-side log lines; `make check` passed on 2026-04-08.
- Remaining limitations: none for the audited 2PC RPC paths; the compliance gap was limited to missing intra-node receiver-side logging.
