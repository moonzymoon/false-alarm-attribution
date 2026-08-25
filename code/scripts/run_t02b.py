"""T0-2b: 自然误报人工标签(多标注人) → 方法准确率 + γ 重校准曲线.
phase precompute (已跑): 120 窗 × 5 方法 conf/delta + 注入 γ, 存 t02b_{combo}.npz.
phase analyze (标签回收后):
  0. 多标注人: 逐人统计 / 两两 Cohen kappa / Fleiss kappa(3类含u + 全v/m子集2类) /
     剔除与众人一致性过低的标注人(平均两两 kappa<0.2, 如实记录) / v-m 多数投票(u弃权)
  A. 各方法(注入γ) vs 多数投票标签一致率(总体+分数据集)
  B. γ 重校准曲线: k∈{10,20,30} 分数据集 / {10,25,50,100} 池化, 20 次抽样
  C. 重校准后跨方法一致率
输出 _cache/t02b_results.json
"""
import glob
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
COMBOS = ("iforest_SWaT", "iforest_SMD", "iforest_MetroPT3")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PKG = os.path.join(ROOT, "04_投稿准备", "T0_投稿前实验包", "标注包")
KAPPA_DROP = 0.2   # 平均两两 Cohen kappa 低于此值的标注人剔除(预登记规则)


def precompute():
    meta = json.load(open(cpath("label_windows_meta.json"), encoding="utf-8"))
    for combo in COMBOS:
        scorer, ds = combo.split("_")
        X, Y = load_raw(ds)
        a, b = split_of(len(X))
        rows = [m for m in meta if m["dataset"] == ds]
        ends = np.array([m["end"] for m in rows], int)
        Wnat = X[ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]
        pool_ends = np.arange(a + WINDOW - 1, b)
        if len(pool_ends) > 60000:
            pool_ends = pool_ends[np.random.default_rng(0).choice(
                len(pool_ends), 60000, replace=False)]
        bank = _RegimeBank(X[pool_ends[:, None] - (WINDOW - 1) +
                             np.arange(WINDOW)[None, :]], seed=0)

        class _U:
            pass
        u = _U()
        u.scorer, u.dataset, u.iforest_model = scorer, ds, None
        u.score = lambda W: tl.rs.score_windows(scorer, ds, W)
        u.name = f"nat_{combo}"
        gu = gp._variable_unit(scorer, ds)
        yv = (gu.gt_type == "variable").astype(int)
        out = {"ends": ends, "wids": np.array([m["window_id"] for m in rows])}
        for mname in METHODS:
            attr_nat = tl.METHODS[mname](u, Wnat, bank)
            attr_val = tl.METHODS[mname](gu, gu.windows(), bank)
            g_inj, d_inj = tl.calibrate(tl._sub(attr_val, gu.val_mask), yv[gu.val_mask])
            out[f"{mname}_conf"] = attr_nat["conf"]
            out[f"{mname}_delta"] = (attr_nat["delta"] if attr_nat["delta"] is None
                                     else np.asarray(attr_nat["delta"], float))
            out[f"{mname}_ginj"] = np.array(
                [g_inj, d_inj if d_inj is None else float(d_inj)], float)
            print(f"[{combo}] {mname}: gamma_inj={g_inj:.4f} delta={d_inj}", flush=True)
        np.savez_compressed(cpath(f"t02b_{combo}.npz"), **out)
        print(f"[{combo}] saved t02b npz ({len(ends)} windows)", flush=True)


# ---------------- 多标注人汇总 ----------------

def read_annotator_file(path):
    import csv
    lab = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            v = (row.get("label") or "").strip().lower()
            if v in ("v", "m"):
                lab[row["window_id"]] = 1 if v == "v" else 0
            elif v == "u":
                lab[row["window_id"]] = None
    return lab


def cohen_kappa(a, b):
    """两标注人共同标过的窗上(仅 v/m)的 Cohen kappa."""
    common = [w for w in a if w in b and a[w] is not None and b[w] is not None]
    if len(common) < 5:
        return None
    pa = np.mean([a[w] == b[w] for w in common])
    p0a = np.mean([a[w] == 0 for w in common])
    p0b = np.mean([b[w] == 0 for w in common])
    pe = p0a * p0b + (1 - p0a) * (1 - p0b)
    return (pa - pe) / (1 - pe + 1e-12)


def fleiss_kappa(labels_by_ann, wids, cats=(0, 1, "u")):
    """labels_by_ann: list of {wid: 0/1/None}; wids: 参与的窗."""
    n_c = len(cats)
    mat = np.zeros((len(wids), n_c))
    idx = {c: i for i, c in enumerate(cats)}
    for j, w in enumerate(wids):
        for lab in labels_by_ann:
            if w in lab:
                mat[j, idx[lab[w] if lab[w] is not None else "u"]] += 1
    ntot = mat.sum(1)
    keep = ntot > 1
    mat = mat[keep]
    ntot = ntot[keep]
    n_r = ntot[0]
    if n_r < 2 or len(mat) < 3:
        return None
    p_i = ((mat ** 2).sum(1) - ntot) / (ntot * (ntot - 1))
    p_c = mat.sum(0) / mat.sum()
    pe = (p_c ** 2).sum()
    return float((p_i.mean() - pe) / (1 - pe + 1e-12))


def build_majority(files, res):
    """读入全部标注文件 → 一致性统计 → 剔除 → 多数投票标签 {wid: 0/1}."""
    anns = {}
    for f in files:
        name = os.path.basename(f)[len("labels_"):-4] if "labels_" in os.path.basename(f) \
            else "annotator1"
        anns[name] = read_annotator_file(f)
    res["annotators"] = {}
    for name, lab in anns.items():
        res["annotators"][name] = {
            "n_vm": sum(1 for v in lab.values() if v is not None),
            "n_u": sum(1 for v in lab.values() if v is None)}
    # 两两 kappa + 一致率
    names = list(anns)
    kappa = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            kappa[f"{names[i]}|{names[j]}"] = cohen_kappa(anns[names[i]], anns[names[j]])
    res["pairwise_kappa"] = kappa
    # 平均两两 kappa → 剔除规则
    keep = []
    for nm in names:
        vals = [v for k, v in kappa.items() if nm in k.split("|") and v is not None]
        mk = float(np.mean(vals)) if vals else None
        res["annotators"][nm]["mean_pairwise_kappa"] = mk
        res["annotators"][nm]["dropped"] = bool(mk is not None and mk < KAPPA_DROP)
        if not (mk is not None and mk < KAPPA_DROP):
            keep.append(nm)
    res["n_kept_annotators"] = len(keep)
    kept = [anns[nm] for nm in keep]
    # Fleiss (3类含u, 全部窗) + (2类, 全员都给 v/m 的窗)
    allw = sorted(set().union(*[set(l) for l in kept])) if kept else []
    res["fleiss_kappa_3cat"] = fleiss_kappa(kept, allw)
    vmw = [w for w in allw if all(w in l and l[w] is not None for l in kept)]
    res["fleiss_kappa_vm"] = fleiss_kappa([l for l in kept], vmw) if len(keep) >= 2 else None
    # 多数投票 (v/m; u 弃权; 平票/零票 → 无标签)
    maj, ties = {}, 0
    for w in allw:
        votes = [l[w] for l in kept if w in l and l[w] is not None]
        if not votes:
            continue
        c1 = sum(votes)
        if c1 * 2 == len(votes):
            ties += 1
            continue
        maj[w] = int(c1 * 2 > len(votes))
    res["n_majority_labels"] = len(maj)
    res["n_ties_excluded"] = ties
    res["majority_mode_frac"] = float(np.mean(list(maj.values()))) if maj else None
    return maj


def _load_all():
    data = {}
    for combo in COMBOS:
        z = np.load(cpath(f"t02b_{combo}.npz"), allow_pickle=True)
        d = {k: z[k] for k in z.files}
        for k in list(d):
            if k.endswith("_delta") and getattr(d[k], "ndim", 0) == 0:
                d[k] = None          # None 被存成 0 维数组, 归一化
        data[combo] = d
    return data


def analyze():
    files = sorted(glob.glob(os.path.join(PKG, "labels_*.csv")))
    if not files and os.path.exists(os.path.join(PKG, "labels.csv")):
        files = [os.path.join(PKG, "labels.csv")]
    print("标注文件:", [os.path.basename(f) for f in files])
    data = _load_all()
    res = {"n_files": len(files), "kappa_drop_rule": KAPPA_DROP}
    maj = build_majority(files, res)
    lab = maj
    print(f"多数投票标签: {len(lab)} (Fleiss 3类 {res['fleiss_kappa_3cat']}, "
          f"v/m 子集 {res['fleiss_kappa_vm']})")

    # A. 注入γ 与多数标签一致率
    per_m, per_ds = {}, {}
    for combo, z in data.items():
        ds = combo.split("_")[1]
        idx = np.array([i for i, w in enumerate(z["wids"]) if w in lab])
        y = np.array([lab[z["wids"][i]] for i in idx], int)
        per_ds.setdefault(ds, {})[combo] = {}
        for m in METHODS:
            g, d = z[f"{m}_ginj"]
            attr = {"conf": z[f"{m}_conf"][idx],
                    "delta": None if np.isnan(d) else z[f"{m}_delta"][idx]}
            pred = tl._predict(attr, float(g), None if np.isnan(d) else float(d))
            acc = float((pred == y).mean())
            per_m.setdefault(m, []).append((combo, acc, len(y)))
            per_ds[ds][combo][m] = acc
    res["acc_inj"], res["acc_by_ds"] = {}, per_ds
    for m in METHODS:
        ntot = sum(n for _, _, n in per_m[m])
        res["acc_inj"][m] = sum(a * n for _, a, n in per_m[m]) / ntot
        print(f"A. {m}: 注入γ 一致率 {res['acc_inj'][m]:.3f} "
              f"(" + ", ".join(f"{c.split('_')[1]}={a:.2f}" for c, a, _ in per_m[m]) + ")")

    # B. γ 重校准曲线 (与多数标签)
    rng = np.random.default_rng(0)
    res["curve"] = {}
    for m in METHODS:
        for mode, ks in (("pooled", (10, 25, 50, 100)), ("per_ds", (10, 20, 30))):
            for k in ks:
                accs = []
                for _ in range(20):
                    pool = [(combo, i) for combo, z in data.items()
                            for i, w in enumerate(z["wids"]) if w in lab]
                    if mode == "per_ds":
                        # 分数据集: 每数据集抽 k/3, 其余作测试
                        tr, te = [], []
                        for combo, z in data.items():
                            cand = [(combo, i) for i, w in enumerate(z["wids"]) if w in lab]
                            take = min(max(1, k // 3), len(cand) - 1) if len(cand) > 1 else 0
                            if take:
                                sel = rng.choice(len(cand), take, replace=False)
                                tr += [cand[s] for s in sel]
                                te += [c for s, c in enumerate(cand) if s not in set(sel.tolist())]
                        if not tr or not te:
                            continue
                    else:
                        sel = rng.choice(len(pool), min(k, len(pool)), replace=False)
                        tr = [pool[i] for i in sel]
                        te = [p for p in pool if p not in tr]
                    y_tr = np.array([lab[data[c]["wids"][i]] for c, i in tr])
                    conf_tr = np.concatenate([data[c][f"{m}_conf"][[i]] for c, i in tr])
                    dlt_tr = None
                    if data[COMBOS[0]][f"{m}_delta"] is not None:
                        dlt_tr = np.concatenate(
                            [np.atleast_1d(data[c][f"{m}_delta"][i]) for c, i in tr])
                    g, dd = tl.calibrate({"conf": conf_tr, "delta": dlt_tr}, y_tr)
                    y_te = np.array([lab[data[c]["wids"][i]] for c, i in te])
                    conf_te = np.concatenate([data[c][f"{m}_conf"][[i]] for c, i in te])
                    dlt_te = None
                    if data[COMBOS[0]][f"{m}_delta"] is not None:
                        dlt_te = np.concatenate(
                            [np.atleast_1d(data[c][f"{m}_delta"][i]) for c, i in te])
                    pred = tl._predict({"conf": conf_te, "delta": dlt_te}, g, dd)
                    accs.append(float((pred == y_te).mean()))
                if accs:
                    res["curve"][f"{m}_{mode}_k{k}"] = {
                        "mean": float(np.mean(accs)), "std": float(np.std(accs))}
                    print(f"B. {m} {mode} k={k}: acc {np.mean(accs):.3f}±{np.std(accs):.3f}")

    # C. 重校准后跨方法一致率 (pooled k=50)
    res["agree"] = {}
    pool = [(c, i) for c, z in data.items() for i, w in enumerate(z["wids"]) if w in lab]
    if len(pool) >= 60:
        preds = {}
        for m in METHODS:
            sel = rng.choice(len(pool), 50, replace=False)
            tr = [pool[i] for i in sel]
            y_tr = np.array([lab[data[c]["wids"][i]] for c, i in tr])
            conf_tr = np.concatenate([data[c][f"{m}_conf"][[i]] for c, i in tr])
            dlt_tr = (None if data[COMBOS[0]][f"{m}_delta"] is None else
                      np.concatenate([np.atleast_1d(data[c][f"{m}_delta"][i]) for c, i in tr]))
            g, dd = tl.calibrate({"conf": conf_tr, "delta": dlt_tr}, y_tr)
            pr = []
            for c, z in data.items():
                idx = [i for i, w in enumerate(z["wids"]) if w in lab]
                attr = {"conf": z[f"{m}_conf"][idx],
                        "delta": None if z[f"{m}_delta"] is None else z[f"{m}_delta"][idx]}
                pr.append(tl._predict(attr, g, dd))
            preds[m] = np.concatenate(pr)
        ms = list(preds)
        ags = [float((preds[a] == preds[b]).mean()) for i, a in enumerate(ms)
               for b in ms[i + 1:]]
        res["agree"]["pairwise_recal_k50"] = float(np.mean(ags))
        print(f"C. 重校准(k=50)后平均两两一致率: {np.mean(ags):.3f}")

    json.dump(res, open(cpath("t02b_results.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print("saved t02b_results.json")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "precompute":
        precompute()
    else:
        analyze()
