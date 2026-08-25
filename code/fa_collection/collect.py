"""误报收集管线 (阶段1 任务1).

协议:
  - 阈值: 校准段 (35%~50%) 正常窗口分数的 (1-target) 分位, FAR 目标位 {1%, 5%};
  - 误报: 测试段 (50%~100%) 中 分数>阈值 且 窗尾标签正常 的窗口;
  - 窗口=16, 窗尾对齐 (与第6篇 cadms 三打分器一致);
  - 分数来源: 第6篇缓存优先; (iforest, MetroPT3) 无缓存, 本地复算并落盘第10篇缓存;
  - AT 无重打分能力: 用其落盘流自身, 前半段正常窗口定阈, 后半段收 FA (偏差如实记录);
  - 连续窗口合并为事件 (gap<=merge_gap).

缓存: _cache/fa_{scorer}_{dataset}_far{5|1}.npz
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (CACHE_DIR, FAR_TARGETS, WINDOW, get_scores,  # noqa: E402
                    load_raw, split_of, cpath)
import scorers_rescore as rs  # noqa: E402


def _chunked(fn, X, ends, chunk=100_000):
    out = []
    for i in range(0, len(ends), chunk):
        out.append(fn(X, ends[i:i + chunk]))
    return np.concatenate(out)


def calib_test_scores(scorer, dataset, X=None, Y=None, force=False):
    """返回 (calib_win_ends, calib_scores, test_win_ends, test_scores, test_labels).
    统一入口: 校准段分数本地复算 (缓存只有测试段); 测试段分数优先用第6篇缓存."""
    tag = f"scores_{scorer}_{dataset}"
    npz = cpath(tag + ".npz")
    if os.path.exists(npz) and not force:
        d = np.load(npz)
        return (d["calib_ends"], d["calib_scores"], d["test_ends"],
                d["test_scores"], d["test_labels"], d["calib_labels"])
    if X is None:
        X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    if scorer == "AT":
        cached = get_scores("AT", dataset)
        assert cached is not None
        s_all, y_all = cached
        # AT 自身流: 前半段正常窗口定阈, 后半段收 FA. 窗口=20 (AT win_size), 窗尾对齐.
        W = 20
        half = len(s_all) // 2
        calib_ends = np.arange(W - 1, half)
        test_ends = np.arange(half, len(s_all))
        calib_scores = s_all[calib_ends]
        calib_labels = y_all[calib_ends]
        test_scores = s_all[test_ends]
        test_labels = y_all[test_ends]
    else:
        calib_ends = np.arange(a + WINDOW - 1, b)
        fn = (lambda Xx, ee: rs.aligned_rescore(scorer, dataset, Xx, ee)) if scorer == "cmhmil" \
            else (lambda Xx, ee: rs.rescore_iforest(dataset, Xx, ee))
        calib_scores = _chunked(fn, X, calib_ends)
        calib_labels = Y[calib_ends]  # 按构造全 0 (异常段拼接在后), 仍显式过滤
        cached = get_scores(scorer, dataset)
        if cached is not None:
            test_scores, test_labels = cached
            test_ends = b + WINDOW - 1 + np.arange(len(test_scores))
        else:  # (iforest, MetroPT3): 本地复算测试段
            test_ends = np.arange(b + WINDOW - 1, len(X))
            test_scores = _chunked(fn, X, test_ends)
            test_labels = Y[test_ends]
    np.savez_compressed(npz, calib_ends=calib_ends, calib_scores=calib_scores,
                        test_ends=test_ends, test_scores=test_scores,
                        test_labels=test_labels, calib_labels=calib_labels)
    return calib_ends, calib_scores, test_ends, test_scores, test_labels, calib_labels


def collect_fa(scorer, dataset, merge_gap=5, force=False):
    """主入口: 对一个 (scorer, dataset) 收集两个 FAR 目标位的全部误报. 返回统计 dict.
    误报定义: 窗口全部点标签正常 (全窗正常, 防止窗体含攻击点被误计) 且 分数>阈值."""
    calib_ends, calib_scores, test_ends, test_scores, test_labels, calib_labels = \
        calib_test_scores(scorer, dataset, force=force)
    calib_normal = calib_scores[calib_labels == 0]
    res = {"scorer": scorer, "dataset": dataset}
    for target in FAR_TARGETS:
        tau = np.quantile(calib_normal, 1 - target)
        normal_mask = test_labels == 0
        if scorer != "AT":
            X, Y = load_raw(dataset)
            cs = np.cumsum(np.concatenate([[0], (Y != 0).astype(np.int64)]))
            w = WINDOW
            body_bad = cs[test_ends + 1] - cs[test_ends + 1 - w]
            normal_mask = normal_mask & (body_bad == 0)
        fa_mask = normal_mask & (test_scores > tau)
        fa_idx = test_ends[fa_mask]
        fa_scores = test_scores[fa_mask]
        # 连续合并为事件 (允许间隔 <= merge_gap)
        events = []
        if len(fa_idx):
            brk = np.where(np.diff(fa_idx) > merge_gap)[0] + 1
            segs = np.split(np.arange(len(fa_idx)), brk)
            events = [(int(fa_idx[s[0]]), int(fa_idx[s[-1]]), len(s)) for s in segs]
        np.savez_compressed(
            cpath(f"fa_{scorer}_{dataset}_far{int(target*100)}.npz"),
            tau=float(tau), fa_idx=fa_idx, fa_scores=fa_scores,
            n_normal_test=int(normal_mask.sum()),
            realized_far=float(fa_mask.sum() / max(normal_mask.sum(), 1)))
        res[target] = {
            "tau": float(tau), "n_fa_windows": int(fa_mask.sum()),
            "realized_far": float(fa_mask.sum() / max(normal_mask.sum(), 1)),
            "n_events": len(events), "events": events,
        }
    return res


def collect_all():
    from common import AVAILABILITY
    all_res = {}
    for (scorer, ds), ok in AVAILABILITY.items():
        if not ok:
            print(f"[{scorer},{ds}] 不可用 (无缓存/checkpoint), 跳过")
            continue
        print(f"[{scorer},{ds}] 收集误报 ...")
        try:
            r = collect_fa(scorer, ds)
            all_res[(scorer, ds)] = r
            for tgt in FAR_TARGETS:
                v = r[tgt]
                print(f"  FAR {tgt:.0%}: tau={v['tau']:.4g} FA窗={v['n_fa_windows']} "
                      f"实际FAR={v['realized_far']:.2%} 事件={v['n_events']}")
        except Exception as e:
            print(f"  失败: {type(e).__name__}: {e}")
            all_res[(scorer, ds)] = {"error": f"{type(e).__name__}: {e}"}
    return all_res


if __name__ == "__main__":
    collect_all()
