"""定位重写 v2: 用位置定位替换贡献段, 避开 LaTeX 转义符."""
BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))
s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()

# ============ 1. 摘要重写 ============
i0 = s.find(BS + "abstract{")
i1 = s.find("}", s.find("deviation readers", i0))  # 摘要末尾的 }
if i1 == -1:
    # 备选: 找 keywords 前的 }
    i1 = s.find(BS + "keywords") - 1
old_abstract = s[i0:i1+1]
new_abstract = (BS + "abstract{Anomaly detectors deployed on industrial monitoring systems\n"
    "produce false alarms that existing research reduces in count but does not\n"
    "explain. We formalize false-alarm attribution as a dual-granularity task\n"
    "(variable-level sensor faults vs." + BS + " " + "regime-level unseen modes) with repair\n"
    "actions, and introduce an injection-based ground-truth protocol that\n"
    "enables controlled evaluation of ten attribution methods across five\n"
    "detectors and five testbeds. Three findings emerge. First, attribution\n"
    "quality is governed by a three-way method--detector--fault-type\n"
    "interaction: counterfactual replacement is near-perfect on\n"
    "transformer/SWaT (top-1 0.93) where reconstruction collapses (0.04), the\n"
    "pattern reverses on tree ensembles, and within one family, drift is\n"
    "localized (0.80) but stuck-at faults are missed (0.17). Second,\n"
    "attribution pays off through repair: mode-directed data addition reduces\n"
    "false-alarm rate by 22.1 percentage points over random controls,\n"
    "replicated on a second detector family. Third, the natural-alarm transfer\n"
    "gap is label-efficient: while injected calibration transfers imperfectly\n"
    "(best method 54" + BS + "% human agreement), as few as 10--25 labelled alarms\n"
    "recover 0.57--0.73 for every method. A cost-aware selection rule\n"
    "(DAAS-v2) with conformal bounds operationalizes the matching findings for\n"
    "deployment.}")
s = s[:i0] + new_abstract + s[i1+1:]
print("1. abstract replaced (positional)")

# ============ 2. 发现第三条 ============
f3_start = s.find("Typing is largely solved by calibration")
if f3_start > 0:
    f3_end = s.find("\\end{enumerate}", f3_start)
    old_f3_block = s[f3_start:f3_end].rstrip()
    # 找到 item 的开始
    item_start = s.rfind("\\item", 0, f3_start)
    old_item = s[item_start:f3_end].rstrip()
    new_item = ("\\item \\textbf{Natural-alarm typing is label-efficient.} Injected calibration\n"
        "transfers imperfectly (best method 54" + BS + "% human agreement, five-annotator\n"
        "majority vote, Fleiss $" + BS + "kappa=0.93$), yet re-fitting the threshold on as few\n"
        "as 10--25 labelled natural alarms recovers 0.57--0.73 for every method,\n"
        "making the transfer gap cheap to close in practice. On injected ground\n"
        "truth, typing itself is largely solved by the confidence gate alone\n"
        "(macro-F1 0.69--0.83), a protocol dividend; the remaining difficulty is\n"
        "fine-grained localization.")
    s = s[:item_start] + new_item + "\n" + s[f3_end:]
    print("2. finding 3 replaced (positional)")
else:
    print("2. WARN: finding 3 anchor not found")

# ============ 3. 贡献段 ============
c_start = s.find("\\textbf{Contributions.}")
c_end = s.find("retained for release.", c_start)
if c_start > 0 and c_end > 0:
    c_end += len("retained for release.")
    old_contrib_block = s[c_start:c_end]
    new_contrib = ("\\textbf{Contributions.} (1)~Empirical matching laws: attribution quality is\n"
        "governed by method--detector--fault-type interaction, quantified for the\n"
        "first time across 62 units and 19 detector--data-set pairs; the\n"
        "three-way interaction (e.g., reconstruction wins on drift but misses\n"
        "stuck-at) is a new empirical finding with direct deployment implications.\n"
        "(2)~DAAS-v2, a cost-aware method-selection rule that exceeds the best\n"
        "fixed method (0.83 vs 0.77 top-1) at lower per-window cost, with a\n"
        "leave-one-out conformal bound. (3)~The injection-based protocol (including\n"
        "the injection-caused filter, the first explicit treatment of the pre-alarm\n"
        "confound in injected attribution benchmarks) that makes these findings\n"
        "reproducible. (4)~Repair-loop validation: mode-directed data collection\n"
        "reduces FAR by 22.1 pp over random controls, replicated on a second\n"
        "detector family. (5)~A five-annotator human validation (Fleiss\n"
        "$" + BS + "kappa=0.93$) showing the natural-alarm transfer gap is label-efficient:\n"
        "10--25 labelled alarms recover 0.57--0.73 for every method.\n"
        "(6)~Task formalization with dual-granularity cause space, the RC-CA\n"
        "regime-conditioned attribution mechanism, and an assumption audit\n"
        "delineating when regime conditioning helps. All code, configurations and\n"
        "per-unit results are retained for release.")
    s = s[:c_start] + new_contrib + s[c_end:]
    print("3. contributions replaced (positional)")
else:
    print("3. WARN: contributions anchors not found")

# ============ 4. RC-CA 标签 ============
s = s.replace("\\textbf{RC-CA (reference implementation).}",
              "\\textbf{RC-CA (regime-conditioned attribution).}")
n_ref = s.count("reference implementation RC-CA")
if n_ref > 0:
    s = s.replace("reference implementation RC-CA",
                  "regime-conditioned attribution mechanism RC-CA", 1)
    print(f"4. RC-CA labels updated ({n_ref} intro refs)")
else:
    print("4. RC-CA intro label not found (may be already updated)")

open("Springer_JIIS_FalseAlarmAttribution.tex", "w", encoding="utf-8").write(s)
print("FILE WRITTEN")
