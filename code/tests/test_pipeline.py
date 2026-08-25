"""单元测试: 注入算子 / 误报收集逻辑 / 工况特征与聚类.

运行: cd src && python -m pytest tests/ -q
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW  # noqa: E402
from injection.inject import (apply_variable_fault, active_channels,  # noqa: E402
                              sample_normal_segments, SEG_LEN)
from regimes.regimes import (RegimeModel, features_at, window_features,  # noqa: E402
                             window_majority, alignment_report)
from evaluation.alignment import hist_kl, mmd_rbf  # noqa: E402

RNG = np.random.default_rng(0)


def _toy_stream(T=2000, D=6):
    t = np.arange(T)
    X = np.zeros((T, D), np.float32)
    X[:, 0] = np.sin(t / 50)                     # 周期通道
    X[:, 1] = RNG.normal(0, 1, T)                # 噪声通道
    X[:, 2] = 1.0                                # 恒定通道
    X[:, 3] = np.where((t % 400) < 200, 2.0, -1.0)  # 方波 = 两个"工况"
    X[:, 4] = RNG.normal(0, 0.5, T) + 0.001 * t
    X[:, 5] = np.cos(t / 30)
    Y = np.zeros(T, np.int8)
    Y[1800:1850] = 1
    return X, Y


# ---------------- 注入 ----------------
class TestInject:
    def setup_method(self):
        self.X, self.Y = _toy_stream()
        self.mu = self.X[:700].mean(0)
        self.sigma = self.X[:700].std(0) + 1e-8
        self.s = 1000

    def test_drift_only_target_var(self):
        Xm, gt = apply_variable_fault(self.X, self.s, 100, [1], "drift", 0.1, self.mu, self.sigma)
        diff = np.abs(Xm - self.X).sum(0)
        assert diff[1] > 0 and np.all(np.delete(diff, 1) == 0)
        assert gt["cause_type"] == "variable" and gt["cause_vars"] == [1]

    def test_drift_is_linear_ramp(self):
        Xm, _ = apply_variable_fault(self.X, self.s, 100, [1], "drift", 0.5, self.mu, self.sigma)
        delta = Xm[self.s:self.s + 100, 1] - self.X[self.s:self.s + 100, 1]
        assert np.allclose(np.diff(delta), 0.5 * self.sigma[1])

    def test_stuck_freezes_value(self):
        Xm, _ = apply_variable_fault(self.X, self.s, 100, [0], "stuck", 1.0, self.mu, self.sigma)
        seg = Xm[self.s:self.s + 100, 0]
        assert np.allclose(seg, self.X[self.s, 0]) and seg.var() < 1e-12

    def test_variance_inflation(self):
        Xm, _ = apply_variable_fault(self.X, self.s, 100, [1], "var", 5.0, self.mu, self.sigma)
        before = (self.X[self.s:self.s + 100, 1] - self.mu[1]).std()
        after = (Xm[self.s:self.s + 100, 1] - self.mu[1]).std()
        assert abs(after / before - 5.0) < 0.1

    def test_active_channels_excludes_constant(self):
        ac = active_channels(self.X, 0, 700)
        assert 2 not in ac and 0 in ac

    def test_segments_avoid_anomalies_and_test_start(self):
        starts = sample_normal_segments(self.Y, b=1000, seg_len=200, n=20, seed=0)
        assert len(starts) > 0
        assert (starts >= 1000).all()
        for s in starts:
            assert self.Y[max(0, s - 32):s + 200 + 32].max() == 0  # margin 内无异常


# ---------------- 工况 ----------------
class TestRegimes:
    def setup_method(self):
        self.X, self.Y = _toy_stream(4000)

    def test_window_features_shape_and_slope(self):
        F = window_features(self.X, window=16, stride=1)
        assert F.shape == (len(self.X) - 15, 3 * self.X.shape[1])
        # 通道 4 (0.001*t 线性趋势) 的斜率特征应为正
        assert F[:, self.X.shape[1] + 4].mean() > 0.0005

    def test_features_at_consistent(self):
        ends = np.array([100, 500, 1000])
        F1 = features_at(self.X, ends)
        F2 = window_features(self.X, 16, 1)
        assert np.allclose(F1, F2[ends - 15])

    def test_window_majority(self):
        lab = np.zeros(100, np.int8); lab[50:] = 1
        m = window_majority(lab, window=10)
        assert m[0] == 0 and m[-1] == 1

    def test_gmm_recovers_two_regimes(self):
        X = np.zeros((4000, 3), np.float32)
        t = np.arange(4000)
        X[:, 0] = np.where((t % 400) < 200, 2.0, -1.0) + RNG.normal(0, 0.05, 4000)
        X[:, 1] = np.where((t % 400) < 200, 0.5, -0.5) + RNG.normal(0, 0.05, 4000)
        X[:, 2] = RNG.normal(0, 1, 4000)
        rm = RegimeModel(K=2).fit(X)
        ends = np.arange(15, 1400)
        pred = rm.transform(features_at(X, ends))
        truth = (X[ends, 0] > 0).astype(int)
        rep = alignment_report(pred, truth)
        assert rep["ari"] > 0.85  # 合成双工况应基本恢复 (GMM 初始化随机性留余量)

    def test_alignment_report(self):
        r = alignment_report([0, 0, 1, 1], [1, 1, 0, 0])
        assert r["ari"] == pytest.approx(1.0)


# ---------------- 误报收集逻辑 ----------------
class TestCollect:
    def test_hist_kl_self_zero(self):
        x = RNG.normal(0, 1, 5000)
        assert hist_kl(x, x) < 0.01

    def test_hist_kl_shifted_positive(self):
        x = RNG.normal(0, 1, 5000)
        y = RNG.normal(3, 1, 5000)
        assert hist_kl(x, y) > 1.0

    def test_mmd_self_zero(self):
        A = RNG.normal(0, 1, (300, 5))
        assert abs(mmd_rbf(A, A)) < 0.05

    def test_mmd_shifted_positive(self):
        A = RNG.normal(0, 1, (300, 5))
        B = RNG.normal(3, 1, (300, 5))
        assert mmd_rbf(A, B) > 0.1
