# -*- coding: utf-8 -*-
"""IDA style fixes: Vancouver numbered refs + anonymization."""
import io

B = chr(92)
p = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(p, encoding="utf-8").read()

old_natbib = B + "usepackage{natbib}"
new_natbib = B + "usepackage[numbers,sort&compress]{natbib}"
assert old_natbib in s
s = s.replace(old_natbib, new_natbib)

old_bst = B + "bibliographystyle{plainnat}"
new_bst = B + "bibliographystyle{unsrtnat}"
assert old_bst in s
s = s.replace(old_bst, new_bst)

old_author = B + "author{Yao Zhang" + B + "thanks{School of Data Science, Baoding University, Baoding, China. Email: zhangyao@bdu.edu.cn}}"
new_author = B + "author{} " + "% anonymized for single-anonymized peer review; see separate Title Page"
assert old_author in s, "author line not found"
s = s.replace(old_author, new_author)

io.open(p, "w", encoding="utf-8", newline=chr(10)).write(s)
print("style fixes applied")
