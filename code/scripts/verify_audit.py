import json
C = r"D:/0科研/工作1/第10篇SCI/src/_cache/"

# A1/A4 audit: find the cache
for cand in ["proposition_checks.json", "ablation.json", "regime_report.json"]:
    d = json.load(open(C + cand, encoding="utf-8"))
    s = json.dumps(d)
    print("=====", cand, len(s), "chars")
    if any(k in s for k in ["perm", "monoton", "offset", "a1", "A1"]):
        print(s[:600])

nv = json.load(open(C + "natural_validation.json", encoding="utf-8"))
print("===== natural_validation:", json.dumps(nv)[:700])

ari = json.load(open(C + "ari_vs_K.json", encoding="utf-8"))
print("===== ari_vs_K:", json.dumps(ari)[:400])
