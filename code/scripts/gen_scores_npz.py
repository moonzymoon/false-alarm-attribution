# -*- coding: utf-8 -*-
"""Generate {DS}_scores.npz via the verified scorers_at path (equivalent to
solver.test; spearman ~1.0 was verified for SWaT/SMD when this adapter was
built). Usage: python gen_scores_npz.py PSM"""
import sys
import os

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), 'src'))
import common  # noqa: E402
import scorers_at  # noqa: E402

ds = sys.argv[1] if len(sys.argv) > 1 else 'PSM'
a = scorers_at._load(ds)
te = a['te']
n_win = (len(te) - 100) // 100 + 1
starts = np.arange(n_win) * 100
W = te[starts[:, None] + np.arange(100)[None, :]]
s = scorers_at.score_windows_at(ds, W)          # (n_win, 100)
s_all = s.reshape(-1)
if len(s_all) < len(te):                        # pad tail with last value
    s_all = np.concatenate([s_all, np.full(len(te) - len(s_all), s_all[-1],
                                            dtype=s_all.dtype)])
np.savez(os.path.join(common.AT_ROOT, 'checkpoints', f'{ds}_scores.npz'),
         scores=s_all.astype(np.float32), labels=a['y'].astype(np.float32),
         threshold=0.0)
print(ds, 'scores.npz written:', s_all.shape)
