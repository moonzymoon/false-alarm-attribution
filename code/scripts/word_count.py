# -*- coding: utf-8 -*-
"""Estimate main-text word count for the title page."""
import re
import io

BS = chr(92)
t = io.open(r'D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex',
            encoding='utf-8').read()
body = t.split('begin{abstract}')[1].split('bibliographystyle')[0]
body = re.sub(r'(?m)^%.*$', ' ', body)
body = re.sub(BS + BS + r'begin\{(table|figure|tabular)\}.*?' + BS + BS + r'end\{(table|figure|tabular)\}',
              ' ', body, flags=re.S)
body = re.sub(r'\$[^$]*\$', ' X ', body)
body = re.sub(BS + r'[a-zA-Z]+', ' ', body)
body = re.sub(r'[{}&%~]', ' ', body)
print('approx main-text words (incl abstract, excl tables/figures):', len(body.split()))
