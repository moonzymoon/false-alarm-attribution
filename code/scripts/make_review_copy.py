"""由 main.tex 重生单文件自包含审阅版 review_copy.tex."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.normpath(os.path.join(HERE, "..", "..", "paper"))
B = chr(92)
NL = chr(10)

HEADER = """\\documentclass[11pt]{article}
% Review copy (self-contained) - compiles anywhere, no external files needed.
\\usepackage[margin=2.5cm]{geometry}
\\usepackage{amsmath,amssymb,amsfonts,booktabs,multirow,graphicx,url,longtable}
\\usepackage[utf8]{inputenc}
\\providecommand{\\keywords}[1]{\\par\\medskip\\noindent\\textbf{Keywords:} #1\\par\\medskip}
\\providecommand{\\fn}[1]{#1}
\\providecommand{\\email}[1]{}
\\providecommand{\\affil}[1]{}
\\providecommand{\\orgname}[1]{#1}
\\newtheorem{definition}{Definition}
\\newcommand{\\pp}{pp}
\\newtheorem{theorem}{Theorem}
\\providecommand{\\bibcommenthead}{}

\\title{Attributing False Alarms in Multivariate Time-Series Anomaly Detection:\\\\
An Injection-Based Ground-Truth Protocol and a Method--Detector Matching Study}
\\author{Yao Zhang\\thanks{School of Data Science, Baoding University, Baoding, China.\\\\
Email: zhangyao@bdu.edu.cn (corresponding author).}}
\\date{}

\\begin{document}
\\maketitle

"""


def main():
    main_tex = open(os.path.join(PAPER, "main.tex"), encoding="utf-8").read()
    i = main_tex.find(B + "abstract{")
    body = main_tex[i:]
    ab_end = main_tex.find(B + "keywords{")
    abstract = main_tex[i + len(B + "abstract{"):ab_end].rstrip()
    if abstract.endswith("}"):
        abstract = abstract[:-1]
    body = body.replace(main_tex[i:ab_end],
                        B + "begin{abstract}" + NL + abstract + NL
                        + B + "end{abstract}" + NL, 1)
    # figure guards
    def guard(m):
        inc, fname = m.group(0), m.group(1)
        safe = fname.replace("_", B + "_")
        return (B + "IfFileExists{" + fname + "}{" + inc + "}{" + B + "fbox{" + B
                + "parbox{0.95" + B + "linewidth}{" + B + "centering " + B
                + "relax[Figure file: " + safe + " --- see submission copy]" + B
                + "vspace{2cm}}}}")
    body = re.sub(re.escape(B) + r"includegraphics\[[^\]]*\]\{([^}]+)\}", guard, body)
    # inline bibliography
    bbl = open(os.path.join(PAPER, "main.bbl"), encoding="utf-8").read()
    body = body.replace(B + "bibliographystyle{sn-basic}" + NL + B + "bibliography{references}", bbl)
    # appendix
    sup = open(os.path.join(PAPER, "supplement_tables.tex"), encoding="utf-8").read()
    appx = (B + "appendix" + NL + B
            + "section*{Appendix: Supplementary Tables S1--S13}" + NL
            + "(Included for review completeness; these accompany the submission as "
            "separate Supplementary Information.)" + NL + NL + sup + NL)
    out = HEADER + body.rstrip() + NL + NL + appx + B + "end{document}" + NL
    open(os.path.join(PAPER, "review_copy.tex"), "w", encoding="utf-8", newline=NL).write(out)
    print("review_copy.tex regenerated:", out.count(NL), "lines")


if __name__ == "__main__":
    main()
