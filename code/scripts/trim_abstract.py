# -*- coding: utf-8 -*-
"""Trim abstract to <=200 words."""
import io
B = chr(92)
NL = chr(10)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()
a = s.index(B + "begin{abstract}") + len(B + "begin{abstract}")
b = s.index(B + "end{abstract}")
old = s[a:b]
print("old words:", len(old.split()))

new = NL.join([
"Alarm management is a core reliability module of industrial",
"monitoring, yet anomaly detectors produce many false alarms that research",
"reduces in count, not in cause. We formalize",
"false-alarm attribution: given an alarm on a process-normal window, decide",
"whether the cause is variable-level (sensor drift, stuck-at) or",
"regime-level (an unseen operating mode) and output a repair action.",
"Because real false alarms carry no cause labels, we introduce an",
"injection-based mixed ground-truth protocol: under one detector and one",
"threshold, variable-level alarms are created by controlled fault injection",
"(injection-caused only) and regime-level alarms by holding out an",
"operating mode before retraining; a two-layer evaluation with calibrated",
"rejection compares nine attribution families. Across five public",
"testbeds and five detectors, three findings emerge: (i) attribution quality",
"is governed by method--detector--data-set matching---counterfactual",
"replacement is near-perfect on a transformer/SWaT pairing (top-1 0.93)",
"where a reconstruction baseline collapses (0.04), the pattern reversing on",
"tree ensembles; (ii) attribution pays off through repair:",
"mode-directed data addition beats a random control by 22.1 percentage",
"points, and correcting the indicated channel resolves 91" + B + "% of",
"variable-type alarms (random: 11" + B + "%); (iii) cause typing is largely solved",
"by calibrated rejection (macro-F1 0.64--0.79), redirecting effort to",
"localization and quantifying the protocol's structural preference for",
"deviation readers.",
])
print("new words:", len(new.split()))
assert len(new.split()) <= 200
s = s[:a] + new + s[b:]
io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print("abstract trimmed")
