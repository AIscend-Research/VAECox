# Results

Two directories, and only one of them is the study.

## `tcga/` — the reproduction

Real TCGA (35 cohorts, 10,993 patients, 20,530 genes) via the open-access UCSC
Xena mirror, produced by `../VAECox_reproduction.ipynb` on a Tesla T4.
**These are the numbers to report.** Settings, seeds and deviations:
[`tcga/reproducibility_card.txt`](tcga/reproducibility_card.txt).

| File | Contents |
|---|---|
| `cindex_comparison.csv` | headline table — 5 models × 10 cancers + mean |
| `cindex_long.csv` | same, with per-cancer standard deviations across seeds |
| `robustness_by_cancer.csv` | C-index under 0–50% missing features and σ 0–2 noise |
| `subgroup_cindex.csv` | within-stratum C-index by age/sex/stage/subtype (all 162 strata, unfiltered) |
| `subgroup_gaps.csv` | best–worst gap per cancer×model×variable, **excluding TCGA free-text histology placeholders** |
| `subgroup_excluded_strata.csv` | the strata that filter removed, for audit |
| `cohort_fairness.csv` | cohort size and event count vs C-index, all 5 models |
| `lightweight_by_cancer.csv`, `lightweight_disparity.csv` | VAE size sweep, and whether shrinking hurts small cohorts more |
| `feature_subset.csv` | C-index vs gene budget, including a CPU-only run |
| `permutation_importance.csv` | top genes by permutation C-index drop |
| `km_summary.csv` | log-rank p-values for high/low predicted-risk split |
| `manuscript_numbers.json` | all of the above consolidated |
| `figures/` | 14 PNGs |

## `phase2/`, `phase3/` — toy-data track

Output of [`../scripts/`](../scripts/) on the 30-patients-per-cancer toy data.
Pipeline verification only: several cohorts have as few as 3 uncensored events,
so the C-index there measures split noise. Kept for provenance; superseded by
`tcga/` in every respect. See §9 of [`../REPRODUCIBILITY.md`](../REPRODUCIBILITY.md).

## A note on the subgroup filter

`subgroup_gaps.csv` was recomputed after the run to drop TCGA histology values
containing "specify" — `'Other, specify'` and `'Mixed Histology (please
specify)'`, both in BRCA. These are free-text placeholders, not clinical
categories: the patients in them share nothing except that whoever completed the
form declined to name a subtype, so a C-index difference between two such buckets
is not a disparity. `'NOS'` labels are kept, since "adenocarcinoma NOS" is a
genuine, if broad, pathology category.

The filter changes the headline: largest gap **0.475 → 0.242** (and moves it from
BRCA/subtype to STAD/age_group), mean subtype gap **0.173 → 0.063** (CoxRidge) and
**0.116 → 0.068** (VAECox). Age is the real disparity axis. The notebook now
applies this filter during the run, so a re-run reproduces the corrected numbers.
