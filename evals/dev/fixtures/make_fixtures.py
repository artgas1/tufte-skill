"""Generate three deliberately defective charts (F1, F2, F3) for the audit experiment.

Defects are listed in defects.md, written before this script was run.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors
from matplotlib import ticker
from matplotlib.patches import Ellipse, Polygon, Rectangle
from scipy.interpolate import make_interp_spline

HERE = os.path.dirname(os.path.abspath(__file__))


def out(name):
    d = os.path.join(HERE, name)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "chart.png")


# ---------------- F1 ----------------
def make_f1():
    years = ["2019", "2020", "2021", "2023", "2024", "2025"]  # 2022 silently missing
    users = [410, 425, 440, 470, 495, 520]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={"width_ratios": [3, 2]})

    # background noise texture (D4)
    rng = np.random.default_rng(7)
    noise = rng.random((60, 90))
    for a in (ax, ax2):
        a.imshow(noise, extent=(0, 1, 0, 1), transform=a.transAxes, cmap="Greys", alpha=0.35, aspect="auto", zorder=0)

    x = np.arange(len(years))
    base = 400  # truncated axis (D1)
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    bars = ax.bar(x, [u - base for u in users], bottom=base, width=0.6, color="none", edgecolor="navy", label="Пользователи", zorder=2)
    for b in bars:  # gradient fill (D3)
        bx, by = b.get_x(), b.get_y()
        w, h = b.get_width(), b.get_height()
        im = ax.imshow(grad, extent=(bx, bx + w, by, by + h), cmap="plasma", aspect="auto", origin="lower", zorder=2)
        im.set_clip_path(b)
    ax.set_xlim(-0.6, len(years) - 0.4)
    ax.set_ylim(base, 530)
    ax.set_xticks(x, years)
    # dark dense grid on top of data (D8)
    ax.set_axisbelow(False)
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax.grid(True, which="both", axis="y", color="black", linewidth=0.9, zorder=5)
    ax.legend(loc="upper left", frameon=True)  # single-series legend (D7)
    ax.set_title("Пользователи", fontsize=13)

    # icons scaled in both dimensions (D2), reverse year order (D9)
    icon_years = ["2025", "2023", "2021", "2019"]
    offices = [10, 8, 6, 4]
    ax2.set_xlim(0, 4)
    ax2.set_ylim(0, 1.25)
    ax2.set_aspect("auto")
    for i, (yr, v) in enumerate(zip(icon_years, offices)):
        s = v / 10.0  # height AND width proportional to value
        cx = i + 0.5
        body_w, body_h = 0.55 * s, 0.75 * s
        ax2.add_patch(Rectangle((cx - body_w / 2, 0.08), body_w, body_h, color="darkorange", zorder=3))
        ax2.add_patch(Ellipse((cx, 0.08 + body_h + 0.14 * s), 0.36 * s, 0.26 * s, color="darkorange", zorder=3))
        ax2.text(cx, 0.02, yr, ha="center", va="bottom", fontsize=11, zorder=4)
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_title("Офисы", fontsize=13)

    fig.suptitle("ВЗРЫВНОЙ РОСТ!", fontsize=22, fontweight="bold", color="crimson")  # (D6)
    fig.tight_layout()
    fig.savefig(out("F1"), dpi=110)
    plt.close(fig)


# ---------------- F2 ----------------
CATS = ["Альфа", "Бета", "Гамма", "Дельта", "Эпсилон", "Дзета", "Эта", "Тета", "Йота"]
V2024 = [27.914, 22.087, 15.203, 10.966, 8.019, 5.991, 4.008, 2.887, 2.925]
V2025 = [24.317, 25.106, 14.052, 12.218, 9.431, 7.075, 5.264, 4.118, 6.093]
ORDER = ["Дзета", "Альфа", "Тета", "Гамма", "Йота", "Бета", "Эта", "Дельта", "Эпсилон"]  # unsorted (D9)


def pie3d(ax, cx, values, colors, explode_cat=None, start=200.0, sq=0.45, depth=0.18):
    total = sum(values[c] for c in ORDER)
    # drop shadow (D11)
    ax.add_patch(Ellipse((cx + 0.06, -depth - 0.07), 2.15, 2.15 * sq, color="black", alpha=0.25, zorder=0))
    ang = np.deg2rad(start)
    wedges = []
    for c in ORDER:
        frac = values[c] / total
        a1, a2 = ang, ang + 2 * np.pi * frac
        ang = a2
        mid = (a1 + a2) / 2
        off = 0.14 if c == explode_cat else 0.0  # exploded slice (D6)
        ox, oy = off * np.cos(mid), off * np.sin(mid) * sq
        t = np.linspace(a1, a2, 80)
        arc = np.column_stack([cx + ox + np.cos(t), oy + np.sin(t) * sq])
        wedges.append((c, arc, (cx + ox, oy), mid, values[c]))
    # side band for front part (sin < 0) — pseudo-3D (D1)
    for c, arc, ctr, mid, v in wedges:
        t_front = np.sin(np.arctan2((arc[:, 1] - ctr[1]) / sq, arc[:, 0] - ctr[0])) < 0
        if t_front.sum() < 2:
            continue
        seg = arc[t_front]
        poly = np.vstack([seg, (seg - [0, depth])[::-1]])
        col = np.array(mcolors.to_rgb(colors[c])) * 0.6
        ax.add_patch(Polygon(poly, closed=True, color=col, zorder=1))
    for c, arc, ctr, mid, v in wedges:
        poly = np.vstack([[ctr], arc])
        ax.add_patch(Polygon(poly, closed=True, facecolor=colors[c], edgecolor="white", linewidth=0.8, zorder=2))
        lx, ly = ctr[0] + 0.68 * np.cos(mid), ctr[1] + 0.68 * np.sin(mid) * sq
        ax.text(lx, ly, f"{v:.3f}%", ha="center", va="center", fontsize=8, zorder=3)  # false precision (D8)


def make_f2():
    pal = plt.get_cmap("tab10")(range(10))
    col24 = {c: pal[i] for i, c in enumerate(CATS)}
    shuffled = [3, 7, 0, 5, 1, 8, 2, 6, 4]
    col25 = {c: pal[shuffled[i]] for i, c in enumerate(CATS)}  # inconsistent colors (D3)
    fig, ax = plt.subplots(figsize=(13, 6))
    pie3d(ax, -1.3, dict(zip(CATS, V2024)), col24, start=200.0)
    pie3d(ax, 1.4, dict(zip(CATS, V2025)), col25, explode_cat="Бета", start=230.0)
    ax.text(-1.3, 0.75, "2024", ha="center", fontsize=14)
    ax.text(1.4, 0.75, "2025", ha="center", fontsize=14)
    ax.set_xlim(-2.6, 3.9)
    ax.set_ylim(-0.9, 0.95)
    ax.set_aspect("equal")
    ax.axis("off")
    # names only in legend, alphabetical order != slice order (D7)
    from matplotlib.patches import Patch

    handles = [Patch(color=col24[c], label=c) for c in sorted(CATS)]
    ax.legend(handles=handles, loc="center right", title="2024", fontsize=9)
    ax.set_title("Доли рынка", fontsize=16)  # (D10)
    fig.tight_layout()
    fig.savefig(out("F2"), dpi=110)
    plt.close(fig)


# ---------------- F3 ----------------
def make_f3():
    years = [2000, 2005, 2010, 2015, 2020, 2021, 2022, 2023, 2024]
    check = [450, 700, 1100, 1600, 2600, 2900, 3300, 3700, 4100]
    clients = [120, 150, 185, 210, 230, 228, 224, 221, 219]
    x = np.arange(len(years))  # equal spacing for unequal intervals (D2)
    xs = np.linspace(0, len(years) - 1, 300)
    c_check, c_cli = "tab:blue", "tab:red"

    fig, ax = plt.subplots(figsize=(4.6, 9))  # tall narrow (D5)
    ax2 = ax.twinx()  # dual axis (D1)
    ax.plot(xs, make_interp_spline(x, check, k=3)(xs), color=c_check, lw=4)  # spline (D4), thick (D6)
    ax.plot(x, check, "o", color=c_check, ms=13, mec="black", mew=2)
    ax.fill_between(xs, make_interp_spline(x, check, k=3)(xs), 1500, color=c_check, alpha=0.25)  # (D7)
    ax2.plot(xs, make_interp_spline(x, clients, k=3)(xs), color=c_cli, lw=4)
    ax2.plot(x, clients, "s", color=c_cli, ms=13, mec="black", mew=2)
    ax.set_ylim(0, 4300)
    ax2.set_ylim(60, 240)
    ax.set_ylabel("Средний чек, руб.", color=c_cli)  # swapped axis colors (D8)
    ax.tick_params(axis="y", colors=c_cli)
    ax2.set_ylabel("Клиенты", color=c_check)
    ax2.tick_params(axis="y", colors=c_check)
    ax.set_xticks(x, [str(y) for y in years], rotation=90)  # (D10)
    ax.grid(True, which="both", linestyle="--", color="gray", linewidth=0.8)
    ax.annotate(
        "Рост цен вызвал\nотток клиентов!",  # causal claim (D9)
        xy=(4.6, 2750), xytext=(0.3, 3700), fontsize=10, fontweight="bold",
        arrowprops={"arrowstyle": "->", "lw": 1.5},
    )
    ax.set_title("Средний чек вырос в 9 раз", fontsize=12)  # (D3) nominal
    fig.tight_layout()
    fig.savefig(out("F3"), dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    make_f1()
    make_f2()
    make_f3()
    print("ok")
