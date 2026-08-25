BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))
s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()
subs = [
    ("SMAP is an intriguing case where both AERec (top-1 0.987)\nand GlobalCF (top-1 0.962) are near-perfect, suggesting some data sets make\nattribution easy regardless of method family.",
     "On SMAP both families are near-perfect (AERec 0.987, GlobalCF 0.962),\nsuggesting some data sets make attribution easy regardless of family."),
    ("the online\ncomponent is a fixed lookup, and the 400-alarm transfer probe of\nSection~" + BS + "ref{sec:natural} is the audit a site should run before trusting\nthe verdicts on its natural alarms.",
     "the online component is a fixed lookup, and the 400-alarm transfer probe\n(Section~" + BS + "ref{sec:natural}) is the audit a site should run first."),
]
for old, new in subs:
    assert s.count(old) == 1, old[:40]
    s = s.replace(old, new)
open("Springer_JIIS_FalseAlarmAttribution.tex", "w", encoding="utf-8").write(s)
print("2 trims applied")
