# -*- coding: utf-8 -*-
"""Replace current tab:detector (already in paper) with updated cache version."""
import io

B = chr(92)
PAPER = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
TAB = r"D:\0科研\工作1\第10篇SCI\src\_cache\detector_table.tex"

s = io.open(PAPER, encoding="utf-8").read()
new_tab = io.open(TAB, encoding="utf-8").read().strip()

cap = "Method--detector matching on all 58 evaluation units"
i = s.index(cap)
j = s.rindex(B + "begin{table}[t]", 0, i)
k = s.index(B + "end{table}", i) + len(B + "end{table}")
s = s[:j] + new_tab + s[k:]
io.open(PAPER, "w", encoding="utf-8", newline=chr(10)).write(s)
print("tab:detector updated (Grad row + caption notes)")
