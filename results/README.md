# Toy-data results

Everything in this directory came from [`../scripts/`](../scripts/) running on the
30-patients-per-cancer toy data. **These are not reproduction results.** Several
cohorts have as few as 3 uncensored events, so the C-index here measures split
noise more than model quality — see §9 of [`../REPRODUCIBILITY.md`](../REPRODUCIBILITY.md).

Real-TCGA results from `VAECox_reproduction.ipynb` land in `../out/` (gitignored;
unzip `vaecox_results.zip` there). Those are the numbers the manuscript reports.

| | |
|---|---|
| `phase2/cindex_comparison.csv` | C-index, 6 models × 10 cancers |
| `phase3/3a_lightweight_models.csv` | hidden/latent dimension sweep |
| `phase3/3b_feature_subset.csv` | C-index vs feature count |
| `phase3/3cd_robustness.csv` | missing / noisy feature robustness |
| `phase3/3e_fairness_correlation.csv` | event rate vs C-index |
| `phase3/feature_importance.csv` | top genes per model and cancer |
| `phase3/km_summary.csv` | log-rank p-values by predicted risk group |
| `phase3/cancer_stats.csv` | per-cohort N, events, censoring rate |
| `phase3/reproducibility_card.txt` | full settings and deviations |
| `phase3/figures/` | the 9 toy-data figures |
