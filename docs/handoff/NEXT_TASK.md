# Next Task
**Last updated:** 2026-03-25
**Owner:** Joe

## Task summary

Complete the final deliverables (Phase G): fill the remaining `\todo{}` placeholders in
`docs/report/report.tex` (student IDs, work division, AI lessons-learned section),
compile the PDF via Overleaf or local TeX Live, and prepare the submission package.

**Task queue reference:** final-deliverables (see `docs/handoff/TASK_QUEUE.md`)

## Why this task is next

Q5 is COMPLETE:
- All 5 failure test cases executed against the live 6-node Docker cluster.
- 5 raw logs in `docs/report/logs/tc{1-5}_raw.txt`.
- 5 PNG screenshots in `docs/report/screenshots/tc{1-5}_*.png`.
- `docs/report/report.tex` has all TC observed-behaviour sections filled in.
- `make check` passes (55/55 tests, lint clean).

The only remaining `\todo{}` items in `report.tex` are student-specific (IDs, names,
work division) and the AI lessons-learned section — these must be filled in by the
team members, not an agent.

Long-horizon references:
- `docs/handoff/OVERVIEW_CHECKLIST.md` (phase A–G status)
- `docs/handoff/TASK_QUEUE.md` (full milestone queue)

## Recommended task order

1. **Fill remaining `\todo{}` placeholders** in `docs/report/report.tex`:
   - Author line: student ID for Joe Caldwell; Team Member 2 name and ID (if applicable).
   - Work Division table: describe each team member's contributions.
   - Section 8 (Lessons Learned from AI Tool Usage): describe how Claude Code / other AI tools were used, benefits observed, verification steps taken.

2. **Compile the PDF** — `make pdf` requires `pdflatex`. Two options:
   - **Overleaf (recommended):** upload the `docs/report/` directory (including `screenshots/`
     subdirectory) to a new Overleaf project and compile there. Note: pdflatex is NOT installed
     on the dev machine.
   - **Local TeX Live:** `brew install --cask mactex` (macOS) then `make pdf`.

3. **Update the README** (`README.md` in repo root):
   - Build instructions: `make install`, `make proto`, `make test`, `make up`, client usage.
   - Unusual notes: proto naming (twopc not 2pc), PYTHONUNBUFFERED=1, PEERS must be set for all nodes.
   - External sources: Raft paper URL, gRPC docs URL, proto3 guide URL.
   - GitHub link.
   See `docs/spec/00_assignment_project3.md` for deliverable requirements.

4. **Final quality gate** — `make check` must still pass.

5. **Prepare submission** — zip the repo (excluding `__pycache__`, `.pytest_cache`, `.git`,
   `.mypy_cache`) and submit per the assignment instructions.

6. **Mandatory final subtask** — update handoff docs (see below).

## Scope (in)

- All `\todo{}` placeholders in `report.tex` replaced (no red text in PDF)
- PDF built and verified (no LaTeX errors)
- README updated with build/run instructions, unusual notes, external sources, GitHub link
- `make check` passes
- Submission package prepared

## Scope (out)

- New Python code / new proto file — not needed
- Additional failure test cases beyond the 5 already collected
- Performance benchmarking

## Dependencies / prerequisites

- Quick orientation: `AGENTS.md` (read first), `docs/handoff/CURRENT_STATUS.md`
- Report source: `docs/report/report.tex`
- Screenshots (already done): `docs/report/screenshots/tc{1-5}_*.png`
- Spec: `docs/spec/00_assignment_project3.md` — deliverable requirements

## Implementation notes

- **pdflatex not installed** on this dev machine. Use Overleaf or install MacTeX.
- **Remaining `\todo{}` items** — search with `grep -n '\\\\todo' docs/report/report.tex`.
  As of 2026-03-25, the remaining items are: student IDs (×2), Team Member 2 name,
  work-division contributions (×2), and the AI lessons-learned section body.
- **Report `\includegraphics` paths** all correctly match the generated PNG filenames — do NOT
  rename the screenshot files without updating the LaTeX source.
- **Bug already fixed:** `docker-compose.yml` PEERS was `""` for nodes 2-6; now corrected.
  This is also documented in the Unusual Notes section of `report.tex`.

## Acceptance criteria (definition of done)

- [ ] No `\todo{}` text remaining in `docs/report/report.tex`
- [ ] PDF compiles without errors (LaTeX warnings OK)
- [ ] `README.md` covers: build, run, unusual notes, external sources, GitHub link
- [ ] `make check` passes (55/55 tests, lint clean)
- [ ] Submission package prepared
- [ ] Handoff docs updated (see mandatory final subtask below)

## Verification checklist

- [ ] `grep '\\todo' docs/report/report.tex` returns nothing
- [ ] PDF opens and all 5 screenshots appear at the correct page locations
- [ ] `make check` passes
- [ ] README.md exists and contains the required sections

## Mandatory final subtask: Update handoff documentation

**Complete this last, after all work is done.**

- [ ] Mark `final-deliverables` as `done` in `docs/handoff/TASK_QUEUE.md`
- [ ] Update Phase G status to `DONE` in `docs/handoff/OVERVIEW_CHECKLIST.md` and tick exit criteria
- [ ] Rewrite `docs/handoff/CURRENT_STATUS.md` to reflect completion
- [ ] Update `docs/handoff/BLOCKERS.md` if any new blockers arose
- [ ] Archive `docs/handoff/NEXT_TASK.md` as completed (no new task after G — project is done)

## Risks / rollback notes

- **pdflatex not available locally**: use Overleaf (upload `docs/report/` folder including
  `screenshots/` subdirectory).
- **Screenshot filenames must match `\includegraphics` paths**: the current `.tex` uses
  `tc{N}_tc{N}_...` slugs — do not rename PNGs without updating the LaTeX source.
