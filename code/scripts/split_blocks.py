# -*- coding: utf-8 -*-
"""Split the current paper into 4 review blocks (long lines, no figure envs, no dup math)."""
import io, re

B = chr(92)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()

def sec(name):
    return s.index(B + "section{" + name + "}")

i_intro = sec("Introduction")
i_form = sec("Problem formulation")
i_results = sec("Results")
i_disc = sec("Discussion")

def strip_figs(text):
    t = re.sub(re.escape(B) + "begin{figure}(.*?)" + re.escape(B) + "end{figure}", "", text, flags=re.S)
    return re.sub(r"\n{3,}", chr(10) + chr(10), t)

def reflow(text):
    lines = text.split(chr(10))
    out, buf = [], []
    VERB = ("begin{equation}", "begin{table}", "begin{align}", "begin{tabular}",
            "begin{definition}", "begin{proposition}", "begin{enumerate}",
            "begin{figure}", "begin{cases}", "begin{itemize}")
    verb_depth = 0
    for ln in lines:
        stripped = ln.strip()
        opens = sum(1 for v in VERB if B + v in ln)
        closes = sum(1 for v in VERB if B + "end{" + v.split("begin{")[1] in ln)
        if verb_depth == 0 and stripped and opens == 0 and not stripped.startswith("%"):
            buf.append(stripped)
        else:
            if buf:
                out.append(" ".join(buf)); buf = []
            out.append(ln)
        verb_depth += opens - closes
    if buf:
        out.append(" ".join(buf))
    res = []
    for l in out:
        if l.strip() == "" and res and res[-1].strip() == "":
            continue
        res.append(l)
    return chr(10).join(res)

blk1 = strip_figs(s[i_intro:i_form])
blk2 = strip_figs(s[i_form:i_results])

# block 3: definition (with inner equation), decision-rule eq, DAAS eq, proposition + remark
parts = []
m = re.search(re.escape(B) + "begin{definition}(.*?)" + re.escape(B) + "end{definition}", s, re.S)
parts.append((m.start(), B + "begin{definition}" + m.group(1) + B + "end{definition}"))
for m in re.finditer(re.escape(B) + "begin{equation}(.*?)" + re.escape(B) + "end{equation}", s, re.S):
    body = m.group(1)
    if "fault" in body:  # skip: already inside the definition env
        continue
    parts.append((m.start(), B + "begin{equation}" + body + B + "end{equation}"))
mp = re.search(re.escape(B) + "begin{proposition}(.*?)" + re.escape(B) + "end{proposition}", s, re.S)
prop_end = mp.end()
decl = s.index(B + "section*{Declarations}")
remark = s[prop_end:decl].strip()
parts.append((prop_end, B + "begin{proposition}" + mp.group(1) + B + "end{proposition}" + chr(10) + remark))
parts.sort()
blk3 = chr(10) + chr(10).join(t for _, t in parts)

blk4 = strip_figs(s[i_results:i_disc])

for tag, txt in [("BLOCK1", blk1), ("BLOCK2", blk2), ("BLOCK3", blk3), ("BLOCK4", blk4)]:
    print("=" * 14 + " " + tag + " " + "=" * 14)
    print(reflow(txt).strip())
    print()
