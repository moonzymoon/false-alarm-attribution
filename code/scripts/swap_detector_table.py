# -*- coding: utf-8 -*-
"""Replace broken tab:detector in the paper with the cache-built version."""
import io, re

B = chr(92)
PAPER = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
TAB = r"D:\0科研\工作1\第10篇SCI\src\_cache\detector_table.tex"

s = io.open(PAPER, encoding="utf-8").read()
new_tab = io.open(TAB, encoding="utf-8").read().strip()

# locate old table: from caption line of tab:detector back to its begin{table}, to end{table}
start_marker = B + "caption{Layer-1 macro-F1 (upper block)"
i = s.index(start_marker)
j = s.index(B + "begin{table}[t]", 0, i)          # enclosing begin
k = s.index(B + "end{table}", i) + len(B + "end{table}")
old = s[j:k]
s = s[:j] + new_tab + s[k:]
io.open(PAPER, "w", encoding="utf-8", newline=chr(10)).write(s)
print("replaced", len(old), "chars with", len(new_tab), "chars")
