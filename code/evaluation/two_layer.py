"""两层公平评估协议 (方案 §5.1 + v3 必改3).

第一层: 成因类型二分类 (variable=1 / regime=0), 统一拒绝规则:
  - 仅 φ 方法: pred=regime if conf < γ;
  - 带 Δ_reg 方法 (RC-CA / RegimeGlobal): pred=regime if Δ_reg>δ 且 conf<γ;
  γ/δ 在各单元的注入验证集上按宏F1标定, 测试集不动; 另报 oracle(测试集反推)上限.
第二层: 变量型子集 top-1/top-3 变量命中; 工况型子集工况命中率 (仅有 regime 输出的方法).
"""
import os
import sys

import numpy as np
from sklearn.metrics import f1_score, precision_recall_fscore_support

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scorers_rescore as rs  # noqa: E402
from rcca.rcca import _RegimeBank, rcca_attribute, regime_aware_global_attribute  # noqa: E402

_CACHE = {}


# ---------------- 基线 ----------------
def _var_replacement_scores(unit, Warr, traj):
    """对每变量 j 用轨迹 traj 替换后打分, 返回 drops (n, D)."""
    n, Wn, D = Warr.shape
    mask = np.arange(D)[None, None, :]
    reps = [np.where(mask == j, traj, Warr).astype(np.float32) for j in range(D)]
    scores = unit.score(np.concatenate(reps, 0))
    s_orig = unit.score(Warr)
    return np.stack([s_orig - scores[i * n:(i + 1) * n] for i in range(D)], 1)


def global_cf_attribute(unit, Warr, bank):
    drops = _var_replacement_scores(unit, Warr, bank.global_mean_traj)
    s_orig = unit.score(Warr)
    conf = drops.max(1) / (np.abs(s_orig) + 1e-9)
    return {"phi": drops, "conf": conf, "delta": None, "regime": None}


def condattr_attribute(unit, Warr, bank):
    """CondAttr(复现) 向量化: 全部查询一次 UMAP transform, K=3 近邻, 逐变量替换."""
    from baselines.condattr import CondAttr
    key = ("condattr", unit.name)
    n, Wn, D = Warr.shape
    if key not in _CACHE:
        def f(flats):
            return unit.score(flats.reshape(len(flats), Wn, -1))
        _CACHE[key] = CondAttr(f).fit(bank.P.reshape(len(bank.P), -1))
    ca = _CACHE[key]
    qe = ca._reducer.transform(Warr.reshape(n, -1).astype(np.float32))     # (n,10)
    d = np.linalg.norm(ca.embed_[None] - qe[:, None], axis=2)              # (n, Ndb)
    nb = np.argsort(d, 1)[:, :ca.K]                                        # (n,K)
    nb_mean = ca.db_feats_[nb].reshape(n, ca.K, Wn, D).mean(1)             # (n,W,D)
    drops = _var_replacement_scores(unit, Warr, nb_mean)
    s_orig = unit.score(Warr)
    conf = drops.max(1) / (np.abs(s_orig) + 1e-9)
    return {"phi": drops, "conf": conf, "delta": None, "regime": None}


def ae_recon_attribute(unit, Warr, bank):
    """重构误差贡献 (基线⑤, OmniAnomaly 思路轻量代理: 正常池小 AE)."""
    import torch
    import torch.nn as nn
    key = ("ae", unit.name)
    P = bank.P
    D = P.shape[2]
    if key not in _CACHE:
        net = nn.Sequential(nn.Flatten(), nn.Linear(P.shape[1] * D, 128), nn.ReLU(),
                            nn.Linear(128, 32), nn.ReLU(), nn.Linear(32, P.shape[1] * D))
        opt = torch.optim.Adam(net.parameters(), 1e-3)
        Xt = torch.from_numpy(P.reshape(len(P), -1)).float()
        for ep in range(30):
            perm = torch.randperm(len(Xt))[:50000]
            loss = nn.functional.mse_loss(net(Xt[perm]), Xt[perm])
            opt.zero_grad(); loss.backward(); opt.step()
        net.eval()
        _CACHE[key] = net
    net = _CACHE[key]
    with torch.no_grad():
        rec = net(torch.from_numpy(Warr.reshape(len(Warr), -1)).float()).numpy()
    err = np.abs(rec.reshape(Warr.shape) - Warr).mean(1)
    conf = err.max(1) / (err.sum(1) + 1e-9)
    return {"phi": err, "conf": conf, "delta": None, "regime": None}


def gradient_attribute(unit, Warr, bank):
    """梯度归因 (基线④, 仅可微打分器 cmhmil; 输入梯度×幅值 的 TimeSHAP 代理)."""
    import torch
    from scorers_rescore import _load_cmhmil
    model, _ = _load_cmhmil(unit.dataset)
    xt = torch.from_numpy(Warr.reshape(len(Warr), 1, Warr.shape[1], Warr.shape[2])).float()
    xt.requires_grad_(True)
    s, _ = model(xt)
    s.sum().backward()
    phi = (xt.grad.abs() * xt.detach().abs()).sum(2).squeeze(1).numpy()
    conf = phi.max(1) / (phi.sum(1) + 1e-9)
    return {"phi": phi, "conf": conf, "delta": None, "regime": None}


def zdev_attribute(unit, Warr, bank):
    """M4: 无模型偏差读取基线 zDev —— phi_j = 窗内通道 j 对池分布的稳健偏离."""
    P = bank.P                                  # (N, T, D)
    med = np.median(P, axis=(0, 1))             # (D,)
    mad = np.median(np.abs(P - med[None, None, :]), axis=(0, 1)) * 1.4826 + 1e-9
    dev = np.abs(Warr - med[None, None, :]).mean(1) / mad[None, :]
    conf = dev.max(1) / (dev.sum(1) + 1e-9)
    return {"phi": dev, "conf": conf, "delta": None, "regime": None}


def random_attribute(unit, Warr, bank):
    rng = np.random.default_rng(0)
    phi = rng.random((len(Warr), Warr.shape[2]))
    return {"phi": phi, "conf": phi.max(1), "delta": None, "regime": None}


def granger_attribute(unit, Warr, bank):
    """Granger 因果基线 (审稿 M3): 正常池拟合 lag-1 多变量线性预测 (岭回归),
    φ_j = 摘除通道 j 作预测子后, 其余通道在查询窗上预测误差的增量之和.
    置信度 conf = φ_max / Σφ (与其他仅 φ 方法同一拒绝规则形式)."""
    key = ("granger", unit.name)
    if key not in _CACHE:
        P = bank.P                                        # (N, T, D)
        X = P[:, :-1].reshape(-1, P.shape[2])
        Y = P[:, 1:].reshape(-1, P.shape[2])
        Xb = np.hstack([X, np.ones((len(X), 1))])
        lam = 1e-3
        G = Xb.T @ Xb + lam * np.eye(Xb.shape[1])
        G[-1, -1] -= lam                                  # 截距不罚
        B = np.linalg.solve(G, Xb.T @ Y)                  # (D+1, D)
        _CACHE[key] = B
    B = _CACHE[key]
    Wn, D = Warr.shape[1], Warr.shape[2]
    Xb = np.hstack([Warr[:, :-1].reshape(-1, D), np.ones((len(Warr) * (Wn - 1), 1))])
    Y = Warr[:, 1:].reshape(-1, D)
    err_full = ((Xb @ B - Y) ** 2).reshape(len(Warr), Wn - 1, D)
    phi = np.zeros((len(Warr), D))
    for j in range(D):
        Bj = B.copy(); Bj[j, :] = 0                       # 摘除 j 作预测子
        err_j = ((Xb @ Bj - Y) ** 2).reshape(len(Warr), Wn - 1, D)
        dj = (err_j - err_full).sum(1)                    # (n, D)
        phi[:, j] = np.delete(dj, j, axis=1).sum(1)
    conf = phi.max(1) / (phi.sum(1) + 1e-9)
    return {"phi": phi, "conf": conf, "delta": None, "regime": None}


METHODS = {
    "RC-CA": lambda u, w, b: rcca_attribute(u, w, b),
    "GlobalCF": global_cf_attribute,
    "RegimeGlobal": lambda u, w, b: regime_aware_global_attribute(u, w, b),
    "CondAttr": condattr_attribute,
    "AERec": ae_recon_attribute,
    "Grad": gradient_attribute,
    "Granger": granger_attribute,
    "zDev": zdev_attribute,
    "Random": random_attribute,
}


# ---------------- 协议 ----------------
def _macro_f1(y, p):
    return float(f1_score(y, p, labels=[0, 1], average="macro", zero_division=0))


def _predict(attr, gamma, delta):
    conf, dl = attr["conf"], attr["delta"]
    if dl is not None and delta is not None:
        return np.where((conf < gamma) & (dl > delta), 0, 1)   # 0=regime, 1=variable
    return (conf >= gamma).astype(int)


def _sub(attr, mask):
    return {k: (v[mask] if isinstance(v, np.ndarray) else v) for k, v in attr.items()}


def calibrate(attr_val, y_val):
    gammas = np.quantile(attr_val["conf"], np.linspace(0.05, 0.95, 19))
    deltas = (np.quantile(attr_val["delta"], np.linspace(0.05, 0.95, 19))
              if attr_val["delta"] is not None else [None])
    best, bg, bd = -1.0, float(gammas[len(gammas) // 2]), None
    for g in gammas:
        for dlt in deltas:
            f = _macro_f1(y_val, _predict(attr_val, g, dlt))
            if f > best:
                best, bg, bd = f, float(g), (float(dlt) if dlt is not None else None)
    return bg, bd


def evaluate_unit(unit, methods=None):
    methods = methods or METHODS
    bank = _RegimeBank(unit.pool_windows(), seed=0)
    W = unit.windows()
    y = (unit.gt_type == "variable").astype(int)
    val, test = unit.val_mask, ~unit.val_mask
    out = {}
    for mname, fn in methods.items():
        if mname == "Grad" and unit.scorer != "cmhmil":
            continue
        try:
            attr = fn(unit, W, bank)
        except Exception as e:
            out[mname] = {"error": f"{type(e).__name__}: {e}"}
            continue
        gamma, delta = calibrate(_sub(attr, val), y[val])
        o_gamma, o_delta = calibrate(_sub(attr, test), y[test])
        pred = _predict(attr, gamma, delta)
        pred_o = _predict(attr, o_gamma, o_delta)
        m = {"gamma": gamma, "delta": delta, "oracle_gamma": o_gamma,
             "oracle_delta": o_delta,
             "layer1_macro_f1": _macro_f1(y[test], pred[test]),
             "layer1_oracle_macro_f1": _macro_f1(y[test], pred_o[test]),
             "n_val": int(val.sum()), "n_test": int(test.sum())}
        prf = precision_recall_fscore_support(y[test], pred[test], labels=[1, 0],
                                              zero_division=0)
        m.update({"var_precision": float(prf[0][0]), "var_recall": float(prf[1][0]),
                  "var_f1": float(prf[2][0]), "reg_precision": float(prf[0][1]),
                  "reg_recall": float(prf[1][1]), "reg_f1": float(prf[2][1])})
        vmask = test & (y == 1)
        if vmask.sum() > 0:
            phi = attr["phi"][vmask]
            top1, top3 = [], []
            for i, gi in enumerate(np.where(vmask)[0]):
                gtv = set(unit.gt_vars[gi])
                o = np.argsort(-phi[i])
                top1.append(int(o[0] in gtv))
                top3.append(int(len(set(o[:3]) & gtv) > 0))
            m["layer2_top1"] = float(np.mean(top1))
            m["layer2_top3"] = float(np.mean(top3))
            m["layer2_hits_top1"] = [int(x) for x in top1]
            m["layer2_hits_top3"] = [int(x) for x in top3]
            if mname == "RC-CA":
                pairs = [(st, unit.gt_kind[gi]) for st, gi in
                         zip(np.array(attr["subtype"])[vmask], np.where(vmask)[0])
                         if unit.gt_kind[gi] in ("drift", "stuck", "var")]
                if pairs:
                    m["subtype_acc"] = float(np.mean([a == b for a, b in pairs]))
        # 注: "预测留出工况 ID" 在留出协议下不可定义 (该工况不在 bank 的簇空间中),
        # 第二层工况粒度以 reg_recall (第一层) + 修复实验的定向有效性代替 —— 协议文档已说明.
        out[mname] = m
    return out


def main(far=0.05, outfile="main_results.json"):
    import json
    from common import cpath
    from evaluation import gt_pool
    gt_pool.set_far(far)
    units = gt_pool.build_all()
    all_res = {}
    for u in units:
        print(f"\n=== {u.name} (n={len(u.ends)}) ===", flush=True)
        all_res[u.name] = evaluate_unit(u)
        for m, r in all_res[u.name].items():
            if "error" in r:
                print(f"  {m:14s} ERROR {r['error'][:70]}")
            else:
                is_var = isinstance(u.gt_type, str) and u.gt_type == "variable"
                extra = (f"top1={r.get('layer2_top1', -1):.2f} top3={r.get('layer2_top3', -1):.2f}"
                         if is_var else "")
                print(f"  {m:14s} L1-macroF1={r['layer1_macro_f1']:.3f} "
                      f"(oracle {r['layer1_oracle_macro_f1']:.3f}) {extra}")
    with open(cpath(outfile), "w", encoding="utf-8") as f:
        json.dump(all_res, f, ensure_ascii=False, indent=1, default=float)
    print("\n结果已写入 _cache/main_results.json")


if __name__ == "__main__":
    main()
