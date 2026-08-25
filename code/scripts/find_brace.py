# -*- coding: utf-8 -*-
"""Locate the extra opening brace via running balance at section markers."""
import io, re
B = chr(92)
t = io.open(r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex", encoding="utf-8").read()
bal = 0
prev = 0
for i, ln in enumerate(t.split("\n"), 1):
    clean = re.sub("\\" + B + "[{}]", "", ln)
    bal += clean.count("{") - clean.count("}")
    if bal != prev:
        pass
    stripped = ln.strip()
    if stripped.startswith(B + "section") or stripped.startswith(B + "begin{table") or \
       stripped.startswith(B + "end{table") or stripped.startswith(B + "textbf{Runtime"):
        print(f"line {i:4d} bal={bal:3d}  {stripped[:56]}")
    prev = bal
print("final:", bal)
