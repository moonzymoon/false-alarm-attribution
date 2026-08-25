BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))
s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()

# S 范围已在上一脚本更新 (S1--S24), 检查
assert "S1--S24" in s, "S range not updated"
print("S range OK:", s.count("S1--S24"), "places")

# 1) 故障类型: 在 DAAS 段落的 detector-generic 句后追加
old1 = ("gap to perfect selection reiterates that the matching relation is\n"
        "detector--data-set specific rather than detector-generic.")
new1 = ("gap to perfect selection reiterates that the matching relation is\n"
        "detector--data-set specific rather than detector-generic, and also\n"
        "fault-type-specific: AERec excels on linear drift (top-1 0.80) but\n"
        "collapses on stuck-at faults (0.17), while CondAttr shows the reverse\n"
        "(0.52/0.69; Table~S21 of Online Resource~1).")
assert s.count(old1) == 1, "fault-type anchor"
s = s.replace(old1, new1)
print("fault-type ref added")

# 2) 运行时表引用
old2 = "at 50--200 times more per-window cost."
if s.count(old2) == 1:
    s = s.replace(old2, old2.rstrip(".") +
                  " (complexity and runtime for all methods: Table~S22 of Online Resource~1).")
    print("runtime ref added")
else:
    # 可能句尾有变化, 搜索子串
    old2b = "50--200 times more per-window cost"
    i = s.find(old2b)
    if i > 0:
        j = s.find(".", i + len(old2b))
        s = s[:j] + " (complexity and runtime: Table~S22 of Online Resource~1)." + s[j+1:]
        print("runtime ref added (alt)")

# 3) Discussion 部署指南
old3 = "For practitioners the results read as a selection guide: deploy DAAS"
if s.count(old3) == 1:
    s = s.replace(old3, "For practitioners the results read as a selection guide "
                   "(condensed in Table~S24 of Online Resource~1): deploy DAAS")
    print("guide ref added")

open("Springer_JIIS_FalseAlarmAttribution.tex", "w", encoding="utf-8").write(s)
print("done")
