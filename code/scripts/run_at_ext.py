# -*- coding: utf-8 -*-
"""Lever 3: AT variable-level units on PSM/SMAP (after checkpoint training).

Mirrors the AT_SWaT_var/AT_SMD_var evaluation: builds the unit via
gt_pool._variable_unit_at, evaluates all applicable methods (incl. SHAP),
saves src/_cache/at_ext.json."""
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

METHODS = ['RC-CA', 'GlobalCF', 'RegimeGlobal', 'CondAttr', 'AERec',
           'Granger', 'zDev', 'Random', 'SHAP']


def main():
    t0 = time.time()
    out = {}
    for ds in ('SMAP',):
        try:
            u = gp._variable_unit_at(ds)
        except Exception as e:
            out[f'AT_{ds}_var'] = {'error': f'{type(e).__name__}: {e}'}
            print(ds, 'unit build failed:', type(e).__name__, e, flush=True)
            continue
        if u is None:
            out[f'AT_{ds}_var'] = {'error': 'no FA instances'}
            print(ds, 'insufficient', flush=True)
            continue
        try:
            bank = _RegimeBank(u.pool_windows(), seed=0)
            W = u.windows()
            y = (u.gt_type == 'variable').astype(int)
            val, test = u.val_mask, ~u.val_mask
            mres = {}
            for mn in METHODS:
                try:
                    if mn == 'SHAP':
                        attr = shap_attribute(u, W, bank)
                    else:
                        attr = tl.METHODS[mn](u, W, bank)
                    g, d = tl.calibrate(tl._sub(attr, val), y[val])
                    pred = tl._predict(attr, g, d)
                    m = {'layer1_macro_f1': tl._macro_f1(y[test], pred[test]),
                         'n_test': int(test.sum())}
                    vm = test & (y == 1)
                    if vm.sum() > 0:
                        phi = attr['phi'][vm]
                        m['layer2_top1'] = float(np.mean([
                            int(np.argsort(-phi[i])[0] in set(u.gt_vars[gi]))
                            for i, gi in enumerate(np.where(vm)[0])]))
                    mres[mn] = m
                    print(f"AT {ds} {mn}: top1 {m.get('layer2_top1', float('nan')):.3f} "
                          f"({time.time()-t0:.0f}s)", flush=True)
                except Exception as e:
                    mres[mn] = {'error': f'{type(e).__name__}: {e}'}
                    print(f"AT {ds} {mn}: ERROR {type(e).__name__}: {e}", flush=True)
            out[f'AT_{ds}_var'] = mres
        except Exception as e:
            out[f'AT_{ds}_var'] = {'error': f'{type(e).__name__}: {e}'}
            print(ds, 'eval failed:', type(e).__name__, e, flush=True)
    json.dump(out, open(cpath('at_ext.json'), 'w', encoding='utf-8'),
              indent=1, default=float)
    print('saved -> at_ext.json', flush=True)


if __name__ == '__main__':
    main()
