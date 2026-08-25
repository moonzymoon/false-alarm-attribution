"""图字号整体放大: fontsize 全部 x1.3, font.size 8.5->11, 图宽 7.0->6.2 (提高最终显示比例).
然后重新生成 7 张图并按 Fig1-7 命名拷入投稿 source."""
import re
import shutil

P = r"D:\0科研\工作1\第10篇SCI\src\scripts\make_figures_v2.py"
PAPER = r"D:\0科研\工作1\第10篇SCI\paper"
SRC = r"D:\0科研\工作1\第10篇SCI\04_投稿准备\JIIS_submission\source"

s = open(P, encoding="utf-8").read()
# 1) font.size 全局
s = s.replace('"font.size": 8.5', '"font.size": 11')
# 2) 显式 fontsize=N 放大 1.3
def bump(m):
    return "fontsize=" + str(round(float(m.group(1)) * 1.3, 1))
s = re.sub(r"fontsize=([0-9.]+)", bump, s)
# 3) 图宽 7.0 -> 6.2 (仅第一维 figsize=(7.0, x))
s = s.replace("figsize=(7.0,", "figsize=(6.2,")
s = s.replace("figsize=(3.2 * len(bc), 2.5)", "figsize=(2.9 * len(bc), 2.5)")
open(P, "w", encoding="utf-8").write(s)
print("fonts bumped x1.3, width 7.0->6.2")

# 4) 重新生成
import subprocess, sys
r = subprocess.run([sys.executable, P], capture_output=True, text=True, cwd=r"D:\0科研\工作1\第10篇SCI\src\scripts")
print(r.stdout[-500:])
if r.returncode != 0:
    print("STDERR:", r.stderr[-800:])
    raise SystemExit(1)

# 5) 拷贝映射
m = {"fig_protocol": "Fig1", "fig_heatmap": "Fig2", "fig_mirror": "Fig3",
     "fig_margin": "Fig4", "fig_beta": "Fig5", "fig_repair": "Fig6",
     "fig_scoredist": "Fig7"}
for old, new in m.items():
    shutil.copy2(PAPER + "\\" + old + ".pdf", SRC + "\\" + new + ".pdf")
print("copied 7 figures -> source as Fig1-7")
