# -*- coding: utf-8 -*-
"""Capitalize sentence-start 'mode-directed' after the bold heading in intro."""
import io
B = chr(92)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()
old = B + "textbf{Attribution pays off through repair.} mode-directed data"
new = B + "textbf{Attribution pays off through repair.} Mode-directed data"
assert old in s and s.count(old) == 1, "pattern not found"
s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline=chr(10)).write(s)
print("capitalized")
