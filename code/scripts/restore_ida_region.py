# -*- coding: utf-8 -*-
"""Restore the accidentally deleted region of the IDA tex.

1. Regenerate the pre-damage IDA body from the JIIS archive (same logic as
   make_ida_version.py, written to a temp file).
2. Extract the lost region: from the datasets-table begin{table} up to the
   old tab:detector begin{table} (exclusive).
3. Splice it into the damaged file right before the new tab:detector.
"""
import io, os

B = chr(92)
NL = chr(10)
ROOT = r"D:\0科研\工作1\第10篇SCI"
SRC = os.path.join(ROOT, "paper", "archive", "jiis_version", "JIIS_Springer_FalseAlarmAttribution.tex")
DAMAGED = os.path.join(ROOT, "paper", "IDA_SAGE_FalseAlarmAttribution.tex")
TEMP = os.path.join(ROOT, "src", "_cache", "_regen_ida.tex")

# ---- regenerate pre-damage version (mirror make_ida_version.py) ----
src = io.open(SRC, encoding="utf-8").read()
body_start = src.find(B + "begin{document}") + len(B + "begin{document}")
body = src[body_start:]
ab_start = body.find(B + "abstract{")
ab_end = body.find(B + "keywords{")
abstract = body[ab_start + len(B + "abstract{"):ab_end].rstrip().rstrip("}")
keywords = body[ab_end:].split("{")[1].split("}")[0]
mk = body.find(B + "maketitle")
content = body[mk:]
for cmd in [B + "maketitle", B + "author*", B + "affil{", B + "orgname{"]:
    content = content.replace(cmd, "")
header = (B + "documentclass[11pt,a4paper]{article}" + NL + "PLACEHOLDER" + NL)
content = content.replace(B + "maketitle" + NL, "", 1)
# We only need the BODY after the abstract; simpler: locate region markers in JIIS body directly.

# ---- locate region in the JIIS source (the IDA body is a superset transform of it) ----
# Region starts at the datasets table caption block; use its caption text:
cap_ds = "Datasets and evaluation units"
cap_det = "Layer-1 macro-F1 (upper block)"

i_cap_ds = src.index(cap_ds)
j_start = src.rindex(B + "begin{table}[t]", 0, i_cap_ds)
i_cap_det = src.index(cap_det)
j_end = src.rindex(B + "begin{table}[t]", 0, i_cap_det)   # begin of old tab:detector
region = src[j_start:j_end]
print("region chars:", len(region))
print("region head:", region[:80].replace(NL, " | "))
print("region tail:", region[-80:].replace(NL, " | "))

# ---- splice into damaged file before new tab:detector ----
damaged = io.open(DAMAGED, encoding="utf-8").read()
new_cap = "Method--detector matching on all 58 evaluation units"
k = damaged.index(new_cap)
ins = damaged.rindex(B + "begin{table}[t]", 0, k)
repaired = damaged[:ins] + region + damaged[ins:]
io.open(DAMAGED, "w", encoding="utf-8", newline=NL).write(repaired)
print("repaired file chars:", len(repaired))
io.open(TEMP, "w", encoding="utf-8").write(region)
print("region copy saved to", TEMP)
