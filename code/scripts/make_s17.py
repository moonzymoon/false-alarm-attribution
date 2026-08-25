# -*- coding: utf-8 -*-
"""Generate Supplementary Table S17 (3-seed stability) and wire into supplement."""
import json, io
import numpy as np

C = r"D:\0科研\工作1\第10篇SCI\src\_cache" + "\\"
seeds = [json.load(open(C + f, encoding="utf-8")) for f in
         ("new_scorer_results.json", "new_scorer_results_seed1000.json",
          "new_scorer_results_seed2000.json")]
METHODS = ["RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger", "zDev", "Random"]

def pooled(d, det, metric):
    out = {}
    for m in METHODS:
        vals = [u[m][metric] for k, u in d.items()
                if k.startswith(det + "_") and m in u
                and isinstance(u[m], dict) and u[m].get(metric) is not None]
        out[m] = float(np.mean(vals)) if vals else None
    return out

B = chr(92)
lines = ["% S17 construction-seed stability (PCA/OCSVM, 3 seeds)", "",
         B + "begin{table}[p]", B + "centering",
         B + "caption{Construction-seed stability: pooled metrics per seed for the PCA and OCSVM streams (seed 0 = main run; seeds 1000/2000 rebuild all units end-to-end with shifted construction seeds).}",
         B + "label{tab:s17}", B + "small", B + "begin{tabular}{lcccccc}", B + "toprule",
         " & " + " & ".join(["L1 s0", "L1 s1k", "L1 s2k", "top1 s0", "top1 s1k", "top1 s2k"]) + " " + B + B + " " + B + "midrule"]
for det, name in (("pca", "PCA"), ("ocsvm", "OCSVM")):
    lines.append(B + "multicolumn{7}{l}{" + B + "emph{" + name + "}}" + B + B)
    for m in METHODS:
        l1s = [pooled(d, det, "layer1_macro_f1")[m] for d in seeds]
        t1s = [pooled(d, det, "layer2_top1")[m] for d in seeds]
        row = [f"{v:.3f}" if v is not None else "--" for v in l1s + t1s]
        lines.append(f"{m.replace('-', '-')} & " + " & ".join(row) + " " + B + B)
    lines.append(B + "midrule")
lines += [B + "bottomrule", B + "end{tabular}", B + "end{table}", ""]
block = chr(10).join(lines)

P_SUP = r"D:\0科研\工作1\第10篇SCI\paper\archive\supplement_tables.tex"
s = io.open(P_SUP, encoding="utf-8").read()
s = s.rstrip() + chr(10) + chr(10) + block
io.open(P_SUP, "w", encoding="utf-8", newline=chr(10)).write(s)
print("S17 appended to supplement_tables.tex")

# update wrapper count and paper references S1--S16 -> S1--S17
P_WRAP = r"D:\0科研\工作1\第10篇SCI\paper\archive\supplement.tex"
w = io.open(P_WRAP, encoding="utf-8").read()
w = w.replace("Tables S1--S16 are generated", "Tables S1--S17 are generated")
io.open(P_WRAP, "w", encoding="utf-8", newline=chr(10)).write(w)
P_T = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
t = io.open(P_T, encoding="utf-8").read()
t = t.replace("Supplementary Tables~S1--S16", "Supplementary Tables~S1--S17")
io.open(P_T, "w", encoding="utf-8", newline=chr(10)).write(t)
print("S1--S17 references updated")
