# -*- coding: utf-8 -*-
"""Style polish P3: adverb density reduction (style only)."""
import io
B = chr(92)
NL = chr(10)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()
n = 0

def rep(old, new, tag):
    global s, n
    assert old in s, f"NOT FOUND: {tag}"
    assert s.count(old) == 1, f"NOT UNIQUE: {tag}"
    s = s.replace(old, new)
    n += 1
    print("P3:", tag)

# therefore 9 -> 4
rep("faults in our protocol (Section~" + B + "ref{sec:protocol}) therefore never change a",
    "faults in our protocol (Section~" + B + "ref{sec:protocol}) never change a",
    "therefore 1")
rep("We therefore retain only windows with",
    "We retain only windows with",
    "therefore 2")
rep("are therefore the wrong instrument for fault localization, even though they",
    "are the wrong instrument for fault localization, even though they",
    "therefore 3")
rep("The advantage is therefore" + NL + "only partly explained",
    "The advantage is" + NL + "only partly explained",
    "therefore 4")
rep("we therefore audit A1 and A4 empirically",
    "we audit A1 and A4 empirically",
    "therefore 5")

# exactly/precisely 4 -> 1
rep("Alarm-management practice requires exactly such rationalization",
    "Alarm-management practice requires precisely such rationalization" if False else "Alarm-management practice asks for exactly this kind of rationalization".replace("exactly this kind of", "this kind of"),
    "exactly 1")
rep("included precisely because their score geometry differs",
    "included because their score geometry differs",
    "precisely 1")
rep("This is precisely why repair" + NL + "effectiveness",
    "This is why repair" + NL + "effectiveness",
    "precisely 2")

# deliberately 4 -> 2
rep("Predicting the " + B + "emph{identity} of an unseen mode is deliberately outside the",
    "Predicting the " + B + "emph{identity} of an unseen mode is outside the",
    "deliberately 1")
rep("well-posed, so we deliberately report no ``mode-ID accuracy''; mode-level",
    "well-posed, so we report no ``mode-ID accuracy''; mode-level",
    "deliberately 2")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in polish P3")
