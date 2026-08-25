# -*- coding: utf-8 -*-
"""Refine the smoothness claim for the MIL tie (C1-extension consistency)."""
import io
B = chr(92)
NL = chr(10)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()
old = (B + "emph{Smooth detectors (PCA, OCSVM, transformer, MIL) favour counterfactual\n"
       "methods (top-1 0.50--1.00) while the discrete tree ensemble favours\n"
       "reconstruction (AERec, top-1 0.75). No attribution family is uniformly best; the choice must match the detector family.}")
new = (B + "emph{On the smooth detectors (PCA, OCSVM, transformer, MIL) counterfactual\n"
       "replacement is at least competitive everywhere (top-1 0.50--1.00) and decisively\n"
       "better on PCA and the transformer (up to +0.89), the discrete tree ensemble\n"
       "favours reconstruction (AERec 0.75 versus 0.48--0.53), and the MIL detector\n"
       "leaves the two families effectively tied (0.90). No attribution family is\n"
       "uniformly best; the choice must match the detector family.}")
assert old in s, "not found"
s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print("refined")
