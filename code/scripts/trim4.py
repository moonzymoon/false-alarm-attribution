BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))
s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()

# 0) 回退文献字号
old = BS + "fontsize{7.6}{9.2}"
new = BS + "footnotesize"
assert old in s
s = s.replace(old, new)

subs = [
    # 1) 消融段 CondAttr masked 变体压缩
    ("A masked-context retrieval variant of CondAttr (retrieval distances computed\nafter zeroing the target channel in both the query and the database windows)\n" + BS + "emph{underperforms} the full-window\nembedding compromise (L1 0.42--0.56 versus 0.63--0.82 on a four-unit\nsubset), with the caveat of a reduced retrieval pool.",
     "A masked-context retrieval variant of CondAttr (distances computed after\nzeroing the target channel) " + BS + "emph{underperforms} the full-window\ncompromise (L1 0.42--0.56 versus 0.63--0.82, four units), with the caveat of\na reduced pool."),
    # 2) 形式化段范围句压缩
    ("We restrict scope to sensor faults that do not trigger process-level\nsafety interlocks (extreme failures that propagate are process anomalies outside\nthis definition), which is the situation alarm-management rationalization targets\n(" + BS + "cite{isa182}).",
     "We restrict scope to sensor faults that do not trigger process-level safety\ninterlocks, the situation alarm-management rationalization targets\n" + BS + "cite{isa182}."),
    # 3) 发现1 尾句压缩
    ("While this may seem intuitively expected given different failure geometries, the direction is not a priori obvious and the quantification across 62 units and 19 detector--data-set pairs provides the first empirical selection basis.",
     "The direction is not a priori obvious, and the quantification across 62\nunits and 19 detector--data-set pairs provides the first empirical selection\nbasis."),
]
for old, new in subs:
    assert s.count(old) == 1, old[:44]
    s = s.replace(old, new)
open("Springer_JIIS_FalseAlarmAttribution.tex", "w", encoding="utf-8").write(s)
print("bibfont reverted + 3 trims")
