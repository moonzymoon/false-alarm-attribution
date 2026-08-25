# -*- coding: utf-8 -*-
"""E2 v2: repair-decomposition with FULL conditional clearance rates (resolves the
arithmetic inconsistency flagged by external review). Also counts gt_kind
fractions (joint share) for the uniform-guess expectation check."""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa
from rcca.rcca import _RegimeBank, rcca_attribute  # noqa
import evaluation.gt_pool as gp

def run():
    rows = []
    kind_counter = {}          # ds -> {kind: count}
    for ds in ("SWaT", "SMD", "MetroPT3", "PSM", "SMAP"):
        units = gp._mixed_unit(ds)
        # count gt_kind shares (all instances incl. regime)
        kc = {}
        for u in units:
            for k in u.gt_kind:
                kc[k] = kc.get(k, 0) + 1
        kind_counter[ds] = kc
        if ds not in ("SWaT", "SMD", "MetroPT3"):
            continue
        for u in units:
            bank = _RegimeBank(u.pool_windows(), seed=0)
            W = u.windows()
            y = (u.gt_type == "variable").astype(int)
            test = ~u.val_mask & (y == 1)
            if test.sum() < 20:
                continue
            attr = rcca_attribute(u, W, bank)
            tmpl, _ = bank.knn_template(W, K=5)
            s0 = attr["s_orig"]
            margin = (s0 - u.tau) / (abs(u.tau) + 1e-12)
            top1 = np.argsort(-attr["phi"], 1)[:, 0]
            n_agree = n_div = 0
            cg_agree = 0                      # guided(=gt) clears among agree
            cg_div = ct_div = both_div = 0    # among divergent
            weak_div = weak_tot = strong_div = strong_tot = 0
            for i in np.where(test)[0]:
                gt_j = u.gt_vars[i][0]
                gj = top1[i]
                w2 = W[i:i + 1].copy(); w2[0, :, gj] = tmpl[i, :, gj]
                res_g = float(u.score(w2)[0] <= u.tau)
                w3 = W[i:i + 1].copy(); w3[0, :, gt_j] = tmpl[i, :, gj]
                res_t = float(u.score(w3)[0] <= u.tau)
                wk = margin[i] < 0.2
                weak_tot += wk; strong_tot += (1 - wk)
                if gj == gt_j:
                    n_agree += 1
                    cg_agree += res_g
                else:
                    n_div += 1
                    cg_div += res_g; ct_div += res_t; both_div += res_g * res_t
                    weak_div += wk; strong_div += (1 - wk)
            n = int(test.sum())
            rows.append({
                "unit": u.name, "n": n,
                "agree_rate": n_agree / n,
                "clear_guided_agree": cg_agree / max(n_agree, 1),
                "clear_guided_div": cg_div / max(n_div, 1),
                "clear_gt_div": ct_div / max(n_div, 1),
                "both_clear_div": both_div / max(n_div, 1),
                "div_weak": weak_div / max(weak_tot, 1),
                "div_strong": strong_div / max(strong_tot, 1),
            })
            print(f"{u.name}: n={n} agree={n_agree/n:.0%} "
                  f"clr_g|agree={cg_agree/max(n_agree,1):.0%} "
                  f"clr_g|div={cg_div/max(n_div,1):.0%} "
                  f"clr_gt|div={ct_div/max(n_div,1):.0%} "
                  f"both|div={both_div/max(n_div,1):.0%}", flush=True)

    def wmean(key, weight="n"):
        return float(np.average([r[key] for r in rows], weights=[r[weight] for r in rows]))
    agg = {k: wmean(k) for k in
           ["agree_rate", "clear_guided_agree", "clear_guided_div", "clear_gt_div",
            "both_clear_div", "div_weak", "div_strong"]}
    # arithmetic check: overall guided clear = agree*clr_g|agree + div*clr_g|div
    ov_g = agg["agree_rate"] * agg["clear_guided_agree"] + \
           (1 - agg["agree_rate"]) * agg["clear_guided_div"]
    ov_t = agg["agree_rate"] * agg["clear_guided_agree"] + \
           (1 - agg["agree_rate"]) * agg["clear_gt_div"]
    agg["implied_guided_clear"] = ov_g
    agg["implied_gt_clear"] = ov_t
    print("\nweighted means:", {k: round(v, 3) for k, v in agg.items()})

    total_kind = {}
    for ds, kc in kind_counter.items():
        for k, c in kc.items():
            total_kind[k] = total_kind.get(k, 0) + c
    tot = sum(total_kind.values())
    var_tot = sum(c for k, c in total_kind.items() if k != "regime_holdout")
    joint_share = total_kind.get("joint_drift", 0) / max(var_tot, 1)
    print("kind shares:", {k: f"{c} ({c/tot:.1%})" for k, c in total_kind.items()})
    print(f"joint share of variable-type instances: {joint_share:.1%}")

    json.dump({"rows": rows, "mean": agg,
               "kind_counts": total_kind, "joint_share": joint_share},
              open(cpath("guided_mechanism_v2.json"), "w"), ensure_ascii=False, indent=1, default=float)
    print("saved -> guided_mechanism_v2.json", flush=True)

if __name__ == "__main__":
    run()
