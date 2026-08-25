# -*- coding: utf-8 -*-
"""Verify key strings render in the compiled manuscript PDF."""
import subprocess

pdf = r'D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.pdf'
out = subprocess.run(['pdftotext', pdf, '-'], capture_output=True,
                     text=True, encoding='utf-8', errors='ignore').stdout
checks = [
    '36% of instances',
    '85% of cases',
    '0--81%',
    '86% versus 63%',
    '0.001--0.006',
    '2--13%',
    '44--100%',
    'six detector--data-set',
    'production monitoring',
    'twice\nas often',
]
for k in checks:
    print(('OK  ' if k in out else 'MISS'), repr(k))
