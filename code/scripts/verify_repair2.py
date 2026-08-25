import json
for f in ["repair_experiment.json", "repair_guided2.json", "repair_seeds.json"]:
    d = json.load(open(r"D:/0科研/工作1/第10篇SCI/src/_cache/" + f, encoding="utf-8"))
    print("=====", f, type(d).__name__, len(d))
    if isinstance(d, list):
        for x in d[:3]:
            print("  ", str(x)[:220])
    else:
        for k in list(d)[:3]:
            print("  ", k, "->", str(d[k])[:220])
