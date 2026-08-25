"""验证重打分适配层能复现第6篇缓存分数 (注入协议的合法性前提)."""
import os
import sys

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_raw, get_scores, split_of, AVAILABILITY  # noqa: E402
import scorers_rescore as rs  # noqa: E402


def check(scorer, dataset, n=2000):
    cached = get_scores(scorer, dataset)
    if cached is None:
        print(f"[{scorer},{dataset}] 无缓存, 跳过")
        return
    s_cache, _ = cached
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    # 缓存分数 i ↔ 全流窗尾 b + WINDOW - 1 + i
    rng = np.random.default_rng(0)
    ci = rng.choice(np.arange(100, len(s_cache) - 100), size=n, replace=False)
    ends = b + rs.__dict__.get("WINDOW", 16) - 1 + ci if False else b + 16 - 1 + ci
    s_new = rs.rescore(scorer, dataset, X, ends)
    # 符号对齐 (cmhmil 缓存可能被 auto_flip 过)
    flip = 1.0 if np.corrcoef(s_cache[ci], s_new)[0, 1] > 0 else -1.0
    s_new = flip * s_new
    rho = spearmanr(s_cache[ci], s_new).statistic
    mae = np.abs(s_cache[ci] - s_new).mean()
    print(f"[{scorer},{dataset}] spearman={rho:.4f} MAE={mae:.4g} "
          f"cache_std={s_cache.std():.3g} flip={flip}")


if __name__ == "__main__":
    for scorer in ("iforest", "cmhmil"):
        for ds in ("SWaT", "SMD", "MetroPT3"):
            if AVAILABILITY[(scorer, ds)]:
                try:
                    check(scorer, ds)
                except Exception as e:
                    print(f"[{scorer},{ds}] 失败: {type(e).__name__}: {e}")
