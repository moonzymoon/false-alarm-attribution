# -*- coding: utf-8 -*-
"""DeepSeek round-2 fixes, batch R1: critical corrections (verified against v2 data)."""
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
    print("R1:", tag)

# R1-1 (#20) decomposition paragraph rewrite (v2, arithmetic-consistent)
rep("A decomposition analysis (Supplementary Table~S15; ground-truth correction" + NL +
    "does not restore 100" + B + "% because the mode-conditioned expectation differs" + NL +
    "from the exact pre-injection values and the injected deviation may propagate to" + NL +
    "correlated neighbours that retain elevated scores) pins down the mechanism: the guided and" + NL +
    "injected channels coincide on only 33" + B + "% of instances; among the" + NL +
    "divergent majority, correcting the guided channel clears the alarm in" + NL +
    "36" + B + "% of cases while correcting the injected channel clears it in" + NL +
    B + "emph{none} (0" + B + "%), and divergence concentrates at weak alarm margins" + NL +
    "(40" + B + "% versus 29" + B + "% of weak versus strong instances). At weak injections the" + NL +
    "alarm is driven by the channels the detector watches, often correlated" + NL +
    "neighbours rather than the injected channel itself; correcting the watched" + NL +
    "channel clears it while correcting the injected one does not. This is why repair" + NL +
    "effectiveness and injected-label matching are complementary metrics: the" + NL +
    "former measures operational value, the latter agreement with the" + NL +
    "experimenter's intervention.",
    "A decomposition (instance-weighted across the 14 units; Supplementary" + NL +
    "Table~S15) pins down the mechanism. The guided and injected channels coincide" + NL +
    "on 36" + B + "% of variable-type instances (per unit 0--55" + B + "%). Among the" + NL +
    "divergent majority, correcting the " + B + "emph{guided} channel still clears the alarm" + NL +
    "in 85" + B + "% of cases, whereas correcting the " + B + "emph{injected} channel clears it in" + NL +
    "43" + B + "%, and almost only in instances the guided correction also clears: the" + NL +
    "injected channel clears an alarm that the guided channel does not in merely" + NL +
    "1" + B + "% of divergent cases. The guided correction therefore dominates the label" + NL +
    "correction operationally even when the two disagree---the channels the detector" + NL +
    "watches carry the removable signal. Divergence is more frequent at weak alarm" + NL +
    "margins (67" + B + "% of weak- versus 50" + B + "% of strong-margin instances), where correlated" + NL +
    "neighbours rather than the injected channel drive the score. By the same" + NL +
    "accounting, ground-truth correction restores 59" + B + "% overall (57--83" + B + "% per unit," + NL +
    "Table~S7), so the 86" + B + "%-versus-59" + B + "% guided advantage over the injected label is the" + NL +
    "operationally meaningful gap; neither correction restores 100" + B + "% because the" + NL +
    "mode-conditioned expectation differs from the exact pre-injection values. This" + NL +
    "is why repair effectiveness and injected-label matching are complementary" + NL +
    "metrics: the former measures operational value, the latter agreement with the" + NL +
    "experimenter's intervention.",
    "decomposition rewrite (v2)")

# R1-2 (#18) Granger random-baseline sentence with measured joint share 24%
rep("$2/d$ for joint two-channel ground truths, averaging about $1.35/d$ because roughly" + NL +
    "a third of variable-type instances are joint injections).",
    "$2/d$ for joint two-channel ground truths; a measured 24" + B + "% of variable-type" + NL +
    "instances are joint, so the expectation is about $1.24/d" + B + "approx 0.048$).",
    "granger joint share")

# R1-3 (#9) seed paragraph: RegimeGlobal exclusion note
rep("The OCSVM" + NL +
    "column is different: per-method swings reach 0.15 (AERec) and the best method" + NL +
    "alternates across three different families (GlobalCF, AERec, CondAttr), so we" + NL +
    "flag the OCSVM column as indicative only, consistent with the marginal OCSVM" + NL +
    "premium noted above.",
    "The OCSVM" + NL +
    "column is different: per-method swings reach 0.15 (AERec) and the best method" + NL +
    "alternates across three different families (GlobalCF, AERec, CondAttr), so we" + NL +
    "flag the OCSVM column as indicative only, consistent with the marginal OCSVM" + NL +
    "premium noted above. (RegimeGlobal was not rerun under the extra seeds; the" + NL +
    "seed-0 column winner on OCSVM, RegimeGlobal 0.870, is therefore untested for" + NL +
    "seed stability, which strengthens the indicative-only reading.)",
    "regimeglobal seed note")

# R1-4 (#22) naive wording with explicit reference frame
rep("naive alarm supplementation is " + B + "emph{ineffective} ($-2.6$" + B + "pp): alarm windows" + NL +
    "are extreme, unrepresentative samples of the missing mode.",
    "naive alarm supplementation is " + B + "emph{ineffective}: it reduces FAR by only" + NL +
    "+3.1" + B + "pp{} on its own, 2.6" + B + "pp{} below the random control. Alarm windows are" + NL +
    "extreme, unrepresentative samples of the missing mode.",
    "naive reference frame")

# R1-5 (#21) seed repair range subset clarity + (#28) SWaT-5 membership
rep("keeps seed-level means between +10.5 and +18.3 pp overall and the sign within a unit stable in 7 of 9 units (e.g., SWaT-5: +42 to +67 pp; Supplementary Table~S16).",
    "keeps seed-level means between +10.5 and +18.3 pp on that nine-unit subset" + NL +
    "(versus +22.1 pp on the full 14) and the sign within a unit stable in 7 of 9 units" + NL +
    "(SWaT-5, one of the nine: +42 to +67 pp; Supplementary Table~S16).",
    "seed repair subset")

# R1-6 (#19) compound chance with d values
rep("against a $3/d$ chance level of about 0.12), so compound micro-shifts are a",
    "against an instance-weighted $3/d$ chance level of 0.13 over the six units," + NL +
    "$d" + B + "in" + B + "{51,38,15" + B + "}$), so compound micro-shifts are a",
    "compound chance level")

# R1-7 (#5/#26) Random gate wording + asymmetry explanation
rep("Random" + NL +
    "uses $" + B + "kappa=" + B + "max_j" + B + "phi_j$, so its gate degenerates to a chance-level cut.",
    "Random" + NL +
    "uses $" + B + "kappa=" + B + "max_j" + B + "phi_j$, the maximum of $d$ uniforms, so its gate operates on a" + NL +
    "random statistic; the calibrated $" + B + "gamma$ positions the cut, and because mode-level" + NL +
    "instances outnumber variable-level ones in most units, its macro-F1-optimal cut" + NL +
    "types many windows as mode (recall asymmetry 0.70 versus 0.28 in" + NL +
    "Table~" + B + "ref{tab:main})---class prior, not attribution signal.",
    "random gate wording")

# R1-8 (#8/#27) random repair 11% explanation
rep("resolves 91" + B + "% of" + NL +
    "variable-type FAs (mean over the 14 isolation-forest units of the repair study, Supplementary Table~S7) versus 11" + B + "% for a random channel, and ",
    "resolves 91" + B + "% of" + NL +
    "variable-type FAs (mean over the 14 isolation-forest units of the repair study," + NL +
    "Supplementary Table~S7) versus 11" + B + "% for a random channel. The random control sits" + NL +
    "well above the $1/d$ label-guessing level because replacing " + B + "emph{any} channel with its" + NL +
    "mode-conditioned expectation can clear a marginal alarm; the attribution value is" + NL +
    "therefore the eight-fold lift over this any-replacement control, not the distance" + NL +
    "from zero. Guided correction also ",
    "random repair 11pct explanation")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in R1")
