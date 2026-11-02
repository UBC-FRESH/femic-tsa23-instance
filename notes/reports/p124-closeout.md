# Phase close-out report: P124 TSA 23 BA-only WS4 consumer test

Phase: P124 TSA 23 BA-only WS4 consumer test
Parent issue: #52
Pull request: #54, `feature/p124-ba-consumer-test` into `main`
Evidence head: `405253c`, the commit that adds the consumer script, tests, report, docs, and planning entries
Report commit: the commit that refreshes this report. Its CI run is posted on the pull request.
Date: 2026-11-02
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #54, and delete the branch `feature/p124-ba-consumer-test`.
2. Close child issue #53 with a closeout comment that cites the merge commit.
3. Close parent issue #52 with a closeout comment that cites the merge commit.
4. Do not create a new model phase. The P122 consumer gap is closed; the BA pilot is
   report-only and remains non-operational.

Settings changes, each with its exact command. Each one runs only after its own approval.

- None.

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| BA table and raster identity; `-9999` abstention | 2,942,755 rows = 2,942,755 valid pixels; max difference 1.9e-6; nodata excluded | met |
| Reproducible cell-to-fragment join with match counts | 2,833,996 matched; 108,759 unmatched (3.7%) | met |
| Report-only fields in copied fragment and block tables | Fragment: `inventory_ba_m2_ha`, `inventory_ba_available`, `inventory_ba_cells`; block: `inventory_ba_m2_ha`, `inventory_ba_available` | met |
| `ws4 validate` and one bounded simulation | validate passed; one-year 100-block FT simulation completed | met |
| Report states read/ignored/refused behavior | Simulator loads the fragment fields; block fields are in the table but the simulator has no block table; fields are report-only | met |
| Production dataset and model unchanged | Only a copy under `runtime/` was modified; the repo changes are script, tests, reports, docs, and planning | met |

## 2. Workflow compliance

- Parent issue before the branch: issue #52 was created before the branch; child
  issue #53 was created immediately after and linked as a sub-issue.
- Branch from `main`: `feature/p124-ba-consumer-test` was created from `main` at
  `4dc9c31`.
- Commit messages that start with task IDs: `405253c` (`P124.1 ...`) and the report
  commit.
- Gates for each commit: section 3.
- Roadmap and changelog in step: both were changed in `405253c`; the report commit
  only adds this report.
- Child issues closed with closeout evidence: #53 remains open until the merge is
  approved, per the workflow.
- Approval gates: the maintainer's `go` instruction approved the consumer-test phase;
  merge, branch deletion, and issue closure wait for approval of this report.
- P123 was corrected from `active` to `complete` in the roadmap.

## 3. Gate evidence

At `405253c`:

```text
python -m pytest tests/test_verify_ba_pilot_consumer.py -q
4 passed

python -m ruff check scripts/verify_ba_pilot_consumer.py tests/test_verify_ba_pilot_consumer.py
All checks passed.

python -m ruff format --check ...
2 files already formatted

sphinx-build -b html docs _build/html -W
Build succeeded.

python -m ws4.cli validate --dataset <copy>
Passed.

python -m ws4.cli simulate --dataset <copy> --schedule <offset schedule> --years 1
Simulation complete.
```

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| not run | report commit | not run | The TSA 23 instance has no pull-request CI workflow; docs deploy runs on `main`. The local test, ruff, and Sphinx gates are recorded above. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| No PR CI run | The only workflow triggers on push to `main` or manual dispatch | Local test, ruff, Sphinx, validate, and simulate evidence is recorded |
| 108,759 valid cells are unmatched | Edge cells and cells outside the fragment grid | Reported as 3.7% and not treated as zero BA |
| The simulator has no separate block table | WS4 exposes `Simulator.fragments` but not a block table | Block fields are checked in the copied table; the report states the limit |

## 6. Next phase

Recommended default: **no new model phase**. The P122 consumer gap is closed.

The BA pilot is consumer-readable as a report-only fragment/block attribute. It is
still 14.9% coverage and non-operational. A production use would need a refit,
more plots, and an explicit model decision; neither is proposed here.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.
