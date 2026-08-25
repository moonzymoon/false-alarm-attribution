"""补注漏掉的 6 条 DOI (严格条目内匹配)."""
import json
import re

BIB = r"D:\0科研\工作1\第10篇SCI\04_投稿准备\JIIS_submission\source\references.bib"
rep = {r["key"]: r for r in json.load(
    open(r"D:\0科研\工作1\第10篇SCI\src\_cache\doi_report.json", encoding="utf-8"))}
dois = {k: r["match"]["doi"] for k, r in rep.items() if r.get("accept")}
dois["mishra2026condattr"] = "10.48550/arXiv.2604.17616"

s = open(BIB, encoding="utf-8").read()
n = 0
for key, doi in dois.items():
    pat = re.compile(r"@\w+\{" + key + r",.*?\n\}", re.S)
    m = pat.search(s)
    if not m or "doi = {" in m.group(0):
        continue
    entry = m.group(0)
    entry2 = entry[:-2] + ",\n  doi = {https://doi.org/" + doi + "}\n}"
    s = s.replace(entry, entry2)
    n += 1
    print("added", key)
open(BIB, "w", encoding="utf-8").write(s)
print("total added:", n)
