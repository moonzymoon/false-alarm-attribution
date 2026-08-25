"""重打分适配层: 对修改后的数据流重新计算窗口分数 (注入协议的核心依赖).

支持:
  - iforest: 按第6篇 cadms 配方确定性复算 (弱训练段拟合, seed=0), 模型 joblib 落盘;
  - cmhmil: 加载第2篇 checkpoint, CPU torch 前向 (窗口=16, 与缓存同口径);
  - AT: 待验证 (需重建 AT 自身预处理管线), 本阶段标记不可用并如实记录.

一致性验证: rescore 原始流应复现第6篇缓存分数 (见 tests/test_rescore.py).
"""
import os
import sys

import numpy as np

from common import PAPER2_SRC, WINDOW, CACHE_DIR, cpath


# ---------------- iforest ----------------
def _iforest_model(dataset, X, window=WINDOW, seed=0):
    """复算 cadms iforest_scores 的拟合模型 (弱训练段 0~35%). 确定性: random_state=seed."""
    import joblib
    from sklearn.ensemble import IsolationForest
    mdl_path = cpath(f"iforest_model_{dataset}.joblib")
    if os.path.exists(mdl_path):
        return joblib.load(mdl_path)
    a = int(len(X) * 0.35)
    # cadms 配方: featW 用 X[weak_train] 的滑窗 (X[0:a]) — 见第6篇 scorers.iforest_scores
    Nw = a - window + 1
    idx = np.arange(window)[None, :] + np.arange(Nw)[:, None]
    featW = X[0:a][idx].reshape(Nw, -1)
    ifo = IsolationForest(n_estimators=100, contamination="auto",
                          random_state=seed, n_jobs=-1)
    ifo.fit(featW)
    joblib.dump(ifo, mdl_path)
    return ifo


def rescore_iforest(dataset, X, win_idx, window=WINDOW, seed=0):
    """对指定窗尾索引 win_idx (相对全流 X) 计算 iforest 分数. 返回 (len(win_idx),)."""
    ifo = _iforest_model(dataset, X, window, seed)
    feats = make_windows_at(X, win_idx, window)
    return -ifo.decision_function(feats)


# ---------------- cmhmil ----------------
_CKPT = {}  # dataset -> (model, flip)


def _load_cmhmil(dataset, seed=7):
    if dataset in _CKPT:
        return _CKPT[dataset]
    import torch
    if PAPER2_SRC not in sys.path:
        sys.path.append(PAPER2_SRC)
    from models.cmh_mil import CMHMIL
    ckpt_path = rf"D:/0科研/工作1/第2篇SCI/Contrastive_TopK_MIL/results/checkpoints/{dataset}_seed{seed}.pt"
    ckpt = torch.load(ckpt_path, map_location="cpu")
    cfg = ckpt["config"]
    model = CMHMIL(D=cfg["D"], d_embed=cfg.get("d_embed", 24), k=cfg.get("k", 3),
                   channels=tuple(cfg.get("channels", [32, 64])),
                   kernel_size=cfg.get("kernel_size", 3), dropout=cfg.get("dropout", 0.1),
                   use_var_attn=cfg.get("use_var_attn", True), pool=cfg.get("pool", "softmax"))
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    _CKPT[dataset] = (model, False)
    return model, False


def rescore_cmhmil(dataset, X, win_idx, window=WINDOW, seed=7, batch=512):
    """对指定窗尾索引 win_idx 计算 cmhmil 分数 (窗口=16=L_INST, 窗尾对齐)."""
    import torch
    model, _ = _load_cmhmil(dataset, seed)
    wins = make_windows_at(X, win_idx, window)                    # (N, window*D)
    wins = wins.reshape(len(wins), 1, window, -1)                 # (N,1,l,D)
    xt = torch.from_numpy(wins).float()
    sc = []
    with torch.no_grad():
        for i in range(0, len(xt), batch):
            s, _ = model(xt[i:i + batch])
            sc.append(s[:, 0].numpy())
    return np.concatenate(sc)


# ---------------- 工具 ----------------
def make_windows_at(X, win_end_idx, window=WINDOW):
    """给定窗尾索引数组, 取展平窗口 (N, window*D). 窗尾索引 i 对应 X[i-window+1 : i+1]."""
    idx = np.asarray(win_end_idx)[:, None] - (window - 1) + np.arange(window)[None, :]
    return X[idx].reshape(len(idx), -1)


def score_windows(scorer, dataset, W, iforest_model=None, batch=512):
    """对显式窗口数组 W: (N, window, D) 打分 (越大越异常). 注入评估的基础原语.
    iforest_model: 可传入外部训练的 IsolationForest (如工况留出重训版);
    未传时按 (scorer, dataset) 走缓存模型/ checkpoint. AT 经 scorers_at 转发."""
    if scorer == "AT":
        import scorers_at
        return scorers_at.score_windows_at(dataset, W).max(1)
    if scorer in ("ocsvm", "pca"):
        import scorers_extra
        idx = np.arange(W.shape[1])[None, :] + np.arange(W.shape[0])[:, None] * 0  # noop
        # W: (N, window, D) → 直接调用 scorers_extra 的窗口版
        if scorer == "ocsvm":
            from common import load_raw
            X, _ = load_raw(dataset)
            return scorers_extra.score_ocsvm(X, W)
        else:
            from common import load_raw
            X, _ = load_raw(dataset)
            return scorers_extra.score_pca(X, W)
    if scorer == "iforest":
        if iforest_model is None:
            ifo = _iforest_model_cache.get((dataset, "default"))
            if ifo is None:
                X, _ = _load_stream(dataset)
                ifo = _iforest_model(dataset, X)
                _iforest_model_cache[(dataset, "default")] = ifo
        else:
            ifo = iforest_model
        return -ifo.decision_function(W.reshape(len(W), -1))
    if scorer == "cmhmil":
        import torch
        model, _ = _load_cmhmil(dataset)
        flips = _load_flips()
        xt = torch.from_numpy(W.reshape(len(W), 1, W.shape[1], W.shape[2])).float()
        sc = []
        with torch.no_grad():
            for i in range(0, len(xt), batch):
                s, _ = model(xt[i:i + batch])
                sc.append(s[:, 0].numpy())
        return flips.get(dataset, 1.0) * np.concatenate(sc)
    raise NotImplementedError(f"score_windows 暂不支持 {scorer}")


_iforest_model_cache = {}


def _load_stream(dataset):
    from common import load_raw
    return load_raw(dataset)


def _load_flips():
    import json
    fpath = cpath("cmhmil_flip.json")
    return json.load(open(fpath)) if os.path.exists(fpath) else {}


def rescore(scorer, dataset, X, win_idx, **kw):
    """统一入口: 修改后的流 X 上, 对窗尾索引 win_idx 重打分. 分数方向与缓存一致(越大越异常)."""
    if scorer == "iforest":
        s = rescore_iforest(dataset, X, win_idx, **kw)
    elif scorer == "cmhmil":
        s = rescore_cmhmil(dataset, X, win_idx, **kw)
    else:
        raise NotImplementedError(f"重打分暂不支持 {scorer} (AT 待验证)")
    # 与缓存方向对齐: iforest 本身无翻转; cmhmil 缓存可能被 auto_flip 过, 调用方负责对齐符号
    return s


# ---------------- 缓存方向对齐 ----------------
def aligned_rescore(scorer, dataset, X, win_idx, **kw):
    """rescore + 与第6篇缓存分数方向对齐 (cmhmil 的 auto_flip 因子从缓存学习并持久化)."""
    if scorer != "cmhmil":
        return rescore(scorer, dataset, X, win_idx, **kw)
    import json
    from common import get_scores, split_of
    fpath = cpath("cmhmil_flip.json")
    flips = json.load(open(fpath)) if os.path.exists(fpath) else {}
    if dataset not in flips:
        cached = get_scores("cmhmil", dataset)
        assert cached is not None, f"cmhmil/{dataset} 无缓存, 无法学习翻转方向"
        s_cache, _ = cached
        _, b = split_of(len(X))
        probe = np.arange(100, min(1100, len(s_cache)))
        s_new = rescore_cmhmil(dataset, X, b + WINDOW - 1 + probe, **kw)
        corr = np.corrcoef(s_cache[probe], s_new)[0, 1]
        flips[dataset] = -1.0 if corr < 0 else 1.0
        json.dump(flips, open(fpath, "w"))
    sign = flips[dataset]
    return sign * rescore_cmhmil(dataset, X, win_idx, **kw)
