# -*- coding: utf-8 -*-
"""Fix S15 header math delimiters in supplement_tables.tex."""
BS = chr(92)
p = r'D:\0科研\工作1\第10篇SCI\paper\archive\supplement_tables.tex'
txt = open(p, encoding='utf-8').read()

old = (BS + "toprule Unit & $n$ & agree & cl-G$" + BS + "|$A$ & cl-G$" + BS +
       "|$D$ & cl-GT$" + BS + "|$D$ & both$" + BS + "|$D$ & GT-only$" + BS + "|$D$ " + BS + BS)
new = (BS + "toprule Unit & $n$ & agree & clG$" + BS + "mid$A & clG$" + BS +
       "mid$D & clGT$" + BS + "mid$D & both$" + BS + "mid$D & GTonly$" + BS + "mid$D " + BS + BS)
assert old in txt, "header not found"
txt = txt.replace(old, new)
open(p, 'w', encoding='utf-8').write(txt)
print("S15 header fixed")
