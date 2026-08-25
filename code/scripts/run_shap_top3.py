# -*- coding: utf-8 -*-
"""Per-unit SHAP iforest top3/recalls, merged into shap_iforest.json."""
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
d = json.load(open(cpath('shap_iforest.json'), encoding='utf-8'))
for ds in ('SWaT', 'SMD', 'MetroPT3', 'PSM', 'SMAP'):
    for u in gp._mixed_unit(ds):
        if 'layer2_top3' in d.get(u.name, {}):
            continue
        bank = _RegimeBank(u.pool_windows(), seed=0)
        W = u.windows()
        y = (u.gt_type == 'variable').astype(int)
        val, test = u.val_mask, ~u.val_mask
        attr = shap_attribute(u, W, bank)
        g, dd = tl.calibrate(tl._sub(attr, val), y[val])
        pred = tl._predict(attr, g, dd)[test]
        yt = y[test]
        vm = test & (y == 1)
        phi = attr['phi'][vm]
        h3 = [int(len(set(np.argsort(-phi[i])[:3]) & set(u.gt_vars[gi])) > 0)
              for i, gi in enumerate(np.where(vm)[0])]
        d[u.name]['layer2_top3'] = float(np.mean(h3))
        d[u.name]['var_recall'] = float((pred[yt == 1] == 1).mean())
        d[u.name]['reg_recall'] = float((pred[yt == 0] == 0).mean())
        print(u.name, f"{time.time()-t0:.0f}s top3 {np.mean(h3):.3f}", flush=True)
json.dump(d, open(cpath('shap_iforest.json'), 'w'), indent=1)
import statistics as st
t3 = [v['layer2_top3'] for v in d.values() if 'layer2_top3' in v]
vr = [v['var_recall'] for v in d.values() if 'var_recall' in v]
rr = [v['reg_recall'] for v in d.values() if 'reg_recall' in v]
print('unit-mean top3', round(st.mean(t3), 3), 'var-R', round(st.mean(vr), 2),
      'reg-R', round(st.mean(rr), 2))
