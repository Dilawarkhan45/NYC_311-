## Pull Request Description
<!-- Provide a brief summary of the changes introduced by this pull request. -->

### Changes Summary
- [ ] Feature / Pipeline Update
- [ ] Bug Fix / Cleaning Constraint Update
- [ ] Documentation / Report Update
- [ ] Model / Evaluation Adjustment

### Related Issue / Checkpoint
<!-- e.g. Fixes Checkpoint 4 (ML Baseline) or Resolves #12 -->

---

## Pre-Merge Quality Verification Checklist
Please verify the following standards before requesting a peer review:

- [ ] **Tests Pass:** All unit tests pass locally via `pytest tests/ -v`.
- [ ] **Reproducibility:** Code runs end-to-end without errors from a fresh clone.
- [ ] **Data Integrity:** Raw ingested data (`data/raw/`) is untouched and never overwritten.
- [ ] **Quality Gate:** Pipeline validation pass rate meets or exceeds the 95.0% threshold.
- [ ] **No Leakage:** Preprocessing transformations (imputers, scalers, encoders) fit exclusively on the training split.
- [ ] **Documentation:** `docs/` and `README.md` have been updated to reflect any schema, metric, or architectural changes.
- [ ] **File Header Comments:** Every modified `.py` file starts with student Name, Roll Number, and Date.

---

## Reviewer Checklist (For Code Reviewer)
- [ ] Logic is clear and explainable.
- [ ] Edge cases (null values, negative durations, out-of-bound coordinates) are handled defensively.
- [ ] Variable and function names are self-documenting.
