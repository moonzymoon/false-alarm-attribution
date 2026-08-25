# -*- coding: utf-8 -*-
"""SHAP-family attribution baseline (lever 4): fills the Shapley gap in the
method taxonomy. Per-channel Shapley values w.r.t. the anomaly score:
- iforest: exact TreeSHAP on the flattened window, per-channel = sum of its
  per-timestep SHAP values.
- pca/ocsvm: channel-grouped KernelSHAP (nsamples=128, seed 0), background =
  20 pool windows, masked channels take background values.
Confidence: max(0, phi_max)/sum|phi| (same single-gate rejection form)."""
import sys
import os
import json
import time

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from common import cpath  # noqa: E402
import evaluation.gt_pool as gp  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402
from rcca.rcca import _RegimeBank  # noqa: E402


def shap_attribute(unit, Warr, bank):
    import shap
    n, T, D = Warr.shape
    scorer = unit.scorer
    if scorer == 'iforest':
        flat = Warr.reshape(n, T * D)
        ex = shap.TreeExplainer(unit.iforest_model)
        sv = np.asarray(ex.shap_values(flat, check_additivity=False))
        if sv.ndim == 3:                       # (n, F, classes)
            sv = sv[..., -1]
        # TreeExplainer on iforest explains path length (higher = more normal);
        # negate so phi measures contribution to the anomaly score (-corr 1.0
        # verified against score_samples in a sign probe).
        phi = -sv.reshape(n, T, D).sum(1)
    else:
        rng = np.random.default_rng(0)
        bg_idx = rng.choice(len(bank.P), 20, replace=False)
        BG = bank.P[bg_idx]                    # (20, T, D)
        nsamp = 128
        phi = np.zeros((n, D))
        for i in range(n):
            w = Warr[i]
            # KernelSHAP coalition sampling with SHAP kernel weights
            zs = rng.random((nsamp, D)) < 0.5
            zs[0, :] = 1
            zs[1, :] = 0
            Xmask = np.empty((nsamp, T, D))
            b = BG[rng.integers(0, len(BG), nsamp)]
            for k in range(nsamp):
                m = zs[k][None, None, :]
                Xmask[k] = m * w[None, :, :] + (1 - m) * b[k]
            s = unit.score(Xmask)
            M = 2 * D
            wgt = np.empty(nsamp)
            for k in range(nsamp):
                nz = zs[k].sum()
                if nz == 0 or nz == D:
                    wgt[k] = 1e6
                else:
                    wgt[k] = M / (nz * (D - nz))
            A = np.hstack([zs, np.ones((nsamp, 1))]) * wgt[:, None] ** 0.5
            yv = s * wgt ** 0.5
            sol, *_ = np.linalg.lstsq(A, yv, rcond=None)
            base = sol[-1]
            phi[i] = sol[:D]
    conf = np.maximum(phi.max(1), 0) / (np.abs(phi).sum(1) + 1e-9)
    return {'phi': phi, 'conf': conf, 'delta': None, 'regime': None}


def main():
    t0 = time.time()
    out = {}
    for ds in ('SWaT', 'SMD', 'MetroPT3', 'PSM', 'SMAP'):
        try:
            units = gp._mixed_unit(ds)
        except Exception as e:
            print(ds, 'mixed_unit failed:', e, flush=True)
            continue
        for u in units:
            try:
                bank = _RegimeBank(u.pool_windows(), seed=0)
                W = u.windows()
                y = (u.gt_type == 'variable').astype(int)
                val, test = u.val_mask, ~u.val_mask
                attr = shap_attribute(u, W, bank)
                g, d = tl.calibrate(tl._sub(attr, val), y[val])
                pred = tl._predict(attr, g, d)
                m = {'layer1_macro_f1': tl._macro_f1(y[test], pred[test])}
                vm = test & (y == 1)
                if vm.sum() > 0:
                    ph = attr['phi'][vm]
                    m['layer2_top1'] = float(np.mean([
                        int(np.argsort(-ph[i])[0] in set(u.gt_vars[gi]))
                        for i, gi in enumerate(np.where(vm)[0])]))
                out[u.name] = m
                print(f"SHAP {u.name}: L1 {m['layer1_macro_f1']:.3f} "
                      f"top1 {m.get('layer2_top1', float('nan')):.3f} "
                      f"({time.time()-t0:.0f}s)", flush=True)
            except Exception as e:
                out[u.name] = {'error': f'{type(e).__name__}: {e}'}
                print(f"SHAP {u.name}: ERROR {type(e).__name__}: {e}", flush=True)
    json.dump(out, open(cpath('shap_iforest.json'), 'w', encoding='utf-8'),
              indent=1)
    print('saved -> shap_iforest.json', flush=True)


if __name__ == '__main__':
    main()
