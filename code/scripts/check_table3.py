# -*- coding: utf-8 -*-
"""Compare paper Table 3 blocks vs detector_table.tex, occurrence-aware."""
import re

paper = open(r'D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex', encoding='utf-8').read()
gen = open(r'D:\0科研\工作1\第10篇SCI\src\_cache\detector_table.tex', encoding='utf-8').read()

i = paper.find('label{tab:detector}')
j = paper.find('end{table}', i)
blk = paper[i:j]
# split into L1 part and top-1 part at the multicolumn header
split_k = blk.find('Variable-type top-1')
paper_l1, paper_t1 = blk[:split_k], blk[split_k:]

def rows_of(text):
    out = []
    for r in text.split('\n'):
        if '&' not in r or r.strip().startswith('%') or 'multicolumn' in r:
            continue
        name = r.split('&')[0].strip()
        if name.lower() in ('method',) or not re.match(r'^[A-Za-z]', name):
            continue
        nums = re.findall(r'\d+\.\d+|--', r)
        if len(nums) >= 3:
            out.append((name, nums))
    return out

gen_rows = rows_of(gen)
gen_first = {}   # L1 block occurrence
gen_second = {}  # top-1 block occurrence
for name, nums in gen_rows:
    if name not in gen_first:
        gen_first[name] = nums
    else:
        gen_second[name] = nums

mism = 0
for name, nums in rows_of(paper_l1):
    g = gen_first.get(name)
    if g is None:
        print('L1 missing in gen:', name); mism += 1
    elif nums[:5] != g[:5]:
        print('L1 MISMATCH', name, nums[:5], 'vs', g[:5]); mism += 1
for name, nums in rows_of(paper_t1):
    g = gen_second.get(name)
    if g is None:
        print('T1 missing in gen:', name); mism += 1
    elif nums[:5] != g[:5]:
        print('T1 MISMATCH', name, nums[:5], 'vs', g[:5]); mism += 1
print('mismatches:', mism)
