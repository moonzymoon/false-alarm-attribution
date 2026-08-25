# -*- coding: utf-8 -*-
"""Switch paper from single-author to three-author presentation.

Manuscript (anonymized): author contribution line replaced by a neutral
pointer (details live on the Title Page, which reviewers do not see).
Cover letter: rewritten on behalf of all three authors.
"""
import io
B = chr(92)
NL = chr(10)

# ---------- 1. manuscript declarations ----------
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()

old_c = B + "textbf{Author contribution:} single author."
new_c = (B + "textbf{Author contribution:} provided on the Title Page "
         "(withheld here for anonymized review).")
assert old_c in s, "contribution line not found"
s = s.replace(old_c, new_c)

old_ci = B + "textbf{Competing interests:} the author declares none."
new_ci = B + "textbf{Competing interests:} the authors declare none."
assert old_ci in s
s = s.replace(old_ci, new_ci)

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print("manuscript declarations updated")

# ---------- 2. cover letter ----------
CL = r"D:\0科研\工作1\第10篇SCI\04_投稿准备\IDA_submission\01_Cover_Letter.txt"
cl = io.open(CL, encoding="utf-8").read()

cl = cl.replace(
    "I am submitting the above manuscript for consideration in Intelligent\nData Analysis: An International Journal.",
    "We are submitting the above manuscript for consideration in Intelligent\n"
    "Data Analysis: An International Journal, on behalf of all authors\n"
    "(Yao Zhang, Lei An and Baocai Li).")
cl = cl.replace(
    "- The manuscript is original, has not been published previously, and is not\n  under consideration by any other journal.",
    "- The manuscript is original, has not been published previously, and is not\n  under consideration by any other journal.\n"
    "- All authors (Yao Zhang, Baoding University; Lei An, Baoding University;\n"
    "  Baocai Li, Baoding University) have read and approved the submission.")
cl = cl.replace(
    "- There is no funding to declare and no competing interests.",
    "- There is no funding to declare and the authors have no competing\n  interests.")
cl = cl.replace(
    "Sincerely,\n\nYao Zhang\nSchool of Data Science, Baoding University, Baoding, China\nzhangyao@bdu.edu.cn",
    "Sincerely,\n\nYao Zhang (corresponding author), on behalf of all authors\n"
    "School of Data Science, Baoding University, Baoding, Hebei, China\n"
    "Tel: +86-151-3225-6160\nzhangyao@bdu.edu.cn\nORCID: 0009-0008-7636-8158")
io.open(CL, "w", encoding="utf-8", newline=NL).write(cl)

CL2 = r"D:\0科研\工作1\第10篇SCI\04_投稿准备\IDA_CoverLetter.txt"
io.open(CL2, "w", encoding="utf-8", newline=NL).write(cl)
print("cover letter updated (3 authors)")
