# -*- coding: utf-8 -*-
"""Strict-review fix batch A: intro / related work / protocol / methods."""
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
    print("A:", tag)

# A1. stale "19 units"
rep("the quantification across 19 units provides the first empirical selection basis",
    "the quantification across 58 units and 15 detector--data-set pairs provides the first empirical selection basis",
    "19 units -> 58 units")

# A2. JIIS paragraph -> anomaly-diagnosis reasoning paragraph (venue-neutral, +Time-RA)
old_jiis = (B + "textbf{Anomaly detection in JIIS.} Recent work in this journal includes" + NL +
            "contrastive representation learning for time-series anomaly detection" + NL +
            "and continual anomaly detection with change-point methods, confirming the" + NL +
            "venue" + B + "'s interest in our problem domain.")
new_jiis = (B + "textbf{Anomaly diagnosis and reasoning.} A recent line of work reframes" + NL +
            "anomaly diagnosis as a reasoning task: Time-RA " + B + "cite{yang2026timera}" + NL +
            "couples time-series detection with LLM feedback over a multimodal benchmark," + NL +
            "targeting fine-grained categorization and explanatory text. Such approaches" + NL +
            "are complementary to ours: they generate diagnoses from (large) models and" + NL +
            "annotations, whereas we evaluate post-hoc attribution against injected causal" + NL +
            "ground truth, model-agnostically and without requiring labels on real alarms.")
rep(old_jiis, new_jiis, "JIIS paragraph -> diagnosis reasoning")

# A3. isa182 wording
rep("Qualitative analyses of nuisance alarms exist in" + NL +
    "the alarm-management literature " + B + "cite{isa182}; to our knowledge, no prior",
    "Alarm-management practice requires exactly such rationalization" + NL +
    "(" + B + "cite{isa182}); to our knowledge, no prior",
    "isa182 wording")

# A4. trim duplicated process-level passage in intro
old_intro = ("Throughout this paper, labels are process-level: a drifting or stuck" + NL +
             "sensor channel typically leaves the process operational (though extreme sensor" + NL +
             "failures can propagate; we restrict scope to faults that do not trigger process-level" + NL +
             "safety interlocks)---the remedy is sensor maintenance, not process intervention---which is exactly the nuisance-alarm situation that" + NL +
             "alarm-management practice asks to be rationalized " + B + "cite{isa182}.")
new_intro = ("Throughout, labels are process-level: a drifting or stuck sensor leaves the" + NL +
             "process operational, and the remedy is sensor maintenance rather than process" + NL +
             "intervention---exactly the nuisance-alarm situation that alarm-management" + NL +
             "practice asks to rationalize " + B + "cite{isa182} (scope refined in" + NL +
             "Section~" + B + "ref{sec:formulation}).")
rep(old_intro, new_intro, "intro process-level dedup")

# A5. broken spacing in filter section
rep("original(pre-injection)", "original (pre-injection)", "spacing 1")
rep("faultinjection", "fault injection", "spacing 2")

# A6. interleaved kappa sentence
old_k = ("This single definition makes If all clipped scores sum to zero, $" + B + "kappa=0$." + NL +
         "the rejection rule $" + B + "kappa<" + B + "gamma$" + " comparable across methods.")
new_k = ("This single definition makes the rejection rule $" + B + "kappa<" + B + "gamma$"
         + " comparable across methods. If all clipped scores sum to zero, $" + B + "kappa=0$.")
rep(old_k, new_k, "kappa sentence order")

# A7. remove "two-channel joint drift" (not in main protocol configs)
rep("variance inflation" + NL + "$" + B + "times 5$, two-channel joint drift) whose post-injection score exceeds",
    "variance inflation" + NL + "$" + B + "times 5$) whose post-injection score exceeds",
    "remove joint drift claim")

# A8. floating note in calibration subsection -> proper sentence; add label to natural FAs
old_note = ("(Note: calibrating and testing on injected data is a design choice; the protocol answers the controlled counterfactual question, with transfer bounded by the 58--71" + B + "% cross-method agreement.)" + NL)
new_note = ("")
rep(old_note, new_note, "remove floating note")
rep("well-posed, so we deliberately report no ``mode-ID accuracy''; mode-level" + NL +
    "value is measured by repair outcomes.",
    "well-posed, so we deliberately report no ``mode-ID accuracy''; mode-level" + NL +
    "value is measured by repair outcomes. Calibrating and testing on injected data is" + NL +
    "a deliberate design choice---the protocol answers the controlled counterfactual" + NL +
    "question---and its transfer to natural alarms is bounded explicitly in" + NL +
    "Section~" + B + "ref{sec:natural} (58--71" + B + "% cross-method agreement).",
    "relocate calibration note")
rep(B + "subsection{Natural false alarms}",
    B + "subsection{Natural false alarms}" + B + "label{sec:natural}",
    "label natural FAs")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in batch A")

# append Time-RA bib entry
BIB = r"D:\0科研\工作1\第10篇SCI\paper\references.bib"
bib = io.open(BIB, encoding="utf-8").read()
if "yang2026timera" not in bib:
    bib += NL.join([
        "",
        "@inproceedings{yang2026timera,",
        "  author = {Yang, Yiyuan and Liu, Zichuan and Song, Lei and Ying, Kai and Wang, Zhiguang and Bamford, Tom and Vyetrenko, Svitlana and Bian, Jiang and Wen, Qingsong},",
        "  title = {{Time-RA}: Towards Time Series Reasoning for Anomaly Diagnosis with {LLM} Feedback},",
        "  booktitle = {Findings of the Association for Computational Linguistics: ACL},",
        "  year = {2026},",
        "  note = {arXiv:2507.15066}",
        "}",
        "",
    ])
    io.open(BIB, "w", encoding="utf-8", newline=NL).write(bib)
    print("bib: Time-RA added")
