"""第10篇公共层: 路径 / 数据加载 / 打分器适配 / 划分.

红线: 不 import cadms.conformal / cadms.thresholds (与第3/6篇切割);
      打分器只作误报来源工具复用 (cadms.scorers.get_scorer).
设计: 照搬第9篇 adapter 的"运行时注册 LOADERS"模式, 不改前作文件.
"""
import os
import sys

import numpy as np

# ===== 路径 =====
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
CACHE_DIR = os.path.join(SRC_DIR, "_cache")          # 第10篇自有缓存 (误报/注入/聚类)
PAPER2_SRC = r"D:/0科研/工作1/第2篇SCI/Contrastive_TopK_MIL/src"
PAPER6_SRC = r"D:/0科研/工作1/第6篇SCI/src"
PAPER6_CACHE = r"D:/0科研/工作1/第6篇SCI/src/_score_cache"
PAPER4_SRC = r"D:/0科研/工作1/第4篇SCI/src"
AT_ROOT = r"D:/0科研/工作1/Anomaly-Transformer"
DATA_ROOT = r"D:/0科研/工作1/第2篇SCI/Contrastive_TopK_MIL/datasets"
DFKI_REPO = os.path.join(ROOT_DIR, "extern", "dfki_conditional_attribution")

os.makedirs(CACHE_DIR, exist_ok=True)

SEED = 7
WINDOW = 16          # 与 cadms 三打分器一致 (cmhmil L_INST=16, iforest window=16)
FAR_TARGETS = (0.01, 0.05)

# 主实验矩阵 (AT_MetroPT3 无落盘分数, 第9篇 AVAILABILITY 已核; 如实记录)
DATASETS = ("SWaT", "SMD", "MetroPT3", "PSM", "SMAP")
SCORERS = ("cmhmil", "AT", "iforest")
AVAILABILITY = {
    ("cmhmil", "SWaT"): True, ("AT", "SWaT"): True, ("iforest", "SWaT"): True,
    ("cmhmil", "SMD"): True, ("AT", "SMD"): True, ("iforest", "SMD"): True,
    ("cmhmil", "MetroPT3"): True, ("AT", "MetroPT3"): False, ("iforest", "MetroPT3"): True,
}


# ===== 数据加载 =====
def load_raw(dataset):
    """加载 (X, Y) 原始流 (与打分器缓存同源同预处理). 返回 (X:(T,D) float32, Y:(T,)).
    TE/MetroPT3 通过运行时注册进第2篇 LOADERS, 不改第2篇文件."""
    if PAPER2_SRC not in sys.path:
        sys.path.append(PAPER2_SRC)
    import data.loaders as p2l
    if dataset == "MetroPT3" and "MetroPT3" not in p2l.LOADERS:
        sys.path.insert(0, SRC_DIR)
        from datasets_local.metropt3 import load_metropt3
        p2l.LOADERS["MetroPT3"] = lambda: (lambda d: (d["X"], d["Y"]))(load_metropt3())
    return p2l.load_dataset(dataset)


def split_of(T, weak_train_ratio=0.35, calib_ratio=0.15):
    """35/15/50 时序切分 (第1篇协议, 工具复用). 返回 (a, b): [0,a)弱训练 [a,b)校准 [b,T)测试."""
    a = int(T * weak_train_ratio)
    b = int(T * (weak_train_ratio + calib_ratio))
    return a, b


def make_windows(X, window=WINDOW):
    """滑窗展平 (用于 iforest/特征). X:(T,D) -> (N, window*D), 窗尾对齐索引 i+window-1."""
    N = len(X) - window + 1
    idx = np.arange(window)[None, :] + np.arange(N)[:, None]
    return X[idx].reshape(N, -1)


# ===== 分数获取 (缓存优先) =====
def get_scores(scorer, dataset, seed=SEED):
    """读第6篇 _score_cache 的分数. 返回 (scores, labels) 或 None (无缓存)."""
    name = f"{scorer}_{dataset}" + (f"_seed{seed}" if scorer == "cmhmil" else "")
    npz = os.path.join(PAPER6_CACHE, f"{name}.npz")
    if not os.path.exists(npz):
        return None
    d = np.load(npz)
    return d["scores"].astype(np.float64), d["labels"].astype(np.int8)


def cpath(*parts):
    return os.path.join(CACHE_DIR, *parts)
