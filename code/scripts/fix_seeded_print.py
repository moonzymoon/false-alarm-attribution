# -*- coding: utf-8 -*-
"""Fix the broken print line in the seeded C2 script (line-based)."""
import io

p = r"D:\0科研\工作1\第10篇SCI\src\scripts\run_new_scorers_seeded.py"
lines = io.open(p, encoding="utf-8").read().split("\n")
for i, ln in enumerate(lines):
    if "units" in ln and "new_scorer_results_seed%d" in ln and "print" in ln:
        lines[i] = '    print(f"{len(all_res)} units saved (seed offset {OFF})", flush=True)'
        print("fixed line", i + 1)
io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
