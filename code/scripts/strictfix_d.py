# -*- coding: utf-8 -*-
"""Round-3 fixes: reference all figures and the dataset table in text."""
import io
B = chr(92)
NL = chr(10)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()
n = 0

def rep(old, new, tag):
    global s, n
    assert old in s, f"NOT FOUND: {tag}"
    assert s.count(old) == 1, f"NOT UNIQUE: {tag}"
    s = s.replace(old, new)
    n += 1
    print("D:", tag)

# D1. protocol figure
rep("An " + B + "emph{evaluation unit} fixes one detector, one threshold, and one cause" + NL +
    "mixture.",
    "An " + B + "emph{evaluation unit} fixes one detector, one threshold, and one cause" + NL +
    "mixture (Figure~" + B + "ref{fig:protocol} gives an overview).",
    "ref fig:protocol")

# D2. heatmap figure
rep("Table~" + B + "ref{tab:main} reports layer-(i) macro-F1 and layer-(ii) top-1 on the",
    "Table~" + B + "ref{tab:main} reports layer-(i) macro-F1 and layer-(ii) top-1 on the",
    "noop")  # placeholder no-op replaced below
# (undo the no-op trick: we actually want to add the heatmap ref after the first results sentence)
rep("while all clearly exceed Random (0.474).",
    "while all clearly exceed Random (0.474). Figure~" + B + "ref{fig:heatmap} shows the" + NL +
    "per-unit layer-1 pattern behind these means.",
    "ref fig:heatmap")
# remove the no-op marker (it replaced text with itself, harmless)

# D3. mirror figure
rep(B + "subsection{Method--detector matching}" + B + "label{sec:matching}" + NL +
    "The pooled means hide the study's central pattern" + NL +
    "(Table~" + B + "ref{tab:detector}).",
    B + "subsection{Method--detector matching}" + B + "label{sec:matching}" + NL +
    "The pooled means hide the study's central pattern" + NL +
    "(Table~" + B + "ref{tab:detector}; the reversal is visualized in" + NL +
    "Figure~" + B + "ref{fig:mirror}).",
    "ref fig:mirror")

# D4. margin figure
rep("Splitting variable-type test instances by alarm margin",
    "Splitting variable-type test instances by alarm margin (Figure~" + B + "ref{fig:margin})",
    "ref fig:margin")

# D5. scoredist figure
rep("To probe how rejection thresholds calibrated on injected data behave" + NL +
    "out of domain,",
    "Figure~" + B + "ref{fig:scoredist} compares the score distributions of natural and" + NL +
    "injected false alarms. To probe how rejection thresholds calibrated on" + NL +
    "injected data behave out of domain,",
    "ref fig:scoredist")

# D6. datasets table
rep("Datasets: SWaT " + B + "cite{goh2017swat,mathur2016swat}",
    "Datasets (Table~" + B + "ref{tab:datasets}): SWaT " + B + "cite{goh2017swat,mathur2016swat}",
    "ref tab:datasets")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in batch D")
