BS = chr(92)
p = r"D:\0科研\工作1\第10篇SCI\04_投稿准备\JIIS_submission\source\Springer_JIIS_FalseAlarmAttribution.tex"
s = open(p, encoding="utf-8").read()
n = 0
for f in ("Fig5", "Fig6"):
    old = "[width=0.72" + BS + "linewidth]{" + f + ".pdf}"
    new = "[width=0.68" + BS + "linewidth]{" + f + ".pdf}"
    if old in s:
        s = s.replace(old, new)
        n += 1
open(p, "w", encoding="utf-8").write(s)
print("shrunk", n, "figures")
