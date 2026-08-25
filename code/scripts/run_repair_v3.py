"""T0-1 修复闭环 v3: 强基线 + 多轮收敛 (预投稿实验包, 回应审稿意见 A4).
在 repair_guided2 (v2) 协议上扩展为 六策略 × R=3 轮:
  guided_rc   归因指导 (RC-CA 判 regime 的报警窗; 部署语义同 v2)
  guided_ae   归因指导换方法 (AERec 判 regime; GPU 同构复刻, 固定种子) —— 归因信号跨方法
  unc         不确定性采样 (每轮用当前模型选 |score-tau| 最小的候选窗, 自适应 AL 基线)
  alarm_rand  报警窗随机 (同候选池不选择 —— 隔离"归因选择"与"报警条件"的最强对照)
  target_rand 定向真 regime-k 窗 (v2 targeted, 上界参照)
  other_rand  其他 regime 窗 (v2 random)
纪律: tau 固定基础模型校准阈值; iforest random_state=0; 预算 B=0.10*|pool| 分 3 轮;
guided_*/target/other 第 0 轮一次性定序; unc 每轮自适应重选; 评测集 >60k 时 rng(5) 子样.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW, load_raw, split_of, cpath  # noqa: E402
from rcca.rcca import _RegimeBank, rcca_attribute  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402
import evaluation.gt_pool as gp  # noqa: E402

R = 3
EVAL_CAP = 60000


def ae_verdicts(u, W, bank):
    """AERec 同构复刻 (two_layer.ae_recon_attribute 结构), GPU + 固定种子 (原实现无种子)."""
    import torch
    import torch.nn as nn
    torch.manual_seed(0)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    P = bank.P
    D = P.shape[2]
    net = nn.Sequential(nn.Flatten(), nn.Linear(P.shape[1] * D, 128), nn.ReLU(),
                        nn.Linear(128, 32), nn.ReLU(), nn.Linear(32, P.shape[1] * D)).to(dev)
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    Xt = torch.from_numpy(P.reshape(len(P), -1)).float().to(dev)
    gcpu = torch.Generator().manual_seed(0)
    for _ in range(30):
        perm = torch.randperm(len(Xt), generator=gcpu)[:50000].to(dev)
        xb = Xt[perm]
        loss = nn.functional.mse_loss(net(xb), xb)
        opt.zero_grad()
        loss.backward()
        opt.step()
    net.eval()
    with torch.no_grad():
        rec = net(torch.from_numpy(W.reshape(len(W), -1)).float().to(dev)).cpu().numpy()
    err = np.abs(rec.reshape(W.shape) - W).mean(1)
    conf = err.max(1) / (err.sum(1) + 1e-9)
    return {"phi": err, "conf": conf, "delta": None, "regime": None}


def flagged_of(u, W, bank, attr_fn):
    """返回 (test 段被判 regime 的 ends, 对应 gt_type 是否真 regime)."""
    attr = attr_fn(u, W, bank)
    y = (u.gt_type == "variable").astype(int)
    g, d = tl.calibrate(tl._sub(attr, u.val_mask), y[u.val_mask])
    pred = tl._predict(attr, g, d)
    m = (~u.val_mask) & (pred == 0)
    return u.ends[m], (u.gt_type[m] == "regime")


def main():
    from sklearn.ensemble import IsolationForest
    rows = []
    for ds in ("SWaT", "SMD", "MetroPT3"):
        print(f"[{ds}] 重建混合单元 ...", flush=True)
        units = gp._mixed_unit(ds)
        ctx = gp._MIX_CTX[ds]
        tn, reg_test = ctx["tn"], ctx["reg_test"]
        X, Y = load_raw(ds)
        a, b = split_of(len(X))

        def wins(e):
            return e[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]

        for u in units:
            k = int(u.gt_regime[0])
            tau_fixed = u.tau
            pool = u.pool_ends
            feats_pool = X[wins(pool)].reshape(len(pool), -1)
            eval_ends = tn[reg_test == k]
            if len(eval_ends) > EVAL_CAP:
                eval_ends = eval_ends[np.sort(np.random.default_rng(5).choice(
                    len(eval_ends), EVAL_CAP, replace=False))]
            ew = X[wins(eval_ends)].reshape(len(eval_ends), -1)
            rng = np.random.default_rng(11)
            B = int(len(pool) * 0.10)
            per_round = max(1, B // R)

            bank = _RegimeBank(u.pool_windows(), seed=0)
            W = u.windows()
            test_m = ~u.val_mask
            fl_rc, fl_rc_gt = flagged_of(u, W, bank, rcca_attribute)
            fl_ae, fl_ae_gt = flagged_of(u, W, bank, ae_verdicts)
            cand_ends = u.ends[test_m]
            cand_gtreg = u.gt_type[test_m] == "regime"
            base_rate = float(cand_gtreg.mean())

            def cap_sub(ends):
                if len(ends) > B:
                    return rng.choice(ends, B, replace=False)
                return np.asarray(ends)

            pool_k = tn[reg_test == k]
            sel = {
                "guided_rc": cap_sub(fl_rc),
                "guided_ae": cap_sub(fl_ae),
                "alarm_rand": cap_sub(cand_ends),
                "target_rand": rng.choice(pool_k, size=min(B, len(pool_k)), replace=False),
                "other_rand": rng.choice(tn[reg_test != k], size=B, replace=False),
            }
            gt_of_end = {int(e): (t == "regime") for e, t in zip(u.ends, u.gt_type)}

            def prec_of(ends):
                if len(ends) == 0:
                    return None
                return float(np.mean([gt_of_end[int(e)] for e in ends]))

            prec = {s: prec_of(sel[s]) for s in ("guided_rc", "guided_ae", "alarm_rand")}

            def fit_far(feats):
                ifo = IsolationForest(n_estimators=100, contamination="auto",
                                      random_state=0, n_jobs=-1).fit(feats)
                return float((-ifo.decision_function(ew) > tau_fixed).mean()), ifo

            far = {s: [] for s in sel}
            far["unc"] = []
            unc_model = None
            base_far, unc_model = fit_far(feats_pool)
            for s in far:
                far[s].append(base_far)
            unc_chosen = []
            unc_rem = list(range(len(cand_ends)))
            feats_cand = W[test_m].reshape(int(test_m.sum()), -1)
            prev_n = {s: 0 for s in sel}
            for r in range(1, R + 1):
                # unc: 用上一轮模型选本轮 per_round 个最不确定候选 (第1轮用基础模型)
                if unc_rem:
                    take = min(per_round, len(unc_rem))
                    sc = np.abs(-unc_model.decision_function(feats_cand[unc_rem]) - tau_fixed)
                    pick = set(int(i) for i in np.argsort(sc)[:take])
                    unc_chosen += [unc_rem[i] for i in sorted(pick)]
                    unc_rem = [unc_rem[i] for i in range(len(unc_rem)) if i not in pick]
                    sel["unc"] = cand_ends[np.asarray(unc_chosen, int)]
                for s, ends in sel.items():
                    e = np.asarray(ends[:r * per_round], int)
                    if len(e) == prev_n.get(s, 0):   # 预算饱和: 特征集不变, 模型不变
                        far[s].append(far[s][-1])
                        continue
                    feats = feats_pool
                    if len(e):
                        feats = np.vstack([feats, X[wins(e)].reshape(len(e), -1)])
                    f, model = fit_far(feats)
                    far[s].append(f)
                    prev_n[s] = len(e)
                    if s == "unc":
                        unc_model = model
                print(f"  [{ds} r{k}] 轮{r}: " + " ".join(
                    f"{s}={far[s][r]:.3f}" for s in far), flush=True)
            rows.append({
                "dataset": ds, "regime": k, "B": B, "per_round": per_round,
                "n_eval": int(len(eval_ends)), "n_cand": int(len(cand_ends)),
                "n_flagged_rc": int(len(fl_rc)), "n_flagged_ae": int(len(fl_ae)),
                "base_rate_regime": base_rate, "prec": prec, "far": far,
            })
    with open(cpath("repair_v3.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1, default=float)
    print("\n=== 汇总 (第%d轮, 相对 alarm_rand 的 pp 差) ===" % R)
    for s in ("guided_rc", "guided_ae", "unc", "target_rand", "other_rand"):
        gaps = [100 * (x["far"]["alarm_rand"][R] - x["far"][s][R]) for x in rows]
        print(f"{s}: mean {np.mean(gaps):+.1f}pp  median {np.median(gaps):+.1f}pp  "
              f"win {sum(g > 0 for g in gaps)}/{len(gaps)}")


if __name__ == "__main__":
    main()
