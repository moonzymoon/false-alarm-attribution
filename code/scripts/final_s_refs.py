BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))
s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()

# 1) S 范围 S1-S20 -> S1-S24
n = s.count("S1--S20")
s = s.replace("S1--S20", "S1--S24")
print("S range:", n, "places updated")

# 2) 匹配节: 故障类型特异性一句 (最短可加的)
old = "The matching relation is detector--data-set specific rather than detector-generic."
new = ("The matching relation is detector--data-set specific rather than detector-generic, "
       "and also fault-type-specific: AERec excels on linear drift (top-1 0.80) but collapses "
       "on stuck-at faults (0.17), while CondAttr shows the reverse (0.52/0.69), so the "
       "injection mixture shifts the comparison (Table~S21 of Online Resource~1).")
assert s.count(old) == 1
s = s.replace(old, new)

# 3) 消融节: 加一句引用运行时表
old2 = "at 50--200 times more per-window cost."
new2 = "at 50--200 times more per-window cost (full complexity and runtime comparison: Table~S22 of Online Resource~1)."
assert s.count(old2) == 1
s = s.replace(old2, new2)

# 4) Discussion: 部署指南引用
old3 = "For practitioners the results read as a selection guide: deploy DAAS"
new3 = "For practitioners the results read as a selection guide (condensed in Table~S24 of Online Resource~1): deploy DAAS"
assert s.count(old3) == 1
s = s.replace(old3, new3)

open("Springer_JIIS_FalseAlarmAttribution.tex", "w", encoding="utf-8").write(s)
print("main text updated with S21/S22/S24 refs")

# 5) SI 摘要范围
t = open("JIIS_SI.tex", encoding="utf-8").read()
t = t.replace("Tables S1--S20", "Tables S1--S24")
open("JIIS_SI.tex", "w", encoding="utf-8").write(t)
print("SI range updated")
