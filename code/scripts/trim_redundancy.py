BS = chr(92)
import os
p = os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备",
                 "JIIS_submission", "source", "Springer_JIIS_FalseAlarmAttribution.tex")
s = open(p, encoding="utf-8").read()
trims = [
    # 1. 自然告警段: 重复数字收敛
    ("We emphasize\nthat the transfer gap is itself a measurable and, to our knowledge, not\npreviously quantified object: cross-method agreement 58--71\\%, mode-fraction\nspreads of 0--59\\% within one detector and 0--100\\% across detector--data-set\ncombinations. The probe",
     "The transfer gap\nis itself a measurable, previously unquantified object (agreement 58--71\\%;\nmode-fraction spreads 0--100\\%). The probe"),
    # 2. 匹配段: AT 池化列举压缩
    ("so the pooled AT column of\nTable~\\ref{tab:detector} averages the SWaT reversal, the SMD parity and\nthe two strong pairings; on the deep-MIL detector",
     "so the pooled AT column of Table~\\ref{tab:detector} averages all four\nbehaviours; on the deep-MIL detector"),
    # 3. 修复段: 部署轮描述已在前文出现
    ("Table~\\ref{tab:repair} summarizes both repair levels. The repair stage simulates a second deployment round: train (mode absent),\ndetect alarms, collect a sample of the current mode, retrain, re-evaluate.",
     "Table~\\ref{tab:repair} summarizes both repair levels; the repair stage\nsimulates a second deployment round."),
    # 5. 消融段: 三协议括注压缩
    ("(Three repair protocols are reported: the primary contrast over 14 units in Figure~\\ref{fig:repair}/Table~S6, a seed-replication over the 9 units with sufficient mode volume, and a stronger-baseline multi-round variant with uncertainty sampling and a second verdict selector over the same 14 units, Table~S19.)",
     "(Three repair protocols are reported: the primary 14-unit contrast (Figure~\\ref{fig:repair}/Table~S6), a 9-unit seed replication, and a stronger-baseline multi-round variant (Table~S19).)"),
    # 6. 结论: 长插入语压缩
    ("---established\nhere on the dense evidence columns (flattened tree ensembles, linear and\nkernel scorers) and supported by the repair loop, with the transformer\nreversal itself resting on a single pairing (its three further pairings give\nparity and both-strong ceilings)---with",
     "---established on the dense evidence\ncolumns (tree ensembles, linear and kernel scorers) and supported by the\nrepair loop; the transformer reversal rests on a single pairing---with"),
]
n = 0
for old, new in trims:
    c = s.count(old)
    assert c == 1, f"match={c}: {old[:50]!r}"
    s = s.replace(old, new)
    n += 1
open(p, "w", encoding="utf-8").write(s)
print("trims applied:", n)
