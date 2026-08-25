# -*- coding: utf-8 -*-
"""Verify DeepSeek claims #8/#15: Random top-1 vs 1/d; paired L1 CIs."""
import json, statistics as st

C = r"D:\0科研\工作1\第10篇SCI\src\_cache" + "\\"
d = json.load(open(C + "all_results_5det.json", encoding="utf-8"))

# iforest mixed units (Table 2 scope): Random top-1 per dataset vs mean 1/d
ds_d = {"SWaT": 51, "SMD": 38, "MetroPT3": 15, "PSM": 25, "SMAP": 25}
print("Random top-1 per dataset (iforest mixed units) vs 1/d:")
per_unit = []
for ds, D in ds_d.items():
    ks = [k for k in d if k.startswith(f"iforest_{ds}_mix")]
    t1 = st.mean(d[k]["Random"]["layer2_top1"] for k in ks if "layer2_top1" in d[k]["Random"])
    print(f"  {ds:9s} d={D:2d} 1/d={1/D:.4f}  Random top1={t1:.4f}  (n_units={len(ks)})")
    per_unit.extend([(d[k]["Random"]["layer2_top1"], 1 / D) for k in ks])
print(f"unit-weighted: mean Random top1={st.mean(x for x, _ in per_unit):.4f}, mean 1/d={st.mean(y for _, y in per_unit):.4f}")

# why higher? check whether gt_vars ever has >1 channel in these units
# (cannot tell from all_results; check gt hits definition in two_layer: top1 in set(gt_vars))
# per-unit random top1 detail:
print()
print("per-unit Random top-1 extremes:")
for k in sorted([k for k in d if k.startswith("iforest_") and "_mix" in k]):
    v = d[k]["Random"].get("layer2_top1")
    if v is not None and (v > 0.08 or v < 0.02):
        print(f"  {k}: {v:.3f}")

# paired L1 CIs
print()
b = json.load(open(C + "bootstrap_ci.json", encoding="utf-8"))
for pair, mv in b["paired"].items():
    l1 = mv["layer1_macro_f1"]
    print(f"paired L1 {pair}: diff={l1['mean_diff']:.4f} [{l1['lo']:.4f},{l1['hi']:.4f}] sig={l1['significant']}")
