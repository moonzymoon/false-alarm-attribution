# -*- coding: utf-8 -*-
"""C1-lite integration: 60 units / 17 pairs everywhere, new MIL column, DAAS numbers."""
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
    print("C1:", tag)

# 1. intro finding 1 counts
rep("the quantification across 58 units and 15 detector--data-set pairs provides the first empirical selection basis.",
    "the quantification across 60 units and 17 detector--data-set pairs provides the first empirical selection basis.",
    "intro counts")

# 2. dataset table: MIL column on PSM/SMAP + caption total
rep("PSM & 25 & 220k & 4 & 4 & 7 & -- & -- " + B + B,
    "PSM & 25 & 220k & 4 & 4 & 7 & -- & $1^{v}$ " + B + B,
    "datasets PSM MIL")
rep("SMAP & 25 & 563k & 5 & -- & -- & -- & -- " + B + B,
    "SMAP & 25 & 563k & 5 & -- & -- & -- & $1^{v}$ " + B + B,
    "datasets SMAP MIL")
rep("mixed + 4 variable-level = 58 units.}",
    "mixed + 6 variable-level = 60 units.}",
    "datasets caption total")

# 3. detectors-and-data coverage sentence
rep("detectors (iv)--(v) contribute native variable-level units on SWaT and SMD.",
    "detectors (iv)--(v) contribute native variable-level units (transformer: SWaT and" + NL +
    "SMD; deep MIL: SWaT, SMD, PSM and SMAP, using existing checkpoints).",
    "detector coverage sentence")

# 4. main comparison pointer count
rep("pooling over all 58 units follows in Table~" + B + "ref{tab:detector}.}",
    "pooling over all 60 units follows in Table~" + B + "ref{tab:detector}.}",
    "tab main caption count")

# 5. matching text: MIL range + counterfactual range
rep("on the deep-MIL detector counterfactuals reach" + NL +
    "0.50--0.95.",
    "on the deep-MIL detector counterfactuals reach" + NL +
    "0.50--1.00 across its four testbeds.",
    "mil counterfactual range")
rep(B + "emph{Smooth detectors (PCA, OCSVM, transformer, MIL) favour counterfactual" + NL +
    "methods (top-1 0.68--0.96) while the discrete tree ensemble favours",
    B + "emph{Smooth detectors (PCA, OCSVM, transformer, MIL) favour counterfactual" + NL +
    "methods (top-1 0.50--1.00) while the discrete tree ensemble favours",
    "smooth range")

# 6. DAAS paragraph: 17-pair numbers
rep("cross-validation over the 15 detector--data-set pairs of the matching" + NL +
    "study, both DAAS and the family-level rule recover the exactly-best" + NL +
    "method in 7 of 15 held-out pairs (47" + B + "%), ahead of the best fixed" + NL +
    "strategy (always-AERec, 5 of 15, 33" + B + "%) and the random baseline (11" + B + "%).",
    "cross-validation over the 17 detector--data-set pairs of the matching" + NL +
    "study, the family-level rule recovers the exactly-best method in 8 of 17" + NL +
    "held-out pairs (47" + B + "%) and the method-level rule in 7 of 17 (41" + B + "%), ahead" + NL +
    "of the best fixed strategy (always-AERec, 5 of 17, 29" + B + "%) and the random" + NL +
    "baseline (12" + B + "%).",
    "daas strict numbers")
rep("the rules then cover 11 of 15" + NL +
    "pairs (73" + B + "%) versus 53" + B + "% for the best fixed method.",
    "the rules then cover 12 of 17" + NL +
    "pairs (71" + B + "%) versus 53" + B + "% for the best fixed method.",
    "daas tolerance numbers")
rep("At $n{=}15$ these proportions carry wide binomial uncertainty (95" + B + "% CIs" + NL +
    "overlap: $[0.25,0.70]$ versus $[0.15,0.58]$ strict, $[0.48,0.89]$ versus" + NL +
    "$[0.30,0.75]$ tolerant), so we present the rules as a consistent label-free",
    "At $n{=}17$ these proportions carry wide binomial uncertainty (95" + B + "% CIs" + NL +
    "overlap: $[0.26,0.69]$ versus $[0.13,0.53]$ strict, $[0.47,0.87]$ versus" + NL +
    "$[0.31,0.74]$ tolerant), so we present the rules as a consistent label-free",
    "daas wilson")
rep("none exceeded the table rules (best 33" + B + "% strict / 67" + B + "% tolerant), so at 15 pairs" + NL +
    "the bottleneck is training volume rather than feature expressiveness.",
    "none exceeded the family rule (best 41" + B + "% strict, matching its 71" + B + "% tolerance)," + NL +
    "so at 17 pairs the bottleneck is training volume rather than feature" + NL +
    "expressiveness.",
    "meta on 17 pairs")

# 7. limitations count
rep("practical constraint is statistical power: 58 evaluation units across five",
    "practical constraint is statistical power: 60 evaluation units across five",
    "limitations count")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "C1 integrations applied")
