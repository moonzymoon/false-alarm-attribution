# -*- coding: utf-8 -*-
"""Count abstract words in the IDA tex (string-scan, no regex)."""
import io
B = chr(92)
s = io.open(r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex", encoding="utf-8").read()
a = s.index(B + "begin{abstract}") + len(B + "begin{abstract}")
b = s.index(B + "end{abstract}")
print("abstract words:", len(s[a:b].split()))
