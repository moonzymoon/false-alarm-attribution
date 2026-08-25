# -*- coding: utf-8 -*-
"""Repair control-character damage in supplement_tables.tex S15 block."""
import re

p = r'D:\0科研\工作1\第10篇SCI\paper\archive\supplement_tables.tex'
data = open(p, 'rb').read()
BS = chr(92)  # backslash

# \x08egin (backspace) or bare 'egin' after {lr rrrrrr} -> \begin
for bad in (b'\x08egin{tabular}', b'egin{tabular}'):
    if bad in data:
        data = data.replace(bad, (BS + 'begin{tabular}').encode())
        print('fixed begin, was:', bad)

# any stray backspace or tab bytes anywhere
n_bs = data.count(b'\x08'); n_tab = data.count(b'\t')
data = data.replace(b'\x08', (BS + 'b').encode())
data = data.replace(b'\t' + b'oprule', (BS + 'toprule').encode())
data = data.replace(b'\t', b' ')
open(p, 'wb').write(data)
print('backspace bytes found:', n_bs, '| tab bytes found:', n_tab)
print('remaining \\x08:', open(p,'rb').read().count(b'\x08'))
