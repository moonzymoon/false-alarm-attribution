"""从 JIIS (sn-jnl) 版本生成 IDA (SAGE, 标准 article) 版本."""
import os, re

B = chr(92)
NL = chr(10)

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "paper", "archive", "jiis_version",
    "JIIS_Springer_FalseAlarmAttribution.tex")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "paper", "IDA_SAGE_FalseAlarmAttribution.tex")

src = open(SRC, encoding="utf-8").read()

# 找到 \begin{document} 之后的正文
body_start = src.find(B + "begin{document}") + len(B + "begin{document}")
body = src[body_start:]

# 提取摘要和关键词
ab_start = body.find(B + "abstract{")
ab_end = body.find(B + "keywords{")
abstract = body[ab_start + len(B + "abstract{"):ab_end].rstrip().rstrip("}")
keywords = body[ab_end:].split("{")[1].split("}")[0]

# 正文从 \maketitle 之后开始（跳过第二次 \maketitle）
mk = body.find(B + "maketitle")
if mk < 0:
    mk = body.find(B + "section{Introduction}")
content = body[mk:]

# 去掉 sn-jnl 特有命令
for cmd in [B + "maketitle", B + "author*", B + "affil{", B + "orgname{"]:
    content = content.replace(cmd, "")

# 构建 IDA 版本头部
header = B + """documentclass[11pt,a4paper]{article}
% Intelligent Data Analysis (SAGE) submission
% Compile: pdflatex -> bibtex -> pdflatex x2
""" + B + """usepackage[margin=2.5cm]{geometry}
""" + B + """usepackage{graphicx,amsmath,amssymb,amsfonts,booktabs,multirow,url}
""" + B + """usepackage[utf8]{inputenc}
""" + B + """usepackage{natbib}
""" + B + """newtheorem{definition}{Definition}
""" + B + """newtheorem{proposition}{Proposition}
""" + B + """newcommand{""" + B + """pp}{pp}
""" + B + """providecommand{""" + B + """fn}[1]{#1}
""" + B + """providecommand{""" + B + """email}[1]{(#1)}
""" + B + """providecommand{""" + B + """affil}[1]{""" + B + B + """ """ + B + """small #1}

""" + B + """title{Attributing False Alarms in Multivariate Time-Series Anomaly Detection:""" + B + B + NL + """An Injection-Based Ground-Truth Protocol and a Method--Detector Matching Study}
""" + B + """author{Yao Zhang""" + B + """thanks{School of Data Science, Baoding University, Baoding, China. Email: zhangyao@bdu.edu.cn}}
""" + B + """date{}

""" + B + """begin{document}
""" + B + """maketitle

""" + B + """begin{abstract}
""" + abstract + """
""" + B + """end{abstract}

""" + B + """noindent""" + B + """textbf{Keywords:} """ + keywords + """

"""

# 拼接（去掉开头的 \maketitle 如果有）
content = content.replace(B + "maketitle" + NL, "", 1)
out = header + content

# 修改参考文献命令
out = out.replace(B + "bibliographystyle{sn-basic}", B + "bibliographystyle{plainnat}")
out = out.replace(B + "bibliography{references}", B + "bibliography{references}")

open(OUT, "w", encoding="utf-8").write(out)
print(f"IDA 版本已生成: {OUT}")
print(f"大小: {len(out)} chars")
