"""GitHub 仓库本地 staging: 代码 + 结果 JSON + README/LICENSE/.gitignore.
排除: 数据集本体(datasets_local) / __pycache__ / npz 等二进制 / 日志 / _archive."""
import os
import shutil

SRC = r"D:\0科研\工作1\第10篇SCI\src"
DST = r"D:\0科研\工作1\第10篇SCI\github_repo\false-alarm-attribution"
EXCLUDE_DIRS = {"__pycache__", "_archive", "datasets_local", ".git"}
EXCLUDE_EXT = {".log", ".npz", ".pyc"}

code_dst = os.path.join(DST, "code")
res_dst = os.path.join(DST, "results")
KEEP_ROOT = {"README.md", "LICENSE", ".gitignore"}
if os.path.exists(DST):
    for f in os.listdir(DST):
        if f not in KEEP_ROOT and f not in ("code", "results"):
            shutil.rmtree(os.path.join(DST, f), ignore_errors=True)
    shutil.rmtree(os.path.join(DST, "code"), ignore_errors=True)
    shutil.rmtree(os.path.join(DST, "results"), ignore_errors=True)
os.makedirs(code_dst)
os.makedirs(res_dst)

n = 0
for root, dirs, files in os.walk(SRC):
    rel = os.path.relpath(root, SRC)
    parts = set(rel.split(os.sep))
    if parts & EXCLUDE_DIRS:
        dirs[:] = []
        continue
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    if "_cache" in parts:
        # 结果目录: 只收 JSON 到 results/
        for f in files:
            if f.endswith(".json"):
                shutil.copy2(os.path.join(root, f), os.path.join(res_dst, f))
                n += 1
        continue
    out_dir = os.path.join(code_dst, rel) if rel != "." else code_dst
    os.makedirs(out_dir, exist_ok=True)
    for f in files:
        if os.path.splitext(f)[1] in EXCLUDE_EXT:
            continue
        shutil.copy2(os.path.join(root, f), os.path.join(out_dir, f))
        n += 1
print(f"staged {n} files -> {DST}")
total = sum(os.path.getsize(os.path.join(r, f))
            for r, _, fs in os.walk(DST) for f in fs)
print(f"total size: {total/1024/1024:.1f} MB")
