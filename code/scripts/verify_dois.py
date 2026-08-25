"""Crossref DOI 核验: 对 references.bib 每条目查 api.crossref.org,
高置信匹配 (标题相似度>=0.92 且年份+-1 且首作者姓匹配) 才输出候选 DOI.
绝不凭记忆写 DOI; 输出报告供人工复核后再入 bib.
"""
import difflib
import json
import re
import sys
import time
import urllib.parse
import urllib.request

BIB = r"D:\0科研\工作1\第10篇SCI\04_投稿准备\JIIS_submission\source\references.bib"
OUT = r"D:\0科研\工作1\第10篇SCI\src\_cache\doi_report.json"
MAILTO = "zhangyao@bdu.edu.cn"


def unlatex(s):
    s = re.sub(r"\{\\'\w\}", lambda m: m.group(0)[2], s)
    s = s.replace("{", "").replace("}", "").replace("\\", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_bib(path):
    s = open(path, encoding="utf-8").read()
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}\n", s, re.S):
        typ, key, body = m.group(1).lower(), m.group(2), m.group(3)

        def field(name):
            fm = re.search(r"\b" + name + r"\s*=\s*\{(.*?)\}\s*,?\s*\n", body, re.S | re.I)
            if not fm:
                fm = re.search(r"\b" + name + r'\s*=\s*"([^"]*)"', body, re.I)
            return unlatex(fm.group(1)) if fm else None

        first_author = None
        au = field("author")
        if au:
            first_author = re.split(r"\s+and\s+", au)[0].split(",")[0].strip()
        ym = re.search(r"\byear\s*=\s*\{?(\d{4})", body)
        entries.append({"key": key, "type": typ, "title": field("title"),
                        "author": first_author, "year": ym.group(1) if ym else None,
                        "venue": field("booktitle") or field("journal")})
    return entries


def crossref(title, author):
    q = urllib.parse.urlencode({"query.bibliographic": f"{title} {author or ''}",
                                "rows": 3, "mailto": MAILTO})
    url = "https://api.crossref.org/works?" + q
    req = urllib.request.Request(url, headers={"User-Agent": f"doi-verify mailto:{MAILTO}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)["message"]["items"]
    except Exception as e:
        print("  crossref error:", e)
        return []


def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", (t or "").lower()).strip()


def main():
    entries = parse_bib(BIB)
    report = []
    for e in entries:
        if not e["title"]:
            report.append({**e, "doi": None, "why": "no title"})
            continue
        items = crossref(e["title"], e["author"])
        best, best_score = None, 0.0
        for it in items:
            ct = " ".join(it.get("title") or [])
            if not ct:
                continue
            sim = difflib.SequenceMatcher(None, norm(ct), norm(e["title"])).ratio()
            year = None
            for k in ("published-print", "published-online", "issued"):
                if it.get(k, {}).get("date-parts"):
                    year = it[k]["date-parts"][0][0]
                    break
            fam = ""
            aus = it.get("author") or []
            if aus:
                fam = (aus[0].get("family") or "").lower()
            year_ok = (e["year"] and year and abs(int(year) - int(e["year"])) <= 1)
            au_ok = (not e["author"] or not fam or norm(e["author"]) in norm(fam)
                     or fam in norm(e["author"] or "x"))
            score = sim * (1.0 if year_ok else 0.6) * (1.0 if au_ok else 0.5)
            if score > best_score:
                best, best_score = {"doi": it.get("DOI"), "ct": ct[:90],
                                    "year": year, "sim": round(sim, 3),
                                    "year_ok": bool(year_ok), "au_ok": bool(au_ok)}, score
        ok = best and best["sim"] >= 0.92 and best["year_ok"] and best["au_ok"]
        report.append({**e, "match": best, "score": round(best_score, 3),
                       "accept": bool(ok)})
        print(("OK " if ok else "-- ") + e["key"] + ("" if not best else
              f" sim={best['sim']} yr={best['year_ok']} au={best['au_ok']} doi={best['doi']}"))
        time.sleep(0.4)
    json.dump(report, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n_ok = sum(r["accept"] for r in report)
    print(f"\n{n_ok}/{len(report)} 高置信匹配; 报告: {OUT}")


if __name__ == "__main__":
    main()
