# -*- coding: utf-8 -*-
"""Fix repair-claim scope (91% is over 14 iforest units, not 58)."""
import io

p = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(p, encoding="utf-8").read()

old = ("variable-type FAs (sample-weighted across all 58 evaluation units across five detectors) versus 11"
       + chr(92) + chr(37) + " for a random channel")
new = ("variable-type FAs (mean over the 14 isolation-forest units of the repair study, Supplementary Table~S7) versus 11"
       + chr(92) + chr(37) + " for a random channel")
assert old in s, "repair scope text not found"
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8", newline=chr(10)).write(s)
print("repair scope fixed")
