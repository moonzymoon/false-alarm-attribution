"""真值实例池 (评估单元) 构建: 误报归因主实验的统一数据接口.

评估单元 EvalUnit:
  - 变量级单元 (scorer, dataset): 打分器=原打分器, τ=fa 缓存阈值(FAR5%),
    实例=注入段内成为 FA 的窗口 (真值=注入变量集/故障类型);
  - 工况级单元 (dataset, regime k): 打分器=剔除 regime k 重训的 iforest,
    实例=测试段属 regime k 且超 τ_k 的全窗正常窗 (真值=regime(k));
  - 每单元内实例按试验奇偶 50/50 分 val(标定 γ/δ)/test;
  - pool_ends: 该打分器训练分布内的正常窗池 (工况级单元剔除 regime k),
    供各方法拟合 (全局统计/UMAP/AE/GMM 工况池).
有效 regime 选取规则 (GoNoGo 文档固定): 测试窗>=200 且 FA>=50, 只用协议内部信息.
"""
import os
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW, load_raw, split_of, cpath  # noqa: E402
from injection.inject import (SEG_LEN, active_channels,  # noqa: E402
                              apply_variable_fault, eval_injected,
                              sample_normal_segments)
import scorers_rescore as rs  # noqa: E402
from regimes.regimes import RegimeModel, features_at  # noqa: E402

FAR = 0.05  # 主实验 FAR 位 (GoNoGo 条件1)


def set_far(t):
    """切换全局 FAR 目标位 (0.05 主实验 / 0.01 鲁棒性附录)."""
    global FAR
    FAR = t
_MIX_CTX = {}   # 数据集 -> (tn, reg_test, tr_ends, reg_tr) 供修复实验复用
VAR_CONFIGS = [("drift", 0.1), ("drift", 0.2), ("stuck", 1.0), ("var", 5.0)]
N_TRIALS = 12
MAX_FA_PER_TRIAL = 15
POOL_MAX = 60000


class EvalUnit:
    def __init__(self, name, scorer, dataset, tau, iforest_model, X,
                 ends, gt_type, gt_vars, gt_kind, gt_regime, val_mask, pool_ends,
                 W_store=None):
        self.name, self.scorer, self.dataset, self.tau = name, scorer, dataset, tau
        self.iforest_model = iforest_model
        self.X = X
        self.ends, self.gt_type = ends, gt_type
        self.gt_vars, self.gt_kind, self.gt_regime = gt_vars, gt_kind, gt_regime
        self.val_mask, self.pool_ends = val_mask, pool_ends
        self.W_store = W_store        # 变量型实例的窗口取自注入后的流 (不能从 X 重建!)

    def windows(self, idx=None):
        if self.W_store is not None:
            return self.W_store if idx is None else self.W_store[idx]
        w = getattr(self, "window_len", WINDOW)
        e = self.ends if idx is None else self.ends[idx]
        i = e[:, None] - (w - 1) + np.arange(w)[None, :]
        return self.X[i]                       # (N, w, D)

    def score(self, W):
        if self.scorer == "AT":
            import scorers_at
            return scorers_at.score_windows_at(self.dataset, W).max(1)
        return rs.score_windows(self.scorer, self.dataset, W,
                                iforest_model=self.iforest_model)

    def pool_windows(self):
        w = getattr(self, "window_len", WINDOW)
        i = self.pool_ends[:, None] - (w - 1) + np.arange(w)[None, :]
        return self.X[i]


def _variable_unit(scorer, dataset):
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    d = np.load(cpath(f"fa_{scorer}_{dataset}_far{int(FAR*100)}.npz"))
    tau = float(d["tau"])
    mu, sigma = X[a:b].mean(0), X[a:b].std(0) + 1e-8
    active = active_channels(X, a, b)
    rng = np.random.default_rng(7)
    ends_all, vars_all, kind_all, trial_all, wins_all = [], [], [], [], []
    trial_id = 0
    for kind, st in VAR_CONFIGS:
        starts = sample_normal_segments(Y, b, SEG_LEN, N_TRIALS,
                                        seed=zlib.crc32(repr((kind, st)).encode()) & 0x7fffffff)
        for s in starts:
            j = int(rng.choice(active))
            Xm, gt = apply_variable_fault(X, s, SEG_LEN, [j], kind, st, mu, sigma)
            ev = eval_injected(scorer, dataset, X, Xm, s, SEG_LEN, tau)
            # 关键: 只收"注入致因"的 FA (注入前<=τ), 排除天然超高窗的混杂
            fa = np.where((ev["scores_after"] > tau) & (ev["scores_before"] <= tau))[0]
            if len(fa) == 0:
                trial_id += 1
                continue
            pick = rng.choice(fa, size=min(MAX_FA_PER_TRIAL, len(fa)), replace=False)
            ends_all.extend(ev["ends"][pick])
            vars_all.extend([[j]] * len(pick))
            kind_all.extend([kind] * len(pick))
            trial_all.extend([trial_id] * len(pick))
            wins_all.append(wins_at_np(Xm, ev["ends"][pick]))
            trial_id += 1
    # 联合漂移 (2 变量)
    starts = sample_normal_segments(Y, b, SEG_LEN, N_TRIALS, seed=1234)
    for s in starts:
        js = rng.choice(active, size=2, replace=False)
        Xm = X.copy()
        t = np.arange(SEG_LEN)
        for j in js:
            Xm[s:s + SEG_LEN, j] += float(rng.choice((0.1, 0.2))) * sigma[j] * t
        ev = eval_injected(scorer, dataset, X, Xm, s, SEG_LEN, tau)
        fa = np.where((ev["scores_after"] > tau) & (ev["scores_before"] <= tau))[0]
        if len(fa):
            pick = rng.choice(fa, size=min(MAX_FA_PER_TRIAL, len(fa)), replace=False)
            ends_all.extend(ev["ends"][pick])
            vars_all.extend([[int(v) for v in js]] * len(pick))
            kind_all.extend(["joint_drift"] * len(pick))
            trial_all.extend([trial_id] * len(pick))
            wins_all.append(wins_at_np(Xm, ev["ends"][pick]))
        trial_id += 1
    ends = np.array(ends_all, int)
    gt_vars = vars_all
    gt_kind = kind_all
    trials = np.array(trial_all)
    val_mask = trials % 2 == 0
    W_store = np.concatenate(wins_all, 0) if wins_all else None
    pool_ends = np.arange(a + WINDOW - 1, b)
    if len(pool_ends) > POOL_MAX:
        pool_ends = pool_ends[np.random.default_rng(0).choice(
            len(pool_ends), POOL_MAX, replace=False)]
    return EvalUnit(f"{scorer}_{dataset}_var", scorer, dataset, tau, None, X,
                    ends, np.array(["variable"] * len(ends)), gt_vars, gt_kind,
                    np.full(len(ends), -1), val_mask, np.sort(pool_ends),
                    W_store=W_store)


def _regime_units(dataset):
    """返回该数据集的全部有效工况级单元 (重训 iforest)."""
    from sklearn.ensemble import IsolationForest
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    rm = RegimeModel().fit(X, seed=0)
    K = rm.K

    def regime_of(ends):
        out = np.empty(len(ends), np.int32)
        for i in range(0, len(ends), 200_000):
            e = ends[i:i + 200_000]
            out[i:i + 200_000] = rm.transform(features_at(X, e))
        return out

    cs = np.cumsum(np.concatenate([[0], (Y != 0).astype(np.int64)]))
    test_ends = np.arange(b + WINDOW - 1, len(X))
    body_ok = (cs[test_ends + 1] - cs[test_ends + 1 - WINDOW]) == 0
    tn = test_ends[body_ok]
    reg_test = regime_of(tn)
    tr_ends = np.arange(a + WINDOW - 1, b)
    reg_tr = regime_of(tr_ends)

    units = []
    for k in range(K):
        fit_ends = tr_ends[reg_tr != k]
        rng = np.random.default_rng(0)
        if len(fit_ends) > 200_000:
            fit_ends = fit_ends[np.sort(rng.choice(len(fit_ends), 200_000, replace=False))]
        idx = np.arange(WINDOW)[None, :] + (fit_ends[:, None] - (WINDOW - 1))
        feats = X[idx].reshape(len(fit_ends), -1)
        ifo = IsolationForest(n_estimators=100, contamination="auto",
                              random_state=0, n_jobs=-1).fit(feats)
        cal_ends = tr_ends[reg_tr != k]
        tau = float(np.quantile(-ifo.decision_function(
            X[np.arange(WINDOW)[None, :] + (cal_ends[:, None] - (WINDOW - 1))].reshape(len(cal_ends), -1)),
            1 - FAR))
        mask_k = reg_test == k
        sk = -ifo.decision_function(
            X[np.arange(WINDOW)[None, :] + (tn[mask_k][:, None] - (WINDOW - 1))].reshape(mask_k.sum(), -1))
        fa_local = sk > tau
        n_win, n_fa = int(mask_k.sum()), int(fa_local.sum())
        if n_win < 200 or n_fa < 50:      # 有效 regime 选取规则 (GoNoGo 固定)
            continue
        ends = tn[mask_k][fa_local]
        rng2 = np.random.default_rng(1)
        if len(ends) > 600:
            ends = ends[np.sort(rng2.choice(len(ends), 600, replace=False))]
        val_mask = rng2.random(len(ends)) < 0.5
        pool_ends = np.sort(fit_ends)
        if len(pool_ends) > POOL_MAX:
            pool_ends = pool_ends[np.sort(rng2.choice(len(pool_ends), POOL_MAX, replace=False))]
        units.append(EvalUnit(f"iforest_{dataset}_regime{k}", "iforest", dataset, tau, ifo, X,
                              ends, "regime",
                              [None] * len(ends), ["regime_holdout"] * len(ends), k,
                              val_mask, pool_ends))
    return units


def _mixed_unit(dataset):
    """混合单元 (主实验): 留出 regime k 重训 iforest 后,
    工况型实例 = 留出 regime 的 FA 窗; 变量型实例 = 同模型同阈值下注入故障的 FA 窗.
    两类真值共享同一打分器与阈值, 第一层二分类才公平. cmhmil 不可重训,
    其变量级单元单独保留 (只进第二层)."""
    from sklearn.ensemble import IsolationForest
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    rm = RegimeModel().fit(X, seed=0)
    K = rm.K

    def regime_of(ends):
        out = np.empty(len(ends), np.int32)
        for i in range(0, len(ends), 200_000):
            e = ends[i:i + 200_000]
            out[i:i + 200_000] = rm.transform(features_at(X, e))
        return out

    def wins_at(e):
        return X[e[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]

    cs = np.cumsum(np.concatenate([[0], (Y != 0).astype(np.int64)]))
    test_ends = np.arange(b + WINDOW - 1, len(X))
    body_ok = (cs[test_ends + 1] - cs[test_ends + 1 - WINDOW]) == 0
    tn = test_ends[body_ok]
    reg_test = regime_of(tn)
    tr_ends = np.arange(a + WINDOW - 1, b)
    reg_tr = regime_of(tr_ends)

    mu, sigma = X[a:b].mean(0), X[a:b].std(0) + 1e-8
    active = active_channels(X, a, b)
    rng = np.random.default_rng(7)

    units = []
    _MIX_CTX[dataset] = dict(tn=tn, reg_test=reg_test, tr_ends=tr_ends, reg_tr=reg_tr)
    for k in range(K):
        fit_ends = tr_ends[reg_tr != k]
        if len(fit_ends) > 200_000:
            fit_ends = fit_ends[np.sort(np.random.default_rng(0).choice(
                len(fit_ends), 200_000, replace=False))]
        idx = np.arange(WINDOW)[None, :] + (fit_ends[:, None] - (WINDOW - 1))
        feats = X[idx].reshape(len(fit_ends), -1)
        ifo = IsolationForest(n_estimators=100, contamination="auto",
                              random_state=0, n_jobs=-1).fit(feats)
        cal_ends = tr_ends[reg_tr != k]
        cw = X[cal_ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]].reshape(len(cal_ends), -1)
        tau = float(np.quantile(-ifo.decision_function(cw), 1 - FAR))
        mask_k = reg_test == k
        if mask_k.sum() == 0:
            continue
        sk = -ifo.decision_function(wins_at(tn[mask_k]).reshape(int(mask_k.sum()), -1))
        fa_local = sk > tau
        if int(mask_k.sum()) < 200 or int(fa_local.sum()) < 50:
            continue
        # 工况型实例
        r_ends = tn[mask_k][fa_local]
        rng2 = np.random.default_rng(1)
        if len(r_ends) > 400:
            r_ends = r_ends[np.sort(rng2.choice(len(r_ends), 400, replace=False))]
        # 变量型实例: 同模型注入
        v_ends, v_vars, v_kind, v_trial, v_wins = [], [], [], [], []
        trial_id = 0
        for kind, st in VAR_CONFIGS + [("joint", 0)]:
            n_tr = N_TRIALS if kind != "joint" else N_TRIALS // 2
            starts = sample_normal_segments(Y, b, SEG_LEN, n_tr,
                                            seed=zlib.crc32(repr((kind, st, k)).encode()) & 0x7fffffff)
            for s in starts:
                if kind == "joint":
                    js = rng.choice(active, size=2, replace=False)
                    Xm = X.copy()
                    t = np.arange(SEG_LEN)
                    for j in js:
                        Xm[s:s + SEG_LEN, j] += 0.15 * sigma[j] * t
                    gtv = [int(v) for v in js]
                    gk = "joint_drift"
                else:
                    j = int(rng.choice(active))
                    Xm, gt = apply_variable_fault(X, s, SEG_LEN, [j], kind, st, mu, sigma)
                    gtv, gk = gt["cause_vars"], kind
                ends = np.arange(s + WINDOW - 1, s + SEG_LEN)
                Wm = wins_at_np(Xm, ends)
                s_after = rs.score_windows("iforest", dataset, Wm, iforest_model=ifo)
                s_before = rs.score_windows("iforest", dataset, wins_at_np(X, ends),
                                            iforest_model=ifo)
                fa = np.where((s_after > tau) & (s_before <= tau))[0]
                if len(fa):
                    pick = rng.choice(fa, size=min(MAX_FA_PER_TRIAL, len(fa)), replace=False)
                    v_ends.extend(ends[pick]); v_vars.extend([gtv] * len(pick))
                    v_kind.extend([gk] * len(pick)); v_trial.extend([trial_id] * len(pick))
                    v_wins.append(Wm[pick])
                trial_id += 1
        ends = np.concatenate([r_ends, np.array(v_ends, int)])
        gt_type = np.array(["regime"] * len(r_ends) + ["variable"] * len(v_ends))
        gt_vars = [None] * len(r_ends) + v_vars
        gt_kind = ["regime_holdout"] * len(r_ends) + v_kind
        gt_regime = np.array([k] * len(ends))
        trials = np.array([0] * len(r_ends) + v_trial)
        val_mask = trials % 2 == 0
        if len(r_ends):
            val_mask[:len(r_ends)] = rng2.random(len(r_ends)) < 0.5
        W_store = (np.concatenate(
            [wins_at_np(X, r_ends)] + ([np.concatenate(v_wins, 0)] if v_wins else []), 0)
            if (len(r_ends) or v_wins) else None)
        pool_ends = np.sort(fit_ends)
        if len(pool_ends) > POOL_MAX:
            pool_ends = pool_ends[np.sort(rng2.choice(len(pool_ends), POOL_MAX, replace=False))]
        units.append(EvalUnit(f"iforest_{dataset}_mix_regime{k}", "iforest", dataset,
                              tau, ifo, X, ends, gt_type, gt_vars, gt_kind,
                              gt_regime, val_mask, pool_ends, W_store=W_store))
    return units


def wins_at_np(Xm, ends):
    return Xm[np.asarray(ends)[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]


def _variable_unit_at(dataset, n_trials=20, max_fa=8):
    """AT 变量级单元 (R3 残余项1): 注入在 AT 自有测试流 (原始未缩放) 上进行,
    窗口=100 (AT win_size), 窗口分数 = 该窗 100 个时间步分数的 max (部署语义:
    窗内任一点超阈即告警). 阈值取 fa 缓存的逐点 τ. 重打分与缓存 spearman: SWaT
    1.000 / SMD 0.99 (见 scorers_at.verify)."""
    import scorers_at
    a = scorers_at._load(dataset)
    X = a["te"].astype(np.float32)
    Y = a["y"].astype(np.int8)
    # 窗口级阈值: AT 校准段 (前半流) 的非重叠 100 点块均值的 95 分位
    # (逐点 τ 不适用于窗聚合分数: max-of-100 对逐点 95 分位几乎必然超阈)
    s_all = np.load(os.path.join(
        __import__("common").AT_ROOT, "checkpoints", f"{dataset}_scores.npz"),
        allow_pickle=True)["scores"]
    n_blocks = len(s_all) // 100
    block_means = s_all[:n_blocks * 100].reshape(n_blocks, 100).mean(1)
    tau = float(np.quantile(block_means[:n_blocks // 2], 1 - FAR))
    mu, sigma = a["mu"], a["sd"]
    active = np.where(a["tr"].std(0) > 0.05)[0]
    rng = np.random.default_rng(7)
    b = len(X) // 2
    W100 = 100

    def at_score(W_raw):
        return scorers_at.score_windows_at(dataset, W_raw).mean(1)   # 窗均值 (与窗级 τ 配套)

    ends_all, vars_all, kind_all, trial_all, wins_all = [], [], [], [], []
    trial_id = 0
    _AT_CFG = VAR_CONFIGS + [("drift", 0.05), ("var", 2.0)]
    for kind, st in _AT_CFG:
        starts = sample_normal_segments(
            Y, b, SEG_LEN, n_trials,
            seed=zlib.crc32(repr(("at", kind, st)).encode()) & 0x7fffffff)
        for s in starts:
            j = int(rng.choice(active))
            Xm, gt = apply_variable_fault(X, s, SEG_LEN, [j], kind, st, mu, sigma)
            ends = np.arange(s + W100 - 1, s + SEG_LEN)
            Wm = Xm[ends[:, None] - (W100 - 1) + np.arange(W100)[None, :]]
            s_after = at_score(Wm)
            s_before = at_score(X[ends[:, None] - (W100 - 1) + np.arange(W100)[None, :]])
            fa = np.where((s_after > tau) & (s_before <= tau))[0]
            if len(fa):
                pick = rng.choice(fa, size=min(max_fa, len(fa)), replace=False)
                ends_all.extend(ends[pick])
                vars_all.extend([[j]] * len(pick))
                kind_all.extend([kind] * len(pick))
                trial_all.extend([trial_id] * len(pick))
                wins_all.append(Wm[pick])
            trial_id += 1
    if not ends_all:
        return None
    ends = np.array(ends_all, int)
    trials = np.array(trial_all)
    rng2 = np.random.default_rng(0)
    pool_starts = rng2.integers(0, len(a["tr"]) - W100, size=20000)
    pool_ends = pool_starts + W100 - 1
    u = EvalUnit(f"AT_{dataset}_var", "AT", dataset, tau, None,
                 X, ends, np.array(["variable"] * len(ends)), vars_all, kind_all,
                 np.full(len(ends), -1), trials % 2 == 0, pool_ends,
                 W_store=np.concatenate(wins_all, 0))
    u.window_len = W100
    tr_stream = a["tr"].astype(np.float32)

    def _at_pool_windows():
        i = pool_ends[:, None] - (W100 - 1) + np.arange(W100)[None, :]
        return tr_stream[i]
    u.pool_windows = _at_pool_windows
    return u


def build_all():
    units = []
    for ds in ("SWaT", "SMD", "MetroPT3", "PSM", "SMAP"):
        print(f"[gt_pool] 混合单元 {ds} ...", flush=True)
        try:
            us = _mixed_unit(ds)
            for u in us:
                nv = int((u.gt_type == "variable").sum())
                nr = int((u.gt_type == "regime").sum())
                print(f"  {u.name}: n={len(u.ends)} (var {nv} / reg {nr}) "
                      f"val={int(u.val_mask.sum())}", flush=True)
            units.extend(us)
        except Exception as e:
            import traceback; traceback.print_exc()
    for scorer in ("cmhmil", "AT"):
        for ds in ("SWaT", "SMD"):
            print(f"[gt_pool] 变量级单元 {scorer}×{ds} ...", flush=True)
            try:
                u = _variable_unit_at(ds) if scorer == "AT" else _variable_unit(scorer, ds)
                if u is not None:
                    print(f"  实例 {len(u.ends)} (val {int(u.val_mask.sum())})", flush=True)
                    if len(u.ends) >= 30:
                        units.append(u)
            except Exception as e:
                import traceback; traceback.print_exc()
    return units


if __name__ == "__main__":
    us = build_all()
    print(f"\n共 {len(us)} 个评估单元:")
    for u in us:
        print(f"  {u.name}: n={len(u.ends)} val={int(u.val_mask.sum())} "
              f"pool={len(u.pool_ends)} tau={u.tau:.4g}")
