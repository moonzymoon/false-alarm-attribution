# -*- coding: utf-8 -*-
"""Insert RegimeGlobal rows into the existing S17 table in supplement_tables.tex."""
import json
import statistics as st

C = r'D:\0科研\工作1\第10篇SCI\src\_cache' + '\\'
BS = chr(92)

def load(fn):
    return json.load(open(C + fn, encoding='utf-8'))

seeds = [load('regimeglobal_new_scorers.json'),
         load('regimeglobal_seed1000.json'),
         load('regimeglobal_seed2000.json')]

def cell(d, det, metric):
    vals = [u['RegimeGlobal'][metric] for k, u in d.items()
            if k.startswith(det + '_') and 'RegimeGlobal' in u
            and isinstance(u['RegimeGlobal'], dict)
            and u['RegimeGlobal'].get(metric) is not None]
    return st.mean(vals) if vals else None

p = r'D:\0科研\工作1\第10篇SCI\paper\archive\supplement_tables.tex'
txt = open(p, encoding='utf-8', newline='').read()

rows = {}
for det in ('pca', 'ocsvm'):
    l1 = [cell(d, det, 'layer1_macro_f1') for d in seeds]
    t1 = [cell(d, det, 'layer2_top1') for d in seeds]
    rows[det] = 'RegimeGlobal & ' + ' & '.join(f'{v:.3f}' for v in l1 + t1) + ' ' + BS + BS

NL = chr(13) + chr(10)  # file uses CRLF
# PCA block: insert before the \midrule that follows the PCA Random row
old_pca = 'Random & 0.462 & 0.455 & 0.469 & 0.026 & 0.024 & 0.038 ' + BS + BS + NL + BS + 'midrule'
new_pca = ('Random & 0.462 & 0.455 & 0.469 & 0.026 & 0.024 & 0.038 ' + BS + BS + NL
           + rows['pca'] + NL + BS + 'midrule')
assert old_pca in txt, 'PCA anchor not found'
txt = txt.replace(old_pca, new_pca)

old_oc = 'Random & 0.466 & 0.450 & 0.466 & 0.017 & 0.026 & 0.062 ' + BS + BS + NL + BS + 'midrule'
new_oc = ('Random & 0.466 & 0.450 & 0.466 & 0.017 & 0.026 & 0.062 ' + BS + BS + NL
          + rows['ocsvm'] + NL + BS + 'midrule')
assert old_oc in txt, 'OCSVM anchor not found'
txt = txt.replace(old_oc, new_oc)

open(p, 'w', encoding='utf-8', newline='').write(txt)
print('S17 RegimeGlobal rows inserted:')
print(rows['pca'])
print(rows['ocsvm'])
