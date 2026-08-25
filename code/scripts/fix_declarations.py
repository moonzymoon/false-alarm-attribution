# -*- coding: utf-8 -*-
"""Add explicit consent sub-headings per official SAGE declarations list."""
import io
B = chr(92)
NL = chr(10)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()

old = B + "textbf{Ethics approval and consent:} not applicable."
new = (B + "textbf{Ethics approval and consent:} not applicable." + NL +
       B + "textbf{Consent to participate:} not applicable." + NL +
       B + "textbf{Consent for publication:} not applicable.")
assert old in s and "Consent to participate" not in s
s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print("declarations updated")
