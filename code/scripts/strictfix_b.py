# -*- coding: utf-8 -*-
"""Strict-review fix batch B: results / discussion / limitations / declarations."""
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
    print("B:", tag)

# B1. garbled transformer caveat passage + wrong 54-window count + lowercase restart
rep("The transformer evidence rests on a" + NL +
    "single 54-window unit (the AT/SMD stream yields too few injection-caused" + NL +
    "alarms to qualify), so we treat its direction, window-level resampling" + NL +
    "within the unit (Supplementary Table~S3) confirms it, but broader transformer" + NL +
    "coverage remains future work. The mirror symmetry between the tree ensemble and the transformer should be interpreted with the caveat that window length (16 for iforest/MIL, 100 for AT) is coupled with detector identity in our design; we cannot fully separate architecture from window-length effects." + NL +
    "flattened-window tree ensembles saturate under single-channel extremes,",
    "The transformer evidence rests on a" + NL +
    "single unit (the AT/SMD stream yields too few injection-caused alarms to" + NL +
    "qualify), so we treat its direction as suggestive: window-level resampling" + NL +
    "within the unit (Supplementary Table~S3) confirms it, but broader transformer" + NL +
    "coverage remains future work. The mirror symmetry between the tree ensemble" + NL +
    "and the transformer also carries the caveat that window length (16 for" + NL +
    "iforest/MIL, 100 for AT) is coupled with detector identity in our design, so" + NL +
    "we cannot fully separate architecture from window-length effects. A" + NL +
    "mechanistic sketch: flattened-window tree ensembles saturate under" + NL +
    "single-channel extremes,",
    "transformer caveat passage")

# B2. smooth-detector range update
rep(B + "emph{Smooth detectors (PCA, OCSVM, transformer, MIL) favour counterfactual" + NL +
    "methods (top-1 0.70--0.96) while the discrete tree ensemble favours",
    B + "emph{Smooth detectors (PCA, OCSVM, transformer, MIL) favour counterfactual" + NL +
    "methods (top-1 0.68--0.96) while the discrete tree ensemble favours",
    "smooth range 0.68")

# B3. Grad/Granger table rows onto separate lines (cosmetic)
rep("Grad        & -- & -- & -- & -- & 0.646" + B + B + "Granger      & 0.045 & 0.000 & 0.000 & 0.019 & 0.000" + B + B,
    "Grad         & -- & -- & -- & -- & 0.646 " + B + B + NL +
    "Granger      & 0.045 & 0.000 & 0.000 & 0.019 & 0.000 " + B + B,
    "Grad row split")

# B4. CondAttr masked-context double parenthetical
rep("A masked-context retrieval variant of CondAttr (retrieval distances computed after zeroing the target channel in both query and database windows) (retrieval distances computed on non-target" + NL +
    "channels, as in the original paper) " + B + "emph{underperforms}",
    "A masked-context retrieval variant of CondAttr (retrieval distances computed" + NL +
    "after zeroing the target channel in both the query and the database windows)" + NL +
    B + "emph{underperforms}",
    "masked-context parens")

# B5. Table~ref{fig:repair} -> Figure
rep("the primary contrast over 14 units in Table~" + B + "ref{fig:repair}/S6,",
    "the primary contrast over 14 units in Figure~" + B + "ref{fig:repair}/Table~S6,",
    "fig/table ref")

# B6. beta-curve overclaim (non-monotone GlobalCF)
rep("show a clean monotone recovery of counterfactual localization with drift" + NL +
    "rate on SWaT (GlobalCF top-1 0.13$" + B + "to$0.91 for $" + B + "beta{=}0.1" + B + "to0.4$) with a" + NL +
    "weak-injection regime below $" + B + "beta" + B + "approx0.1$ where all counterfactual" + NL +
    "methods degrade---the limitation anticipated by the protocol design; the" + NL +
    "causal-influence baseline stays at zero throughout.",
    "show a sharp recovery of counterfactual localization with drift rate on" + NL +
    "SWaT (GlobalCF top-1 0.13 at $" + B + "beta{=}0.1$ rising to 0.91 at $" + B + "beta{=}0.2$;" + NL +
    "RC-CA and CondAttr increase monotonically through $" + B + "beta{=}0.4$, where" + NL +
    "CondAttr reaches 0.99, while GlobalCF dips to 0.84) with a weak-injection" + NL +
    "regime below $" + B + "beta" + B + "approx0.1$ where all counterfactual methods" + NL +
    "degrade---the limitation anticipated by the protocol design; the" + NL +
    "causal-influence baseline stays at zero throughout.",
    "beta curve honesty")

# B7. fig_beta caption monotone -> sharp
rep(B + "caption{Variable-type top-1 versus drift rate $" + B + "beta$ on the" + NL +
    "isolation-forest detector. Counterfactual methods recover monotonically" + NL +
    "with injection strength on SWaT and degrade in the weak-injection regime;",
    B + "caption{Variable-type top-1 versus drift rate $" + B + "beta$ on the" + NL +
    "isolation-forest detector. Counterfactual methods recover sharply" + NL +
    "with injection strength on SWaT and degrade in the weak-injection regime;",
    "beta caption")

# B8. FAR1% "ordering preserved" nuance
rep("At the stricter 1" + B + "% target the ordering is preserved (AERec 0.818," + NL +
    "RC-CA 0.636, GlobalCF 0.599, Granger 0.737 with top-1 0.02; 11 units qualify),",
    "At the stricter 1" + B + "% target the AERec lead is preserved (AERec 0.818" + NL +
    "versus RC-CA 0.636 and GlobalCF 0.599; Granger's typing rises to 0.737 but" + NL +
    "its top-1 stays at 0.02; 11 units qualify),",
    "FAR1 wording")

# B9. repair note out of mid-sentence
rep("evaluating on " + B + "emph{all} normal windows of" + NL +
    "(Note: the mode-level repair experiment is intentionally constructed to be self-consistent---the held-out mode is restored by design. Its value lies in the contrast between directed and random supplementation, which tests whether knowing the cause type leads to better data collection strategy. The variable-level repair, where the guided channel differs from the injected channel in 67" + B + "% of cases, is the non-circular evidence.)" + NL +
    "the held-out mode under the fixed base threshold.",
    "evaluating on " + B + "emph{all} normal windows of the held-out mode under the" + NL +
    "fixed base threshold. (Note: the mode-level repair experiment is intentionally" + NL +
    "constructed to be self-consistent---the held-out mode is restored by design;" + NL +
    "its value lies in the directed-versus-random contrast, which tests whether" + NL +
    "knowing the cause type leads to a better data-collection strategy. The" + NL +
    "variable-level repair, where the guided channel differs from the injected" + NL +
    "channel in 67" + B + "% of cases, is the non-circular evidence.)",
    "repair note relocation")

# B10. decomposition double parenthetical
rep("A decomposition analysis (GT correction does not restore 100" + B + "% because the mode-conditioned expectation differs from exact pre-injection values and correlated channels may retain elevated scores)" + NL +
    "(Supplementary Table~S15) pins down the mechanism",
    "A decomposition analysis (Supplementary Table~S15; ground-truth correction" + NL +
    "does not restore 100" + B + "% because the mode-conditioned expectation differs" + NL +
    "from the exact pre-injection values and correlated channels may retain" + NL +
    "elevated scores) pins down the mechanism",
    "decomposition parens")

# B11. A1 garbled phrase
rep("(A1) the scorer responds differently to same-marginal different-joint windows structure at" + NL +
    "fixed marginals; (A2)",
    "(A1) the scorer responds differently to windows that share the same" + NL +
    "per-channel marginals but differ in joint (cross-channel and temporal)" + NL +
    "structure; (A2)",
    "A1 wording")

# B12. A1 triple parens
rep(B + "emph{A1 test:} permuting each" + NL +
    "channel's within-window order (which preserves every channel's" + NL +
    "within-window marginal---the multiset of values---while destroying joint" + NL +
    "temporal alignment) moves scores by only 0.01--0.11 score standard deviations (note: this permutation also destroys within-channel autocorrelation, so the result bounds sensitivity to both joint structure and temporal ordering) (new-alarm rate 0.3--1.3" + B + "%)",
    B + "emph{A1 test:} permuting each channel's within-window order---which preserves" + NL +
    "every channel's within-window marginal (the multiset of values) while" + NL +
    "destroying joint temporal alignment and within-channel autocorrelation, so" + NL +
    "the result bounds sensitivity to both---moves scores by only 0.01--0.11 score" + NL +
    "standard deviations (new-alarm rate 0.3--1.3" + B + "%)",
    "A1 parens")

# B13. intelligent information systems -> data-analysis systems
rep("Within the scope of intelligent information systems, the protocol",
    "Within the scope of intelligent data-analysis systems, the protocol",
    "venue wording")

# B14. limitations double-First + fourfold + single/dual channel
rep("The protocol's boundaries are threefold. First, injected faults are structured single/dual-channel deviations and the protocol structurally favours learned deviation readers (quantified via margin stratification); real false alarms may involve multivariate micro-shifts, concept drift, or detector overfitting that our injections do not cover. First, injected causes are input" + NL +
    "deviations by construction; the learned-reconstruction advantage partly" + NL +
    "reflects this structural preference (quantified in Section~" + B + "ref{sec:margin})," + NL +
    "and rejection thresholds calibrated on injected data transfer only partially" + NL +
    "to natural alarms (58--71" + B + "% cross-method agreement). Second, coverage:",
    "The protocol's boundaries are fourfold. First, injected faults are" + NL +
    "structured single-channel deviations, and real false alarms may involve" + NL +
    "multivariate micro-shifts, concept drift, or detector overfitting that our" + NL +
    "injections do not cover. Second, injected causes are input deviations by" + NL +
    "construction; the learned-reconstruction advantage partly reflects this" + NL +
    "structural preference (quantified in Section~" + B + "ref{sec:margin}), and" + NL +
    "rejection thresholds calibrated on injected data transfer only partially to" + NL +
    "natural alarms (58--71" + B + "% cross-method agreement). Third, coverage:",
    "limitations renumber 1")

rep("limiting comparability. Third, the five testbeds span specific industrial domains",
    "limiting comparability. Fourth, the five testbeds span specific industrial domains",
    "limitations renumber 2")

# B15. move statistical-power paragraph from Conclusion to Limitations end
rep("attribution value realized in repair actions." + NL + NL +
    "A practical limitation is statistical power: 58 evaluation units across five detectors limit the ability to" + NL +
    "distinguish methods; reported equivalence should be read as insufficient evidence" + NL +
    "rather than proven equivalence. Several open problems remain.",
    "attribution value realized in repair actions." + NL + NL +
    "Several open problems remain.",
    "remove power para from conclusion")
rep("for statistical coherence rather than physical semantics." + NL + NL +
    B + "section{Conclusion}",
    "for statistical coherence rather than physical semantics. Finally, a" + NL +
    "practical constraint is statistical power: 58 evaluation units across five" + NL +
    "detectors limit the ability to distinguish methods, so reported equivalence" + NL +
    "should be read as insufficient evidence rather than proven equivalence." + NL + NL +
    B + "section{Conclusion}",
    "power para to limitations")

# B16. 68 archived files -> uncounted
rep("all 68 archived result files, and one-command reproduction scripts",
    "all archived result files, and one-command reproduction scripts",
    "uncount caches")

# B17. duplicate author-contribution line
rep(B + "textbf{Author contribution:} provided on the Title Page (withheld here for anonymized review)." + NL +
    B + "textbf{Author contribution:} provided on the Title Page (withheld here for anonymized review).",
    B + "textbf{Author contribution:} provided on the Title Page (withheld here for anonymized review).",
    "dup contribution")

# B18. from the author -> from the corresponding author
rep("are detailed in Supplementary Tables~S1--S16 and are available from the author on reasonable request.",
    "are detailed in Supplementary Tables~S1--S16 and are available from the corresponding author on reasonable request.",
    "corresponding author")

# B19. proposition framing remark
rep(B + "end{proposition}" + NL + NL + B + "section*{Declarations}",
    B + "end{proposition}" + NL + NL +
    B + "noindent The condition is deliberately minimal---a necessary sensitivity" + NL +
    "requirement rather than a sufficiency theorem. Its value is to connect the" + NL +
    "empirical matching pattern to a scorer-level property, which the matching" + NL +
    "study then measures." + NL + NL + B + "section*{Declarations}",
    "proposition remark")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in batch B")
