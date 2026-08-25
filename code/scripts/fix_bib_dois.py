"""修复 references.bib: 元数据纠错 + 删虚构/未引用条目 + 注入 Crossref 核验 DOI.
DOI 来源: src/_cache/doi_report.json (accept=True) + mishra arXiv DOI (官方页面核验).
"""
import json
import re

BIB = r"D:\0科研\工作1\第10篇SCI\04_投稿准备\JIIS_submission\source\references.bib"
TEX = BIB.replace("references.bib", "Springer_JIIS_FalseAlarmAttribution.tex")
REPORT = r"D:\0科研\工作1\第10篇SCI\src\_cache\doi_report.json"

s = open(BIB, encoding="utf-8").read()

# 1. schemmer2023evaluation: 真实论文 arXiv:2302.03302 (标题/作者此前被写错)
old = re.search(r"@article\{schemmer2023evaluation,.*?\n\}", s, re.S).group(0)
new = ("@article{schemmer2023evaluation,\n"
       "  author = {Schemmer, Max and Holstein, Joshua and Bauer, Niklas and "
       "Kuhl, Niklas and Satzger, Gerhard},\n"
       "  title = {Towards Meaningful Anomaly Detection: The Effect of Counterfactual "
       "Explanations on the Investigation of Anomalies in Multivariate Time Series},\n"
       "  journal = {arXiv preprint arXiv:2302.03302},\n"
       "  year = {2023}\n}")
s = s.replace(old, new)
print("fixed schemmer2023evaluation")

# 2. liu2024contralsp: 真实 ICLR 2024 论文 (标题此前被写错)
old = re.search(r"@inproceedings\{liu2024contralsp,.*?\n\}", s, re.S).group(0)
new = ("@inproceedings{liu2024contralsp,\n"
       "  author = {Liu, Zichuan and Zhang, Yingying and Wang, Tianchun and others},\n"
       "  title = {Explaining Time Series via Contrastive and Locally Sparse "
       "Perturbations},\n"
       "  booktitle = {Proc. ICLR},\n"
       "  year = {2024}\n}")
s = s.replace(old, new)
print("fixed liu2024contralsp")

# 3. zhang2022mts (CETVAE/Hoellig): 查无此文 —— 删除条目
m = re.search(r"@inproceedings\{zhang2022mts,.*?\n\}\n?", s, re.S)
if m:
    s = s.replace(m.group(0), "")
    print("DELETED fabricated zhang2022mts")

# 4. redlamp2025: 未被引用 —— 删除条目
m = re.search(r"@inproceedings\{redlamp2025,.*?\n\}\n?", s, re.S)
if m:
    s = s.replace(m.group(0), "")
    print("DELETED uncited redlamp2025")

# 5. mishra arXiv DOI (官方页面: Accepted ECML PKDD 2026, arXiv:2604.17616)
extra = {"mishra2026condattr": "10.48550/arXiv.2604.17616"}

# 6. 注入 DOI: Crossref accept=True 的 21 条 + extra
rep = {r["key"]: r for r in json.load(open(REPORT, encoding="utf-8"))}
dois = {k: r["match"]["doi"] for k, r in rep.items()
        if r.get("accept") and r.get("match", {}).get("doi")}
dois.update(extra)
n = 0
for key, doi in dois.items():
    if re.search(r"doi\s*=\s*\{", s[s.find("{" + key + ","):s.find("{" + key + ",") + 2000],
                  re.I) if s.find("{" + key + ",") >= 0 else False:
        continue  # 已有 doi
    def add(m_):
        global n
        n += 1
        return m_.group(0)[:-2] + ",\n  doi = {https://doi.org/" + doi + "}\n}"
    s2 = re.sub(r"@\w+\{" + key + r",.*?\n\}", lambda m_, d=doi, k=key: add(m_)
                if "doi = {" not in m_.group(0) else m_.group(0), s, count=1, flags=re.S)
    s = s2
print(f"DOIs injected: {n}")

open(BIB, "w", encoding="utf-8").write(s)

# 7. 正文去掉虚构引用键
t = open(TEX, encoding="utf-8").read()
t2 = t.replace(",zhang2022mts}", "}").replace(",zhang2022mts,", ",").replace(
    "zhang2022mts,", "")
if t2 != t:
    open(TEX, "w", encoding="utf-8").write(t2)
    print("removed zhang2022mts from cite")
print("done")
