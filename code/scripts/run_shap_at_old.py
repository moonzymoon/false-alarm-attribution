# -*- coding: utf-8 -*-
"""SHAP on AT_SWaT_var / AT_SMD_var (completes the SHAP AT cell over 3 units)."""
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

t0 = time.time()
out = json.load(open(cpath('at_ext.json'), encoding='utf-8'))
for ds in ('SWaT', 'SMD'):
    u = gp._variable_unit_at(ds)
    if u is None:
        continue
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
    key = f'AT_{ds}_var'
    out.setdefault(key, {})
    out[key]['SHAP'] = m
    print(f"SHAP AT {ds}: top1 {m.get('layer2_top1', float('nan')):.3f} "
          f"({time.time()-t0:.0f}s)", flush=True)
json.dump(out, open(cpath('at_ext.json'), 'w'), indent=1, default=float)
print('at_ext.json updated', flush=True)
