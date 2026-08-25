"""R1/R2 新增模块的单元测试: RC-CA 银行、模板替换、两层协议的标定/预测逻辑."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW  # noqa: E402
from rcca.rcca import _RegimeBank, rcca_attribute, regime_aware_global_attribute  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402


def _two_regime_pool(n=600, seed=0):
    """两个工况的合成正常池: 工况A 均值+1, 工况B 均值-1, 各通道独立噪声."""
    rng = np.random.default_rng(seed)
    D = 5
    P = rng.normal(0, 0.2, (n, WINDOW, D)).astype(np.float32)
    lab = rng.random(n) < 0.5
    P[lab] += 1.0
    P[~lab] -= 1.0
    return P, lab


class _ToyUnit:
    def __init__(self, P, scorer=None):
        self.scorer, self.dataset, self.iforest_model = "toy", "toy", None
        self.score = scorer or (lambda W: np.abs(W.mean(1).mean(1)))  # 均值幅值=异常分
        self.W_store = None


class TestBank:
    def test_knn_template_pulls_toward_own_regime(self):
        P, lab = _two_regime_pool()
        bank = _RegimeBank(P, seed=0)
        w = np.full((1, WINDOW, 5), 1.0, np.float32)          # 工况A 的窗
        tmpl, labs = bank.knn_template(w, K=5)
        assert tmpl.shape == w.shape
        assert tmpl.mean() > 0.5                              # 模板应接近 +1 工况
        w2 = np.full((1, WINDOW, 5), -1.0, np.float32)
        tmpl2, _ = bank.knn_template(w2, K=5)
        assert tmpl2.mean() < -0.5

    def test_global_mean_traj(self):
        P, lab = _two_regime_pool()
        bank = _RegimeBank(P, seed=0)
        assert abs(bank.global_mean_traj.mean()) < 0.3        # 两工况抵消


class TestRcca:
    def test_phi_identifies_shifted_channel(self):
        """单通道 +3σ 偏移的 FA 窗, RC-CA 的 top-1 应命中该通道."""
        P, _ = _two_regime_pool()
        bank = _RegimeBank(P, seed=0)
        unit = _ToyUnit(P)
        w = np.full((1, WINDOW, 5), 1.0, np.float32)
        w[0, :, 2] += 3.0
        attr = rcca_attribute(unit, w, bank)
        assert attr["phi"].shape == (1, 5)
        assert int(np.argmax(attr["phi"][0])) == 2
        assert attr["conf"].shape == (1,) and attr["delta"].shape == (1,)


class TestProtocol:
    def test_predict_gamma_only(self):
        attr = {"conf": np.array([0.9, 0.1]), "delta": None}
        np.testing.assert_array_equal(tl._predict(attr, 0.5, None), [1, 0])

    def test_predict_with_delta(self):
        attr = {"conf": np.array([0.1, 0.9, 0.1]),
                "delta": np.array([5.0, 5.0, -1.0])}
        # (conf<γ 且 Δ>δ) -> regime(0)
        np.testing.assert_array_equal(tl._predict(attr, 0.5, 1.0), [0, 1, 1])

    def test_calibrate_recovers_separable_case(self):
        rng = np.random.default_rng(0)
        conf = np.concatenate([rng.normal(0.9, 0.02, 100), rng.normal(0.2, 0.02, 100)])
        dl = np.concatenate([rng.normal(0.0, 0.1, 100), rng.normal(5.0, 0.1, 100)])
        y = np.concatenate([np.ones(100, int), np.zeros(100, int)])
        g, d = tl.calibrate({"conf": conf, "delta": dl}, y)
        assert g is not None and d is not None
        pred = tl._predict({"conf": conf, "delta": dl}, g, d)
        assert (pred == y).mean() > 0.95

    def test_macro_f1_single_class(self):
        assert tl._macro_f1(np.ones(10, int), np.ones(10, int)) == pytest.approx(0.5)
