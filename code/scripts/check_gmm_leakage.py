# -*- coding: utf-8 -*-
"""#7 GMM transductive-leakage check: does fitting the regime GMM on the full
series vs the train+validation segment change test-window mode assignments?"""
import sys, os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_raw, split_of, WINDOW
from regimes.regimes import RegimeModel, features_at
from sklearn.metrics import adjusted_rand_score

for ds in ("SWaT", "SMD", "MetroPT3", "PSM", "SMAP"):
    X, Y = load_raw(ds)
    a, b = split_of(len(X))
    rm_full = RegimeModel().fit(X, seed=0)
    rm_tr = RegimeModel().fit(X[:b], seed=0)
    # test normal windows (subsample for speed)
    te = np.arange(b + WINDOW - 1, len(X), 7)
    f = features_at(X, te)
    lab_full = rm_full.transform(f)
    lab_tr = rm_tr.transform(f)
    ari = adjusted_rand_score(lab_full, lab_tr)
    agree = float((lab_full == lab_tr).mean())
    print(f"{ds:9s} K_full={rm_full.K} K_train={rm_tr.K} ARI={ari:.3f} label-agree={agree:.1%} (n={len(te)})")
