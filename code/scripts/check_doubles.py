# -*- coding: utf-8 -*-
"""Detect doubled words and common typo patterns in the manuscript."""
import re

p = r'D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex'
txt = open(p, encoding='utf-8').read()
# strip comments and math to reduce false positives
lines = [l.split('%')[0] if not l.lstrip().startswith('%') else '' for l in txt.split('\n')]
body = ' '.join(lines)
body = re.sub(r'\$[^$]*\$', ' MATH ', body)
body = re.sub(r'\\[a-zA-Z]+', ' CMD ', body)
body = re.sub(r'\s+', ' ', body)

hits = 0
for m in re.finditer(r'\b([a-z]{2,})\s+\1\b', body, re.IGNORECASE):
    w = m.group(1).lower()
    if w in ('that', 'had', 'the', 'is', 'of', 'and', 'in', 'to', 'a', 'an', 'on', 'we', 'it'):
        ctx = body[max(0, m.start()-45):m.end()+45]
        print('DOUBLE:', m.group(0), '|', ctx)
        hits += 1
print('doubled-word candidates:', hits)

for pat in [r'\s;', r'\s,', r'\(\s', r'\s\)', r'\.\.', r',,']:
    for m in re.finditer(pat, body):
        if pat == r'\s;' and '; and' in body[m.start():m.start()+6]:
            continue
        ctx = body[max(0, m.start()-40):m.end()+40]
        print('PATTERN', pat, '|', ctx)
        hits += 1
print('total flags:', hits)
