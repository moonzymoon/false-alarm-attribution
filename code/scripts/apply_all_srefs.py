BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))
s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()

# 1) S 范围
n = s.count("S1--S20")
if n > 0:
    s = s.replace("S1--S20", "S1--S24")
print("S range: %d -> S24" % n)

# 2) 故障类型
old1 = "detector--data-set specific rather than detector-generic."
new1 = ("detector--data-set specific rather than detector-generic, and also\n"
        "fault-type-specific: AERec excels on linear drift (top-1 0.80) but\n"
        "collapses on stuck-at faults (0.17), while CondAttr shows the reverse\n"
        "(0.52/0.69; Table~S21 of Online Resource~1).")
c = s.count(old1)
if c >= 1:
    s = s.replace(old1, new1, 1)  # 只换第一处
    print("fault-type ref added (%d occurrences, replaced first)" % c)
else:
    print("WARN: fault-type anchor not found")

# 3) 运行时表
old2 = "50--200 times more per-window cost."
c2 = s.count(old2)
if c2 >= 1:
    s = s.replace(old2, "50--200 times more per-window cost (complexity and runtime:\n"
                   "Table~S22 of Online Resource~1).", 1)
    print("runtime ref added")
else:
    print("WARN: runtime anchor not found")

# 4) 部署指南
old3 = "For practitioners the results read as a selection guide"
c3 = s.count(old3)
if c3 >= 1:
    s = s.replace(old3, "For practitioners the results read as a selection guide "
                   "(Table~S24 of Online Resource~1)", 1)
    print("guide ref added")

open("Springer_JIIS_FalseAlarmAttribution.tex", "w", encoding="utf-8").write(s)
print("FILE WRITTEN")

# 5) SI 范围
t = open("JIIS_SI.tex", encoding="utf-8").read()
if "S1--S20" in t:
    t = t.replace("Tables S1--S20", "Tables S1--S24")
    open("JIIS_SI.tex", "w", encoding="utf-8").write(t)
    print("SI range updated")
