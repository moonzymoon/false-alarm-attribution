"""定位重写: 摘要(扬长避短) + 发现第三条(label-efficient) + 贡献段(发现优先) + RC-CA标签."""
BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))
s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()

# ============ 1. 摘要重写 (~200 词, 扬长避短) ============
old_abstract = ("""\\abstract{Alarm management is a core reliability module of industrial
monitoring, yet anomaly detectors produce false alarms that research
reduces in count, not cause. We formalize
false-alarm attribution: given an alarm on a process-normal window, decide
whether the cause is variable-level (sensor drift, stuck-at) or
regime-level (an unseen mode) with a repair action.
Real false alarms carry no cause labels, so we introduce an
injection-based mixed ground-truth protocol: under one detector and
threshold, variable-level alarms are created by controlled fault injection
(injection-caused) and regime-level alarms by holding out one mode
before retraining; a two-layer evaluation with calibrated
rejection compares ten methods. Across five testbeds
and five detectors, three findings emerge: (i) attribution quality
is governed by method--detector--data-set matching: counterfactual
replacement is near-perfect on a transformer/SWaT pairing (top-1 0.93;
one pairing)
where a reconstruction baseline collapses (0.04), the pattern reversing on
tree ensembles; (ii) attribution pays off through repair:
mode-directed data addition beats a random control by 22.1 percentage
points; correcting the indicated channel resolves 91\\% of
variable alarms (random: 11\\%); (iii) typing on injected ground truth is largely solved
by the confidence gate alone (macro-F1 0.69--0.74; 0.83 learned
reader), redirecting effort to
localization and quantifying the protocol's preference for
deviation readers.}""")

new_abstract = ("""\\abstract{Anomaly detectors deployed on industrial monitoring systems
produce false alarms that existing research reduces in count but does not
explain. We formalize false-alarm attribution as a dual-granularity task
(variable-level sensor faults vs.\\ regime-level unseen modes) with repair
actions, and introduce an injection-based ground-truth protocol that
enables controlled evaluation of ten attribution methods across five
detectors and five testbeds. Three findings emerge. First, attribution
quality is governed by a three-way method--detector--fault-type
interaction: counterfactual replacement is near-perfect on
transformer/SWaT (top-1 0.93) where reconstruction collapses (0.04), the
pattern reverses on tree ensembles, and within one family, drift is
localized (0.80) but stuck-at faults are missed (0.17). Second,
attribution pays off through repair: mode-directed data addition reduces
false-alarm rate by 22.1 percentage points over random controls,
replicated on a second detector family. Third, the natural-alarm transfer
gap is label-efficient: while injected calibration transfers imperfectly
(best method 54\\% human agreement), as few as 10--25 labelled alarms
recover 0.57--0.73 for every method. A cost-aware selection rule
(DAAS-v2) with conformal bounds operationalizes the matching findings for
deployment.}""")

assert old_abstract in s, "abstract not found"
s = s.replace(old_abstract, new_abstract)
print("1. abstract rewritten")

# ============ 2. 发现第三条重写 ============
old_f3 = """\\item \\textbf{Typing is largely solved by calibration; the protocol audit delimits
its boundaries.} A calibrated confidence gate alone reaches macro-F1 0.69--0.74 across
counterfactual methods on injected cause typing (0.83 with the learned reader;
natural-alarm typing remains open), but the calibration data come from
the injected validation
split: a protocol dividend rather than a method-design advantage. The remaining difficulty is
fine-grained localization, where the injection-protocol preference for
deviation readers is explicitly quantified and bounded."""

new_f3 = """\\item \\textbf{Natural-alarm typing is label-efficient.} Injected calibration
transfers imperfectly (best method 54\\% human agreement, five-annotator
majority vote, Fleiss $\\kappa=0.93$), yet re-fitting the threshold on as few
as 10--25 labelled natural alarms recovers 0.57--0.73 for every method,
making the transfer gap cheap to close in practice. On injected ground
truth, typing itself is largely solved by the confidence gate alone
(macro-F1 0.69--0.83), a protocol dividend; the remaining difficulty is
fine-grained localization."""

assert old_f3 in s, "finding 3 not found"
s = s.replace(old_f3, new_f3)
print("2. finding 3 rewritten")

# ============ 3. 贡献段重写 ============
old_contrib = """\\textbf{Contributions.} (1)~Formalization of false-alarm attribution with a
dual-granularity cause space and repair mapping. (2)~The injection-based
mixed ground-truth protocol, including the injection-caused filter, the
effective-mode selection rule, and the calibrated two-layer evaluation with
oracle controls. (3)~The method--detector matching study across nine
non-trivial attribution families (plus a random control), five detectors and five testbeds, with bootstrap confidence
intervals. (4)~The repair-loop validation and the repair-effectiveness
metric. (5)~DAAS, a detector-aware selection rule that, for localization, matches or
outperforms any single fixed method, and its cost-aware variant DAAS-v2, which
exceeds the best fixed method in accuracy at roughly half its per-window cost with an
empirical leave-one-out conformal regret bound. (6)~An open reference implementation of one such mechanism (RC-CA)
with the assumption audit, a study instrument for testing when regime-conditioning helps rather than a claim of
method superiority; the audit's negative results are themselves findings that
delimit the mechanism's applicability, not a failure of the tool. All code, protocol configuration
and per-unit results are retained for release."""

new_contrib = """\\textbf{Contributions.} (1)~Empirical matching laws: attribution quality is
governed by method--detector--fault-type interaction, quantified for the
first time across 62 units and 19 detector--data-set pairs; the
three-way interaction (e.g., reconstruction wins on drift but misses
stuck-at) is a new empirical finding with direct deployment implications.
(2)~DAAS-v2, a cost-aware method-selection rule that exceeds the best
fixed method (0.83 vs 0.77 top-1) at lower per-window cost, with a
leave-one-out conformal bound. (3)~The injection-based protocol (including
the injection-caused filter, the first explicit treatment of the pre-alarm
confound in injected attribution benchmarks) that makes these findings
reproducible. (4)~Repair-loop validation: mode-directed data collection
reduces FAR by 22.1 pp over random controls, replicated on a second
detector family. (5)~A five-annotator human validation (Fleiss
$\\kappa=0.93$) showing the natural-alarm transfer gap is label-efficient:
10--25 labelled alarms recover 0.57--0.73 for every method.
(6)~Task formalization with dual-granularity cause space, the RC-CA
regime-conditioned attribution mechanism, and an assumption audit
delineating when regime conditioning helps. All code, configurations and
per-unit results are retained for release."""

assert old_contrib in s, "contributions not found"
s = s.replace(old_contrib, new_contrib)
print("3. contributions rewritten")

# ============ 4. RC-CA 标签: 方法节 ============
old_rcca = "\\textbf{RC-CA (reference implementation).}"
new_rcca = "\\textbf{RC-CA (regime-conditioned attribution).}"
if old_rcca in s:
    s = s.replace(old_rcca, new_rcca)
    print("4a. RC-CA method-section label updated")
else:
    print("4a. RC-CA label already updated or not found")

# 相关工作中的 reference implementation
old_rcca2 = "our reference implementation RC-CA"
new_rcca2 = "our regime-conditioned attribution mechanism RC-CA"
c = s.count(old_rcca2)
if c >= 1:
    s = s.replace(old_rcca2, new_rcca2, 1)
    print(f"4b. RC-CA intro label updated ({c} occurrences, changed first)")
else:
    print("4b. RC-CA intro label not found")

open("Springer_JIIS_FalseAlarmAttribution.tex", "w", encoding="utf-8").write(s)
print("FILE WRITTEN")
