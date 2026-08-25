BS = chr(92)
import os
ROOT = os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission")
MAIN = os.path.join(ROOT, "source", "Springer_JIIS_FalseAlarmAttribution.tex")
SI = os.path.join(ROOT, "source", "JIIS_SI.tex")
LET = os.path.join(ROOT, "01_Cover_Letter.txt")

# ============ A. 通讯作者: Yao Zhang -> Lei An ============
old_au = ("\\author*[1]{\\fn{Yao Zhang}}\\email{zhangyao@bdu.edu.cn}\n"
          "\\author[1]{\\fn{Lei An}}\\email{anlei@bdu.edu.cn}")
new_au = ("\\author[1]{\\fn{Yao Zhang}}\\email{zhangyao@bdu.edu.cn}\n"
          "\\author*[1]{\\fn{Lei An}}\\email{anlei@bdu.edu.cn}")
for p in (MAIN, SI):
    s = open(p, encoding="utf-8").read()
    assert old_au in s, p
    s = s.replace(old_au, new_au)
    open(p, "w", encoding="utf-8").write(s)
print("corresponding author -> Lei An (main + SI)")

s = open(LET, encoding="utf-8").read()
old_sig = ("Sincerely,\n\nYao Zhang (corresponding author), on behalf of all authors\n"
           "Department of Artificial Intelligence, Baoding University, Baoding, Hebei, China\n"
           "Tel: +86-151-3225-6160\nzhangyao@bdu.edu.cn\nORCID: 0009-0008-7636-8158")
new_sig = ("Sincerely,\n\nLei An (corresponding author), on behalf of all authors\n"
           "Department of Artificial Intelligence, Baoding University, Baoding, Hebei, China\n"
           "anlei@bdu.edu.cn")
assert old_sig in s, "letter signature"
s = s.replace(old_sig, new_sig)
open(LET, "w", encoding="utf-8").write(s)
print("cover letter signature -> Lei An")

# ============ B. 破折号降密度 (19 处散文破折号 -> 保留 8 处, 其余改写) ============
s = open(MAIN, encoding="utf-8").read()
subs = [
    # 我自己近期加的优先
    ("PCA units reproduces the conditional pattern---mean directed gap $+7.3$\\,pp,\nup to $+64$\\,pp where headroom exists, null where the base FAR is\nsaturated---so the findings are not iforest-specific.",
     "PCA units reproduces the conditional pattern: mean directed gap $+7.3$\\,pp,\nup to $+64$\\,pp where headroom exists, and null where the base FAR is\nsaturated. The findings are therefore not iforest-specific."),
    ("OCSVM 0.870/0.817/0.789, ceding its lead---supporting\nthe indicative-only reading.",
     "OCSVM 0.870/0.817/0.789, ceding its lead, which supports\nthe indicative-only reading."),
    ("selection (median gaps $+0.7/-0.8/0.0$\\pp{}, wins 8/14, 4/14, 2/14)---even\nthough the verdict filters do raise the regime purity",
     "selection (median gaps $+0.7/-0.8/0.0$\\pp{}, wins 8/14, 4/14, 2/14), even\nthough the verdict filters do raise the regime purity"),
    ("relabel---by verdicts or by uncertainty---does not help.",
     "relabel, by verdicts or by uncertainty, does not help."),
    # 原稿中的
    ("We therefore report both validity targets throughout---agreement with the\nintervention (top-$k$) and operational success (repair)---and read their",
     "We therefore report both validity targets throughout (agreement with the\nintervention, i.e.\\ top-$k$, and operational success, i.e.\\ repair), and read their"),
    ("Table~\\ref{tab:main})---class prior, not attribution signal.",
     "Table~\\ref{tab:main}); this is class prior, not attribution signal."),
    ("and 0.73 within the tied MIL band---the matching relation is robust\nto an exact attribution scheme.",
     "and 0.73 within the tied MIL band. The matching relation is robust\nto an exact attribution scheme."),
    ("at 0.905/0.902/0.900, OCSVM 0.870/0.817/0.789, ceding its lead, which supports\nthe indicative-only reading.)",  # 已在上面改过的防重复
     None),
    ("correction operationally even when the two disagree---the channels the detector\nwatches carry the removable signal.",
     "correction operationally even when the two disagree: the channels the detector\nwatches carry the removable signal."),
    ("accounting---crediting the injected channel with clearance on every\ncoincident instance, an upper bound---the gap is 86\\% versus 63\\%.",
     "accounting (crediting the injected channel with clearance on every\ncoincident instance, an upper bound), the gap is 86\\% versus 63\\%."),
    ("mode-level---under the same injected-calibration procedure, the verdict\ndistribution moves from near-zero to universal across data sets.",
     "mode-level. Under the same injected-calibration procedure, the verdict\ndistribution moves from near-zero to universal across data sets."),
    ("directions---the tree ensemble still favours reconstruction (AERec 0.80,",
     "directions: the tree ensemble still favours reconstruction (AERec 0.80,"),
    ("replacement (0.93 versus 0.04)---so the reversal is not explained by window",
     "replacement (0.93 versus 0.04), so the reversal is not explained by window"),
]
n = 0
for old, new in subs:
    if new is None:
        continue
    if old in s:
        s = s.replace(old, new)
        n += 1
    else:
        print("SKIP(未匹配):", old[:50].replace("\n", " "))
open(MAIN, "w", encoding="utf-8").write(s)
print(f"em-dash reduction: {n} 处改写")
