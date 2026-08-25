# -*- coding: utf-8 -*-
"""Verify repair claims against the correct caches (v2 protocol)."""
import json, statistics as st

C = r"D:\0科研\工作1\第10篇SCI\src\_cache" + "\\"

for f in ["repair_experiment.json", "repair_guided2.json", "repair_seeds.json"]:
    d = json.load(open(C + f, encoding="utf-8"))
    if isinstance(d, dict):
        top = list(d.keys())
        print("---", f, ":", len(top), "keys; sample:", str(top[:3]))
        k0 = top[0]
        print("    unit:", str(d[k0])[:260])
        print()
