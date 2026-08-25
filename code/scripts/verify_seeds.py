import json, statistics as st
d = json.load(open(r"D:/0科研/工作1/第10篇SCI/src/_cache/repair_seeds.json", encoding="utf-8"))
print("n units:", len(d))
seed_means = []
for s in range(3):
    vals = [x["dir_minus_rnd_pp"][s] for x in d]
    seed_means.append(st.mean(vals))
print("per-seed overall means:", [round(m, 1) for m in seed_means])
stable = 0
for x in d:
    signs = set((v > 0) for v in x["dir_minus_rnd_pp"])
    if len(signs) == 1:
        stable += 1
    else:
        print("  unstable:", x["unit"], [round(v, 1) for v in x["dir_minus_rnd_pp"]])
print("sign-stable units:", stable, "/", len(d))
r5 = [x for x in d if "regime5" in x["unit"]]
if r5:
    print("SWaT-5 range:", round(min(r5[0]["dir_minus_rnd_pp"]), 1), "to", round(max(r5[0]["dir_minus_rnd_pp"]), 1))
