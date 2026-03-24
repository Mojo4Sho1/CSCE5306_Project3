# NEXT_TASK.md Template

Use this template when rewriting `NEXT_TASK.md` as part of the mandatory handoff subtask. Replace all `<placeholder>` values. Delete sections that don't apply. Keep it scannable — the next agent must be able to load this file and immediately know what to do.

---

```markdown
# Next Task
**Last updated:** <YYYY-MM-DD>
**Owner:** Joe

## Task summary

<One or two sentences. State the milestone being implemented and its primary deliverable.>

**Task queue reference:** <task-id> (see `docs/handoff/TASK_QUEUE.md`)

## Why this task is next

- <What was completed in the prior batch that unblocks this one.>
- <What gap or milestone gate this batch addresses.>

Long-horizon references:
- `docs/handoff/OVERVIEW_CHECKLIST.md` (phase A–G status)
- `docs/handoff/TASK_QUEUE.md` (full milestone queue)

## Recommended task order

<List subtasks in order. Note any that can be run in parallel.>

1. **<Subtask 1>:** <description>
2. **<Subtask 2>:** <description>
...

## Scope (in)

- <Concrete deliverable 1>
- <Concrete deliverable 2>
- Unit tests for all new code (per `AGENTS.md` testing policy)
- `make check` passes (lint + unit tests)

## Scope (out)

- <Explicitly excluded work, with brief reason.>

## Dependencies / prerequisites

- Quick orientation: `AGENTS.md` (read first), `docs/handoff/CURRENT_STATUS.md`
- Environment setup: `requirements-dev.txt`, `Makefile`
- Specs (read only what's needed):
  - `docs/spec/<spec>.md` — <why>
- Inputs from prior phase: <list files produced by prior milestone>

## Implementation notes

- <Key constraint or gotcha the agent must know.>
- Run `make check` after every significant code change.
- <Log format or protocol requirement if applicable.>

## Acceptance criteria (definition of done)

- [ ] <Verifiable criterion 1>
- [ ] <Verifiable criterion 2>
- [ ] All unit tests pass (`make test`)
- [ ] `make check` passes (lint + unit tests)
- [ ] Handoff docs updated (see mandatory final subtask below)

## Verification checklist

- [ ] `make check` passes
- [ ] `docker compose -f server/docker-compose.yml up --build` starts 5+ containers
- [ ] <Milestone-specific validation step>
- [ ] No unresolved placeholder text in new code or docs

## Mandatory final subtask: Update handoff documentation

**Complete this last, after all code is written and all tests pass.**

Using `docs/handoff/NEXT_TASK_TEMPLATE.md` as a guide, update the following before closing this batch:

- [ ] Mark `<task-id>` as `done` in `docs/handoff/TASK_QUEUE.md`
- [ ] Update Phase <X> status to `DONE` in `docs/handoff/OVERVIEW_CHECKLIST.md` and tick exit criteria
- [ ] Rewrite `docs/handoff/CURRENT_STATUS.md`:
  - What was completed (concrete, verifiable — list files created/modified)
  - Checks run and their outcomes
  - Any remaining blockers or caveats
- [ ] Update `docs/handoff/BLOCKERS.md`: mark any blockers resolved this session; add any new unresolved blockers that need Joe's input
- [ ] Rewrite `docs/handoff/NEXT_TASK.md` to brief the next agent on <next milestone>, following `docs/handoff/NEXT_TASK_TEMPLATE.md`

The next `NEXT_TASK.md` must itself include this same "Mandatory final subtask" section so the pattern propagates to every future agent.

## Risks / rollback notes

- <Risk 1 and mitigation.>
- <Risk 2 and mitigation.>
```

---

## Milestone reference

| Milestone | Phase | Spec doc |
|-----------|-------|----------|
| q1-2pc-voting | B | `docs/spec/03_2pc_contract.md` |
| q2-2pc-decision | C | `docs/spec/03_2pc_contract.md` |
| q3-raft-election | D | `docs/spec/04_raft_election_contract.md` |
| q4-raft-log-replication | E | `docs/spec/05_raft_log_replication_contract.md` |
| q5-failure-tests | F | `docs/spec/06_failure_test_matrix.md` |
| final-deliverables | G | `docs/spec/00_assignment_project3.md` |
