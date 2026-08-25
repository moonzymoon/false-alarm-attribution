"""标注示例 PDF v3: 修正版式 (程序化检查过页: 文字块不越界不互相压叠).
p1 图的解剖 | p2 什么是m | p3 什么是v | p4 三步判断+对比 | p5 u 的形态+更多例子."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath, load_raw, split_of, WINDOW  # noqa: E402

OUT_DIR = os.path.normpath(os.path.join(cpath(".."), "..", "04_投稿准备",
                                        "T0_投稿前实验包", "标注包"))
PDF = os.path.join(OUT_DIR, "标注示例_看图识m和v.pdf")

Z_CLIP = 12.0
HM_CLIP = 8.0


def robust_z_profile(X, a, b, ends):
    mu_med = np.median(X[a:b], 0)
    mad = 1.4826 * np.median(np.abs(X[a:b] - mu_med), 0) + 1e-9
    i = ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]
    W = X[i]
    Z = (W - mu_med[None, None, :]) / mad[None, None, :]
    prof = np.clip(np.abs(Z), 0, Z_CLIP).mean(1)
    return Z, prof


def draw_window(ax1, ax2, Z_k, p):
    order = np.argsort(-p)
    top12 = order[:12][::-1]
    top15h = order[:15]
    ax1.barh(range(len(top12)), p[top12], color="#3b6fb6")
    ax1.set_yticks(range(len(top12)))
    ax1.set_yticklabels([f"ch{j}" for j in top12], fontsize=7)
    ax1.set_xlim(0, Z_CLIP)
    ax1.axvline(np.median(p), ls="--", lw=0.8, color="#888888")
    ax1.set_xlabel("平均|z| 偏离（上限12）", fontsize=9)
    ax1.set_title("通道偏离柱状图（前12）", fontsize=10)
    im = ax2.imshow(np.clip(Z_k[:, top15h].T, -HM_CLIP, HM_CLIP), aspect="auto",
                    cmap="RdBu_r", vmin=-HM_CLIP, vmax=HM_CLIP, interpolation="nearest")
    ax2.set_yticks(range(len(top15h)))
    ax2.set_yticklabels([f"ch{j}" for j in top15h], fontsize=6)
    ax2.set_xlabel("窗口内时间步（共16步）", fontsize=9)
    ax2.set_title("窗口热力图（前15通道）", fontsize=10)
    return im, order


def stat_line(rec):
    return (f"{rec['window_id']} | {rec['dataset']} | score={rec['score']:.3f} "
            f"(tau={rec['tau']:.3f}) | channels|z|>5: {rec['n_ch_z5']}, "
            f">3: {rec['frac_z3']:.0%}")


def box(fig, x, y, s, fc="#f0f4fa", ec="#3b6fb6", fs=10.5):
    fig.text(x, y, s, fontsize=fs, ha="left", va="top", linespacing=1.65,
             bbox=dict(boxstyle="round,pad=0.55", fc=fc, ec=ec, lw=1.2))


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
    matplotlib.rcParams["axes.unicode_minus"] = False

    meta = json.load(open(cpath("label_windows_meta.json"), encoding="utf-8"))
    byid = {x["window_id"]: x for x in meta}

    def pick(ids, fallback):
        out = [byid[i] for i in ids if i in byid]
        return out if len(out) == len(ids) else fallback()

    m_sel = pick(["SMD_w011", "SWaT_w009"], lambda: sorted(
        [x for x in meta if x["frac_z3"] >= 0.5], key=lambda x: -x["frac_z3"])[:2])
    v_sel = pick(["MetroPT3_w018", "SMD_w000"], lambda: sorted(
        [x for x in meta if x["n_ch_z5"] <= 2], key=lambda x: x["n_ch_z5"])[:2])
    u_sel = pick(["SWaT_w025", "SWaT_w032"], lambda: [
        x for x in meta if 4 <= x["n_ch_z5"] <= 7 and 0.2 <= x["frac_z3"] <= 0.45][:2])

    cache = {}

    def get_win(rec):
        ds = rec["dataset"]
        if ds not in cache:
            X, Y = load_raw(ds)
            a, b = split_of(len(X))
            cache[ds] = (X, a, b)
        X, a, b = cache[ds]
        Z, prof = robust_z_profile(X, a, b, np.array([rec["end"]]))
        return Z[0], prof[0]

    def example_page(rec, kind, title, color, fc, body, verdict):
        """图占上部 [0.60, 0.885], 说明框从 0.545 向下, 徽标 0.06."""
        Z_k, p = get_win(rec)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.27, 11.69),
                                       gridspec_kw={"width_ratios": [1, 1.3]})
        order = np.argsort(-p)
        draw_window(ax1, ax2, Z_k, p)
        if kind == "m":
            ax1.annotate("高的柱子不止三两根，\n普遍都高、分不出主次",
                         xy=(Z_CLIP * 0.55, 6), xytext=(Z_CLIP * 0.42, 2.2),
                         fontsize=10.5, weight="bold", color=color, ha="center",
                         arrowprops=dict(arrowstyle="->", color=color, lw=2),
                         bbox=dict(boxstyle="round,pad=0.35", fc="#ffffff", ec=color, alpha=0.95))
            ax2.annotate("一半以上的行同时有色\n（整体偏移）",
                         xy=(8, 10), xytext=(8, 4),
                         fontsize=10.5, weight="bold", color=color, ha="center",
                         arrowprops=dict(arrowstyle="->", color=color, lw=2),
                         bbox=dict(boxstyle="round,pad=0.35", fc="#ffffff", ec=color, alpha=0.95))
        elif kind == "v":
            ax1.annotate("只有这一根突出，\n其余普遍很矮",
                         xy=(p[order[0]], 11), xytext=(Z_CLIP * 0.42, 6.5),
                         fontsize=10.5, weight="bold", color=color, ha="center",
                         arrowprops=dict(arrowstyle="->", color=color, lw=2),
                         bbox=dict(boxstyle="round,pad=0.35", fc="#ffffff", ec=color, alpha=0.95))
            ax2.annotate("只有顶部 1–2 行有色，\n其余行基本白色",
                         xy=(8, 0), xytext=(8, 5),
                         fontsize=10.5, weight="bold", color=color, ha="center",
                         arrowprops=dict(arrowstyle="->", color=color, lw=2),
                         bbox=dict(boxstyle="round,pad=0.35", fc="#ffffff", ec=color, alpha=0.95))
        fig.suptitle(title, fontsize=14, weight="bold", color=color, y=0.965)
        fig.text(0.5, 0.925, stat_line(rec), ha="center", fontsize=9.5,
                 bbox=dict(boxstyle="round,pad=0.3", fc="#eeeeee", ec="#bbbbbb"))
        fig.subplots_adjust(left=0.13, right=0.86, top=0.885, bottom=0.60)
        box(fig, 0.07, 0.545, body, fc=fc, ec=color)
        fig.text(0.5, 0.05, verdict, ha="center", fontsize=15, weight="bold", color="white",
                 bbox=dict(boxstyle="round,pad=0.5", fc=color, ec="none"))
        return fig

    with PdfPages(PDF) as pdf:
        # ============ p1: 任务 + 图的解剖 ============
        rec = v_sel[0]
        Z_k, p = get_win(rec)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.27, 11.69),
                                       gridspec_kw={"width_ratios": [1, 1.3]})
        draw_window(ax1, ax2, Z_k, p)
        fig.suptitle("第一步：看懂这张图（待标注的图都长这样）", fontsize=15,
                     weight="bold", y=0.96)
        fig.text(0.5, 0.925, stat_line(rec), ha="center", fontsize=9.5,
                 bbox=dict(boxstyle="round,pad=0.3", fc="#eeeeee", ec="#bbbbbb"))
        fig.subplots_adjust(left=0.13, right=0.86, top=0.885, bottom=0.42)
        for (x, y, n) in ((0.10, 0.925, 1), (0.075, 0.875, 2), (0.425, 0.875, 3),
                          (0.885, 0.70, 4)):
            fig.text(x, y, f" {n} ", fontsize=12, weight="bold", ha="center", va="center",
                     color="white",
                     bbox=dict(boxstyle="circle,pad=0.32", fc="#3b6fb6", ec="none"))
        legend = (
            " 1  顶部灰条 = 图的自动统计，两个数的用法：\n"
            "        高偏离通道数 ≤3 → 偏 v；4–7 → 偏 u；≥8 → 偏 m\n"
            "        （它是较严口径，通常比你眼数的略少，别用它推翻你看到的形态）\n"
            "        偏离占比 >50% → 支持 m 的加分项（有的数据集占比天生偏低，\n"
            "        达不到 50% 很正常，不能用它否决“一片都高”的形态）\n\n"
            " 2  左图：每根柱子 = 一个传感器。柱子越高 = 它的读数越偏离平时水平。\n"
            "     （“平时水平”由正常运行的历史数据自动算出，你不用管）\n\n"
            " 3  右图：每行 = 一个传感器，每列 = 一个时刻。红 = 比平时高，蓝 = 比平时低，\n"
            "     白/浅色 = 正常。看“有色的是几行”就够了，不用细看颜色深浅。\n\n"
            " 4  色标：最深的红/蓝对应很大的偏离，再大也这么深（上限）。\n\n"
            "你的任务：对每张图回答一个问题 —— 这次报警像是“个别传感器坏了”(v)，\n"
            "还是“整个系统状态变了”(m)？说不清就选 u（u 是正常选项，不是错误）。"
        )
        box(fig, 0.07, 0.38, legend, fs=10.5)
        pdf.savefig(fig)
        plt.close(fig)

        # ============ p2: m ============
        body_m = (
            "一句话：不是哪个传感器坏了，而是整个系统进入了另一种工作状态，\n"
            "大多数传感器一起偏离了平时的水平。\n\n"
            "生活类比：体检报告上好几项一起偏高——可能不是哪项出毛病，\n"
            "而是你刚跑完步，整体状态变了。\n"
            "工厂类比：从生产切换到停机检修、白天模式切换到夜间模式。\n\n"
            "认 m 的两个特征（满足其一就倾向 m）：\n"
            "  ① 左图：一大片柱子都高（约 8 根以上）且高矮接近、分不出主犯\n"
            "  ② 右图：一半以上的行同时有色\n\n"
            "本例（SMD_w011）：前 12 根柱子全部很高、完全分不出主犯；\n"
            "高偏离 17 个、占比 55% —— 三个信号一致指向 m。\n\n"
            "再看第 5 页复习例 SWaT_w009：12 根柱子同样全高，但占比只有 37% ——\n"
            "占比达不到 50% 不代表不是 m（这就是“占比只作加分项”的由来）。"
        )
        fig = example_page(m_sel[0], "m", "什么是 m（状态/工况级偏移）", "#b30000",
                           "#fff7f7", body_m, "判定：m")
        pdf.savefig(fig)
        plt.close(fig)

        # ============ p3: v ============
        body_v = (
            "一句话：只有个别传感器出了问题（坏了、被干扰、卡住了），\n"
            "系统其他部分一切照旧。\n\n"
            "生活类比：体检报告 20 项里只有一项不合格，多半是那一项的问题。\n"
            "工厂类比：一个温度计坏了疯狂报数，其他设备读数全部正常。\n\n"
            "认 v 的两个特征（满足其一就倾向 v）：\n"
            "  ① 左图：只有 1–3 根柱子明显高出其他柱子一截\n"
            "  ② 右图：只有 1–3 行有色，其余行基本白色\n\n"
            "本例统计：高偏离通道 " + str(v_sel[0]["n_ch_z5"]) + " 个、占比 "
            + f"{v_sel[0]['frac_z3']:.0%}"
            + " —— 两个数都指向 v。\n\n"
            "注意：第二、三名柱子若只是“中等高”（不到最高那根的一半），仍算 v ——\n"
            "看的是“有没有明显的少数主犯”，不是“其余必须为零”。"
        )
        fig = example_page(v_sel[0], "v", "什么是 v（点/传感器级异常）", "#006400",
                           "#f6fcf6", body_v, "判定：v")
        pdf.savefig(fig)
        plt.close(fig)

        # ============ p4: 三步判断 + 对比 ============
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.5, 0.955, "三步判断法（照着走，每张约 10 秒，全程约 20 分钟）", ha="center",
                 fontsize=15.5, weight="bold")
        flow = (
            "第 1 步 · 看左图：找出“明显高出其他柱子一截”的柱子，数有几根\n"
            "          1–3 根 → 可能是 v，去第 2 步确认\n"
            "          约 8 根以上都高、分不出主犯 → 可能是 m，去第 2 步确认\n"
            "          4–7 根或拿不准 → 直接去第 3 步\n\n"
            "第 2 步 · 看右图确认：\n"
            "          只有个别行有色、其余白 → 按 v\n"
            "          一半以上的行有色 → 按 m\n\n"
            "第 3 步 · 走完仍犹豫超过 10 秒 → 按 u，看下一张，不要停"
        )
        box(fig, 0.08, 0.915, flow, fs=11)
        fig.text(0.5, 0.615, "口诀：一根两根尖按 v；一片都是高按 m；高矮分不清按 u",
                 ha="center", fontsize=13, weight="bold",
                 bbox=dict(boxstyle="round,pad=0.45", fc="#fffaea", ec="#7a5c00"))

        axL = fig.add_axes([0.10, 0.36, 0.36, 0.20])
        axR = fig.add_axes([0.55, 0.36, 0.36, 0.20])
        for ax, rc, name, col in ((axL, m_sel[0], "m：一片都高", "#b30000"),
                                  (axR, v_sel[0], "v：一根突出", "#006400")):
            _, pp = get_win(rc)
            o = np.argsort(-pp)
            t12 = o[:12][::-1]
            ax.barh(range(len(t12)), pp[t12], color=col, alpha=0.85)
            ax.set_yticks(range(len(t12)))
            ax.set_yticklabels([f"ch{j}" for j in t12], fontsize=7)
            ax.set_xlim(0, Z_CLIP)
            ax.set_title(f"{name}（{rc['window_id']}）", fontsize=12, weight="bold", color=col)
            ax.set_xlabel("平均|z| 偏离", fontsize=9)
        fig.text(0.5, 0.30, "左：数不出“哪几根”是主犯 → m　　右：主犯一目了然 → v",
                 ha="center", fontsize=12, weight="bold",
                 bbox=dict(boxstyle="round,pad=0.4", fc="#f0f4fa", ec="#3b6fb6"))
        tips = (
            "统计数复核（图顶部灰条里的两个数）：\n"
            "     高偏离通道数（严口径）≤3 → 偏 v；≥8 → 偏 m；4–7 → 候选 u\n"
            "     它通常比你眼数的略少——别用它推翻你在图上看到的形态\n"
            "     偏离占比 >50% → 支持 m 的加分项；部分数据集占比普遍到不了 50%，\n"
            "     达不到不代表不是 m\n\n"
            "三条纪律：独立完成不讨论 ｜ 每人标全部 120 张 ｜ 第一印象不回头纠结\n"
            "标错了可以返回重按覆盖；进度自动保存，可分多次完成。"
        )
        box(fig, 0.08, 0.245, tips, fs=10.5)
        pdf.savefig(fig)
        plt.close(fig)

        # ============ p5: u 详解 + m/v 复习例 ============
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.5, 0.955, "什么时候按 u —— 两个真实例子手把手回放", ha="center",
                 fontsize=16, weight="bold")
        txt = (
            "u 不是偷懒，是诚实。按第 4 页三步法走到第 3 步仍定不下来，就按 u。\n"
            "最常见的两种卡法（下面各配一个真实例子的判断回放）：\n"
            "  ① 数出来 4–7 根突出的柱子：比 v 的 1–3 根多，又不成 m 的一片 → 两头都像\n"
            "  ② 柱子从高到矮连续下滑、没有断崖：“哪几根算主犯”本身数不出来"
        )
        box(fig, 0.08, 0.915, txt, fc="#fffaea", ec="#7a5c00", fs=11)

        # ---- u 例 1: 断崖但在 4-7 根之间 ----
        rc = u_sel[0]
        ax = fig.add_axes([0.10, 0.60, 0.36, 0.185])
        _, pp = get_win(rc)
        o = np.argsort(-pp)
        t12 = o[:12][::-1]
        ax.barh(range(len(t12)), pp[t12], color="#7a5c00", alpha=0.85)
        ax.set_yticks(range(len(t12)))
        ax.set_yticklabels([f"ch{j}" for j in t12], fontsize=6.5)
        ax.set_xlim(0, Z_CLIP)
        ax.tick_params(axis="x", labelsize=8)
        ax.set_title(f"u 例一 {rc['window_id']}｜高偏离{rc['n_ch_z5']}个 占比{rc['frac_z3']:.0%}",
                     fontsize=10.5, weight="bold", color="#7a5c00")
        ax.annotate("这 6 根明显是主犯，\n但已多于 v 的 1–3 根",
                    xy=(float(pp[o[5]]), 6), xytext=(4.8, 2.6),
                    fontsize=9.5, weight="bold", color="#7a5c00", ha="center",
                    arrowprops=dict(arrowstyle="->", color="#7a5c00", lw=1.8),
                    bbox=dict(boxstyle="round,pad=0.3", fc="#ffffff", ec="#7a5c00", alpha=0.95))
        ax.annotate("断崖之后\n全是矮柱", xy=(float(pp[o[6]]), 5), xytext=(9.5, 5),
                    fontsize=9, color="#555555", ha="center",
                    arrowprops=dict(arrowstyle="->", color="#888888", lw=1.4))
        box(fig, 0.10, 0.565,
            "回放：第 1 步数柱子 = 6 根 → 落进“4–7 根”的夹缝；\n"
            "占比仅 " + f"{rc['frac_z3']:.0%}" + "，够不上 m 的一片都高 → 按 u。",
            fc="#fffdf5", ec="#7a5c00", fs=10)

        # ---- u 例 2: 连续下滑无断崖 ----
        rc2 = u_sel[1]
        _, pp2 = get_win(rc2)
        o2 = np.argsort(-pp2)
        t12b = o2[:12][::-1]
        ax = fig.add_axes([0.55, 0.60, 0.36, 0.185])
        ax.barh(range(len(t12b)), pp2[t12b], color="#7a5c00", alpha=0.85)
        ax.set_yticks(range(len(t12b)))
        ax.set_yticklabels([f"ch{j}" for j in t12b], fontsize=6.5)
        ax.set_xlim(0, Z_CLIP)
        ax.tick_params(axis="x", labelsize=8)
        ax.set_title(f"u 例二 {rc2['window_id']}｜高偏离{rc2['n_ch_z5']}个 占比{rc2['frac_z3']:.0%}",
                     fontsize=10.5, weight="bold", color="#7a5c00")
        ax.annotate("从高到矮连续下滑，\n没有断崖——第 7 根 6.7、\n第 8 根 4.6，算不算高？",
                    xy=(float(pp2[o2[7]]), 4), xytext=(4.8, 1.8),
                    fontsize=9.5, weight="bold", color="#7a5c00", ha="center",
                    arrowprops=dict(arrowstyle="->", color="#7a5c00", lw=1.8),
                    bbox=dict(boxstyle="round,pad=0.3", fc="#ffffff", ec="#7a5c00", alpha=0.95))
        box(fig, 0.55, 0.565,
            "回放：第 1 步就卡住——“主犯是哪几根”数不出来；\n"
            "热力图也定不下来 → 第 3 步，按 u。",
            fc="#fffdf5", ec="#7a5c00", fs=10)

        # ---- m / v 复习例 (小图) ----
        slots = [(m_sel[0], "m 例（复习）", "#b30000"),
                 (m_sel[1] if len(m_sel) > 1 else m_sel[0], "m 例（复习）", "#b30000"),
                 (v_sel[0], "v 例（复习）", "#006400"),
                 (v_sel[1] if len(v_sel) > 1 else v_sel[0], "v 例（复习）", "#006400")]
        for k, (r3, name, col) in enumerate(slots):
            row, c = divmod(k, 2)
            ax = fig.add_axes([0.12 + c * 0.45, 0.335 - row * 0.20, 0.34, 0.135])
            _, pp3 = get_win(r3)
            o3 = np.argsort(-pp3)
            t3 = o3[:12][::-1]
            ax.barh(range(len(t3)), pp3[t3], color=col, alpha=0.85)
            ax.set_yticks(range(len(t3)))
            ax.set_yticklabels([f"ch{j}" for j in t3], fontsize=5.5)
            ax.set_xlim(0, Z_CLIP)
            ax.tick_params(axis="x", labelsize=7)
            ax.set_title(f"{name} {r3['window_id']}｜高偏离{r3['n_ch_z5']}个",
                         fontsize=9, weight="bold", color=col)
        fig.text(0.5, 0.055, "看完这 5 页就可以开始：打开 标注工具.html → 输入姓名 → 逐张判断",
                 ha="center", fontsize=12, weight="bold",
                 bbox=dict(boxstyle="round,pad=0.5", fc="#f0f4fa", ec="#3b6fb6"))
        pdf.savefig(fig)
        plt.close(fig)

    print("written:", PDF)
    print("m:", [x["window_id"] for x in m_sel], "| v:", [x["window_id"] for x in v_sel],
          "| u:", [x["window_id"] for x in u_sel])


if __name__ == "__main__":
    main()
