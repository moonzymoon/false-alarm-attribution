"""第4/5种检测器: PCA reconstruction error + One-Class SVM.
均为可廉价重训的浅层方法, 支持混合单元协议的模式留出."""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WINDOW

_MODELS = {}

def _pca_model(dataset, X, window=WINDOW, n_comp=None):
    key = ("pca", dataset)
    if key in _MODELS:
        return _MODELS[key]
    from sklearn.decomposition import PCA
    a = int(len(X) * 0.35)
    Nw = a - window + 1
    idx = np.arange(window)[None, :] + np.arange(Nw)[:, None]
    featW = X[0:a][idx].reshape(Nw, -1)
    if n_comp is None:
        n_comp = min(featW.shape[1], featW.shape[0] // 10, 50)
    pca = PCA(n_components=n_comp, random_state=0).fit(featW)
    _MODELS[key] = pca
    return pca

def _ocsvm_model(dataset, X, window=WINDOW):
    key = ("ocsvm", dataset)
    if key in _MODELS:
        return _MODELS[key]
    from sklearn.svm import OneClassSVM
    a = int(len(X) * 0.35)
    Nw = a - window + 1
    # 子采样以避免 OOM
    if Nw > 50000:
        rng = np.random.default_rng(0)
        sel = np.sort(rng.choice(Nw, 50000, replace=False))
        idx = np.arange(window)[None, :] + sel[:, None]
    else:
        idx = np.arange(window)[None, :] + np.arange(Nw)[:, None]
    featW = X[0:a][idx].reshape(-1, X.shape[1] * window)
    ocsvm = OneClassSVM(kernel="rbf", nu=0.05).fit(featW)
    _MODELS[key] = ocsvm
    return ocsvm

def score_pca_windows(dataset, W):
    """PCA reconstruction error: 越大越异常."""
    pca = _pca_model(dataset, np.zeros((1000, 10)))  # dummy to get model
    # 实际需要全流 X; 由调用方保证模型已 fit
    flat = W.reshape(len(W), -1)
    proj = pca.inverse_transform(pca.transform(flat))
    return np.mean((flat - proj) ** 2, axis=1)

def score_ocsvm_windows(dataset, W):
    """OC-SVM: decision_function 越小越异常, 取负使越大越异常."""
    ocsvm = _ocsvm_model(dataset, np.zeros((1000, 10)))  # dummy
    flat = W.reshape(len(W), -1)
    return -ocsvm.decision_function(flat)

# 兼容 score_windows 接口
_score_cache = {}

def fit_pca(dataset, X, window=WINDOW):
    from sklearn.decomposition import PCA
    a = int(len(X) * 0.35)
    Nw = a - window + 1
    if Nw > 50000:
        rng = np.random.default_rng(0)
        sel = np.sort(rng.choice(Nw, 50000, replace=False))
        idx = np.arange(window)[None, :] + sel[:, None]
    else:
        idx = np.arange(window)[None, :] + np.arange(Nw)[:, None]
    featW = X[0:a][idx].reshape(-1, X.shape[1] * window)
    n_comp = min(featW.shape[1], 50)
    pca = PCA(n_components=n_comp, random_state=0).fit(featW)
    _score_cache[("pca", dataset)] = pca
    return pca

def fit_ocsvm(dataset, X, window=WINDOW):
    from sklearn.svm import OneClassSVM
    a = int(len(X) * 0.35)
    Nw = a - window + 1
    if Nw > 50000:
        rng = np.random.default_rng(0)
        sel = np.sort(rng.choice(Nw, 50000, replace=False))
        idx = np.arange(window)[None, :] + sel[:, None]
    else:
        idx = np.arange(window)[None, :] + np.arange(Nw)[:, None]
    featW = X[0:a][idx].reshape(-1, X.shape[1] * window)
    ocsvm = OneClassSVM(kernel="rbf", nu=0.05).fit(featW)
    _score_cache[("ocsvm", dataset)] = ocsvm
    return ocsvm

def score_new(scorer, dataset, W):
    """统一入口: 'pca' | 'ocsvm' -> (n,) 越大越异常."""
    flat = W.reshape(len(W), -1)
    if scorer == "pca":
        mdl = _score_cache.get(("pca", dataset))
        if mdl is None:
            raise ValueError(f"PCA not fitted for {dataset}")
        proj = mdl.inverse_transform(mdl.transform(flat))
        return np.mean((flat - proj) ** 2, axis=1)
    elif scorer == "ocsvm":
        mdl = _score_cache.get(("ocsvm", dataset))
        if mdl is None:
            raise ValueError(f"OCSVM not fitted for {dataset}")
        return -mdl.decision_function(flat)
    raise ValueError(f"Unknown scorer: {scorer}")
