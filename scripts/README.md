# Toy-data pipeline

> **This is not the study.** These scripts run the VAECox pipeline on the 30-patients-per-cancer
> toy data shipped with the original repository. They verify that the pipeline
> executes; they cannot test the paper's claim, because several cohorts have as
> few as 3 uncensored events and the C-index there is dominated by split noise.
>
> The actual reproduction is [`../VAECox_reproduction.ipynb`](../VAECox_reproduction.ipynb)
> on real TCGA. See [`../RUN.md`](../RUN.md).

## Provenance

| File | Origin |
|---|---|
| `main.py`, `models.py`, `utils.py` | upstream [dmis-lab/VAECox](https://github.com/dmis-lab/VAECox), unmodified |
| `vae_main.py`, `vae_models.py`, `vae_utils.py` | upstream, unmodified |
| `vae_run.py` | upstream; patched to resolve `vae_main.py` by absolute path so it can be launched from the repo root |
| `data_preparation.py`, `create_vae_dataset.py` | upstream, unmodified (full-TCGA prep; not used by the toy track) |
| `create_toy_vae_dataset.py` | added for this study |
| `phase1_data_prep.py` | added — z-normalisation, stratified splits, CV indices |
| `phase2_reproduction.py` | added — trains all models, evaluates C-index |
| `phase3_extensions.py` | added — lightweight models, robustness, fairness |
| `phase3_additional.py` | added — feature importance, Kaplan–Meier, writes `REPRODUCIBILITY.md` |
| `generate_figures.py` | added — renders the 9 toy-data figures from saved CSVs |

The `phase*` scripts import `models` and `vae_models` from upstream, which is why
everything sits in one directory.

## Running

**Always invoke from the repository root**, not from inside `scripts/`. Python
puts the script's own directory on `sys.path` (so the `models` import resolves)
while the working directory stays at the root (so `data/` and `results/` paths
resolve):

```bash
python scripts/create_toy_vae_dataset.py   # → data/toyforVAE_*  (gitignored)
python scripts/phase1_data_prep.py         # → data/prepared/    (gitignored)
python scripts/vae_run.py                  # → results/vae/      (~2 min, CPU)
python scripts/phase2_reproduction.py      # → results/phase2/cindex_comparison.csv
python scripts/phase3_extensions.py        # → results/phase3/3*.csv
python scripts/phase3_additional.py        # → results/phase3/, rewrites REPRODUCIBILITY.md
python scripts/generate_figures.py         # → results/phase3/figures/
```

Everything under `data/prepared/`, `data/embeddings/` and `results/vae/` is
rebuildable and therefore gitignored. Total runtime is roughly 30–40 minutes on
a CPU.
