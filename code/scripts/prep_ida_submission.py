# -*- coding: utf-8 -*-
"""Prepare IDA (SAGE) submission package:
1. Anonymized main manuscript (author removed, acks removed)
2. Separate Title Page file
3. Cover letter
4. Trim abstract to <=200 words
5. Switch references to SAGE Vancouver (numbered, citation order)
"""
import re, os, shutil

PAPER = r"D:\0科研\工作1\第10篇SCI\paper"
TEX = os.path.join(PAPER, "IDA_SAGE_FalseAlarmAttribution.tex")

tex = open(TEX, encoding="utf-8").read()

# ---------- diagnostics ----------
m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
abstract_words = len(m.group(1).split())
print("Abstract words:", abstract_words)
print("cite count:", len(re.findall(r"\\cite\{", tex)))
print("citep count:", len(re.findall(r"\\citep\{", tex)))
print("natbib:", re.findall(r"\\usepackage\[[^\]]*\]\{natbib\}|\\usepackage\{natbib\}", tex))
print("acks:", re.findall(r"\\section\{Acknowledg[^\}]*\}", tex))
print("funding mention:", "funding" in tex.lower())
print("data availability:", re.findall(r"Data avail\w*", tex, re.I))
print("declarations section:", re.findall(r"\\section\{[^\}]*[Dd]eclar[^\}]*\}|\\section\{[^\}]*[Cc]onflict[^\}]*\}", tex))
print("author line:", re.findall(r"\\author\{[^\n]*", tex))
