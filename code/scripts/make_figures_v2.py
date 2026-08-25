"""R10: Nature (NPG) 配色重绘全部图 + 新增 3 张图.
NPG palette: #E64B35 #4DBBD5 #00A087 #3C5488 #F39B7F #8491B4 #91D1C2 #DC0000 #7E6148
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402

PAPER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "paper")

NATURE = {"pale_blue": "#DDE6F3", "periwinkle": "#7FA4C8", "lilac": "#B59BC8",
          "orchid": "#D08AB6", "mint": "#8FB79B", "violet": "#6A5A8F",
          "indigo": "#3F345B"}
MC = {"GlobalCF": NATURE["violet"], "RC-CA": NATURE["indigo"],
      "CondAttr": NATURE["mint"], "AERec": NATURE["orchid"],
      "Granger": NATURE["periwinkle"], "zDev": NATURE["lilac"],
      "Random": NATURE["pale_blue"], "RegimeGlobal": NATURE["periwinkle"]}
BG = NATURE["pale_blue"]
plt.rcParams.update({"font.size": 11, "figure.dpi": 200, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.axisbelow": True,
                     "axes.spines.top": False, "axes.spines.right": False})


def load(n):
    p = cpath(n)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


# ===== 图1: 协议流程示意 =====
def fig_protocol():
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis("off")
    boxes = [
        (0.3, 3.0, "Normal\nstream", NATURE["periwinkle"]),
        (2.5, 3.0, "Hold out\nmode $k$", NATURE["mint"]),
        (4.7, 3.0, "Retrain\n+ $\\tau_k$", NATURE["violet"]),
        (7.1, 3.0, "Mixed FA\ninstances", NATURE["orchid"]),
        (2.3, 0.8, "Inject faults\n(drift / stuck / var)", NATURE["lilac"]),
        (7.1, 0.8, "Two-layer\nevaluation", NATURE["indigo"]),
    ]
    for x, y, txt, c in boxes:
        bb = FancyBboxPatch((x, y), 2.2, 1.4, boxstyle="round,pad=0.15",
                            fc=c, ec="black", lw=0.8, alpha=0.85)
        ax.add_patch(bb)
        ax.text(x + 1.1, y + 0.7, txt, ha="center", va="center", fontsize=10,
                fontweight="bold", color="white")
    arrows = [(2.3, 3.7, 2.5, 3.7), (4.5, 3.7, 4.7, 3.7), (6.7, 3.7, 7.1, 3.7),
              (3.4, 2.2, 3.4, 3.0), (4.5, 1.5, 7.0, 1.5), (8.2, 2.2, 8.2, 3.0),
              (2.3, 1.5, 0.3, 1.5)]
    for x1, y1, x2, y2 in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color="#555"))
    ax.text(0.3, 1.9, "Filter: $s_b < \\tau < s_a$", fontsize=10,
            style="italic", color=NATURE["indigo"])
    fig.tight_layout()
    fig.savefig(os.path.join(PAPER, "fig_protocol.pdf"), bbox_inches="tight")
    plt.close(fig)


# ===== 图2: 镜像发现 (Nature 配色 + CI 误差条) =====
def fig_mirror():
    r = load("main_results.json")
    if not r:
        return
    wb = load("window_bootstrap.json") or {}
    scen = [("iforest\nSWaT", "iforest_SWaT_mix"), ("iforest\nMetroPT3", "iforest_MetroPT3_mix"),
            ("cmhmil\nSMD", None), ("AT\nSWaT", None), ("AT\nSMD", None)]
    data = {}
    for m in ("GlobalCF", "RC-CA", "CondAttr", "AERec"):
        vals = [np.mean([r[u][m]["layer2_top1"] for u in r if "_mix_" in u and "SWaT" in u])]
        vals.append(np.mean([r[u][m]["layer2_top1"] for u in r if "_mix_" in u and "MetroPT3" in u]))
        vals.append(r["cmhmil_SMD_var"][m]["layer2_top1"] if r.get("cmhmil_SMD_var", {}).get(m) else np.nan)
        vals.append(wb.get("AT_SWaT_var", {}).get(m, {}).get("top1", np.nan))
        vals.append(wb.get("AT_SMD_var", {}).get(m, {}).get("top1", np.nan))
        errs = []
        for tag in ("cmhmil_SMD_var", "AT_SWaT_var", "AT_SMD_var"):
            w = wb.get(tag, {}).get(m)
            errs.append((w["top1"] - w["lo"], w["hi"] - w["top1"]) if w else (0, 0))
        data[m] = (vals, errs)
    x = np.arange(len(scen)); w = 0.19
    fig, ax = plt.subplots(figsize=(6.2, 2.8))
    for i, m in enumerate(("GlobalCF", "RC-CA", "CondAttr", "AERec")):
        vals, errs = data[m]
        lo = [0] * 2 + [e[0] for e in errs]
        hi = [0] * 2 + [e[1] for e in errs]
        ax.bar(x + (i - 1.5) * w, vals, w, label=m, color=MC[m], edgecolor="black",
               linewidth=0.4, yerr=[lo, hi], capsize=2, error_kw={"lw": 0.8})
        for xi, v in zip(x + (i - 1.5) * w, vals):
            if not np.isnan(v):
                pass  # 数值在 Table 4 / S2, 图内不标
    ax.set_xticks(x); ax.set_xticklabels([s[0] for s in scen])
    ax.set_ylabel("variable-type top-1"); ax.set_ylim(0, 1.18)
    ax.legend(ncol=4, fontsize=9.1, loc="upper left", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(PAPER, "fig_mirror.pdf"), bbox_inches="tight")
    plt.close(fig)


# ===== 图3: 逐单元热图 =====
def fig_heatmap():
    r = load("main_results.json")
    if not r:
        return
    mix = [u for u in r if "_mix_" in u]
    methods = ["RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger", "zDev", "Random"]
    mat = np.array([[r[u].get(m, {}).get("layer1_macro_f1", np.nan) for u in mix] for m in methods])
    fig, ax = plt.subplots(figsize=(6.2, 2.2))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("nature", [NATURE["pale_blue"], NATURE["periwinkle"], NATURE["violet"], NATURE["indigo"]])
    im = ax.imshow(mat, cmap=cmap, vmin=0.2, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(mix)))
    ax.set_xticklabels([u.replace("iforest_", "").replace("_mix_", "\n") for u in mix],
                       rotation=60, ha="right", fontsize=11)
    ax.set_yticks(range(len(methods))); ax.set_yticklabels(methods, fontsize=11)
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02); cb.set_label("L1 macro-F1", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(PAPER, "fig_heatmap.pdf"), bbox_inches="tight")
    plt.close(fig)


# ===== 图4: 修复 (Nature 配色) =====
def fig_repair():
    rp = load("repair_guided2.json")
    if not rp:
        return
    labs = [f"{x['dataset'][:3]}-{x['regime']}" for x in rp]
    base = [x["far"]["base"] * 100 for x in rp]
    dir_ = [x["far"]["targeted"] * 100 for x in rp]
    gui = [x["far"]["guided"] * 100 for x in rp]
    rnd = [x["far"]["random"] * 100 for x in rp]
    x = np.arange(len(labs)); w = 0.2
    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    for off, vals, lab, c in [(-1.5*w, base, "base", NATURE["pale_blue"]), (-0.5*w, dir_, "mode-directed", NATURE["violet"]),
                               (0.5*w, gui, "alarm-window", NATURE["lilac"]), (1.5*w, rnd, "random control", NATURE["orchid"])]:
        ax.bar(x + off, vals, w, label=lab, color=c, edgecolor="black", linewidth=0.4)
    ax.set_xticks(x); ax.set_xticklabels(labs, rotation=45, ha="right", fontsize=10.5)
    ax.set_ylabel("FAR on held-out mode (%)"); ax.legend(fontsize=9.1, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(PAPER, "fig_repair.pdf"), bbox_inches="tight")
    plt.close(fig)


# ===== 图5: beta 曲线 (Nature 配色) =====
def fig_beta():
    bc = load("attribution_beta_curve.json")
    if not bc:
        return
    fig, axes = plt.subplots(1, len(bc), figsize=(2.9 * len(bc), 2.5), squeeze=False)
    for ax, (ds, rec) in zip(axes[0], bc.items()):
        betas = sorted(float(b) for b in rec if rec[b].get("n", 0) > 0)
        for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger"):
            ys = [rec[str(b)].get(m) for b in betas]
            if all(y is not None for y in ys):
                ax.plot(betas, ys, "o-", label=m, color=MC.get(m), ms=4, lw=1.5)
        ax.set_xlabel("drift rate $\\beta$"); ax.set_ylim(-0.03, 1.05)
    axes[0][0].set_ylabel("top-1"); axes[0][0].legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(PAPER, "fig_beta.pdf"), bbox_inches="tight")
    plt.close(fig)


# ===== 图6: margin (Nature 配色) =====
def fig_margin():
    mg = load("margin_analysis.json")
    if not mg:
        return
    agg = {}
    for u, rec in mg.items():
        for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec"):
            if m in rec:
                if rec[m].get("low", {}).get("n", 0) >= 5:
                    agg.setdefault(m, [[], []])[0].append(rec[m]["low"]["top1"])
                if rec[m].get("high", {}).get("n", 0) >= 5:
                    agg.setdefault(m, [[], []])[1].append(rec[m]["high"]["top1"])
    x = np.arange(2); w = 0.19
    fig, ax = plt.subplots(figsize=(3.6, 2.5))
    for i, m in enumerate(("RC-CA", "GlobalCF", "CondAttr", "AERec")):
        v = [np.mean(agg[m][0]), np.mean(agg[m][1])]
        ax.bar(x + (i - 1.5) * w, v, w, label=m, color=MC[m], edgecolor="black", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(["weak alarm\n(margin$<20\\%$)", "strong alarm\n(margin$\\geq 20\\%$)"], fontsize=9.1)
    ax.set_ylabel("top-1"); ax.set_ylim(0, 0.95); ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(PAPER, "fig_margin.pdf"), bbox_inches="tight")
    plt.close(fig)


# ===== 图7: 自然 vs 注入分数分布 =====
def fig_scoredist():
    from common import load_raw, split_of, WINDOW
    import evaluation.two_layer as tl
    fig, axes = plt.subplots(1, 3, figsize=(6.2, 2.2), squeeze=False, sharey=False)
    rng = np.random.default_rng(0)
    for ax, ds in zip(axes[0], ("SWaT", "SMD", "MetroPT3")):
        d = np.load(cpath(f"fa_iforest_{ds}_far5.npz"))
        nat = d["fa_scores"]
        X, Y = load_raw(ds)
        a, b = split_of(len(X))
        mu, sigma = X[a:b].mean(0), X[a:b].std(0) + 1e-8
        tau = float(d["tau"])
        active = np.where(X[a:b].std(0) > 0.05)[0]
        b2 = split_of(len(X))[1]
        s = b2 + 500
        seg_ok = s + 200 < len(X)
        sc_nat = []
        from injection.inject import apply_variable_fault, eval_injected
        for trial in range(8):
            j = int(rng.choice(active))
            Xm, _ = apply_variable_fault(X, s, min(200, len(X)-s-1), [j], "drift", 0.2, mu, sigma)
            ev = eval_injected("iforest", ds, X, Xm, s, min(200, len(X)-s-1), tau)
            m = ev["scores_after"] > tau
            if m.sum() > 3:
                sc_nat.append(ev["scores_after"][m])
        inj = np.concatenate(sc_nat) if sc_nat else np.array([np.nan])
        bins = np.linspace(min(nat.min(), np.nanmin(inj)), max(nat.max(), np.nanmax(inj)), 35)
        ax.hist(nat, bins=bins, alpha=0.6, color=NATURE["violet"], label="natural FA", density=True, edgecolor="none")
        ax.hist(inj, bins=bins, alpha=0.6, color=NATURE["orchid"], label="injected FA", density=True, edgecolor="none")
        ax.set_title(ds, fontsize=10.4, fontweight="bold")
        ax.set_xlabel("anomaly score")
    axes[0][0].set_ylabel("density"); axes[0][0].legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(PAPER, "fig_scoredist.pdf"), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_protocol(); print("fig_protocol")
    fig_mirror(); print("fig_mirror")
    fig_heatmap(); print("fig_heatmap")
    fig_repair(); print("fig_repair")
    fig_beta(); print("fig_beta")
    fig_margin(); print("fig_margin")
    fig_scoredist(); print("fig_scoredist")
