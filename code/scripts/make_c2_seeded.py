# -*- coding: utf-8 -*-
"""Generate run_new_scorers_seeded.py: a seed-shifted variant of run_new_scorers.py.
Usage: python run_new_scorers_seeded.py <offset>   (e.g. 1000)
"""
import io

B = chr(92)
SRC = r"D:\0科研\工作1\第10篇SCI\src\scripts\run_new_scorers.py"
DST = r"D:\0科研\工作1\第10篇SCI\src\scripts\run_new_scorers_seeded.py"

s = io.open(SRC, encoding="utf-8").read()

# inject offset support after imports
anchor = 'FAR = 0.05'
assert anchor in s
s = s.replace(anchor, 'FAR = 0.05\nOFF = int(sys.argv[1]) if len(sys.argv) > 1 else 0', 1)

# shift every explicit seed
reps = [
    ('np.random.default_rng(7)', 'np.random.default_rng(7 + OFF)'),
    ('np.random.default_rng(1)', 'np.random.default_rng(1 + OFF)'),
    ('np.random.default_rng(0)', 'np.random.default_rng(0 + OFF)'),
    ('seed=abs(hash((kind, st, k, scorer))) % 2**31',
     'seed=(abs(hash((kind, st, k, scorer))) % 2**31 + OFF) % 2**31'),
]
for old, new in reps:
    assert old in s, old
    s = s.replace(old, new)

# redirect output cache file
old_out = 'new_scorer_results.json'
assert old_out in s
s = s.replace(old_out, '"new_scorer_results_seed%d.json" % OFF')

# header
s = ('"""C2 multi-seed variant: run_new_scorers with all seeds shifted by OFF."""\n'
     + s)

io.open(DST, "w", encoding="utf-8", newline=chr(10)).write(s)
print("generated ->", DST)
