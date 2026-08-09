#!/usr/bin/env python3
"""Fill the manuscript template with the numbers from an actual run.

Reads `results/manuscript_numbers.json` (written by the notebook's §6k), renders
every table and headline figure, and substitutes them into `manuscript.md`,
writing `manuscript_filled.md`. Nothing is typed by hand, so the paper can never
drift out of sync with the results.

    python paper/build_manuscript.py                 # looks in ./out/results
    python paper/build_manuscript.py --results DIR   # or wherever you unpacked it

Placeholders in manuscript.md look like {{NAME}}. Any placeholder with no value
is left visibly as {{NAME — NOT AVAILABLE}} rather than silently blanked, so an
unfinished section is impossible to miss on a read-through.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RESULTS = os.path.join(os.path.dirname(HERE), "out", "results")

MODEL_ORDER = ["CoxLasso", "CoxRidge", "Coxnnet", "CoxMLP", "VAECox"]


# --------------------------------------------------------------------------- #
# tiny markdown table helper (no pandas dependency — this must run anywhere)
# --------------------------------------------------------------------------- #
def md_table(headers, rows):
    if not rows:
        return "_(no data)_"
    out = ["| " + " | ".join(str(h) for h in headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else str(v) for v in r) + " |")
    return "\n".join(out)


def fmt(v, nd=3):
    if v is None or (isinstance(v, float) and v != v):
        return "—"
    if isinstance(v, (int, float)):
        return f"{v:.{nd}f}" if isinstance(v, float) else str(v)
    return str(v)


# --------------------------------------------------------------------------- #
# section builders
# --------------------------------------------------------------------------- #
def build_dataset_table(d):
    per = d.get("per_cohort", {})
    evaluated = d.get("evaluated", sorted(per))
    rows = []
    for c in evaluated:
        s = per.get(c)
        if not s:
            continue
        rows.append([c, s["n"], s["events"], f'{s["censor_pct"]}%',
                     int(s["median_survival_days"])])
    return md_table(["Cancer", "N patients", "Uncensored events", "Censoring rate",
                     "Median survival (days)"], rows)


def build_cindex_table(p2, evaluated):
    tbl = p2.get("table", [])
    if not tbl:
        return "_(no data)_", "_(no data)_"
    by = {}
    for r in tbl:
        by.setdefault(r["model"], {})[r["cancer"]] = r
    models = [m for m in MODEL_ORDER if m in by] + [m for m in by if m not in MODEL_ORDER]

    rows = []
    for m in models:
        row = [m]
        for c in evaluated:
            r = by[m].get(c)
            row.append("—" if not r else f'{fmt(r["mean_cindex"])} ± {fmt(r["std_cindex"], 2)}')
        mean = p2.get("mean_cindex", {}).get(m)
        row.append(fmt(mean))
        rows.append(row)
    table = md_table(["Model"] + evaluated + ["Mean"], rows)

    wins = p2.get("wins", {})
    win_rows = [[m, f'{wins.get(m, 0)}/{len(evaluated)}'] for m in models]
    return table, md_table(["Model", "Cancers won"], win_rows)


def build_robustness_table(rows):
    if not rows:
        return "_(no data)_"
    agg = {}
    for r in rows:
        k = (r["experiment"], r["level"])
        a = agg.setdefault(k, {"CoxRidge": [], "VAECox": []})
        for m in ("CoxRidge", "VAECox"):
            if r.get(m) is not None:
                a[m].append(r[m])
    out = []
    baseline = {}
    for (exp, lev), a in agg.items():
        cr = sum(a["CoxRidge"]) / len(a["CoxRidge"]) if a["CoxRidge"] else None
        vc = sum(a["VAECox"]) / len(a["VAECox"]) if a["VAECox"] else None
        baseline.setdefault(exp, (cr, vc))
        b_cr, b_vc = baseline[exp]
        d_cr = f"{(cr - b_cr) / b_cr * 100:+.1f}%" if cr and b_cr else "—"
        d_vc = f"{(vc - b_vc) / b_vc * 100:+.1f}%" if vc and b_vc else "—"
        out.append([exp, lev, fmt(cr), d_cr, fmt(vc), d_vc])
    return md_table(["Corruption", "Level", "CoxRidge", "Δ vs clean",
                     "VAECox", "Δ vs clean"], out)


def build_subgroup_table(gaps, limit=12):
    if not gaps:
        return "_(no data)_"
    rows = [[g["cancer"], g["model"], g["variable"], g["best_group"], fmt(g["best_cindex"]),
             g["worst_group"], fmt(g["worst_cindex"]), fmt(g["gap"])]
            for g in sorted(gaps, key=lambda x: -x["gap"])[:limit]]
    return md_table(["Cancer", "Model", "Variable", "Best group", "C-index",
                     "Worst group", "C-index", "Gap"], rows)


def build_lightweight_table(light):
    if not light:
        return "_(no data)_"
    agg = {}
    for r in light:
        a = agg.setdefault(r["config"], {"n_params": r["n_params"], "train_sec": r["train_sec"],
                                         "cis": []})
        if r.get("cindex") is not None:
            a["cis"].append(r["cindex"])
    rows = [[k, f'{v["n_params"]/1e6:.1f}M', f'{v["train_sec"]}s',
             fmt(sum(v["cis"]) / len(v["cis"]) if v["cis"] else None)]
            for k, v in agg.items()]
    return md_table(["VAE config", "Parameters", "Pretrain time", "Mean C-index"], rows)


def build_disparity_table(disp):
    if not disp:
        return "_(no data)_"
    evs = sorted(set(r["n_events"] for r in disp))
    med = evs[len(evs) // 2]
    rows = []
    for cfg in sorted(set(r["config"] for r in disp)):
        g = [r for r in disp if r["config"] == cfg and r.get("delta_vs_full") is not None]
        small = [r["delta_vs_full"] for r in g if r["n_events"] <= med]
        large = [r["delta_vs_full"] for r in g if r["n_events"] > med]
        rows.append([cfg,
                     f'{sum(small)/len(small):+.4f}' if small else "—",
                     f'{sum(large)/len(large):+.4f}' if large else "—"])
    return md_table([f"VAE config", f"Δ C-index, ≤{med} events",
                     f"Δ C-index, >{med} events"], rows)


def build_featsub_table(fs):
    if not fs:
        return "_(no data)_"
    rows = [[r["k_genes"], r["model"], fmt(r["mean_cindex"]),
             f'{r["vae_params"]/1e6:.2f}M', f'{r["vae_pretrain_sec"]}s',
             f'{r["survival_fit_sec"]}s', r["device"]] for r in fs]
    return md_table(["Genes kept", "Model", "Mean C-index", "VAE params",
                     "VAE pretrain", "Survival fits", "Device"], rows)


def build_importance_table(imp, top=10):
    if not imp:
        return "_(no data)_"
    rows = []
    for (c, m) in sorted({(r["cancer"], r["model"]) for r in imp}):
        sel = [r for r in imp if r["cancer"] == c and r["model"] == m][:top]
        rows.append([c, m, ", ".join(r["gene"] for r in sel),
                     fmt(sel[0]["base_cindex"]) if sel else "—"])
    return md_table(["Cancer", "Model", f"Top-{top} genes by permutation drop",
                     "Base C-index"], rows)


def build_km_table(km):
    if not km:
        return "_(no data)_"
    rows = [[r["cancer"], r["n_test"], r["n_events"], r["n_high"], r["n_low"],
             fmt(r["log_rank_p"], 4), "yes" if r.get("significant") else "no"] for r in km]
    return md_table(["Cancer", "N test", "Events", "High risk", "Low risk",
                     "Log-rank p", "p<0.05"], rows)


def build_paper_comparison(cmp_rows):
    if not cmp_rows:
        return ("_Paper Table 1 not supplied — fill in `paper/paper_table1.csv` and re-run "
                "§6j.4 of the notebook to populate this._")
    rows = [[r["cancer"], r["model"], fmt(r["mean_cindex"]), fmt(r["paper_cindex"]),
             f'{r["delta"]:+.3f}'] for r in cmp_rows]
    deltas = [abs(r["delta"]) for r in cmp_rows]
    tbl = md_table(["Cancer", "Model", "Ours", "Paper", "Δ"], rows)
    return (f"{tbl}\n\nMean |Δ| = {sum(deltas)/len(deltas):.4f}, "
            f"max |Δ| = {max(deltas):.4f} over {len(deltas)} cells.")


# --------------------------------------------------------------------------- #
def _verdict(wins, n_evaluated):
    """The paper's claim is 7/10 = 0.7 of cancers won; score ours on the same scale."""
    if not n_evaluated:
        return "not evaluated"
    frac = wins / n_evaluated
    if frac >= 0.7:
        return "reproduced"
    if frac >= 0.4:
        return "partially reproduced"
    return "not reproduced"


def collect(nums):
    d, setup, p2 = nums["data"], nums["setup"], nums["phase2"]
    ext = nums.get("extensions", {})
    evaluated = d.get("evaluated", [])

    cindex_tbl, wins_tbl = build_cindex_table(p2, evaluated)
    wins = p2.get("wins", {})
    vaecox_wins = wins.get("VAECox", 0)

    v = {
        "DATA_SOURCE": d.get("source", "—"),
        "N_COHORTS": d.get("n_cohorts_loaded", "—"),
        "N_GENES": d.get("n_genes", "—"),
        "COHORT_LIST": ", ".join(d.get("cohorts", [])),
        "EVALUATED_LIST": ", ".join(evaluated),
        "N_EVALUATED": len(evaluated),
        "DATASET_TABLE": build_dataset_table(d),

        "DEVICE": setup.get("gpu", setup.get("device", "—")),
        "VAE_ARCH": f'{d.get("n_genes")}→{setup.get("vae_hidden")}→{setup.get("vae_latent")}',
        "VAE_EPOCHS": setup.get("vae_epochs"),
        "SURV_EPOCHS": setup.get("surv_epochs"),
        "N_SEEDS": len(setup.get("seeds", [])),
        "HP_GRID": ", ".join(str(tuple(h)) for h in setup.get("hp_grid", [])),

        "CINDEX_TABLE": cindex_tbl,
        "WINS_TABLE": wins_tbl,
        "VAECOX_WINS": f"{vaecox_wins}/{len(evaluated)}",
        "BEST_MEAN_MODEL": p2.get("best_mean_model", "—"),
        "BEST_MEAN_VALUE": fmt(max((x for x in p2.get("mean_cindex", {}).values()
                                    if x is not None), default=None)),
        "VAECOX_MEAN": fmt(p2.get("mean_cindex", {}).get("VAECox")),
        # Judged as a fraction of the cancers actually evaluated, so a partial
        # cohort list is not automatically scored as a failure.
        "REPRODUCED_VERDICT": _verdict(vaecox_wins, len(evaluated)),
        "PAPER_COMPARISON": build_paper_comparison(nums.get("paper_comparison", [])),

        "ROBUSTNESS_TABLE": build_robustness_table(ext.get("robustness", [])),
        "SUBGROUP_TABLE": build_subgroup_table(ext.get("subgroup_gaps", [])),
        "LIGHTWEIGHT_TABLE": build_lightweight_table(ext.get("lightweight", [])),
        "DISPARITY_TABLE": build_disparity_table(ext.get("lightweight_disparity", [])),
        "FEATSUB_TABLE": build_featsub_table(ext.get("feature_subset", [])),
        "IMPORTANCE_TABLE": build_importance_table(ext.get("importance", [])),
        "KM_TABLE": build_km_table(ext.get("kaplan_meier", [])),
    }
    km = ext.get("kaplan_meier", [])
    v["KM_SIGNIFICANT"] = (f'{sum(1 for r in km if r.get("significant"))}/{len(km)}'
                           if km else "—")
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=DEFAULT_RESULTS,
                    help="directory containing manuscript_numbers.json")
    ap.add_argument("--template", default=os.path.join(HERE, "manuscript.md"))
    ap.add_argument("--out", default=os.path.join(HERE, "manuscript_filled.md"))
    a = ap.parse_args()

    src = os.path.join(a.results, "manuscript_numbers.json")
    if not os.path.exists(src):
        sys.exit(f"error: {src} not found.\n"
                 f"Run the notebook through §6k, download /kaggle/working, and unpack it "
                 f"as ./out — or pass --results DIR.")
    with open(src) as f:
        nums = json.load(f)
    with open(a.template) as f:
        text = f.read()

    values = collect(nums)
    missing = []

    def sub(m):
        key = m.group(1).strip()
        if key in values and values[key] is not None:
            return str(values[key])
        missing.append(key)
        return f"{{{{{key} — NOT AVAILABLE}}}}"

    filled = re.sub(r"\{\{([A-Z0-9_]+)\}\}", sub, text)
    with open(a.out, "w") as f:
        f.write(filled)

    print(f"wrote {a.out}")
    if missing:
        print(f"warning: {len(set(missing))} placeholder(s) had no value: "
              f"{', '.join(sorted(set(missing)))}")
    else:
        print("all placeholders filled")


if __name__ == "__main__":
    main()
