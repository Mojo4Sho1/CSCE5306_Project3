# Compliance Task C — “New Node Entering the System” Audit + Wording/Doc Patch

LAST_UPDATED: 2026-04-08
TASK_ID: compliance-new-node-audit-wording-patch
STATUS: DONE
PRIORITY: MEDIUM
DEPENDENCY_STATUS: Independent task; queued after Tasks A and B because it is primarily an accuracy/wording follow-up.
COMPLETED: 2026-04-08

## Objective

Determine whether the current project truly supports dynamic node membership or only a bounded approximation such as late startup of a preconfigured node. Prefer accurate wording and documentation over implementing new membership mechanics unless a tiny nearly-finished fix already exists.

## Why This Matters

The compliance scope calls out possible overstatement around the "new node entering the system" failure test. This task protects the final repo and report language from claiming capabilities that the implementation may not actually provide.

## Source Traceability

- Primary source: `docs/archive/agent_tasks/compliance_patch_scope.md` ("'New node entering the system' test accuracy")
- Assignment source: `docs/spec/00_assignment_project3.md`
- Failure-test source: `docs/spec/06_failure_test_matrix.md`
- Active workflow context: `AGENTS.md`, `docs/handoff/CURRENT_STATUS.md`, `docs/handoff/TASK_QUEUE.md`

## Likely Files Involved

- `docs/spec/06_failure_test_matrix.md`
- `README.md`
- `server/docker-compose.yml`
- `server/server.py`
- `server/raft_node.py`
- `docs/handoff/SPEC_CONFORMANCE_CHECKLIST.md` only if wording or evidence should be narrowed

## Scope (In)

- Determine whether membership is dynamic or preconfigured
- Trace how the current "new node" scenario is actually constructed
- Patch only the smallest code or documentation changes needed to make the repo's claims accurate
- Produce exact recommended wording for the final report

## Scope (Out)

- No full dynamic membership implementation
- No architecture redesign
- No cluster-topology expansion beyond a tiny already-nearly-present fix
- No broad Raft refactor
- No speculative feature work

## Expected Deliverables

- Behavioral assessment of what the implementation really supports
- Minimal code/doc patch if needed to align wording with reality
- Validation steps and outcomes
- Exact recommended wording for the final report

## Validation Expectations

- Show the concrete evidence used to distinguish dynamic join from late start of a preconfigured node
- Run `make check` only if code changes are made
- If the outcome is documentation-only, still record the specific files inspected and why they support the conclusion

## Recommended Agent Instructions

1. Read `AGENTS.md`, `docs/handoff/CURRENT_STATUS.md`, `docs/archive/agent_tasks/compliance_patch_scope.md`, `docs/spec/00_assignment_project3.md`, and `docs/spec/06_failure_test_matrix.md`.
2. Inspect cluster configuration and peer discovery before touching any wording.
3. Treat "late-start of a node already present in config" as different from true dynamic membership unless the code proves otherwise.
4. Prefer narrowing terminology in docs/report guidance over adding new runtime behavior.
5. If a tiny change is genuinely enough to make the wording accurate, keep it minimal and defend why it is still within scope.
6. When done, update `docs/handoff/TASK_QUEUE.md`, `docs/handoff/CURRENT_STATUS.md`, `docs/handoff/NEXT_TASK.md`, and `docs/handoff/BLOCKERS.md` as needed.

## Success Criteria

- The repo has an evidence-backed statement about what "new node entering the system" actually means
- Any wording change is precise and honest
- The final report wording can be copied directly from the task output without overstating capability

## Completion Notes

- Audit result: the implementation does not support dynamic Raft membership. The observed Q5 behavior is late startup of a node already defined in `server/docker-compose.yml` and already present in the other nodes' `PEERS` lists.
- Patch applied: narrowed repo wording in `docs/spec/06_failure_test_matrix.md`, `README.md`, and `docs/handoff/OVERVIEW_CHECKLIST.md` to describe a late-started preconfigured sixth node rather than dynamic membership or quorum reconfiguration.
- Validation: verified the bounded interpretation against `server/docker-compose.yml`, the assignment's ambiguity note in `docs/spec/00_assignment_project3.md`, and the updated Q5 spec text; `make check` still passed after the documentation changes.
- Exact recommended wording for the final report: "Our Q5 'new node entering the system' scenario is a bounded late-start test of a preconfigured sixth node, not full dynamic Raft membership. The node was already defined in Docker Compose and in the cluster peer lists; when started later, it joined as a follower and caught up via heartbeat-based full-log replication."
