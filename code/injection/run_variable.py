"""变量级注入批量运行: {cmhmil, iforest} × {SWaT, SMD, MetroPT3} × 故障类型 × 强度.

输出: _cache/inj_var_{scorer}_{dataset}.npz (逐试验记录) + 汇总统计.
真值: cause_type=variable, cause_vars=注入变量集, kind, strength.
有效性 (可自动判定真值类别) = 注入段内出现 FA 窗 (score>tau, 窗标签正常).
注: cmhmil/MetroPT3 分数退化 (std~1.6e-4) 已在误报收集中发现, 此处跳过并记录.
"""
import os
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_raw, split_of, cpath, FAR_TARGETS  # noqa: E402
from fa_collection.collect import calib_test_scores  # noqa: E402
from injection.inject import (DRIFT_BETAS, VAR_ALPHAS, SEG_LEN, N_TRIALS,  # noqa: E402
                              active_channels, apply_variable_fault,
                              eval_injected, sample_normal_segments)

SKIP = {("cmhmil", "MetroPT3")}  # 分数退化, 诚实剔除 (见误报统计表注)


def run_one(scorer, dataset):
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    taus = {}
    for target in FAR_TARGETS:
        d = np.load(cpath(f"fa_{scorer}_{dataset}_far{int(target*100)}.npz"))
        taus[target] = float(d["tau"])
    mu = X[a:b].mean(0)
    sigma = X[a:b].std(0) + 1e-8
    active = active_channels(X, a, b)
    rng = np.random.default_rng(7)

    records = []
    configs = ([("drift", be) for be in DRIFT_BETAS]
               + [("stuck", 1.0)]
               + [("var", al) for al in VAR_ALPHAS])
    for kind, strength in configs:
        starts = sample_normal_segments(Y, b, SEG_LEN, N_TRIALS, seed=zlib.crc32((str(kind), str(strength)).encode()) & 0x7fffffff)
        for s in starts:
            j = int(rng.choice(active))
            Xm, gt = apply_variable_fault(X, s, SEG_LEN, [j], kind, strength, mu, sigma)
            for target in FAR_TARGETS:
                ev = eval_injected(scorer, dataset, X, Xm, s, SEG_LEN, taus[target])
                records.append({
                    **gt, "far_target": target, "tau": taus[target],
                    "n_fa_after": ev["n_fa_after"], "n_fa_before": ev["n_fa_before"],
                    "n_windows": ev["n_windows"], "fa_rate_after": ev["fa_rate_after"],
                    "score_gain": ev["score_gain"],
                    "scores_after_mean": float(ev["scores_after"].mean()),
                })
    # 多变量联合漂移 (2~3 变量)
    starts = sample_normal_segments(Y, b, SEG_LEN, N_TRIALS, seed=1234)
    for s in starts:
        k = int(rng.integers(2, 4))
        js = rng.choice(active, size=k, replace=False)
        Xm = X.copy()
        t = np.arange(SEG_LEN)
        per = []
        for j in js:
            be = float(rng.choice(DRIFT_BETAS))
            Xm[s:s + SEG_LEN, j] += be * sigma[j] * t
            per.append((int(j), be))
        gt = {"cause_type": "variable", "cause_vars": [int(v) for v in js],
              "kind": "joint_drift", "strength": per, "start": int(s), "seg_len": SEG_LEN}
        for target in FAR_TARGETS:
            ev = eval_injected(scorer, dataset, X, Xm, s, SEG_LEN, taus[target])
            records.append({**gt, "far_target": target, "tau": taus[target],
                            "n_fa_after": ev["n_fa_after"], "n_fa_before": ev["n_fa_before"],
                            "n_windows": ev["n_windows"], "fa_rate_after": ev["fa_rate_after"],
                            "score_gain": ev["score_gain"],
                            "scores_after_mean": float(ev["scores_after"].mean())})
    return records


def summarize(records):
    """按 (far_target, kind, strength) 汇总: 试验数 / 有效性比例 / 平均FA率."""
    from collections import defaultdict
    agg = defaultdict(list)
    for r in records:
        agg[(r["far_target"], r["kind"], str(r["strength"]))].append(r)
    out = []
    for (tgt, kind, st), rs in sorted(agg.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
        valid = [r for r in rs if r["n_fa_after"] > 0]
        out.append({"far_target": tgt, "kind": kind, "strength": st, "n_trials": len(rs),
                    "valid_rate": len(valid) / len(rs),
                    "mean_fa_rate": float(np.mean([r["fa_rate_after"] for r in rs])),
                    "mean_score_gain": float(np.mean([r["score_gain"] for r in rs]))})
    return out


if __name__ == "__main__":
    import json
    all_stats = {}
    for scorer in ("iforest", "cmhmil"):
        for ds in ("SWaT", "SMD", "MetroPT3"):
            if (scorer, ds) in SKIP:
                print(f"[{scorer},{ds}] 跳过 (分数退化)")
                continue
            print(f"[{scorer},{ds}] 变量级注入 ...", flush=True)
            try:
                recs = run_one(scorer, ds)
                np.savez_compressed(
                    cpath(f"inj_var_{scorer}_{ds}.npz"),
                    records=np.array(recs, dtype=object))
                stats = summarize(recs)
                all_stats[f"{scorer}_{ds}"] = stats
                for st in stats:
                    print(f"  FAR{st['far_target']:.0%} {st['kind']}@{st['strength']}: "
                          f"valid={st['valid_rate']:.0%} fa_rate={st['mean_fa_rate']:.2f}")
            except Exception as e:
                print(f"  失败: {type(e).__name__}: {e}")
                import traceback; traceback.print_exc()
    with open(cpath("inj_var_summary.json"), "w", encoding="utf-8") as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=1)
    print("汇总已写入 inj_var_summary.json")
