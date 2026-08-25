import json, statistics as st
C = r"D:/0科研/工作1/第10篇SCI/src/_cache/"

# v1 protocol: repair_experiment.json
v1 = json.load(open(C + "repair_experiment.json", encoding="utf-8"))
diffs = [(x["dataset"], x["regime"], x["far_base"], (x["drop_targeted"] - x["drop_random"]) * 100) for x in v1]
all_d = [d for _, _, _, d in diffs]
hi = [d for b, d in [(x[2], x[3]) for x in diffs] if b > 0.10]
pos = sum(1 for d in hi if d > 0)
print("v1: mean all-14 =", round(st.mean(all_d), 1), "pp")
print("v1: base>10%: n =", len(hi), "mean =", round(st.mean(hi), 1), "pp, positive =", pos)

# naive alarm supplementation effectiveness in v2
v2 = json.load(open(C + "repair_guided2.json", encoding="utf-8"))
naive = [x for x in v2 if "gap_guided_pp" in x]
print("v2 keys of first:", list(v2[0].keys()))
print("v2 far keys:", list(v2[0]["far"].keys()))
# targeted vs random in v2
t_r = [(x["far"]["targeted"], x["far"]["random"], x["far"]["base"]) for x in v2]
d2 = [((r - t) * 100) for t, r, b in t_r]  # random_far - targeted_far = improvement gap
hi2 = [((r - t) * 100) for t, r, b in t_r if b > 0.10]
print("v2: targeted-vs-random all-14 mean =", round(st.mean(d2), 1), "pp; base>10%: n =", len(hi2),
      "mean =", round(st.mean(hi2), 1), "pp, positive =", sum(1 for x in hi2 if x > 0))
