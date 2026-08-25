"""牌1 探针 v1: 新判据下的扩展仲裁器 (从 _cache/fusion_probe 的 φ 缓存直评, 秒级).

新 DeepSeek 判据 (2026-08-23 修订):
  必须同时赢 best-single 与 简单平均集成; 与 oracle 上界的差距只报告不作门槛.
  PASS 口径 (宁严勿宽): 三列(iforest/pca/ocsvm)每列同时赢两条基线, 且 pooled 也赢.

仲裁器 (逐实例, θ/偏置在注入验证段标定, 测试段不动):
  v0-tv / v0-rank / v0-conf : 上轮三变体 (复算入表, 便于对照)
  R1 conf-duel    : 路由到自身置信 κ(top份额) 更高者, 含验证段标定偏置 b
  R2 agree-margin : argmax 一致则直接输出; 分歧时取 top1-top2 margin 更大者(含偏置 b)
  R3 default-swap : 默认=验证段较优法; 仅当对方 margin 超出默认 margin 超过 θ 时切换
                    (θ 网格含 -inf..+inf, 方向由验证段学出)
输出: _cache/fusion_probe_v1.json + 控制台判据表
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402

PHI_DIR = cpath("fusion_probe")


def norm(phi):
    p = phi - phi.min(1, keepdims=True)
    return p / (p.sum(1, keepdims=True) + 1e-12)


def hits_of(phi, gtv, sel):
    o = np.argmax(phi[sel], 1)
    return np.array([int(oi in set(gtv[gi])) for oi, gi in zip(o, sel)])


def col_of(name):
    if name.startswith("iforest"):
        return "iforest"
    if name.startswith("pca"):
        return "pca"
    return "ocsvm"


def route_eval(phi_cf, phi_rec, gtv, sel_t, sel_v):
    """返回 dict: 各路由器测试段 top1 + 基线."""
    p_cf, p_rec = norm(phi_cf), norm(phi_rec)
    if len(sel_t) == 0:
        return {"n": 0}
    hc_t, hr_t = hits_of(phi_cf, gtv, sel_t), hits_of(phi_rec, gtv, sel_t)
    hc_v, hr_v = hits_of(phi_cf, gtv, sel_v), hits_of(phi_rec, gtv, sel_v)
    hc_t = hc_t.astype(int); hr_t = hr_t.astype(int)
    out = {"n": int(len(sel_t)),
           "cf": float(hc_t.mean()), "rec": float(hr_t.mean()),
           "ens": float(hits_of(0.5 * (p_cf + p_rec), gtv, sel_t).mean()),
           "orcU": float(max(hc_t.mean(), hr_t.mean())),
           "orcI": float((hc_t | hr_t).mean())}

    # ---------- v0 三变体 (上轮口径, 复算) ----------
    D_tv = 0.5 * np.abs(p_cf - p_rec).sum(1)
    j_cf, j_rec = np.argmax(phi_cf, 1), np.argmax(phi_rec, 1)
    D_rank = (j_cf != j_rec).astype(float)
    D_conf = np.abs(p_cf.max(1) - p_rec.max(1))

    def cal_route(D, hc_v2, hr_v2, hc_t2, hr_t2, min_val=5):
        if len(sel_v) < min_val:
            return None
        best = (-1.0, None, None)
        Dv = D[sel_v]
        for direction in ("rec_on_high", "cf_on_high"):
            for q in np.linspace(0.05, 0.95, 19):
                th = float(np.quantile(Dv, q))
                use_rec = (Dv > th) if direction == "rec_on_high" else (Dv <= th)
                acc = float(np.mean(np.where(use_rec, hr_v2, hc_v2)))
                if acc > best[0]:
                    best = (acc, th, direction)
        _, th, direction = best
        use_rec = (D[sel_t] > th) if direction == "rec_on_high" else (D[sel_t] <= th)
        return float(np.mean(np.where(use_rec, hr_t2, hc_t2)))

    out["v0_tv"] = cal_route(D_tv, hc_v, hr_v, hc_t, hr_t)
    out["v0_rank"] = cal_route(D_rank, hc_v, hr_v, hc_t, hr_t)
    out["v0_conf"] = cal_route(D_conf, hc_v, hr_v, hc_t, hr_t)

    # ---------- R1 conf-duel: κ 更高者, 含验证段偏置 b ----------
    k_cf, k_rec = p_cf.max(1), p_rec.max(1)
    diff = k_rec - k_cf            # >0 → rec 更自信
    if len(sel_v) >= 5:
        bs = [float(np.mean(np.where(diff[sel_v] > b, hr_v, hc_v)))
              for b in np.linspace(-0.5, 0.5, 41)]
        b = float(np.linspace(-0.5, 0.5, 41)[int(np.argmax(bs))])
    else:
        b = 0.0
    out["R1_confdual"] = float(np.mean(np.where(diff[sel_t] > b, hr_t, hc_t)))

    # ---------- R2 agree-margin ----------
    def margins(p):
        srt = np.sort(p, 1)
        return srt[:, -1] - srt[:, -2]
    m_cf, m_rec = margins(p_cf), margins(p_rec)
    agree = (j_cf == j_rec)
    if len(sel_v) >= 5:
        hv_a = np.where(agree[sel_v], hc_v, np.where(
            (m_rec - m_cf)[sel_v] > 0, hr_v, hc_v))
        # 标定偏置: 分歧时 rec 需要的 margin 优势
        bs = [float(np.mean(np.where(agree[sel_v], hc_v, np.where(
            (m_rec - m_cf)[sel_v] > b2, hr_v, hc_v))))
            for b2 in np.linspace(-0.5, 0.5, 41)]
        b2 = float(np.linspace(-0.5, 0.5, 41)[int(np.argmax(bs))])
    else:
        b2 = 0.0
    use_rec_dis = (m_rec - m_cf) > b2
    pick_rec = np.where(agree, False, use_rec_dis)   # 一致时任取 (hits 相同)
    hits_r2 = np.where(pick_rec[sel_t], hr_t, hc_t)
    out["R2_agreemargin"] = float(np.mean(hits_r2))

    # ---------- R3 default-swap ----------
    if len(sel_v) >= 5:
        acc_cf_v, acc_rec_v = float(hc_v.mean()), float(hr_v.mean())
        default_rec = acc_rec_v >= acc_cf_v
        sw = (m_rec - m_cf) if default_rec else (m_cf - m_rec)
        h_def_v, h_oth_v = (hr_v, hc_v) if default_rec else (hc_v, hr_v)
        h_def_t, h_oth_t = (hr_t, hc_t) if default_rec else (hc_t, hr_t)
        best = (-1.0, None)
        for th in np.concatenate([[np.inf], np.linspace(-0.5, 0.5, 41)]):
            acc = float(np.mean(np.where(sw[sel_v] > th, h_oth_v, h_def_v)))
            if acc > best[0]:
                best = (acc, float(th))
        _, th = best
        out["R3_defaultswap"] = float(np.mean(
            np.where(sw[sel_t] > th, h_oth_t, h_def_t)))
    else:
        out["R3_defaultswap"] = None
    return out


def main():
    files = sorted(f for f in os.listdir(PHI_DIR) if f.endswith(".npz"))
    per_unit = {}
    for f in files:
        d = np.load(os.path.join(PHI_DIR, f), allow_pickle=True)
        name = f[:-4]
        r = route_eval(d["phi_cf"], d["phi_rec"], d["gt_vars"],
                       d["sel_test"], d["sel_val"])
        per_unit[name] = r

    arb = ["v0_tv", "v0_rank", "v0_conf", "R1_confdual", "R2_agreemargin",
           "R3_defaultswap"]
    cols = ("iforest", "pca", "ocsvm")
    summary = {}
    print("%-16s %-8s %6s %6s %6s | %6s %6s %6s %6s" %
          ("arbiter", "column", "best1", "means", "route", "Δbest", "Δmeans",
           "oracleU", "gap_orc"))
    for a in arb:
        summary[a] = {}
        for c in cols:
            rows = [r for n, r in per_unit.items()
                    if col_of(n) == c and r.get(a) is not None]
            if not rows:
                continue
            best1 = max(float(np.mean([r["cf"] for r in rows])),
                        float(np.mean([r["rec"] for r in rows])))
            means = float(np.mean([r["ens"] for r in rows]))
            route = float(np.mean([r[a] for r in rows]))
            orcU = float(np.mean([r["orcU"] for r in rows]))
            summary[a][c] = {"best_single": best1, "mean_ens": means,
                             "route": route, "oracle_unit": orcU,
                             "n_units": len(rows),
                             "gap_oracle": route - orcU,
                             "beat_best": route > best1,
                             "beat_means": route > means}
            print("%-16s %-8s %6.3f %6.3f %6.3f | %+6.3f %+6.3f %6.3f %+6.3f" %
                  (a, c, best1, means, route, route - best1, route - means,
                   orcU, route - orcU))
        # pooled (全部单元均值)
        rows = [r for r in per_unit.values() if r.get(a) is not None]
        if rows:
            best1 = max(float(np.mean([r["cf"] for r in rows])),
                        float(np.mean([r["rec"] for r in rows])))
            means = float(np.mean([r["ens"] for r in rows]))
            route = float(np.mean([r[a] for r in rows]))
            summary[a]["pooled"] = {"best_single": best1, "mean_ens": means,
                                    "route": route, "n_units": len(rows)}
            print("%-16s %-8s %6.3f %6.3f %6.3f | %+6.3f %+6.3f" %
                  (a, "POOLED", best1, means, route, route - best1,
                   route - means))
        print()

    # ---- 新判据判定: 每列 + pooled 都须赢两条基线 ----
    print("===== 新 DeepSeek 判据 (赢 best-single & 赢 mean-ens; oracle 只报差距) =====")
    for a in arb:
        cs = [c for c in cols if c in summary[a]]
        ok_cols = all(summary[a][c]["beat_best"] and summary[a][c]["beat_means"]
                      for c in cs)
        ok_pool = ("pooled" in summary[a] and
                   summary[a]["pooled"]["route"] > summary[a]["pooled"]["best_single"]
                   and summary[a]["pooled"]["route"] > summary[a]["pooled"]["mean_ens"])
        gaps = ", ".join("%s %+0.3f" % (c, summary[a][c]["gap_oracle"])
                         for c in cs)
        print("%-16s 列内全过: %s | pooled 过: %s | oracle差距: %s" %
              (a, "PASS" if ok_cols else "FAIL", "PASS" if ok_pool else "FAIL",
               gaps))

    json.dump({"per_unit": per_unit, "summary": summary},
              open(cpath("fusion_probe_v1.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print("\n写入 _cache/fusion_probe_v1.json")


if __name__ == "__main__":
    main()
