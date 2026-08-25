BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))
s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()
old1 = ("(RegimeGlobal, rerun under the same two extra seeds,\nconfirms the split: its PCA pooled top-1 is seed-stable at\n0.905/0.902/0.900, but its OCSVM seed-0 premium does not survive\nreseeding---pooled top-1 0.870/0.817/0.789, ceding the column lead to AERec\nand CondAttr under the new seeds---which directly supports the\nindicative-only reading.)")
new1 = ("(RegimeGlobal under the same reseeding confirms the split: PCA seed-stable\nat 0.905/0.902/0.900, OCSVM 0.870/0.817/0.789, ceding its lead---supporting\nthe indicative-only reading.)")
old2 = ("Extending the\nsame 400-alarm probe to the deep-MIL detector on the two remaining testbeds\nshows the instability is not an artefact of one scorer:")
new2 = ("Extending the probe to the deep-MIL detector shows the instability is not\none scorer's artefact:")
for old, new in ((old1, new1), (old2, new2)):
    assert s.count(old) == 1, old[:40]
    s = s.replace(old, new)
open("Springer_JIIS_FalseAlarmAttribution.tex", "w", encoding="utf-8").write(s)
print("2 more trims")
