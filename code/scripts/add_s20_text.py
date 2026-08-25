BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))

s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()

# 1) 自然报警小节: 在 "The probe is cheap..." 段后加人标句
anchor = ("The transfer gap\nis itself a measurable, previously unquantified object (agreement 58--71" + BS + "%;\n"
          "mode-fraction spreads 0--100" + BS + "%). The probe")
add_after = ("is cheap (400 alarms per site) and reusable as a transfer audit by any\n"
             "injected-label evaluation before its verdicts are trusted on natural\n"
             "alarms.")
assert s.count(add_after) == 1, "anchor tail"
new_tail = add_after + ("""
A human-reference check on a stratified subset of these alarms closes the
loop: five independent annotators labelled 120 natural-alarm windows
(variable-like / mode-like / unsure), and majority vote over the committed
verdicts (Fleiss $\\kappa=0.93$ on the all-commit subset; 104 reference
labels) shows the best method agrees with the human majority on only 54\\%
of windows (AERec; RC-CA 24\\%), while re-fitting $\\gamma$ on as few as
10--25 human-labelled alarms raises every method's agreement to 0.57--0.73
(Table~S20 of Online Resource~1). Natural-alarm typing is thus open but
label-efficient: a site that can label a few dozen alarms closes most of
the transfer gap.""")
s = s.replace(add_after, new_tail)

# 2) S 范围 S1--S19 -> S1--S20 (正文两处 + 结尾一处)
n = s.count("S1--S19")
s = s.replace("S1--S19", "S1--S20")
print("S range updated:", n, "places")

open("Springer_JIIS_FalseAlarmAttribution.tex", "w", encoding="utf-8").write(s)

# 3) SI 摘要范围
t = open("JIIS_SI.tex", encoding="utf-8").read()
t = t.replace("Tables S1--S19", "Tables S1--S20")
open("JIIS_SI.tex", "w", encoding="utf-8").write(t)
print("SI range updated")
