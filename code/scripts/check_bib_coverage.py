# -*- coding: utf-8 -*-
"""Cross-check bib entries vs citations (orphans / missing)."""
import re
import io

BS = chr(92)
bib = io.open(r'D:\0科研\工作1\第10篇SCI\paper\references.bib', encoding='utf-8').read()
keys = re.findall(r'@\w+\{([^,]+),', bib)
tex = io.open(r'D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex',
              encoding='utf-8').read()
cited = set()
for m in re.finditer(BS + BS + r'cite\{([^}]+)\}', tex):
    for k in m.group(1).split(','):
        cited.add(k.strip())
orphans = [k for k in keys if k not in cited]
missing = [k for k in cited if k not in keys]
print('bib entries:', len(keys), '| cited:', len(cited))
print('orphans (in bib, not cited):', orphans)
print('cited but not in bib:', missing)
