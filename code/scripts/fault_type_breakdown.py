"""A. 故障类型分解: 每种注入故障类型 (drift/stuck/variance/joint) 的 top-1, 代表性子集."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath, load_raw, split_of, WINDOW  # noqa: E402
from rcca.rcca import _RegimeBank  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402
import evaluation.gt_pool as gp  # noqa: E402

METHODS = ("RC-CA", "GlobalCF", "CondAttr", "AERec", "zDev")
KIND_NAMES = {"drift": "linear drift", "stuck": "stuck-at", "var": "variance infl.",
              "joint": "joint drift"}
# VAR_CONFIGS = [("drift", 0.1), ("drift", 0.2), ("stuck", 1.0), ("var", 5.0)] + [("joint", 0)]


def main():
    out = {}
    for ds in ("SWaT", "SMD", "MetroPT3"):
        units = gp._mixed_unit(ds)
        for u in units[:2]:  # 每数据集取前 2 个单元
            vm = (u.gt_type == "variable")
            kinds = np.array([k if k != "regime_holdout" else "regime"
                              for k in u.gt_kind])
            bank = _RegimeBank(u.pool_windows(), seed=0)
            W = u.windows()
            y = (u.gt_type == "variable").astype(int)
            for m in METHODS:
                attr = tl.METHODS[m](u, W, bank)
                g, d = tl.calibrate(tl._sub(attr, u.val_mask), y[u.val_mask])
                pred = tl._predict(attr, g, d)
                # top-1: 只看 variable-type 且按故障类型分组
                phi = attr["phi"]
                top1_ch = np.argmax(phi, 1)
                for kind in ("drift", "stuck", "var", "joint", "regime"):
                    mask = vm & (kinds == kind) if kind != "regime" else (kinds == "regime")
                    if mask.sum() == 0:
                        continue
                    if kind == "regime":
                        # mode-level: 看 pred == 0 (mode) 的比例
                        acc = float((pred[mask] == 0).mean())
                    else:
                        # variable-level: 看 top-1 通道是否命中 gt_vars
                        hits = []
                        for i in np.where(mask)[0]:
                            gt_ch = u.gt_vars[i]
                            if gt_ch and int(top1_ch[i]) in [int(c) for c in gt_ch]:
                                hits.append(1)
                            else:
                                hits.append(0)
                        acc = float(np.mean(hits)) if hits else None
                    if acc is not None:
                        key = f"{u.name}|{m}|{KIND_NAMES.get(kind, kind)}"
                        out[key] = {"acc": acc, "n": int(mask.sum())}
            print(f"  {u.name} done", flush=True)
    # 汇总: 每方法×每故障类型, 跨单元平均
    summary = {}
    for m in METHODS:
        for kind in list(KIND_NAMES.values()) + ["regime"]:
            vals = [v["acc"] for k, v in out.items() if f"|{m}|{kind}" in k]
            ns = [v["n"] for k, v in out.items() if f"|{m}|{kind}" in k]
            if vals:
                summary[f"{m}|{kind}"] = {
                    "mean": round(float(np.average(vals, weights=ns)), 3),
                    "n_total": int(sum(ns))}
    json.dump({"per_unit": out, "summary": summary},
              open(cpath("fault_type_breakdown.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print("\n=== 故障类型分解汇总 ===")
    for m in METHODS:
        row = [f"{kind}: {summary.get(m+'|'+kn, {}).get('mean', '--')}"
               for kn in list(KIND_NAMES.values()) + ["regime"]]
        print(f"  {m:12s} " + " | ".join(row))
    print("saved fault_type_breakdown.json")


if __name__ == "__main__":
    main()
