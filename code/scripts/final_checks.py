BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))
s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()
i = s.find(BS + "abstract{")
j = s.find("}", i) if i >= 0 else -1
# abstract 可能为多段: 找到下一个 BS+keywords 或 maketitle 前的收尾
end = s.find(BS + "keywords")
if end < 0:
    end = s.find(BS + "maketitle")
ab = s[i + 9:end]
# 去掉 latex 命令干扰粗算词数
import re
ab_txt = re.sub(BS + BS + "w+", " ", ab)
print("摘要词数(粗):", len(ab_txt.split()))

body = s[:s.find(BS + "bibliography{")]
tabs = {}
for lab in ("tab:datasets", "tab:main", "tab:detector", "tab:claims", "tab:repair"):
    tabs[lab] = (body.find("ref{" + lab + "}"), s.find("label{" + lab + "}"))
by_def = sorted(tabs, key=lambda k: tabs[k][1])
by_cit = sorted([k for k in tabs if tabs[k][0] >= 0], key=lambda k: tabs[k][0])
print("表定义序(=编号):", by_def)
print("表首次引用序:  ", by_cit)
print("表一致:", by_def == by_cit)
figs = {}
for lab in ("fig:protocol", "fig:heatmap", "fig:mirror", "fig:margin",
            "fig:beta", "fig:repair", "fig:scoredist"):
    figs[lab] = (body.find("ref{" + lab + "}"), s.find("label{" + lab + "}"))
fd = sorted(figs, key=lambda k: figs[k][1])
fc = sorted([k for k in figs if figs[k][0] >= 0], key=lambda k: figs[k][0])
print("图定义序:", fd)
print("图引用序:", fc)
print("图一致:", fd == fc)
