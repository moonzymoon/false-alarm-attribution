# -*- coding: utf-8 -*-
"""Reorder calibration subsection: rule first, variable-only reduction after."""
import io
B = chr(92)
NL = chr(10)
p = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(p, encoding="utf-8").read()

old = ("Each method outputs per-channel scores $" + B + "phi_j(w)$ and a scalar confidence" + NL +
       "$" + B + "kappa(w)$. For variable-only methods, $" + B + "Delta$ is undefined and the rule reduces to a single" + NL +
       "gate: a window is typed mode-level exactly when $" + B + "kappa<" + B + "gamma$ (equivalently," + NL +
       "$" + B + "Delta=+" + B + "infty$, so the second condition is always satisfied). Variable-only" + NL +
       "methods therefore still issue mode verdicts on low-confidence windows; their" + NL +
       "non-zero mode recall in Table~" + B + "ref{tab:main} reflects this confidence gate, not" + NL +
       "an explicit mode model." + NL +
       "Regime-aware methods additionally" + NL +
       "output a mode-evidence gap $" + B + "Delta$ and use the conjunctive rule")
new = ("Each method outputs per-channel scores $" + B + "phi_j(w)$ and a scalar confidence" + NL +
       "$" + B + "kappa(w)$. Regime-aware methods additionally" + NL +
       "output a mode-evidence gap $" + B + "Delta$ and use the conjunctive rule")
assert old in s, "ordering block not found"
s = s.replace(old, new)

anchor = "All thresholds $(" + B + "gamma," + B + "delta)$ are selected"
insertion = ("For variable-only methods, $" + B + "Delta$ is undefined and the rule reduces to a single" + NL +
             "gate: a window is typed mode-level exactly when $" + B + "kappa<" + B + "gamma$ (equivalently," + NL +
             "$" + B + "Delta=+" + B + "infty$, so the second condition is always satisfied). Variable-only" + NL +
             "methods therefore still issue mode verdicts on low-confidence windows; their" + NL +
             "non-zero mode recall in Table~" + B + "ref{tab:main} reflects this confidence gate, not" + NL +
             "an explicit mode model. " + anchor)
assert anchor in s, "anchor not found"
s = s.replace(anchor, insertion)

s = s.replace("a rejection threshold is such a confidence gate that routes a",
              "a rejection threshold is a confidence gate that routes a")
io.open(p, "w", encoding="utf-8", newline=NL).write(s)
print("reordered + nit fixed")
