"""Generate JIIS SI tables (S1-S17) from the current result caches.

Output: 04_投稿准备/JIIS_submission/source/JIIS_SI_tables.tex
Numbers are bitwise identical to the main-text source (62-unit sync).
SHAP unit-level bootstrap CI uses seed 2026, B=2000 (documented in Notes).
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "04_投稿准备",
    "JIIS_submission", "source", "JIIS_SI_tables.tex"))
BS = chr(92)
BT = BS * 2


def load(name):
    p = cpath(name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def esc(s):
    return str(s).replace("_", BS + "_")


def tab(cols, rows, note=None):
    L = [BS + "begin{tabular}{" + "l" + "r" * (len(cols) - 1) + "}",
         BS + "toprule " + " & ".join(cols) + " " + BT + " " + BS + "midrule"]
    L += [r + " " + BT for r in rows]
    if note:
        L.append(BS + "midrule")
        L.append(BS + "multicolumn{" + str(len(cols)) + "}{l}{{" + BS + "small " + note + "}} " + BT)
    L.append(BS + "bottomrule" + BS + "end{tabular}")
    return L


def block(sid, caption, lines):
    return ([BS + "begin{table}[t]", BS + "centering",
             BS + "caption{" + caption + "}",
             BS + "label{tab:" + sid + "}"] + lines + [BS + "end{table}"])


def main():
    L = []

    r = load("main_results.json")
    sh_if = load("shap_iforest.json")

    # ---- S1 per-unit L1/top1, 23 iforest mixed units (+SHAP) ----
    mix = sorted(u for u in r if "_mix_" in u)
    rows = []
    for u in mix:
        cells = [esc(u), str(r[u]["RC-CA"]["n_test"])]
        for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec"):
            v = r[u][m]
            t1 = v.get("layer2_top1")
            cells.append("%.2f/%.2f" % (v["layer1_macro_f1"], t1) if t1 is not None
                         else "%.2f" % v["layer1_macro_f1"])
        sv = (sh_if or {}).get(u)
        if sv and sv.get("layer2_top1") is not None:
            cells.append("%.2f/%.2f" % (sv["layer1_macro_f1"], sv["layer2_top1"]))
        else:
            cells.append("--")
        rows.append(" & ".join(cells))
    L += block("S1", "Per-unit layer-1 macro-F1 / variable-type top-1 on the 23 "
               "isolation-forest mixed units (FAR 5" + BS + "%). Columns: four core "
               "methods and the exact-Shapley baseline (SHAP).",
               tab(["Unit", "n", "RC-CA", "GlobalCF", "CondAttr", "AERec", "SHAP"], rows))

    # ---- S2 variable-level units ----
    at = load("at_ext_all.json")
    ce = load("cmhmil_ext.json")
    sh_mi = load("shap_cmhmil.json")
    rows = []
    for u in sorted(x for x in r if x.endswith("_var")):
        cells = [esc(u), str(r[u]["RC-CA"]["n_test"])]
        for m in ("RC-CA", "CondAttr", "AERec", "Grad"):
            v = r[u].get(m) or {}
            t1, t3 = v.get("layer2_top1"), v.get("layer2_top3")
            cells.append("%.2f/%.2f" % (t1, t3) if t1 is not None else "--")
        rows.append(" & ".join(cells))
    for tag, n, t1 in (("AT" + BS + "_PSM" + BS + "_var", "--",
                        at["AT_PSM_var_reconstructed"]),
                       ("AT" + BS + "_SMAP" + BS + "_var", "--", at["AT_SMAP_var"])):
        cells = [tag, n]
        for m in ("RC-CA", "CondAttr", "AERec", "Grad"):
            cells.append("%.2f/--" % t1[m] if m in t1 else "--")
        rows.append(" & ".join(cells))
    for ds in ("PSM", "SMAP"):
        v = ce[ds]
        cells = ["cmhmil" + BS + "_" + ds + BS + "_var", str(v["RC-CA"]["n"])]
        for m in ("RC-CA", "CondAttr", "AERec", "Grad"):
            mm = v.get(m) or {}
            cells.append("%.2f/%.2f" % (mm.get("top1", float("nan")),
                                        mm.get("top3", float("nan"))) if mm else "--")
        rows.append(" & ".join(cells))
    L += block("S2", "Variable-level units: top-1/top-3 (top-3 unavailable for the "
               "two AT units trained for this study, marked --). Eight units across "
               "the AT and deep-MIL detectors.",
               tab(["Unit", "n", "RC-CA", "CondAttr", "AERec", "Grad"], rows))

    # ---- S3 bootstrap CIs (merged: unit-level + paired + window-level) ----
    b = load("bootstrap_ci.json")["ci"]
    rows = []
    for m in ("RC-CA", "GlobalCF", "RegimeGlobal", "CondAttr", "AERec",
              "Granger", "zDev", "Random"):
        c = b[m]
        l1, t1 = c["layer1_macro_f1"], c["layer2_top1"]
        rows.append("%s & %.3f [%.3f, %.3f] & %.3f [%.3f, %.3f]" %
                    (m, l1["mean"], l1["lo"], l1["hi"], t1["mean"], t1["lo"], t1["hi"]))
    us = list(sh_if.values())
    n = len(us)
    rng = np.random.default_rng(2026)
    b1, b2 = [], []
    for _ in range(2000):
        idx = rng.integers(0, n, n)
        b1.append(np.mean([us[i]["layer1_macro_f1"] for i in idx]))
        b2.append(np.mean([us[i]["layer2_top1"] for i in idx]))
    rows.append("SHAP & %.3f [%.3f, %.3f] & %.3f [%.3f, %.3f]" %
                (np.mean(b1), np.percentile(b1, 2.5), np.percentile(b1, 97.5),
                 np.mean(b2), np.percentile(b2, 2.5), np.percentile(b2, 97.5)))
    L += [BS + "begin{table}[t]", BS + "centering",
          BS + "caption{Bootstrap 95" + BS + "% CIs (resampling the 23 mixed units, "
          + BS + "emph{B}=2000). (a) Unit-level means per method (SHAP CI from the same "
          "scheme, seed 2026); (b) paired differences of variable-type top-1 within the "
          "counterfactual family and versus the reconstruction reader (positive = first "
          "method better); (c) window-level resampling within the AT/SWaT unit, confirming "
          "the reversal.}",
          BS + "label{tab:S3}",
          BS + "small", BS + "textbf{(a) Unit-level}",
          BS + "par " + BS + "vspace{2pt}"]
    L += tab(["Method", "L1 CI", "top1 CI"], rows)
    # paired differences from per-unit values
    mr = load("main_results.json")
    mixu = sorted(u for u in mr if "_mix_" in u)
    pairs = [("RC-CA", "GlobalCF"), ("RC-CA", "CondAttr"), ("RC-CA", "RegimeGlobal"),
             ("GlobalCF", "CondAttr"), ("GlobalCF", "RegimeGlobal"),
             ("CondAttr", "RegimeGlobal"), ("AERec", "GlobalCF")]
    rng2 = np.random.default_rng(2026)
    rows2 = []
    for ma, mb in pairs:
        da = np.array([mr[u][ma]["layer2_top1"] for u in mixu])
        db = np.array([mr[u][mb]["layer2_top1"] for u in mixu])
        dd = da - db
        bs = [np.mean(dd[rng2.integers(0, len(dd), len(dd))]) for _ in range(2000)]
        rows2.append("%s $-$ %s & %+.3f & [%+.3f, %+.3f] & %s" %
                     (ma, mb, np.mean(dd), np.percentile(bs, 2.5),
                      np.percentile(bs, 97.5),
                      "yes" if (np.percentile(bs, 2.5) <= 0 <= np.percentile(bs, 97.5))
                      else "no"))
    L += [BS + "par " + BS + "vspace{4pt}" + BS + "textbf{(b) Paired top-1 differences "
          "(CI covers 0?)}", BS + "par " + BS + "vspace{2pt}"]
    L += tab(["Pair", "mean diff", "CI", "covers 0"], rows2)
    w = load("window_bootstrap.json")["AT_SWaT_var"]
    rows3 = ["%s & %.3f [%.3f, %.3f]" % (m, w[m]["top1"], w[m]["lo"], w[m]["hi"])
             for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "zDev", "Random")]
    L += [BS + "par " + BS + "vspace{4pt}" + BS + "textbf{(c) Window-level, AT/SWaT "
          "(207 windows)}", BS + "par " + BS + "vspace{2pt}"]
    L += tab(["Method", "top1 CI"], rows3)
    L += [BS + "end{table}"]

    # ---- S4 ablations ----
    a = load("ablation.json")
    for cat in ("K_gmm", "K_nn", "seed"):
        agg = {}
        for u, rec in a[cat].items():
            for k, v in rec.items():
                agg.setdefault(str(k), []).append(v)
        rows = []
        for k, vals in sorted(agg.items(), key=lambda x: float(x[0])):
            l1 = np.mean([v["layer1_macro_f1"] for v in vals])
            t1 = np.mean([v["layer2_top1"] for v in vals if v.get("layer2_top1") is not None])
            rows.append("%s & %.3f / %.3f" % (k, l1, t1))
        L += block("S4" + cat, "RC-CA ablation over " + esc(cat) +
                   " (mean L1 / top-1 over the 23 mixed units).",
                   tab([esc(cat), "L1/top1"], rows))

    # ---- S5 margin stratification ----
    mg = load("margin_analysis.json")
    agg = {}
    for u, rec in mg.items():
        for meth in ("RC-CA", "GlobalCF", "CondAttr", "AERec"):
            if meth in rec:
                if rec[meth].get("low", {}).get("n", 0) >= 5:
                    agg.setdefault(meth, [[], []])[0].append(rec[meth]["low"]["top1"])
                if rec[meth].get("high", {}).get("n", 0) >= 5:
                    agg.setdefault(meth, [[], []])[1].append(rec[meth]["high"]["top1"])
    rows = ["%s & %.3f & %.3f" % (m, np.mean(lo), np.mean(hi)) for m, (lo, hi) in agg.items()]
    L += block("S5", "Margin stratification (weak/strong at the 20" + BS + "% cut): "
               "mean variable-type top-1 over the units with at least 5 instances "
               "per stratum.", tab(["Method", "weak", "strong"], rows))

    # ---- S6 mode-level repair ----
    rp = load("repair_guided2.json")
    rows = []
    for x in rp:
        f = x["far"]
        rows.append("%s-r%d & %.1f & %.1f & %.1f & %.1f & %+.1f" %
                    (x["dataset"], x["regime"], f["base"] * 100, f["targeted"] * 100,
                     f["guided"] * 100, f["random"] * 100, x["gap_targeted_pp"]))
    L += block("S6", "Mode-level repair (FAR" + BS + "% over all normal windows of the "
               "held-out mode, fixed base threshold): base FAR, mode-directed (dir), "
               "guided, random supplementation, and the directed-minus-random gap (pp).",
               tab(["Unit", "base", "dir", "guided", "random", "gap pp"], rows))

    # ---- S7 variable repair ----
    g = load("repair_guided.json")["variable"]
    rows = ["%s & %.0f & %.0f & %.0f" % (esc(u), v["guided"] * 100, v["gt"] * 100,
                                         v["random"] * 100) for u, v in sorted(g.items())]
    N = sum(v["n"] for v in g.values())
    wi = lambda k: sum(v[k] * v["n"] for v in g.values()) / N
    rows.append(BS + "textit{instance-weighted mean} & %.0f & %.0f & %.0f" %
                (wi("guided") * 100, wi("gt") * 100, wi("random") * 100))
    rows.append(BS + "textit{unit mean} & %.0f & %.0f & %.0f" %
                tuple(np.mean([v[k] for v in g.values()]) * 100
                      for k in ("guided", "gt", "random")))
    L += block("S7", "Variable-level repair: share of variable-type alarms resolved by "
               "guided (RC-CA top-1) channel correction, ground-truth-channel "
               "correction, and random-channel correction, per unit (percent).",
               tab(["Unit", "guided", "groundtruth", "random"], rows))

    # ---- S8 assumption audit ----
    pr = load("proposition_checks.json")
    rows = ["%s & %.2f & %.2f" % (esc(k), pr["A1"][k]["abs_shift_over_std"],
                                  pr["A4"][k]["monotone_frac"]) for k in pr["A1"]]
    L += block("S8a", "Assumption audit: A1 median score shift (score standard "
               "deviations) under within-window channel permutation; A4 monotonicity "
               "fraction under out-of-distribution offsets.",
               tab(["Det-data", "A1", "A4"], rows))
    rows2 = ["%s-r%d & %.2f & %+.3f & %.0f" %
             (d, x["regime"], x["kl_mean_ch"], x["delta_reg_mean"],
              x["delta_reg_pos_frac"] * 100) for d, xs in pr["boundary"].items() for x in xs]
    L += block("S8b", "KL boundary: mode--global KL distance versus the mode-evidence "
               "gap $" + BS + "Delta$ (pos = share of mode-level test instances with "
               + "$" + BS + "Delta>0$, percent).",
               tab(["Unit", "KL", "Delta", "pos"], rows2))

    # ---- S9 masked retrieval ----
    cm = load("condattr_masked.json")
    rows = ["%s & %.3f/%.3f & %.3f/%.3f" %
            (esc(u), v["masked"]["L1"], v["masked"]["top1"], v["full"]["L1"], v["full"]["top1"])
            for u, v in cm.items()]
    L += block("S9", "CondAttr masked-context retrieval (L1/top-1) versus the "
               "full-window embedding compromise.", tab(["Unit", "masked", "full"], rows))

    # ---- S10 KL vs beta ----
    kl = load("kl_strength_curve.json")
    rows = []
    for combo, rr in kl.items():
        vals = [rr.get(str(x), {}).get("kl") for x in (0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4)]
        rows.append(esc(combo) + " & " + " & ".join("--" if v is None else "%.2f" % v for v in vals))
    L += block("S10", "Histogram KL between injected-FA and natural-FA score "
               "distributions at drift rate $" + BS + "beta$.",
               tab(["Combo", "0.01", "0.02", "0.05", "0.1", "0.2", "0.3", "0.4"], rows))

    # ---- S11 natural cases ----
    rows = []
    for tag, fname in (("iforest SWaT", "natural_cases.json"),
                       ("iforest SMD", "natural_cases_iforest_SMD.json"),
                       ("iforest MetroPT3", "natural_cases_iforest_MetroPT3.json"),
                       ("cmhmil SMD", "natural_cases_cmhmil_SMD.json")):
        nc = load(fname)
        if nc:
            nr = sum(x["verdict"] == "regime-like" for x in nc)
            rows.append("%s & %d/%d" % (esc(tag), nr, len(nc)))
    L += block("S11a", "Natural false alarms (top-20 events by peak score): "
               "mode-like verdicts per detector--data-set combination.",
               tab(["Combo", "mode-like"], rows))

    nv = load("natural_validation.json")
    ne = load("natural_ext.json")
    rows = []
    vf = dict(nv["verdict_frac"])
    vf.update({("cmhmil_" + k): {m: d["mode_frac"] for m, d in v.items()}
               for k, v in ne.items()})
    methods = ("RC-CA", "GlobalCF", "CondAttr", "AERec", "zDev")
    for combo, rec in vf.items():
        rows.append(esc(combo) + " & " + " & ".join(
            "--" if m not in rec else "%.0f" % (rec[m] * 100) for m in methods))
    L += block("S11b", "400-alarm transfer probe: mode-level verdict fraction (percent) "
               "per method and detector--data-set combination, using injected-validation "
               "$" + BS + "gamma$ thresholds on randomly sampled natural alarms.",
               tab(["Combo"] + list(methods), rows))
    rows2 = ["%s & %.0f & %.0f" % (esc(k), v["mean_pairwise"] * 100, v["min"] * 100)
             for k, v in nv["agreement"].items()]
    L += block("S11c", "400-alarm transfer probe: cross-method agreement on the binary "
               "type verdict (mean over method pairs, and minimum pair; percent).",
               tab(["Combo", "mean", "min"], rows2))
    mm = load("mmd_permutation.json")
    rows3 = ["%s & %.2f & %.3f & %d & %d" % (k, v["mmd2"], v["perm_p"], v["n_nat"], v["n_inj"])
             for k, v in mm.items()]
    L += block("S11d", "Confidence-distribution shift between natural and injected "
               "alarms: RBF-kernel MMD-squared (median-heuristic bandwidth, permutation "
               "over 200 shuffles; " + "$p<0.001$" + " everywhere).",
               tab(["Data", "MMD2", "p", "n nat", "n inj"], rows3))

    # ---- S12 FAR1 ----
    f1 = load("main_results_far1.json")
    mix1 = [u for u in f1 if "_mix_" in u]
    rows = []
    for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger", "zDev", "Random"):
        if m not in f1[mix1[0]]:
            continue
        l1s = [f1[u][m]["layer1_macro_f1"] for u in mix1 if "error" not in f1[u][m]]
        t1s = [f1[u][m]["layer2_top1"] for u in mix1 if f1[u][m].get("layer2_top1") is not None]
        rows.append("%s & %.3f & %.3f" % (m, np.mean(l1s), np.mean(t1s)))
    L += block("S12", "FAR-1" + BS + "% robustness (11 qualifying units): mean L1 and "
               "top-1.", tab(["Method", "L1", "top1"], rows))

    # ---- S13 beta curve ----
    bc = load("attribution_beta_curve.json")
    rows = []
    for ds, rec in bc.items():
        cells = []
        for b_ in ("0.05", "0.1", "0.2", "0.4"):
            v = rec.get(b_, {})
            cells.append("--" if not v.get("n") else "%.2f" % v.get("AERec", float("nan")))
        rows.append("%s & %s & %d" % (esc(ds), " & ".join(cells), rec.get("0.2", {}).get("n", 0)))
    L += block("S13", "Variable-type top-1 (AERec) versus drift rate $" + BS + "beta$.",
               tab(["Combo", "0.05", "0.1", "0.2", "0.4", "n02"], rows))

    # ---- S14 margin cuts (3 units -> S14a/b/c) ----
    ms = load("margin_sensitivity.json")
    for idx, u in enumerate(list(ms)[:3]):
        rows = []
        for cut in ("0.1", "0.2", "0.5"):
            e = ms[u][cut].get("AERec", (None, None))
            rows.append("%s & %s / %s" % (cut, "--" if e[0] is None else "%.2f" % e[0],
                                          "--" if e[1] is None else "%.2f" % e[1]))
        suffix = chr(97 + idx)  # a, b, c
        L += block("S14" + suffix, "Margin-cut sensitivity (AERec weak/strong top-1) for " +
                   esc(u) + ".", tab(["cut", "weak", "strong"], rows))

    # ---- S15 guided mechanism v2 ----
    gm = load("guided_mechanism_v2.json")
    rows = ["%s & %d & %.2f & %.2f & %.2f & %.2f & %.2f & %.2f & %.2f" %
            (esc(x["unit"]), x["n"], x["agree_rate"], x["clear_guided_agree"],
             x["clear_guided_div"], x["clear_gt_div"], x["both_clear_div"],
             x["div_weak"], x["div_strong"]) for x in gm["rows"]]
    rr = gm["rows"]
    N = sum(x["n"] for x in rr)
    aw = lambda k: sum(x[k] * x["n"] for x in rr) / N
    rows.append(BS + "textit{instance-weighted} & %.2f & %.2f & %.2f & %.2f & %.2f & %.2f & %.2f & %.2f" %
                (aw("n"), aw("agree_rate"), aw("clear_guided_agree"), aw("clear_guided_div"),
                 aw("clear_gt_div"), aw("both_clear_div"), aw("div_weak"), aw("div_strong")))
    L += block("S15", "Guided-correction mechanism decomposition (v2): agreement rate "
               "between guided and injected channels; clearance of the alarm conditional "
               "on correcting the guided / injected channel among divergent instances; "
               "both-clear among divergent; divergence share among weak/strong-margin "
               "instances.", tab(["Unit", "n", "agree", "cGA", "cGdiv", "cGTdiv",
                                  "bothDiv", "divW", "divS"], rows))

    # ---- S16 repair seed robustness ----
    rse = load("repair_seeds.json")
    rows = ["%s & %+.1f & %+.1f & %+.1f" %
            (esc(x["unit"]), x["dir_minus_rnd_pp"][0], x["dir_minus_rnd_pp"][1],
             x["dir_minus_rnd_pp"][2]) for x in rse]
    L += block("S16", "Mode-level repair gap (directed minus random, pp) over three "
               "retraining/sampling seeds on the nine units with sufficient mode volume.",
               tab(["Unit", "seed0", "seed1", "seed2"], rows))

    # ---- S17 construction seeds ----
    ss = load("seed_stability_3seed.json")
    rows = []
    for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger", "zDev", "Random"):
        pca = ss.get("pca_top1_" + m)
        oc = ss.get("ocsvm_top1_" + m)
        if pca:
            rows.append("PCA " + m + " & %.3f & %.3f & %.3f & %.3f" % tuple(pca))
        if oc:
            rows.append("OCSVM " + m + " & %.3f & %.3f & %.3f & %.3f" % tuple(oc))
    rows.append(BS + "midrule PCA best & " + " & ".join(ss.get("pca_top1_best", [])) +
                " & " + BS + "multicolumn{1}{l}{}")
    rows.append("OCSVM best & " + " & ".join(ss.get("ocsvm_top1_best", [])) +
                " & " + BS + "multicolumn{1}{l}{}")
    L += block("S17", "Construction-seed stability: pooled top-1 per method under three "
               "end-to-end construction seeds (final column = max--min spread); best "
               "method per seed listed beneath.",
               tab(["Det-method", "seed0", "seed1", "seed2", "spread"], rows))

    # ---- S18 DAAS-v2 cost-aware Pareto + conformal ----
    dv = load("daas_v2.json")
    if dv:
        rows = []
        seen = set()
        for c in dv["curve"]:
            key = (round(c["top1"], 3), round(c["cost_ms"], 2))
            if key in seen:
                continue
            seen.add(key)
            rows.append("%g & %.3f & %.2f" % (c["lam"], c["top1"], c["cost_ms"]))
        for m in ("AERec", "GlobalCF", "CondAttr", "RC-CA"):
            f = dv["fixed"][m]
            rows.append(BS + "textit{fixed " + m + "} & %.3f & %.2f" %
                        (f["top1"], f["cost_ms"]))
        L += block("S18", "DAAS-v2 cost-aware selection: leave-one-out mean variable-type "
                   "top-1 versus per-window attribution cost (ms) along the $" + BS +
                   "lambda$ sweep (upper block; the frontier point is $" + BS +
                   "lambda{=}0.0075$, 0.827 at 1.8 ms), with fixed-method reference rows "
                   "(lower block, italic). Regret = per-pair best minus recommended "
                   "top-1: mean 0.048, median 0.010; leave-one-out conformal bounds "
                   "cover " + "84/79/68" + BS + "% of held-out pairs at nominal "
                   "90/80/70" + BS + "% (bounds 0.111/0.076/0.053; n=19 pairs, "
                   "empirical small-sample).",
                   tab(["$" + BS + "lambda$", "top1", "cost ms"], rows))

    # ---- S19 repair v3: stronger baselines + multi-round ----
    v3 = load("repair_v3.json")
    PC = BS + "%"
    if v3:
        strat = ("guided_rc", "guided_ae", "unc", "alarm_rand", "target_rand", "other_rand")
        rows = []
        for x in v3:
            cells = ["%s-r%d" % (x["dataset"], x["regime"]),
                     "%.1f" % (100 * x["far"][strat[0]][0])]
            for s in strat:
                cells.append("%.1f" % (100 * x["far"][s][3]))
            rows.append(" & ".join(cells))
        R3 = len(v3)
        gap = lambda s: [100 * (x["far"]["alarm_rand"][3] - x["far"][s][3]) for x in v3]
        own = lambda s: [100 * (x["far"][s][0] - x["far"][s][3]) for x in v3]
        pr = lambda s: [x["prec"][s] for x in v3 if x["prec"][s] is not None]
        rows.append(BS + "midrule " + BS + "textit{own red.} & -- & " + " & ".join(
            "%.1f" % np.mean(own(s)) for s in strat))
        rows.append(BS + "textit{gap vs a-rand} & -- & " + " & ".join(
            "--" if s == "alarm_rand" else "%+.1f" % np.median(gap(s)) for s in strat))
        rows.append(BS + "textit{wins} & -- & " + " & ".join(
            "--" if s == "alarm_rand" else "%d/%d" % (sum(g > 0 for g in gap(s)), R3)
            for s in strat))
        rows.append(BS + "textit{regime purity} & -- & %.2f & %.2f & -- & %.2f & -- & --" % (
            np.mean(pr("guided_rc")), np.mean(pr("guided_ae")),
            np.mean([x["base_rate_regime"] for x in v3])))
        L += block("S19", "Mode-level repair under stronger selection baselines and "
                   "three incremental budget rounds (FAR in " + PC + " at the final "
                   "round; base = round 0). guided\\_rc/guided\\_ae: alarm windows "
                   "selected by the RC-CA / AERec regime verdict; unc: adaptive "
                   "uncertainty sampling ($|s-" + BS + "tau|$ nearest the "
                   "threshold); alarm\\_rand: random alarm windows; target\\_rand: "
                   "mode-directed representative windows; other\\_rand: windows of "
                   "other modes. No alarm-window selection strategy separates from "
                   "random alarm selection (median gaps within $" + BS +
                   "pm 1$ pp), although the verdict filters do raise the "
                   "regime purity of the added set (0.72$" + BS + "to$0.88/0.86). "
                   "Mode-directed repair improves monotonically with budget (unit "
                   "trajectories in the text), confirming coverage, not alarm "
                   "selection, as the operative factor.",
                   tab(["Unit", "base", "RCgui", "AEgui", "US", "alrmR",
                        "modeR", "othrR"], rows))

    # ---- S20 natural-alarm human annotation (T0-2b) ----
    t2 = load("t02b_results.json")
    if t2:
        METHODS5 = ("RC-CA", "GlobalCF", "CondAttr", "AERec", "zDev")
        rows = []
        for m in METHODS5:
            by_ds = t2["acc_by_ds"]
            cells = ["%.2f" % t2["acc_inj"][m]]
            for ds in ("SWaT", "SMD", "MetroPT3"):
                v = list(by_ds[ds].values())[0].get(m)
                cells.append("%.2f" % v if v is not None else "--")
            for k in (10, 25, 50, 100):
                c = t2["curve"].get(f"{m}_pooled_k{k}")
                cells.append("--" if c is None else "%.2f" % c["mean"])
            rows.append(" & ".join([m] + cells))
        L += block("S20", "Natural-alarm human-reference check. Five independent "
                   "annotators labelled 120 natural alarm windows (stratified sample "
                   "of the 400-window probe; v = variable-like, m = mode-like, "
                   "u = unsure). Majority vote over v/m verdicts (u abstains; 16 "
                   "windows tied and were excluded) yields 104 reference labels; "
                   "Fleiss $" + BS + "kappa$ = 0.93 on the subset where all five "
                   "committed to v/m. Upper block: agreement of each method's "
                   "injected-validation $" + BS + "gamma$ with the human majority "
                   "(overall and per data set). Lower columns: agreement after "
                   "re-fitting $" + BS + "gamma$ on k human-labelled natural alarms "
                   "(mean over 20 draws). A few dozen labels lift every method above "
                   "its injected-calibration agreement.",
                   tab(["Method", "inj-$" + BS + "gamma$", "SWaT", "SMD", "Met3",
                        "k10", "k25", "k50", "k100"], rows))

    # ---- S21 Fault-type breakdown ----
    ftb = load("fault_type_breakdown.json")
    if ftb:
        KIND_COLS = ["linear drift", "stuck-at", "variance infl.", "joint drift", "regime"]
        rows = []
        for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "zDev"):
            cells = [m]
            for kn in KIND_COLS:
                v = ftb["summary"].get(m + "|" + kn)
                cells.append("--" if v is None else "%.2f" % v["mean"])
            rows.append(" & ".join(cells))
        L += block("S21", "Per-fault-type variable-level top-1 accuracy (instance-weighted "
                   "mean over six representative isolation-forest mixed units, two per "
                   "data set) and mode-level typing accuracy. The counterfactual family "
                   "localizes linear drift best; AERec is strongest on stuck-at and "
                   "variance inflation; joint two-channel drift is hardest for all "
                   "methods.",
                   tab(["Method"] + [k.replace(" ", "~") for k in KIND_COLS], rows))

    # ---- S22 Runtime / complexity comparison ----
    enh = load("enhancement_data.json")
    if enh and "runtime_table" in enh:
        rows = []
        for r in enh["runtime_table"]:
            rows.append("%s & %s & %.2f & %.2f--%.2f" %
                        (r["method"].replace("_", BS + "_"),
                         r["complexity"].replace("$", "$").replace("^", "^"),
                         r["mean_ms"], r["range_ms"][0], r["range_ms"][1]))
        L += block("S22", "Attribution cost per window: theoretical complexity and measured "
                   "runtime (mean and range across SWaT/SMD/MetroPT3; isolation-forest "
                   "detector). AERec's single forward pass is two orders of magnitude "
                   "cheaper than any replacement-based method; the counterfactual "
                   "premium buys accuracy on smooth detectors but not on tree ensembles "
                   "(matching conclusion of the main text).",
                   tab(["Method", "Complexity", "mean ms", "range ms"], rows))

    # ---- S23 Statistical power ----
    if enh and "power_units" in enh:
        pu = enh["power_units"]
        pp = enh.get("power_pairs", {})
        rows = [
            "Paired method contrast (Wilcoxon) & " + str(pu["n"]) + " units & $|d_z| "
            + BS + "geq " + "%.2f$" % pu["min_detectable_paired_effect_dz"]
            + " & detects the AERec$-$GlobalCF gap ($d_z" + BS + "approx 1.1$) with margin",
            "DAAS pair recovery & " + str(pp.get("n", 19)) + " pairs & 95" + BS
            + "% CI width $" + BS + "approx 0.47$ & 42" + BS + "% vs 26" + BS
            + "% separated; smaller gaps require $n>50$",
        ]
        L += block("S23", "Statistical power at the study's sample sizes. "
                   "The paired design over units has adequate power for the large "
                   "counterfactual-vs-reconstruction gaps reported; the DAAS selection "
                   "rule's advantage over the best fixed method ($42" + BS + "%$ vs "
                   "$26" + BS + "%$) is detectable but with a wide confidence interval "
                   "at $n=19$ pairs.",
                   tab(["Analysis", "n", "Threshold", "Interpretation"], rows))

    # ---- S24 Practitioner's deployment guide ----
    if enh and "deployment_guide" in enh:
        rows = []
        for g in enh["deployment_guide"]:
            rows.append("%s & %s & %s & %s" %
                        (g["detector"].replace("_", BS + "_"),
                         g["method"].replace("_", BS + "_"),
                         g["top1"], g["cost"]))
        L += block("S24", "Practitioner's deployment guide: recommended attribution "
                   "method by detector family, with expected variable-type top-1 and "
                   "per-window attribution cost (from Table~S22). This table "
                   "operationalizes the method--detector matching findings: the "
                   "cheapest method that wins on the deployed detector family should "
                   "be chosen.",
                   tab(["Detector family", "Method", "top-1", "ms/window"], rows))

    open(OUT, "w", encoding="utf-8").write("\n\n".join(L) + "\n")
    print("written", OUT, "(%d lines)" % len(L))


if __name__ == "__main__":
    main()
