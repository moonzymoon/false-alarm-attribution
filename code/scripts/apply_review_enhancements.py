"""综合修正: S14重复修复后重新生成SI + 正文写作修正 + Discussion定位强化."""
BS = chr(92)
import os
import subprocess
import sys

ROOT = os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI")
os.chdir(ROOT)

# ============ 1. 重新生成 SI 表 (S14a/b/c) ============
r = subprocess.run([sys.executable, "src/scripts/make_supplement_jiis.py"],
                   capture_output=True, text=True)
print("SI regen:", r.stdout.strip()[-30:] if r.stdout else r.stderr[-60:])

# ============ 2. 正文写作修正 ============
MAIN = os.path.join("04_投稿准备", "JIIS_submission", "source",
                    "Springer_JIIS_FalseAlarmAttribution.tex")
s = open(MAIN, encoding="utf-8").read()

edits = [
    # (a) "not a free lunch" → 正式表述
    ("a protocol dividend, not a free lunch",
     "a protocol dividend rather than a method-design advantage"),

    # (b) "we flag openly" → 正式表述 (只改第一处)
    ("Two methodological points we flag openly for the reviewers:",
     "Two methodological points are explicitly reported for the reviewers:"),

    # (c) MMD "three times" → 精确值
    ("with effect sizes about three times larger on SMD",
     "with effect sizes 2.4--3.1 times larger on SMD"),

    # (d) Discussion 加元论证 (在 "Within the scope of" 之前)
    ("Within the scope of intelligent information systems, the protocol is a",
     "The core contribution of this work lies in the measurement layer rather "
     "than in a new attribution network: formalizing the task and establishing "
     "a reproducible protocol are necessary prerequisites for any method "
     "iteration in this emerging direction, and the matching findings provide "
     "concrete empirical guidance for future method design. Within the scope "
     "of intelligent information systems, the protocol is a"),
]
n = 0
for old, new in edits:
    c = s.count(old)
    if c >= 1:
        s = s.replace(old, new, 1)
        n += 1
    else:
        print(f"WARN not found: {old[:40]}")
open(MAIN, "w", encoding="utf-8").write(s)
print(f"main text: {n} edits applied")
