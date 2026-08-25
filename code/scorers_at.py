"""AT (Anomaly-Transformer) 重打分适配器 — R3 残余项 1.

复刻其 solver.test 的打分: StandardScaler(训练集拟合) -> win_size=100 非重叠窗 ->
metric = softmax(-(series_loss+prior_loss)) * MSE(input, output) (逐时间步).
验证口径: 对原始测试窗重算, 与 checkpoints/{ds}_scores.npz 的 spearman 应≈1.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import AT_ROOT  # noqa: E402

AT_WIN = 100
_AT = {}


def _load(dataset):
    if dataset in _AT:
        return _AT[dataset]
    import torch
    if AT_ROOT not in sys.path:
        sys.path.insert(0, AT_ROOT)
    from model.AnomalyTransformer import AnomalyTransformer
    from solver import my_kl_loss
    import torch.nn as nn
    tr = np.load(os.path.join(AT_ROOT, "dataset", dataset, f"{dataset}_train.npy"))
    te = np.load(os.path.join(AT_ROOT, "dataset", dataset, f"{dataset}_test.npy"))
    y = np.load(os.path.join(AT_ROOT, "dataset", dataset, f"{dataset}_test_label.npy")).reshape(-1)
    mu, sd = tr.mean(0), tr.std(0) + 1e-8
    ckpt = torch.load(os.path.join(AT_ROOT, "checkpoints", f"{dataset}_checkpoint.pth"),
                      map_location="cpu")
    D = tr.shape[1]
    model = AnomalyTransformer(win_size=AT_WIN, enc_in=D, c_out=D, e_layers=3)
    model.load_state_dict(ckpt)
    model.eval()
    _AT[dataset] = dict(tr=tr, te=te, y=y, mu=mu, sd=sd, model=model,
                        kl=my_kl_loss, mse=nn.MSELoss(reduction="none"))
    return _AT[dataset]


def score_windows_at(dataset, W_raw, batch=256, temperature=50):
    """W_raw: (N, w, D) 未缩放窗口 (w 需=100 或会被补齐到 100 的任意窗, 仅支持 100).
    返回 (N, w) 逐时间步分数 (与 AT 落盘分数同口径)."""
    import torch
    a = _load(dataset)
    assert W_raw.shape[1] == AT_WIN, f"AT 窗长须为 {AT_WIN}"
    Ws = (W_raw - a["mu"]) / a["sd"]
    out = []
    with torch.no_grad():
        for i in range(0, len(Ws), batch):
            x = torch.from_numpy(Ws[i:i + batch]).float()
            o, series, prior, _ = a["model"](x)
            loss = torch.mean(a["mse"](x, o), dim=-1)
            sl = pl = None
            for u in range(len(prior)):
                p = prior[u] / torch.unsqueeze(torch.sum(prior[u], dim=-1), dim=-1).repeat(
                    1, 1, 1, AT_WIN)
                s_u = a["kl"](series[u], p.detach()) * temperature
                p_u = a["kl"](p, series[u].detach()) * temperature
                sl = s_u if sl is None else sl + s_u
                pl = p_u if pl is None else pl + p_u
            metric = torch.softmax((-sl - pl), dim=-1)
            out.append((metric * loss).numpy())
    return np.concatenate(out, 0)


def verify(dataset="SWaT", n=20):
    """原始测试块重算 vs 落盘分数 (spearman)."""
    from scipy.stats import spearmanr
    a = _load(dataset)
    cached = np.load(os.path.join(AT_ROOT, "checkpoints", f"{dataset}_scores.npz"),
                     allow_pickle=True)
    s_cache = cached["scores"]
    n_blocks = len(s_cache) // AT_WIN
    rng = np.random.default_rng(0)
    blocks = rng.choice(np.arange(1, n_blocks - 1), size=n, replace=False)
    W = np.stack([a["te"][b * AT_WIN:(b + 1) * AT_WIN] for b in blocks])
    s_new = score_windows_at(dataset, W).reshape(-1)
    s_old = np.concatenate([s_cache[b * AT_WIN:(b + 1) * AT_WIN] for b in blocks])
    rho = spearmanr(s_old, s_new).statistic
    mae = np.abs(s_old - s_new).mean()
    print(f"[AT,{dataset}] spearman={rho:.4f} MAE={mae:.3g} "
          f"(cache std={s_cache.std():.3g})  n_blocks={n_blocks}")
    return rho


if __name__ == "__main__":
    for ds in ("SWaT", "SMD"):
        try:
            verify(ds)
        except Exception as e:
            print(f"[AT,{ds}] 失败: {type(e).__name__}: {e}")
