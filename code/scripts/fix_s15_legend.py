# -*- coding: utf-8 -*-
"""Restore S16 comment and un-comment the S15 legend."""
BS = chr(92)
NL = chr(10)
p = r'D:\0科研\工作1\第10篇SCI\paper\archive\supplement_tables.tex'
txt = open(p, encoding='utf-8').read()

bad = ("% " + BS + "small clG = guided-channel correction clears the alarm; clGT = ground-truth-channel "
       "correction; " + BS + "mid" + BS + ";A / " + BS + "mid" + BS + ";D = share conditional on "
       "coinciding / divergent guided-vs-injected channels." + NL + NL + "S16 repair gap seed robustness (pp)")
good = (BS + "small clG = guided-channel correction clears the alarm; clGT = ground-truth-channel "
        "correction; suffix A / D = conditional on coinciding / divergent guided-vs-injected "
        "channels." + NL + NL + "% S16 repair gap seed robustness (pp)")
assert bad in txt, "block not found"
txt = txt.replace(bad, good)
open(p, 'w', encoding='utf-8').write(txt)
print("legend restored as text, S16 comment restored")
