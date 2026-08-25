# -*- coding: utf-8 -*-
"""Build tab:detector LaTeX from caches (all_results_5det + regimeglobal run)."""
import json, os, collections, statistics as st

CACHE = r"D:\0科研\工作1\第10篇SCI\src\_cache"
d = json.load(open(os.path.join(CACHE, "all_results_5det.json"), encoding="utf-8"))
rg_path = os.path.join(CACHE, "regimeglobal_new_scorers.json")
if os.path.exists(rg_path):
    rg = json.load(open(rg_path, encoding="utf-8"))
    for unit, mv in rg.items():
        if unit in d:
            d[unit].update(mv)
        else:
            d[unit] = mv
    print(f"merged {len(rg)} RegimeGlobal units")
else:
    print("regimeglobal_new_scorers.json not found - cells stay --")
ext_path = os.path.join(CACHE, "cmhmil_ext.json")
if os.path.exists(ext_path):
    ext = json.load(open(ext_path, encoding="utf-8"))
    for ds, mres in ext.items():
        if "error" in mres:
            continue
        d[f"cmhmil_{ds}_var"] = {m: {"layer2_top1": v["top1"]} for m, v in mres.items()
                                 if isinstance(v, dict) and "top1" in v}
    print("merged cmhmil_ext units (PSM/SMAP)")

dets = [("iforest", "iforest"), ("pca", "PCA"), ("ocsvm", "OCSVM"), ("AT", "AT"), ("cmhmil", "MIL")]
methods = ["RC-CA", "GlobalCF", "RegimeGlobal", "CondAttr", "AERec", "Granger", "zDev", "Random"]

def pooled(det, metric):
    vals = []
    for k, u in d.items():
        if not k.startswith(det + "_"):
            continue
        m = u.get(methods[0]) if False else None
        # method-agnostic presence handled by caller
    return vals

def cell(det, mm, metric):
    vals = [u[mm][metric] for k, u in d.items()
            if k.startswith(det + "_") and mm in u
            and isinstance(u[mm], dict) and u[mm].get(metric) is not None]
    return st.mean(vals) if vals else None

# L1 block: mixed detectors only (iforest, pca, ocsvm) — AT/MIL are single-type units
l1_dets = [("iforest", "iforest"), ("pca", "PCA"), ("ocsvm", "OCSVM")]
t1_dets = dets

B = chr(92)
lines = []
lines.append(B + "begin{table}[t]")
lines.append(B + "caption{Method--detector matching on all 58 evaluation units "
              "(pooled mean per detector). Upper block: layer-1 cause-typing macro-F1 "
              "on the three mixed-unit detectors (iforest/PCA/OCSVM; the AT and MIL "
              "units are single-type variable-level streams, where layer-1 typing is "
              "not applicable). Lower block: variable-type top-1 on all five detectors "
              "(AT: SWaT and SMD; MIL: SWaT, SMD, PSM and SMAP). "
              "Best per column in bold.}")
lines.append(B + "label{tab:detector}")
lines.append(B + "begin{tabular}{l" + "c"*5 + "}")
lines.append(B + "toprule")
lines.append(" & iforest & PCA & OCSVM & AT & MIL " + B + B)
lines.append(B + "midrule")
lines.append(B + "multicolumn{6}{l}{" + B + "emph{Layer-1 macro-F1 (mixed units)}}" + B + B)

best_l1 = {}
for det, _ in l1_dets:
    vals = {mm: cell(det, mm, "layer1_macro_f1") for mm in methods}
    vals = {m: v for m, v in vals.items() if v is not None}
    if vals: best_l1[det] = max(vals, key=vals.get)
for mm in methods:
    row = mm.ljust(12) + " & "
    for det, _ in l1_dets:
        v = cell(det, mm, "layer1_macro_f1")
        txt = f"{v:.3f}" if v is not None else "--"
        if best_l1.get(det) == mm: txt = B + "textbf{" + txt + "}"
        row += txt + " & "
    row += "-- & -- " + B + B
    lines.append(row)

lines.append(B + "midrule")
lines.append(B + "multicolumn{6}{l}{" + B + "emph{Variable-type top-1}}" + B + B)
best_t1 = {}
for det, _ in t1_dets:
    vals = {mm: cell(det, mm, "layer2_top1") for mm in methods}
    vals = {m: v for m, v in vals.items() if v is not None}
    if vals: best_t1[det] = max(vals, key=vals.get)
for mm in methods:
    row = mm.ljust(12) + " & "
    for det, _ in t1_dets:
        v = cell(det, mm, "layer2_top1")
        txt = f"{v:.3f}" if v is not None else "--"
        if best_t1.get(det) == mm: txt = B + "textbf{" + txt + "}"
        row += txt + " & "
    row = row.rstrip("& ") + B + B
    lines.append(row)
lines.append(B + "bottomrule")
lines.append(B + "end{tabular}")
lines.append(B + "end{table}")

out = os.path.join(CACHE, "detector_table.tex")
open(out, "w", encoding="utf-8").write(chr(10).join(lines) + chr(10))
print(chr(10).join(lines))
print("\nsaved →", out)
