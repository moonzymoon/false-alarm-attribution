import json, statistics as st
v2 = json.load(open(r"D:/0科研/工作1/第10篇SCI/src/_cache/repair_guided2.json", encoding="utf-8"))
rows = []
for x in v2:
    f = x["far"]
    gap_tr = (f["random"] - f["targeted"]) * 100
    rows.append((x["dataset"], x["regime"], f["base"], gap_tr))
for ds, r, base, g in rows:
    flag = "*" if base > 0.10 else " "
    print(f"{ds:9s} r{r} base={base:.3f} {flag} targeted-vs-random={g:+.1f}pp")
hi = [g for ds, r, b, g in rows if b > 0.10]
print("base>10%:", len(hi), "units; positive(>0):", sum(1 for g in hi if g > 0),
      "; positive(>1pp):", sum(1 for g in hi if g > 1.0))
gaps = [x["gap_guided_pp"] for x in v2]
print("naive gap_guided_pp mean =", round(st.mean(gaps), 1))
