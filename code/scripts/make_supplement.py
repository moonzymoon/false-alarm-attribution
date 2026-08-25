"""从 _cache JSON 生成补充材料 LaTeX 表 (paper/supplement_tables.tex). S1-S16."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "paper", "supplement_tables.tex")
BS = chr(92)
BT = BS + BS          # LaTeX 行终止符
PC = BS + "%"        # 运行时 \% (在 %-format 串内)


def load(name):
    p = cpath(name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def esc(s):
    return str(s).replace("_", BS + "_")


def tab(cols, rows):
    L = [BS + "begin{tabular}{" + "r" * len(cols) + "}",
         BS + "toprule " + " & ".join(cols) + " " + BT + " " + BS + "midrule"]
    L += [r + " " + BT for r in rows]
    L.append(BS + "bottomrule" + BS + "end{tabular}")
    return L


def main():
    L = []

    r = load("main_results.json")
    mix = [u for u in r if "_mix_" in u] if r else []
    if mix:
        rows = []
        for u in mix:
            cells = [esc(u), str(r[u]["RC-CA"]["n_test"])]
            for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec"):
                v = r[u][m]
                t1 = v.get("layer2_top1")
                cells.append("%.2f/%.2f" % (v["layer1_macro_f1"], t1) if t1 is not None
                             else "%.2f" % v["layer1_macro_f1"])
            rows.append(" & ".join(cells))
        L.append("% S1 per-unit L1/top1 (FAR 5)")
        L += tab(["Unit", "n", "RC-CA", "GlobalCF", "CondAttr", "AERec"], rows)

    if r:
        rows = []
        for u in [x for x in r if x.endswith("_var")]:
            cells = [esc(u), str(r[u]["RC-CA"]["n_test"])]
            for m in ("RC-CA", "CondAttr", "AERec", "Grad"):
                v = r[u].get(m) or {}
                t1, t3 = v.get("layer2_top1"), v.get("layer2_top3")
                cells.append("%.2f/%.2f" % (t1, t3) if t1 is not None else "--")
            rows.append(" & ".join(cells))
        L.append("% S2 variable-level units top1/top3")
        L += tab(["Unit", "n", "RC-CA", "CondAttr", "AERec", "Grad"], rows)

    b = load("bootstrap_ci.json")
    if b:
        rows = []
        for m, c in b["ci"].items():
            l1, t1 = c.get("layer1_macro_f1"), c.get("layer2_top1")
            if l1 and t1:
                rows.append("%s & %.3f [%.3f, %.3f] & %.3f [%.3f, %.3f]" %
                            (m, l1["mean"], l1["lo"], l1["hi"], t1["mean"], t1["lo"], t1["hi"]))
        L.append("% S3 bootstrap CI (unit level)")
        L += tab(["Method", "L1 CI", "top1 CI"], rows)

    a = load("ablation.json")
    if a:
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
            L.append("% S4 ablation " + cat)
            L += tab([esc(cat), "L1/top1"], rows)

    mg = load("margin_analysis.json")
    if mg:
        agg = {}
        for u, rec in mg.items():
            for meth in ("RC-CA", "GlobalCF", "CondAttr", "AERec"):
                if meth in rec:
                    if rec[meth].get("low", {}).get("n", 0) >= 5:
                        agg.setdefault(meth, [[], []])[0].append(rec[meth]["low"]["top1"])
                    if rec[meth].get("high", {}).get("n", 0) >= 5:
                        agg.setdefault(meth, [[], []])[1].append(rec[meth]["high"]["top1"])
        if agg:
            rows = ["%s & %.3f & %.3f" % (m, np.mean(lo), np.mean(hi)) for m, (lo, hi) in agg.items()]
            L.append("% S5 margin stratification")
            L += tab(["Method", "weak", "strong"], rows)

    rp = load("repair_guided2.json")
    if rp:
        rows = []
        for x in rp:
            f = x["far"]
            rows.append("%s-r%d & %.1f%s & %.1f%s & %.1f%s & %.1f%s & %+.1f" %
                        (x["dataset"], x["regime"], f["base"] * 100, PC,
                         f["targeted"] * 100, PC, f["guided"] * 100, PC,
                         f["random"] * 100, PC, x["gap_targeted_pp"]))
        L.append("% S6 repair v2 (FAR" + PC + ", all mode windows, fixed tau)")
        L += tab(["Unit", "base", "dir", "guided", "random", "gap pp"], rows)

    g = load("repair_guided.json")
    if g and g.get("variable"):
        rows = ["%s & %.0f%s & %.0f%s & %.0f%s" %
                (esc(u), v["guided"] * 100, PC, v["gt"] * 100, PC, v["random"] * 100, PC)
                for u, v in g["variable"].items()]
        L.append("% S7 variable repair resolution")
        L += tab(["Unit", "guided", "groundtruth", "random"], rows)

    pr = load("proposition_checks.json")
    if pr:
        rows = ["%s & %.2f & %.2f" % (esc(k), pr["A1"][k]["abs_shift_over_std"],
                                      pr["A4"][k]["monotone_frac"]) for k in pr["A1"]]
        L.append("% S8a assumption audit A1/A4")
        L += tab(["Det-data", "A1", "A4"], rows)
        rows2 = ["%s-r%d & %.2f & %+.3f & %.0f%s" %
                 (d, x["regime"], x["kl_mean_ch"], x["delta_reg_mean"],
                  x["delta_reg_pos_frac"] * 100, PC)
                 for d, xs in pr["boundary"].items() for x in xs]
        L.append("% S8b KL boundary")
        L += tab(["Unit", "KL", "Delta", "pos"], rows2)

    cm = load("condattr_masked.json")
    if cm:
        rows = ["%s & %.3f/%.3f & %.3f/%.3f" %
                (esc(u), v["masked"]["L1"], v["masked"]["top1"], v["full"]["L1"], v["full"]["top1"])
                for u, v in cm.items()]
        L.append("% S9 masked vs full retrieval")
        L += tab(["Unit", "masked", "full"], rows)

    kl = load("kl_strength_curve.json")
    if kl:
        rows = []
        for combo, rr in kl.items():
            vals = [rr.get(str(x), {}).get("kl") for x in (0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4)]
            rows.append(esc(combo) + " & " + " & ".join("--" if v is None else "%.2f" % v for v in vals))
        L.append("% S10 KL vs beta")
        L += tab(["Combo", "0.01", "0.02", "0.05", "0.1", "0.2", "0.3", "0.4"], rows)

    rows = []
    for tag, fname in (("iforest SWaT", "natural_cases.json"),
                       ("iforest SMD", "natural_cases_iforest_SMD.json"),
                       ("iforest MetroPT3", "natural_cases_iforest_MetroPT3.json"),
                       ("cmhmil SMD", "natural_cases_cmhmil_SMD.json")):
        nc = load(fname)
        if nc:
            nr = sum(x["verdict"] == "regime-like" for x in nc)
            rows.append("%s & %d/%d" % (esc(tag), nr, len(nc)))
    L.append("% S11 natural cases")
    L += tab(["Combo", "mode-like"], rows)

    f1 = load("main_results_far1.json")
    if f1:
        mix1 = [u for u in f1 if "_mix_" in u]
        rows = []
        for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger", "zDev", "Random"):
            if m not in f1[mix1[0]]:
                continue
            l1 = [f1[u][m]["layer1_macro_f1"] for u in mix1 if "error" not in f1[u][m]]
            t1 = [f1[u][m]["layer2_top1"] for u in mix1 if f1[u][m].get("layer2_top1") is not None]
            rows.append("%s & %.3f & %.3f" % (m, np.mean(l1), np.mean(t1)))
        L.append("% S12 FAR1 robustness")
        L += tab(["Method", "L1", "top1"], rows)

    bc = load("attribution_beta_curve.json")
    if bc:
        rows = []
        for ds, rec in bc.items():
            cells = []
            for b_ in ("0.05", "0.1", "0.2", "0.4"):
                v = rec.get(b_, {})
                cells.append("--" if not v.get("n") else "%.2f" % v.get("AERec", float("nan")))
            rows.append("%s & %s & %d" % (esc(ds), " & ".join(cells), rec.get("0.2", {}).get("n", 0)))
        L.append("% S13 beta curve (AERec top1)")
        L += tab(["Combo", "0.05", "0.1", "0.2", "0.4", "n02"], rows)

    ms = load("margin_sensitivity.json")
    if ms:
        for u in list(ms)[:3]:
            rows = []
            for cut in ("0.1", "0.2", "0.5"):
                e = ms[u][cut].get("AERec", (None, None))
                rows.append("%s & %s / %s" % (cut,
                            "--" if e[0] is None else "%.2f" % e[0],
                            "--" if e[1] is None else "%.2f" % e[1]))
            L.append("% S14 margin cuts " + esc(u))
            L += tab(["cut", "weak", "strong"], rows)

    gm = load("guided_mechanism.json")
    if gm:
        rows = ["%s & %.2f & %.2f & %.2f & %.2f" %
                (esc(x["unit"]), x["agree_rate"], x["diverge_rate"],
                 x["guided_only"], x["gt_only"]) for x in gm["rows"]]
        m = gm["mean"]
        rows.append(BS + "midrule mean & %.2f & %.2f & %.2f & %.2f" %
                    (m["agree_rate"], m["diverge_rate"], m["guided_only"], m["gt_only"]))
        L.append("% S15 guided mechanism decomposition")
        L += tab(["Unit", "agree", "diverge", "guidedonly", "gtonly"], rows)

    rse = load("repair_seeds.json")
    if rse:
        rows = ["%s & %+.1f & %+.1f & %+.1f" %
                (esc(x["unit"]), x["dir_minus_rnd_pp"][0], x["dir_minus_rnd_pp"][1],
                 x["dir_minus_rnd_pp"][2]) for x in rse]
        L.append("% S16 repair gap seed robustness (pp)")
        L += tab(["Unit", "seed0", "seed1", "seed2"], rows)

    L.append(BS + "paragraph{Notes} "
             "S8b: pos is the share of mode-level test instances with "
             "$" + BS + "Delta>0$. "
             "S10: histogram KL between injected-FA and natural-FA score "
             "distributions at drift rate $" + BS + "beta$. "
             "Window-level and hierarchical bootstrap CIs are archived in the result files.")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n\n".join(L) + "\n")
    print("written", OUT, "(%d lines)" % len(L))


if __name__ == "__main__":
    main()
