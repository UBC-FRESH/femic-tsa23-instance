# Phase close-out report: P123 Target semantics and forest-condition card

Phase: P123 Target semantics and forest-condition card
Parent issue: #49
Pull request: #51, `feature/p123-target-semantics-condition-card` into `main`
Evidence head: `f8ab590`, the commit that adds the semantics note, the card, the test, and the roadmap/changelog entries
Report commit: the commit that adds this report. Its CI run is posted on the pull request.
Date: 2026-11-02
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #51, and delete the branch `feature/p123-target-semantics-condition-card`.
2. Close child issue #50 with a closeout comment that cites the merge commit.
3. Close parent issue #49 with a closeout comment that cites the merge commit.
4. Launch P124 "BA-only pilot consumer test" only if the maintainer wants to close the
   remaining consumer gap: create its parent and child issues, branch from `main`, and
   test one WS4/FHOPS consumer against the published BA-only pilot. If not, leave the
   phase unstarted.

Settings changes, each with its own exact command. Each one runs only after its own approval.

- None.

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| Interpret the 10,000,000 CAD route-build bound as a soft aspiration | `reports/tsa23-target-semantics.md`; cites the five targets and weights | met |
| Do not call the miss a solver failure | The note states the bound is a lower-weight one-sided hinge and does not claim infeasibility | met |
| Publish a valid `ws4.forest_condition.report.v1` card | `reports/tsa23-forest-condition-2026.json`; loads through the WS4 P90 module and renders to `.md` | met |
| Card carries review status, source, version, applicability, uncertainty, and an advisory alert | JSON fields and Markdown rendering | met |
| Local test rejects missing source, non-finite value, and invalid review status | `tests/test_forest_condition_card.py`; 5 passed | met |
| No model, data, target, or solver value changed | The change set adds reports, a test, roadmap, and changelog only | met |

## 2. Workflow compliance

- Parent issue before the branch: issue #49 was created before the branch; child issue
  #50 was created immediately after and linked as a sub-issue.
- Branch from `main`: `feature/p123-target-semantics-condition-card` was created from
  `main` at `4170451`.
- Commit messages that start with task IDs: `f8ab590` (`P123.1 ...`) and the report
  commit.
- Gates for each commit: section 3.
- Roadmap and changelog in step: both were changed in `f8ab590`; the report commit
  only adds this report.
- Child issues closed with closeout evidence: #50 remains open until the merge is
  approved, per the workflow.
- Approval gates: the maintainer's `plan and go` instruction was taken as approval to
  activate P123 and start P123.1. Merge, branch deletion, and issue closure remain
  gated on approval of this report.
- Scope adjustment: the parent and child issues were edited and a comment was posted
  to record that the card carries the BA-only indicator only, because the instance has
  no TSA 23 DHI calculation or source.

## 3. Gate evidence

The TSA23 instance does not ship the seeded `scripts/dashboard.py`; the available
gates for this docs-and-card change are the focused test and the JSON parse:

```text
python -m pytest tests/test_forest_condition_card.py -q
5 passed in 0.16s

python -m json.tool reports/tsa23-forest-condition-2026.json >/dev/null
OK
```

The card was also loaded and rendered through the open WS4 P90
`ws4.forest_condition` module:

```text
PYTHONPATH=<p90-worktree> python -c "from ws4.forest_condition import load_report; ..."
OK
```

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| pending | report commit | pending | The report commit's CI run is posted on pull request #51 before approval. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| No DHI indicator in the card | The instance has no TSA 23 DHI calculation or source | The parent and child issues were edited and a scope comment was posted; the WS4 P90 DHI fixture is not copied |
| No full dashboard gate | The TSA23 instance does not ship the seeded dashboard | The focused test and JSON parse are recorded as the available gates |

## 6. Next phase

Recommended default: **P124 TSA 23 BA-only pilot consumer test**, only if the
maintainer wants to close the remaining gap.

Goal: verify one WS4 or FHOPS consumer against the published BA-only pilot without
changing the inventory or making an operational claim.

Tasks:
- P124.1 Register the BA-only pilot as an optional WS4 feature source in a bounded
  test dataset, and record the row/pixel identity and abstention handling. Child issue
  to be created on approval.
- P124.2 Run one simulator or FHOPS consumer and record whether the BA values are
  read, ignored, or refused, with the reason.

Acceptance: the consumer test is reproducible; `-9999` is treated as abstention; no
AAC, THLB, target, or operational claim changes.

Reason for the default: the P122 acceptance record states that no WS4/FHOPS consumer
run was executed. This is the smallest remaining verification gap for the published
pilot.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.
