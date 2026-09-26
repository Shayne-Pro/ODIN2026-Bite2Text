# Validation record — 26 September 2026

This records the **checks performed for the Q58 reproduction update**, not a
claim that all historical experiments were retrained. No existing training
directory, original checkpoint, submitted image tag or raw dataset was modified.

## Passed in this update

| Check | Result / scope |
|---|---|
| Source controls | All 11 pre-existing sanitizer/risk-reranking tests pass |
| Reproduction helper tests | 8 tests pass: manifest, checksums, safe extraction, no overwrite, input staging, fold separation, geometry validation |
| Static checks | Python compilation, individual Bash syntax checks, `git diff --check` |
| Fresh upstream acquisition | Cloned the two public pinned commits into a previously absent vendor directory; all four patches applied successfully; second/third bootstrap runs were idempotent |
| Patched training imports | Copied the freshly patched Pointcept source to the isolated server directory; `MultiTaskClassifier(freeze_backbone=...)`, `Bite2TextDataset` and the evaluator registry import successfully with CUDA hidden, using the existing training environment |
| Patched normalizer loading | The freshly patched normalizer loads the verified published checkpoint on CPU with the required seed argument (20260809), using the existing normalizer environment |
| Q51/Q54 archive integrity | Both complete local release ZIPs match the published sizes and SHA-256 values |
| Q51 unpacking | Actual 4.48 GB bundle extracted into a new local directory; image archive and all nine model files match their recorded hashes |
| Server model consistency | The server's nine final model assets independently pass the same release verifier |
| Submitted image identity | Existing server Docker image ID matches `v9_assets.json`; no image tag overwritten |
| Report parsing | Rebuilt from the authorized raw training data in an isolated server directory; `report_labels.csv` and `patient_splits.csv` are byte-identical to the historical v3 artifacts |
| Twelve-head manifest | Rebuilt `manifest.jsonl` is byte-identical to the historical official-photo-first manifest (993 rows) |
| Data cohorts | Validated 991 prepared point cases, 867 supervised cases, empty final val/test, aligned labels/vocabularies and disjoint training/validation membership in every fold |
| Five-fold reconstruction | Recreated fold directories and assignments from existing normalized point arrays; `fold_assignments.csv` matches historical bytes; validation counts are 172/173/173/174/175 |
| Retrieval reconstruction | Rebuilt all three 867-case assets from existing normalized points and raw reports; **all three SHA-256 hashes match the published release exactly** |
| Model assembly | New nine-file runtime directory assembled from original training checkpoints plus the newly rebuilt retrieval assets; no existing artifact overwritten |

All 11 Bash command blocks in the reproduction README also passed `bash -n`.
The retrieval checks verified patient ordering, all descriptor values, mean and
scale, not just dimensions. Expected published hashes:

```text
retrieval_index.npz   10626d3d22ec2f221ac24779033687a4170ca835bd965ee859f5875a63a5e4b5
retrieval_reports.json 860701e6e14c0b5c916e1d4520ff4b2df3bd5f60ff40052584f87a08d673a95b
retrieval_labels.json bb40fa9402b7dfd1a0ce2b77ff30a18b98c29458451851aa6a83ba385b034ade
```

Patient-level logs, labels, reports and reconstructed outputs remain ignored
and are not included in this commit. Source tests ran locally with Python 3.9
and NumPy 1.26.4; CI additionally specifies Python 3.11. Data reconstruction
used the existing Linux development environment, not a newly provisioned machine.

## Not rerun / not established

- All-200 pretraining, five-fold PTv3/photo fitting and full-867 fitting were
  **not repeated**. Their commands/seeds/schedules are provided and were checked
  against source and original experiment metadata, not a fresh complete run.
- Full IOS normalization and 991-case mesh-to-point preprocessing were not
  repeated; fold/retrieval checks reused historical normalized point arrays.
  Input staging was exercised; raw pair count is 994 and the historical
  normalization exclusion `F5500` is explicit in the recipe.
- A full source Docker build and a new GPU report-generation smoke run were
  not executed in this update. Both server GPUs were occupied by other jobs;
  existing allocations were left untouched. Route A's runner and exact image
  are supplied, with source/test integrity checked separately.
- New anonymous downloads from Drive were not performed in this update;
  archive verification used the local bytes that were previously uploaded.
- Official BLEU/METEOR, hidden-test RadFact and Arena were not rescored. The
  historical scores are labelled as historical; lightweight local metrics
  and an LLM proxy must not be presented as the official evaluator.
- Full pipeline independence / cross-dataset patient non-overlap is not
  established by these checks. See the main reproduction README's limitations.

## What Q58 can truthfully mean

The repository now documents assets, environments, data policies, complete
training/reconstruction commands, evaluation boundaries and validation outcomes.
After this draft PR is reviewed and merged (or if the questionnaire links to
this exact branch/commit), **“Yes, a README sufficient to reproduce the
experiments is provided”** refers to that documentation and source completeness.
It does **not** assert an independent full GPU rerun or numerical identity.
Until merged, the default branch still contains the previous documentation.
