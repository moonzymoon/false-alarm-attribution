# -*- coding: utf-8 -*-
"""Rewrite abstract to exactly <=200 words (post DeepSeek-R2 scoping additions)."""
import io
B = chr(92)
NL = chr(10)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()
a = s.index(B + "begin{abstract}") + len(B + "begin{abstract}")
b = s.index(B + "end{abstract}")
new_abs = NL.join([
"Alarm management is a core reliability module of industrial",
"monitoring, yet anomaly detectors produce false alarms that research",
"reduces in count, not cause. We formalize",
"false-alarm attribution: given an alarm on a process-normal window, decide",
"whether the cause is variable-level (sensor drift, stuck-at) or",
"regime-level (an unseen mode) with a repair action.",
"Real false alarms carry no cause labels, so we introduce an",
"injection-based mixed ground-truth protocol: under one detector and",
"threshold, variable-level alarms are created by controlled fault injection",
"(injection-caused) and regime-level alarms by holding out one mode",
"before retraining; a two-layer evaluation with calibrated",
"rejection compares nine methods. Across five testbeds",
"and five detectors, three findings emerge: (i) attribution quality",
"is governed by method--detector--data-set matching: counterfactual",
"replacement is near-perfect on a transformer/SWaT pairing (top-1 0.93;",
"one pairing)",
"where a reconstruction baseline collapses (0.04), the pattern reversing on",
"tree ensembles; (ii) attribution pays off through repair:",
"mode-directed data addition beats a random control by 22.1 percentage",
"points; correcting the indicated channel resolves 91" + B + "% of",
"variable alarms (random: 11" + B + "%); (iii) typing on injected ground truth is largely solved",
"by the confidence gate alone (macro-F1 0.69--0.74; 0.83 learned",
"reader), redirecting effort to",
"localization and quantifying the protocol's preference for",
"deviation readers.",
])
print("words:", len(new_abs.split()))
assert len(new_abs.split()) <= 200
s = s[:a] + new_abs + s[b:]
io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print("abstract rewritten")
