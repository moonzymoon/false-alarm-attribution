# -*- coding: utf-8 -*-
"""Style polish P2: results/discussion em-dashes, Granger rewrite, adverbs."""
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
    print("P2:", tag)

# --- results: main comparison ---
rep("(not the window) as the exchangeable unit---windows within a unit share a" + NL +
    "detector, threshold and injection configuration,",
    "(not the window) as the exchangeable unit: windows within a unit share a" + NL +
    "detector, threshold and injection configuration,",
    "res dash exchangeable")
rep("RC-CA (0.697) and CondAttr (0.692)---all pairwise counterfactual-family" + NL +
    "differences have CIs covering zero---while all clearly exceed Random (0.474).",
    "RC-CA (0.697) and CondAttr (0.692); all pairwise counterfactual-family" + NL +
    "differences have CIs covering zero, and all clearly exceed Random (0.474).",
    "res dash indistinguishable")
rep("far below the learned AERec (0.828/0.754)---what" + NL +
    "wins is a reconstruction model trained on the normal pool, not deviation" + NL +
    "reading per se.",
    "far below the learned AERec (0.828/0.754); what" + NL +
    "wins is a reconstruction model trained on the normal pool, not deviation" + NL +
    "reading per se.",
    "res dash zdev")

# --- results: Granger monster sentence rewrite (style only, all facts kept) ---
rep("yet fails to localize injected faults (top-1 0.045, below the random baseline of 1/d; this is expected because Granger importance measures prediction contribution under normal dynamics, so normal channels score higher than faulted ones---the ranking is inverted relative to the task; simply negating the score would give a trivially high-rank normal channel, not the faulted one, because the metric measures causal influence rather than deviation)---fault" + NL +
    "injection shifts a channel's value, not its predictability structure, so" + NL +
    "influence-based rankings from normal behaviour are the wrong instrument for" + NL +
    "fault localization even though they separate the two cause families.",
    "yet fails to localize injected faults (top-1 0.045, below the random baseline of" + NL +
    "1/d). The failure is expected. Granger importance measures prediction" + NL +
    "contribution under normal dynamics, so normal channels score higher than" + NL +
    "faulted ones and the ranking is inverted relative to the task; negating the" + NL +
    "score would not help either, since that would promote a trivially high-ranked" + NL +
    "normal channel rather than the faulted one. The metric captures causal" + NL +
    "influence, not deviation, and fault injection shifts a channel's value, not" + NL +
    "its predictability structure. Influence-based rankings from normal behaviour" + NL +
    "are therefore the wrong instrument for fault localization, even though they" + NL +
    "separate the two cause families.",
    "Granger rewrite")

# --- results: matching ---
rep("counterfactual replacement is nearly perfect---GlobalCF and RC-CA top-1" + NL +
    "0.93 [0.89, 0.96] (window-level bootstrap)---while AERec collapses to",
    "counterfactual replacement is nearly perfect (GlobalCF and RC-CA top-1" + NL +
    "0.93 [0.89, 0.96], window-level bootstrap), while AERec collapses to",
    "match dash perfect")

# --- margin ---
rep("favours this family---a usage caveat we make explicit rather than hide.",
    "favours this family; we make this usage caveat explicit rather than hide it.",
    "margin dash caveat")

# --- ablations ---
rep("GlobalCF [0.30, 0.55]---method ordering is preserved under the more conservative uncertainty model.",
    "GlobalCF [0.30, 0.55]: method ordering is preserved under the more conservative uncertainty model.",
    "abl dash ordering")
rep("degrade---the limitation anticipated by the protocol design; the",
    "degrade, which is the limitation anticipated by the protocol design; the",
    "abl dash degrade")

# --- repair ---
rep("constructed to be self-consistent---the held-out mode is restored by design;",
    "constructed to be self-consistent: the held-out mode is restored by design;",
    "repair dash selfcon")
rep("naive alarm supplementation is " + B + "emph{ineffective} ($-2.6$" + B + "pp)---alarm windows" + NL +
    "are extreme, unrepresentative samples of the missing mode.",
    "naive alarm supplementation is " + B + "emph{ineffective} ($-2.6$" + B + "pp): alarm windows" + NL +
    "are extreme, unrepresentative samples of the missing mode.",
    "repair dash naive")
rep("time---in practice, ``collect current-mode data'' means collecting recent",
    "time. In practice, ``collect current-mode data'' means collecting recent",
    "repair dash practice")
rep("versus 11" + B + "% for a random channel---and, remarkably," + NL +
    B + "emph{exceeds} ground-truth-channel correction (57--83" + B + "%).",
    "versus 11" + B + "% for a random channel, and " + NL +
    B + "emph{exceeds} ground-truth-channel correction (57--83" + B + "%).",
    "repair dash remarkably")
rep("alarm is driven by the channels the detector watches---often correlated" + NL +
    "neighbours rather than the injected channel itself---so correcting the" + NL +
    "watched channel clears it while correcting the injected one does not.",
    "alarm is driven by the channels the detector watches, often correlated" + NL +
    "neighbours rather than the injected channel itself; correcting the watched" + NL +
    "channel clears it while correcting the injected one does not.",
    "repair dash watches")

# --- natural FAs ---
rep("not solve---a boundary of the protocol stated explicitly.",
    "not solve; we state this boundary of the protocol openly.",
    "natural dash boundary")

# --- audit ---
rep(B + "emph{A1 test:} permuting each channel's within-window order---which preserves" + NL +
    "every channel's within-window marginal (the multiset of values) while" + NL +
    "destroying joint temporal alignment and within-channel autocorrelation, so" + NL +
    "the result bounds sensitivity to both---moves scores by only 0.01--0.11 score" + NL +
    "standard deviations (new-alarm rate 0.3--1.3" + B + "%)",
    B + "emph{A1 test:} permuting each channel's within-window order (which preserves" + NL +
    "every channel's within-window marginal, the multiset of values, while" + NL +
    "destroying joint temporal alignment and within-channel autocorrelation, so" + NL +
    "the result bounds sensitivity to both) moves scores by only 0.01--0.11 score" + NL +
    "standard deviations (new-alarm rate 0.3--1.3" + B + "%)",
    "audit dash A1")
rep("offset magnitude)---a concrete" + NL +
    "counterexample to A4.",
    "offset magnitude): a concrete" + NL +
    "counterexample to A4.",
    "audit dash A4")
rep("value must be re-validated per detector---which is precisely what the" + NL +
    "matching study above provides.",
    "value must be re-validated per detector, which is what the" + NL +
    "matching study above provides.",
    "audit dash precisely")

# --- discussion/conclusion ---
rep("ensembles), and do not spend effort on exotic typing mechanisms---a" + NL +
    "calibrated rejection rule is a strong, cheap baseline.",
    "ensembles), and do not spend effort on exotic typing mechanisms: a" + NL +
    "calibrated rejection rule is a strong, cheap baseline.",
    "disc dash mechanisms")
rep("method--detector matching as the governing factor for localization---with" + NL +
    "attribution value realized in repair actions.",
    "method--detector matching as the governing factor for localization, with" + NL +
    "attribution value realized in repair actions.",
    "conc dash governing")
rep(B + "noindent The condition is deliberately minimal---a necessary sensitivity" + NL +
    "requirement rather than a sufficiency theorem.",
    B + "noindent The condition is minimal, a necessary sensitivity" + NL +
    "requirement rather than a sufficiency theorem.",
    "prop dash minimal")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in polish P2")
