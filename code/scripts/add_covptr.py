# -*- coding: utf-8 -*-
"""#11: forward pointer from injection list to limitations."""
import io
B = chr(92)
NL = chr(10)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()
old = ("two-channel joint drift) whose post-injection score exceeds" + NL +
       "$" + B + "tau_k$. (The classical PCA/OCSVM streams use the four")
new = ("two-channel joint drift; the coverage boundary of these injection" + NL +
       "families is discussed in Section~" + B + "ref{sec:limitations}) whose" + NL +
       "post-injection score exceeds $" + B + "tau_k$. (The classical PCA/OCSVM streams use the four")
assert old in s, "anchor not found"
s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print("coverage pointer added")
