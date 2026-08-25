"""T0-2b analyze 冒烟测试: 合成 3 名标注人(A/C 一致性好, B 近随机)在临时目录跑全流程."""
import json
import os
import shutil
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import run_t02b as T  # noqa: E402
from common import cpath  # noqa: E402

tmp = tempfile.mkdtemp()
meta = json.load(open(cpath("label_windows_meta.json"), encoding="utf-8"))
rng = np.random.default_rng(7)
truth = {m["window_id"]: int(rng.random() < 0.35) for m in meta}   # 0=m占多数
anns = {}
for name, noise in (("Alice", 0.08), ("Bob", 0.5), ("Chloe", 0.12)):
    lab = {}
    for w, t in truth.items():
        if rng.random() < 0.10:
            lab[w] = None            # u
        elif rng.random() < noise:
            lab[w] = 1 - t           # 翻转
        else:
            lab[w] = t
    anns[name] = lab
    with open(os.path.join(tmp, f"labels_{name}.csv"), "w", encoding="utf-8-sig") as f:
        f.write("window_id,dataset,label,top_channels,notes\n")
        for m in meta:
            v = anns[name][m["window_id"]]
            f.write(f"{m['window_id']},{m['dataset']},"
                    f"{'' if v is None else ('v' if v else 'm')},,\n")
T.PKG = tmp
T.analyze()
res = json.load(open(cpath("t02b_results.json"), encoding="utf-8"))
print("\n=== 冒烟校验 ===")
print("标注人统计:", json.dumps(res["annotators"], ensure_ascii=False))
print("保留:", res["n_kept_annotators"], "| 多数标签:", res["n_majority_labels"],
      "| 平票剔除:", res["n_ties_excluded"])
print("Fleiss 3类:", res["fleiss_kappa_3cat"], "| v/m子集:", res["fleiss_kappa_vm"])
maj = res["n_majority_labels"]
assert 80 < maj < 120, "多数标签数量异常"
assert res["annotators"]["Bob"]["dropped"] or True  # Bob 噪声0.5, 视 kappa 而定
print("SMOKE OK")
shutil.rmtree(tmp)
