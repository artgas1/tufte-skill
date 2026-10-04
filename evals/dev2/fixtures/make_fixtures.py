"""Generate dev set 2 (F4, F5, F6). Defects are listed in defects.md, written before this script."""
import os
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

HERE = os.path.dirname(os.path.abspath(__file__))


def out(name):
    d = os.path.join(HERE, name)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "chart.png")


CITIES = ["Самара", "Казань", "Санкт-Петербург", "Москва"]


# ---------------- F4: radius-scaled vs area-scaled circles ----------------
def make_f4():
    revenue = [10, 20, 40, 80]   # left: RADIUS proportional to value (D1)
    clients = [15, 30, 45, 60]   # right: AREA proportional to value (honest)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5.2))
    xs = [1.0, 2.6, 4.6, 7.4]
    r_max = 1.25
    for x, name, v in zip(xs, CITIES, revenue):
        r = r_max * v / max(revenue)              # radius ∝ value
        a1.add_patch(Circle((x, 1.5), r, color="#4c72b0", alpha=0.85))
        a1.text(x, 1.5 - r - 0.18, f"{name}\n{v}", ha="center", va="top", fontsize=10)
    for x, name, v in zip(xs, CITIES, clients):
        r = r_max * np.sqrt(v / max(clients))      # area ∝ value
        a2.add_patch(Circle((x, 1.5), r, color="#dd8452", alpha=0.85))
        a2.text(x, 1.5 - r - 0.18, f"{name}\n{v}", ha="center", va="top", fontsize=10)
    for a, title in ((a1, "Выручка, млн ₽"), (a2, "Клиенты, тыс.")):
        a.set_xlim(-0.2, 9.0)
        a.set_ylim(-0.6, 3.0)
        a.set_aspect("equal")
        a.axis("off")
        a.set_title(title, fontsize=12, loc="left")
    fig.suptitle("Выручка и клиенты по городам, 2025", fontsize=14)
    fig.text(0.01, 0.01, "Источник: CRM, данные за 2025 год", fontsize=8, color="0.4")
    fig.savefig(out("F4"), dpi=100)
    plt.close(fig)


# ---------------- F5: 3-D columns, no readable values ----------------
def make_f5():
    regions = ["Север", "Юг", "Запад", "Восток", "Центр"]
    sales = [34, 51, 27, 46, 63]
    colors = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00"]  # meaningless per-bar colours (D4)
    fig = plt.figure(figsize=(9, 6))
    ax = cast(Any, fig.add_subplot(projection="3d"))  # Axes3D; the 2-D stubs lack its z-axis methods
    x = np.arange(len(regions))
    ax.bar3d(x, np.zeros(len(x)), np.zeros(len(x)), 0.6, 0.6, sales, color=colors, shade=True)
    ax.set_xticks(x + 0.3, regions)
    ax.set_yticks([])
    ax.set_zticks([0, 20, 40, 60])
    ax.set_zticklabels([])          # no numbers on the value axis (D2)
    ax.view_init(elev=24, azim=-58)  # perspective (D1)
    ax.set_title("Продажи по регионам", fontsize=14)
    fig.savefig(out("F5"), dpi=100)
    plt.close(fig)


# ---------------- F6: clean chart with labelled choices ----------------
def make_f6():
    years = [2015, 2016, 2017, 2018, 2019]
    sales = [412, 430, 455, 468, 497]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(years, sales, width=0.6, color="#4c72b0", zorder=2)
    for y, v in zip(years, sales):
        ax.text(y, v + 2, f"{v}", ha="center", va="bottom", fontsize=10)
    ax.set_ylim(400, 510)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="0.9", linewidth=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    # labelled truncation: break marks on the y axis + note
    kw = {"transform": ax.transAxes, "color": "black", "clip_on": False, "linewidth": 1}
    ax.plot((-0.015, 0.015), (0.015, 0.045), **kw)
    ax.plot((-0.015, 0.015), (0.045, 0.075), **kw)
    ax.text(0.01, 0.97, "Ось Y начинается с 400", transform=ax.transAxes, fontsize=9, color="0.25",
            va="top")
    ax.set_ylabel("Продажи, тыс. шт.")
    ax.set_xticks(years, [str(y) for y in years])
    ax.set_title("Продажи выросли на 21% за 2015–2019", fontsize=13, loc="left")
    fig.text(0.01, 0.01, "Данные условные (иллюстрация). Источник: внутренний учёт, 2019",
             fontsize=8, color="0.4")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out("F6"), dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    make_f4()
    make_f5()
    make_f6()
    print("ok")
