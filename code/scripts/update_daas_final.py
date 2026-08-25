# -*- coding: utf-8 -*-
"""Update DAAS paragraph with complete-matrix LOO numbers."""
import io
B = chr(92)
NL = chr(10)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()

old = ("study, DAAS recovers the exactly-best method in 6 of 15 held-out pairs" + NL +
       "(40" + B + "%) and the family-level rule in 7 of 15 (47" + B + "%), ahead of the best" + NL +
       "fixed strategy (always-AERec or always-RC-CA, 5 of 15, 33" + B + "%) and the" + NL +
       "random baseline (11" + B + "%). Because several pairs are near-ties, we also score" + NL +
       "predictions within 0.05 top-1 of the pair's best method: the family rule" + NL +
       "then covers 11 of 15 pairs (73" + B + "%) versus 53" + B + "% for the best fixed method.")
new = ("study, both DAAS and the family-level rule recover the exactly-best" + NL +
       "method in 7 of 15 held-out pairs (47" + B + "%), ahead of the best fixed" + NL +
       "strategy (always-AERec, 5 of 15, 33" + B + "%) and the random baseline (11" + B + "%)." + NL +
       "Because several pairs are near-ties, we also score predictions within" + NL +
       "0.05 top-1 of the pair's best method: the rules then cover 11 of 15" + NL +
       "pairs (73" + B + "%) versus 53" + B + "% for the best fixed method.")
assert old in s, "DAAS paragraph not found"
s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print("DAAS numbers updated to complete matrix")
