# -*- coding: utf-8 -*-
"""Style polish P1: de-AI-flavor pass. Style only; no numbers or claims change."""
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
    print("P1:", tag)

# --- abstract ---
rep("is governed by method--detector--data-set matching---counterfactual",
    "is governed by method--detector--data-set matching: counterfactual",
    "abstract dash 1")

# --- intro ---
rep("that nuisance alarms be rationalized---each must receive a documented cause" + NL +
    "and a corrective action " + B + "cite{isa182}---and alarm floods driven by false",
    "that nuisance alarms be rationalized (each must receive a documented cause" + NL +
    "and a corrective action " + B + "cite{isa182}), and alarm floods driven by false",
    "intro dash isa")
rep("intervention---exactly the nuisance-alarm situation that alarm-management" + NL +
    "practice asks to rationalize " + B + "cite{isa182} (scope refined in" + NL +
    "Section~" + B + "ref{sec:formulation}).",
    "intervention. This is the nuisance-alarm situation that alarm-management" + NL +
    "practice asks to rationalize " + B + "cite{isa182}; Section~" + B + "ref{sec:formulation}" + NL +
    "refines the scope.",
    "intro nuisance dedup")
rep("output a cause in a dual-granularity space---variable-level causes",
    "output a cause in a dual-granularity space: variable-level causes",
    "intro dash dual")
rep("causes (a legitimate operating mode absent from training)---together with a" + NL +
    "repair suggestion",
    "causes (a legitimate operating mode absent from training), together with a" + NL +
    "repair suggestion",
    "intro dash repair")
rep("construction---variable-level faults injected into normal test regions",
    "construction: variable-level faults injected into normal test regions",
    "intro dash construction")
rep("best, and the matching relation is pairing-specific---a selection rule with" + NL +
    "direct operational value.",
    "best, and the matching relation is pairing-specific, which is what gives the" + NL +
    "selection rule its direct operational value.",
    "intro dash pairing")
rep("ground-truth-channel correction---repair effectiveness is operationally more" + NL +
    "relevant than injected-label matching.",
    "ground-truth-channel correction; repair effectiveness is operationally more" + NL +
    "relevant than injected-label matching.",
    "intro dash gt")
rep("split---a protocol dividend, not a free lunch.",
    "split: a protocol dividend, not a free lunch.",
    "intro dash dividend")
rep("show, and because it " + B + "emph{strengthens} the protocol's value---the",
    "show, and because it " + B + "emph{strengthens} the protocol's value: the",
    "intro dash strengthens")
rep("with the assumption audit---a study instrument for testing when regime-conditioning helps, not a claim of",
    "with the assumption audit, a study instrument for testing when regime-conditioning helps rather than a claim of",
    "intro dash audit")

# --- related work ---
rep("fired on a benign window---sensor data-quality degradation or an unseen operating mode).",
    "fired on a benign window: sensor data-quality degradation or an unseen operating mode).",
    "related dash window")

# --- formulation ---
rep("process-benign---the required action is sensor maintenance, not process" + NL +
    "intervention---which is exactly the nuisance-alarm situation that" + NL +
    "alarm-management practice asks to be rationalized " + B + "cite{isa182}. Injected",
    "process-benign; the required action is sensor maintenance rather than process" + NL +
    "intervention, the situation that alarm-management rationalization targets" + NL +
    "(" + B + "cite{isa182}). Injected",
    "formulation dash nuisance")

# --- protocol ---
rep("(a)~" + B + "emph{mode-level} FAs---normal test windows",
    "(a)~" + B + "emph{mode-level} FAs: normal test windows",
    "proto dash a")
rep("(b)~" + B + "emph{variable-level}" + NL +
    "FAs---faults injected into normal test regions",
    "(b)~" + B + "emph{variable-level}" + NL +
    "FAs: faults injected into normal test regions",
    "proto dash b")
rep("a deliberate design choice---the protocol answers the controlled counterfactual" + NL +
    "question---and its transfer to natural alarms is bounded explicitly in",
    "a deliberate design choice (the protocol answers the controlled counterfactual" + NL +
    "question), and its transfer to natural alarms is bounded in",
    "proto dash design")

# --- methods ---
rep("trajectory (no neighbourhood conditioning)---isolates what mode-aware" + NL +
    "replacement adds over global replacement.",
    "trajectory (no neighbourhood conditioning); this isolates what mode-aware" + NL +
    "replacement adds over global replacement.",
    "methods dash regimeglobal")
rep("reconstruction error of channel $j$---the ``deviation reader'' family.",
    "reconstruction error of channel $j$, the ``deviation reader'' family.",
    "methods dash aerec")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in polish P1")
