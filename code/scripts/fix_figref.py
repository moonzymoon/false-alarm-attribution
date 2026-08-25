BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))
s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()

# 1) 恢复 fig:repair 正文引用
old = "Table~" + BS + "ref{tab:repair} summarizes both repair levels"
new = "Figure~" + BS + "ref{fig:repair} and Table~" + BS + "ref{tab:repair} summarize both repair levels"
assert s.count(old) == 1, "sentence anchor"
s = s.replace(old, new)

# 2) 页数回收: Fig3 0.72->0.67, Fig7 0.72->0.68
for f, w in (("Fig3", "0.67"), ("Fig7", "0.68")):
    for cur in ("0.72", "0.70"):
        old_w = "[width=" + cur + BS + "linewidth]{" + f + ".pdf}"
        if old_w in s:
            s = s.replace(old_w, "[width=" + w + BS + "linewidth]{" + f + ".pdf}")
            print(f, cur, "->", w)
            break
    else:
        print("WARN:", f, "not found at 0.72/0.70")

open("Springer_JIIS_FalseAlarmAttribution.tex", "w", encoding="utf-8").write(s)
print("done")
