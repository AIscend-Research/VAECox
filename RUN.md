# What to run, in order

Two tracks exist in this repo and they are **not** interchangeable:

> **Runtime:** ~3.5–5 h on a T4. Every expensive stage caches its CSV, so an
> interrupted run resumes instead of restarting — see *If you are short on GPU
> quota* below.

| Track | Data | Purpose | Status |
|---|---|---|---|
| [`scripts/`](scripts/) (toy pipeline + upstream fork) | Toy data, 30 patients/cancer | Verify the pipeline executes | Done — results in `results/` |
| `VAECox_reproduction.ipynb` | Real TCGA (open-access Xena mirror) | **The actual reproduction + extensions** | Not yet run |

Toy-data C-indices cannot test the paper's claim (as few as 3 uncensored events
per cancer). Everything the report says about reproduction has to come from the
notebook run.

---

## Step 1 — Run the notebook on Kaggle (the long one)

1. Upload `VAECox_reproduction.ipynb` to Kaggle.
2. **Add data** → search *GenoTEX: LLM Agent Benchmark for Genomic Analysis*
   (uploader `haoyangliu14`) → attach it.
3. **Settings** → Accelerator → **GPU T4 x2** (or P100). Internet can stay Off.
4. **Run all.** Expect several hours; §5 (Phase 2) and §6i (lightweight sweep)
   dominate. Everything is checkpointed to `/kaggle/working`, so if the 12-hour
   session limit hits, re-running resumes from the cached VAE.
5. Sanity-check the §1 printout before letting it run on: per-cohort event counts
   must be in the dozens–hundreds. Single digits means it loaded toy data and
   the whole run is worthless.

**Want a fast smoke test first?** In §0 set `VAE_EPOCHS=50`, `SEEDS=list(range(3))`,
`HP_SEARCH=False`. It finishes in well under an hour and exercises every cell. Then
reset those three values and do the real run.

### If you are short on GPU quota

Kaggle allots 30 GPU-hours/week. The full run is ~3.5–5 h, so if you have less
than ~6 h left, **split it across two committed runs** — the notebook is
resumable and will not redo completed work.

**Session A** — Run All, then stop after §5 finishes (or just let it run; if the
quota kills it later, §5's output is already committed). Produces
`vae_pretrained.pt` and `results/cindex_long.csv`. Roughly 1.5–2.5 h.

**Session B** — *Add Data → Your Datasets → Notebook Output*, attach Session A's
output, then Run All. §3 finds the checkpoint and skips VAE pretraining; §5 finds
`cindex_long.csv` and prints `[resume] … Phase 2 not re-run`. Roughly 2–3 h.

The same mechanism covers every expensive extension —
`subgroup_cindex`, `lightweight_by_cancer`, `feature_subset`,
`permutation_importance`, `robustness_by_cancer`, `km_summary` each reload from
CSV if a previous run produced them. So a third session picks up wherever the
second stopped. Set `CFG["RESUME"]=False` to force a clean recompute.

**Always use Save Version → Save & Run All (Commit).** An interactive session's
`/kaggle/working` is lost when the session ends; only a committed run publishes
its output, and only a published output can be attached to the next session.

What the notebook now produces, beyond what it did before:

| Section | Output | Roadmap item it covers |
|---|---|---|
| §6g | clinical metadata (age, sex, stage, subtype) | prerequisite for subgroup analysis |
| §6h | `subgroup_cindex.csv`, `subgroup_gaps.csv`, `cohort_fairness.csv` | Phase 3 → "Evaluate performance by clinical subgroup" |
| §6i.a | `lightweight_by_cancer.csv`, `lightweight_disparity.csv` | "Report whether lightweight models disproportionately reduce performance on underrepresented groups" |
| §6i.b | `feature_subset.csv` (incl. a forced CPU-only run) | "CPU-only training on a smaller feature subset to measure accessibility" |
| §6j.1 | `permutation_importance.csv` | "SHAP-style analysis to identify genes contributing most" |
| §6j.2 | `robustness_by_cancer.csv` | robustness on all 10 cancers, not just one |
| §6j.3 | `km_summary.csv`, `km_all_cohorts.png` | "Kaplan-Meier curves by predicted risk group" |
| §6j.4 | `paper_comparison.csv` | direct comparison against the paper's Table 1 |
| §6k | `manuscript_numbers.json` + 5 extension figures | feeds Phase 4 |
| §7 | `ph2_cindex_per_cancer.png` (with seed error bars), `ph2_cindex_heatmap.png`, `ph2_wins.png`, `ph2_vs_paper.png` | visuals for the headline result |
| §9 | `vaecox_results.zip` | one small download containing everything above |

## Step 2 — Transcribe the paper's Table 1

Open the paper and fill the `paper_cindex` column of
[paper/paper_table1.csv](paper/paper_table1.csv). The rows are already laid out
with matching cancer/model names; partial fills are fine.

The paper's numbers are deliberately **not** hard-coded anywhere in this repo —
nothing attributed to the original authors should be a guess. Without this file
§6j.4 skips and §3.3 of the manuscript stays visibly empty.

Attach the filled CSV as a Kaggle dataset (or upload it to `/kaggle/working`)
before the run if you want the comparison inside the same session; otherwise
re-run §6j.4 locally later.

## Step 3 — Pull the results back

The last cell (§9) writes `vaecox_results.zip` containing **only** the CSVs,
figures, card and `manuscript_numbers.json` — a few MB. Do not use "Download
all": `/kaggle/working` also holds the ~680 MB VAE checkpoint, which is
gitignored and only useful for resuming a Kaggle run.

§9 also verifies every expected output exists and prints `!! EXPECTED OUTPUT
MISSING` for anything absent, so a section that failed silently can't slip past.

```bash
unzip vaecox_results.zip -d out/     # → out/results/*.csv, out/figures/*.png
```

## Step 4 — Build the paper

```bash
python paper/build_manuscript.py           # reads out/results/, writes paper/manuscript_filled.md
```

Every table and headline number in the manuscript is injected from the run — no
number is retyped. Write prose in [paper/manuscript.md](paper/manuscript.md)
(the `_[bracketed italic]_` notes say what to write in each section), then re-run
the build. If a placeholder has no data it appears as
`{{NAME — NOT AVAILABLE}}` rather than silently vanishing.

## Step 5 — Regenerate the toy-data checklist (optional)

Only if you re-run the local scripts:

```bash
python scripts/phase3_additional.py    # rewrites REPRODUCIBILITY.md, section 9 computed from the CSV
```

---

## Known issue fixed in this round

`VAECox.__init__` assigned the pretrained encoder's modules directly instead of
copying them, so all fine-tuning mutated the one shared VAE in place: the second
cancer trained started from the first cancer's fine-tuned weights, and results
depended on evaluation order. It now deep-copies. Any C-index produced by an
earlier version of the notebook should be discarded.
