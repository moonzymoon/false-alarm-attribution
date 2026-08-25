"""修复通义千问审稿发现的4个真问题."""
BS = chr(92)
import os
os.chdir(os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "04_投稿准备", "JIIS_submission", "source"))
s = open("Springer_JIIS_FalseAlarmAttribution.tex", encoding="utf-8").read()

# 1. SMAP 指标混淆: L1=0.967 vs top-1=0.987, 第二处加 "(top-1)" 标注
old1 = "On SMAP both families are near-perfect (AERec 0.987, GlobalCF 0.962)"
new1 = "On SMAP both families are near-perfect (top-1: AERec 0.987, GlobalCF 0.962)"
c1 = s.count(old1)
if c1 == 1:
    s = s.replace(old1, new1)
    print("1. SMAP top-1 label added")

# 2. 语法修复: "same standard controlled intervention provides"
old2 = "the same standard controlled intervention provides elsewhere in causal inference."
new2 = "the same validity standard that controlled intervention provides elsewhere in causal inference."
c2 = s.count(old2)
if c2 == 1:
    s = s.replace(old2, new2)
    print("2. grammar fixed")

# 3. Fig2 caption 加方法范围说明
old3 = "\\caption{Layer-1 macro-F1 per mixed unit (rows: methods; columns: units).}"
new3 = ("\\caption{Layer-1 macro-F1 per mixed unit for the seven primary methods "
        "(rows) across all 23 units (columns); RegimeGlobal and SHAP are omitted "
        "for readability and reported in Table~" + BS + "ref{tab:main}.}")
c3 = s.count(old3)
if c3 == 1:
    s = s.replace(old3, new3)
    print("3. Fig2 caption updated with method scope note")

# 4. Fig1 tau 符号: 改图脚本中的文本
SCRIPT = os.path.join("D:" + BS, "0科研", "工作1", "第10篇SCI", "src", "scripts", "make_figures_v2.py")
try:
    sc = open(SCRIPT, encoding="utf-8").read()
    old4 = '"Filter: s_before < tau < s_a"'
    # 实际值可能是 "Filter: s_before < tau < s_after"
    for variant in ('"Filter: s_before < tau < s_after"',
                    "'Filter: s_before < tau < s_after'",
                    '"Filter: s_b < tau < s_a"'):
        if variant in sc:
            # 用 matplotlib mathtext 格式替换
            new4 = variant.replace("tau", "$\\\\tau$").replace("s_before", "$s_b$").replace("s_after", "$s_a$")
            sc = sc.replace(variant, new4)
            open(SCRIPT, "w", encoding="utf-8").write(sc)
            print("4. Fig1 tau symbol fixed in script")
            break
    else:
        print("4. Fig1 tau: variant not found, checking...")
        # 找实际文本
        import re
        m = re.search(r'Filter.*?tau', sc)
        if m:
            print("   Found:", m.group(0)[:60])
except Exception as e:
    print("4. Fig1 skip:", e)

open("Springer_JIIS_FalseAlarmAttribution.tex", "w", encoding="utf-8").write(s)
print("TEX WRITTEN")
