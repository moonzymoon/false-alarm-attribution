# -*- coding: utf-8 -*-
"""SHAP on the deep-MIL (cmhmil) variable-level units: completes the SHAP row."""
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
from run_shap_attr import shap_attribute  # noqa: E402


def main():
    t0 = time.time()
    out = {}
    for ds in ('SWaT', 'SMD', 'PSM', 'SMAP'):
        try:
            u = gp._variable_unit('cmhmil', ds)
        except Exception as e:
            print(ds, 'unit failed:', type(e).__name__, e, flush=True)
            continue
        if u is None or len(u.ends) < 30:
            print(ds, 'insufficient', flush=True)
            continue
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
                phi = attr['phi'][vm]
                m['layer2_top1'] = float(np.mean([
                    int(np.argsort(-phi[i])[0] in set(u.gt_vars[gi]))
                    for i, gi in enumerate(np.where(vm)[0])]))
            out[u.name] = m
            print(f"SHAP {u.name}: top1 {m.get('layer2_top1', float('nan')):.3f} "
                  f"({time.time()-t0:.0f}s)", flush=True)
        except Exception as e:
            out[f'cmhmil_{ds}_var'] = {'error': f'{type(e).__name__}: {e}'}
            print(ds, 'ERROR', type(e).__name__, e, flush=True)
    json.dump(out, open(cpath('shap_cmhmil.json'), 'w', encoding='utf-8'),
              indent=1)
    print('saved -> shap_cmhmil.json', flush=True)


if __name__ == '__main__':
    main()
