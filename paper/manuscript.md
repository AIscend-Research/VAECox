# Reproducing VAECox: Transfer Learning from Pan-Cancer Transcriptomic Data for Robust Patient Survival Prediction

*A reproducibility study of* Kim, Kim, Choe, Lee & Kang (2020), **"Improved survival
analysis by learning shared genomic information from pan-cancer data"**,
*Bioinformatics* 36(Suppl_1):i389–i398. DOI: [10.1093/bioinformatics/btaa462](https://doi.org/10.1093/bioinformatics/btaa462).
Original code: <https://github.com/dmis-lab/VAECox>.

> **How to use this file.** Double-brace placeholders are filled automatically by
> `python paper/build_manuscript.py`, which reads `manuscript_numbers.json` from
> the notebook run and writes `manuscript_filled.md`. Write prose here; never
> retype a number. Sentences in _[square brackets, italic]_ are prompts telling
> you what to write once you have seen the filled numbers — delete them as you go.

---

## Abstract

We reproduce VAECox, a deep survival model that pretrains a variational
autoencoder (VAE) on pan-cancer RNA-seq data and transfers the learned encoder
into a Cox proportional-hazards network fine-tuned per cancer type. Using
{{N_COHORTS}} TCGA cohorts and {{N_GENES}} genes drawn from open-access UCSC Xena
data, we retrain the full pipeline and evaluate it against four baselines on
{{N_EVALUATED}} cancer types by concordance index (C-index). The original paper
reports that VAECox wins on 7 of 10 cancers; in our run it wins on
**{{VAECOX_WINS}}**, which we characterise as **{{REPRODUCED_VERDICT}}**. We then
extend the study in four directions aimed at responsible, low-resource medical
AI: robustness to missing and noisy expression values, fairness across cancer
cohorts and clinical subgroups (age, sex, stage, histological subtype), a
lightweight-model sweep that asks whether compression disproportionately harms
small cohorts, and permutation-based gene attribution. _[One or two sentences on
your single most interesting extension finding.]_

---

## 1 · Introduction and motivation

Survival prediction from tumour transcriptomes sits at the centre of cancer
prognosis and treatment planning, but it is a statistically hostile problem: a
cohort has hundreds of patients and tens of thousands of genes, so
high-capacity models overfit before they generalise. Censoring compounds this —
a patient still alive at last follow-up contributes only a lower bound on
survival time, so the effective sample size is the number of *observed deaths*,
often a small fraction of the cohort.

VAECox attacks the sample-size problem with transfer learning. Because RNA-seq
measures the same genes regardless of tissue of origin, an unsupervised model
trained across *all* cancers can learn shared structure from far more samples
than any single cohort provides, and that representation can then be fine-tuned
on one cancer with far fewer parameters exposed to the small labelled set.

We reproduce this claim and ask a second question the original paper does not:
**who does the method work for, and at what compute cost?** A prognosis model
that is accurate only on the largest, best-studied cohorts, or that requires a
GPU cluster to train, is not usable by the research groups and clinics that most
need it.

### 1.1 · Background: survival analysis in one page

- **Survival time and censoring.** Each patient has a time $t_i$ and an
  indicator $\delta_i$ ($1$ = death observed, $0$ = censored at last follow-up).
- **Cox proportional hazards.** The model predicts a scalar risk
  $\theta_i = f(x_i)$ and assumes hazard $h_i(t) = h_0(t)\exp(\theta_i)$; the
  baseline $h_0$ cancels in the partial likelihood, so only the *ordering* of
  risks is learned.
- **Partial log-likelihood loss.** $\ \ell = -\frac{1}{|D|}\sum_{i \in D}
  \left[\theta_i - \log \sum_{j \in R(t_i)} e^{\theta_j}\right]$, where $D$ is
  the set of observed deaths and $R(t_i) = \{j : t_j \ge t_i\}$ is the risk set.
- **C-index.** The fraction of comparable patient pairs whose predicted risk
  ordering matches their observed survival ordering. $0.5$ = random, $1.0$ =
  perfect. It is a *ranking* metric, which is why the loss above only needs to
  get orderings right.

### 1.2 · The original method

1. **Pretrain** a VAE on pan-cancer expression: encoder
   $p \to 4096 \to (\mu, \sigma) \in \mathbb{R}^{128}$, decoder mirrored, Tanh
   activations, loss = MSE reconstruction + KL divergence.
2. **Transfer** the encoder into a survival model: $\mu$ feeds a Cox-nnet head.
3. **Fine-tune** the whole stack on one cancer's labelled data with the Cox
   partial-likelihood loss.

---

## 2 · Reproduction: what we did

### 2.1 · Data

{{DATASET_TABLE}}

Source: **{{DATA_SOURCE}}**. Cohorts loaded for VAE pretraining: {{COHORT_LIST}}.
Cohorts evaluated for survival: {{EVALUATED_LIST}}.

**Data-access deviation.** The paper obtains TCGA through the ICGC Data Portal,
which for the controlled-access tier requires dbGaP approval under accession
phs000178 — a registration and data-transfer-agreement process that does not fit
inside a course-length project. We instead use the open-access UCSC Xena TCGA
Hub mirror (`HiSeqV2_PANCAN`), which ships the same RNA-seq measurements,
already log2-transformed and pan-cancer normalised, with no access barrier. The
gene set is therefore {{N_GENES}} genes rather than the paper's 20,502, and
normalisation is pan-cancer rather than per-cohort. _[State whether you think
this plausibly moves the C-index, and in which direction.]_

### 2.2 · Preprocessing

Per-gene z-normalisation with the scaler **fit on the training split only** —
fitting on the full matrix would leak test-set distribution into training and
inflate the C-index. Splits are stratified 80/20 by survival-time quintile, and
every experiment is repeated over {{N_SEEDS}} random seeds.

### 2.3 · Models compared

| Model | Description | Role |
|---|---|---|
| CoxLasso | Linear Cox with L1 penalty | paper baseline |
| CoxRidge | Linear Cox with L2 penalty | paper baseline |
| Cox-nnet | Single hidden layer ($\sqrt{p}$ units), Tanh | paper baseline |
| CoxMLP | Two-layer MLP, ReLU | additional baseline |
| **VAECox** | Pretrained VAE encoder, **fine-tuned**, + Cox-nnet head | method under test |

### 2.4 · Training setup

- VAE: {{VAE_ARCH}}, Adam, {{VAE_EPOCHS}} epochs.
- Survival models: {{SURV_EPOCHS}} epochs, Adam, hyperparameters chosen per
  cancer from the reduced grid {{HP_GRID}}.
- Hardware: {{DEVICE}}.
- Seeds: {{N_SEEDS}}.

**Implementation notes and bugs found.** _[List what actually broke and what you
had to change — this is one of the most valuable parts of a reproduction. Known
items to cover: the original repo targets Python 3.8 and needed fixes to run on a
current interpreter; and in our own first implementation, `VAECox` aliased the
pretrained encoder module instead of copying it, so fine-tuning silently mutated
the shared pretrained weights and every cancer after the first started from the
previous one's fine-tuned encoder. Describe how you found it and what it changed.]_

---

## 3 · Reproduction results

### 3.1 · C-index across cancer types

{{CINDEX_TABLE}}

### 3.2 · Win counts

{{WINS_TABLE}}

The paper reports VAECox winning **7/10**. We observe **{{VAECOX_WINS}}**. The
best mean C-index across all cancers is achieved by **{{BEST_MEAN_MODEL}}**
({{BEST_MEAN_VALUE}}); VAECox averages {{VAECOX_MEAN}}.

_[Interpret honestly. If VAECox wins fewer cancers than reported, say so plainly
and give your best explanation — reduced HP search, different gene set,
normalisation, seed variance — rather than presenting a partial result as a
confirmation. If per-cancer standard deviations overlap heavily, note that win
counts are a brittle summary statistic.]_

### 3.3 · Cell-by-cell comparison with the original Table 1

{{PAPER_COMPARISON}}

---

## 4 · Extensions

### 4.1 · Robustness to missing and noisy expression values

Real transcriptomic pipelines drop genes and add batch noise. We corrupt the
**test** set only — the model is trained once on clean data and then scored under
each corruption level — which isolates inference-time robustness from any change
in what was learned. Missing values are zeroed after z-normalisation (i.e. set to
the training mean); noise is additive Gaussian in z-units.

{{ROBUSTNESS_TABLE}}

_[The interesting question is not which model scores higher, but which
**degrades more slowly**. Report relative degradation. If VAECox is more robust,
argue why the pan-cancer latent space would absorb per-gene corruption; if it is
not, say so.]_

### 4.2 · Fairness across cohorts and clinical subgroups

{{SUBGROUP_TABLE}}

Strata with fewer than 10 test patients or 3 uncensored events are excluded: the
C-index is not estimable there, and reporting it would manufacture disparities
out of noise. _[Discuss which variable produces the widest gaps. Distinguish
"the model is worse for this group" from "this group has fewer events, so the
estimate is noisier" — the second is a measurement problem, the first is a
fairness problem, and only the per-stratum sample sizes let you tell them apart.]_

### 4.3 · Lightweight models

{{LIGHTWEIGHT_TABLE}}

Every configuration is pretrained for the same number of epochs, so the
comparison is at equal compute budget rather than equal convergence.

**Does compression fall unevenly?** Cohorts are split at the median number of
uncensored events; the table reports the mean change in C-index relative to the
full-size VAE.

{{DISPARITY_TABLE}}

_[This is the core responsible-AI result of the study. A negative Δ that is
larger in magnitude for low-event cohorts means the cheap model is cheapest
precisely where it is least accurate — i.e. the accessibility gain is paid for
by the least-studied cancers. State clearly whichever direction you observe.]_

### 4.4 · Low-resource accessibility: feature budget and CPU feasibility

{{FEATSUB_TABLE}}

Genes are ranked by pan-cancer variance, which never touches survival labels, so
selection cannot leak into the test split. _[Report the smallest gene budget that
retains usable accuracy, and the wall-clock CPU numbers. This is the concrete
"can a student without a GPU run this?" answer — give it as a recipe.]_

### 4.5 · Interpretability: permutation-based gene attribution

VAECox's weights are uninterpretable per gene — the encoder mixes all
{{N_GENES}} inputs before the Cox head sees anything — so `|Cox weight|` cannot
rank genes for it. We instead shuffle one gene's column across test patients and
measure the resulting C-index drop, a model-agnostic attribution that puts
VAECox and the linear baselines on equal footing.

{{IMPORTANCE_TABLE}}

_[Check a handful of top genes against the literature for that cancer type. Be
candid if they look like noise: with small event counts, permutation importance
is unstable, and saying so is more useful than a confident-sounding gene list.]_

### 4.6 · Kaplan–Meier risk stratification

Test patients are split at the median predicted risk and compared by log-rank
test.

{{KM_TABLE}}

Risk stratification is significant (p < 0.05) in **{{KM_SIGNIFICANT}}** cohorts.
_[Note that KM separation and C-index measure different things: a model can rank
pairs well yet fail to split the cohort cleanly at the median, and vice versa.]_

---

## 5 · Limitations

1. **Data provenance.** Open-access Xena data rather than the paper's ICGC
   controlled-access tier; a different gene set and normalisation scheme.
2. **Reduced hyperparameter search.** The paper searches 18 combinations per
   cancer under 5-fold CV; we search {{HP_GRID}} once per cancer. All models are
   handicapped equally, but absolute C-indices are pessimistic.
3. **Extensions use fixed hyperparameters**, not the per-cancer search, so
   extension C-indices are not directly comparable to the Phase 2 table.
4. **Small event counts.** Several cohorts have few uncensored events; C-index
   estimates there have wide seed-to-seed variance, and win counts inherit it.
5. **Subgroup coverage is uneven.** Stage is undefined for cohorts that are
   graded rather than staged; some cohorts are single-sex by construction. No
   race or socioeconomic variable is analysed, so the fairness analysis is
   partial by construction.
6. **No clinical validation.** C-index on a held-out TCGA split is not evidence
   of clinical utility. Nothing here is validated for patient care.

---

## 6 · Conclusion

_[Write last. Cover, in order: (1) what reproduced and what did not, with the
win count stated plainly; (2) which deviations you believe explain the gap; (3)
what the extensions add that the original paper does not answer — especially the
robustness and equity-of-compression results; (4) what this implies for
low-resource groups wanting to use transfer learning for cancer prognosis.]_

---

## Reproducibility

Everything in this paper is regenerated by:

```bash
# 1. Run VAECox_reproduction.ipynb on Kaggle (GPU, GenoTEX dataset attached)
# 2. Download /kaggle/working and unpack it as ./out
python paper/build_manuscript.py       # → paper/manuscript_filled.md
```

Full settings, seeds, deviations and per-experiment commands:
`out/results/reproducibility_card.txt` and `REPRODUCIBILITY.md`.

## References

1. Kim S., Kim K., Choe J., Lee I., Kang J. Improved survival analysis by
   learning shared genomic information from pan-cancer data. *Bioinformatics*
   36(Suppl_1):i389–i398, 2020.
2. Ching T., Zhu X., Garmire L.X. Cox-nnet: An artificial neural network method
   for prognosis prediction of high-throughput omics data. *PLoS Computational
   Biology* 14(4), 2018.
3. Goldman M.J. et al. Visualizing and interpreting cancer genomics data via the
   Xena platform. *Nature Biotechnology* 38:675–678, 2020.
