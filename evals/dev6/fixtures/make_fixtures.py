"""Generate dev set 6 (F17, F18, F19). Defects are listed in defects.md, written before this script."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FormatStrFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
GREY = "#555555"


def out(name):
    d = os.path.join(HERE, name)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "chart.png")


def clean(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def make_f17():
    months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
    sup = [92, 91, 93, 94, 93, 95, 96, 95, 97, 97, 98, 98]
    sal = [74, 78, 77, 81, 84, 83, 86, 88, 87, 90, 92, 94]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    x = np.arange(12)
    ax.plot(x, sup, color="#1b5e9e", linewidth=1.8)
    ax.plot(x, sal, color="#b2182b", linewidth=1.8)
    ax.annotate("Поддержка", (11.0, float(sup[-1])), xytext=(6, 0), textcoords="offset points", color="#1b5e9e",
                va="center")
    ax.annotate("Продажи", (11.0, float(sal[-1])), xytext=(6, 0), textcoords="offset points", color="#b2182b",
                va="center")
    ax.set_xticks(x, months)
    ax.set_xlim(-0.3, 12.8)
    ax.set_ylim(70, 100)                                     # D1: starts at 70, no mark, no note
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))  # ticks read «70.0»
    ax.set_ylabel("Решённые обращения, %")
    ax.set_title("Продажи догоняют поддержку по доле решённых обращений, 2025", fontsize=12)
    ax.grid(True, axis="y", color="#eeeeee", linewidth=0.6)
    clean(ax)
    fig.text(0.01, 0.01, "Источник: служба поддержки, 2025", fontsize=8, color=GREY)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out("F17"), dpi=110)
    plt.close(fig)


def make_f18():
    cities = ["Тула", "Уфа", "Казань", "Пермь", "Омск"]
    v = [71, 66, 62, 55, 48]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    y = np.arange(len(cities))
    ax.scatter(v, y, color="#1b5e9e", s=60, zorder=3)
    for yi, vi in zip(y, v):
        ax.annotate(f"{vi}%", (float(vi), float(yi)), xytext=(8, 0), textcoords="offset points", va="center",
                    fontsize=9)
    ax.set_yticks(y, cities)
    ax.invert_yaxis()
    ax.set_xlim(40, 80)
    # drawn axis-break mark at the left end of the x axis
    ax.plot([-0.012, 0.012], [-0.03, 0.03], transform=ax.transAxes, color="k", clip_on=False, linewidth=1)
    ax.plot([0.008, 0.032], [-0.03, 0.03], transform=ax.transAxes, color="k", clip_on=False, linewidth=1)
    ax.set_xlabel("Доставлено вовремя, %")
    ax.set_title("Тула доставляет вовремя чаще всех, 2025\nШкала начинается с 40%", fontsize=12)
    ax.grid(True, axis="x", color="#eeeeee", linewidth=0.6)
    clean(ax)
    fig.text(0.01, 0.01, "Источник: логистика, 2025", fontsize=8, color=GREY)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out("F18"), dpi=110)
    plt.close(fig)


def make_f19():
    from matplotlib.patches import Patch

    q = np.arange(4)
    online = [42, 48, 51, 57]
    offline = [30, 28, 27, 25]
    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(projection="3d")
    # shorter series in front (y = 0), taller behind (y = 1), so both stay visible
    ax.bar3d(q, np.zeros(4), np.zeros(4), 0.5, 0.5, offline, color="#fdae61", shade=True)
    ax.bar3d(q, np.ones(4), np.zeros(4), 0.5, 0.5, online, color="#1b3a6b", shade=True)
    for qi, a, b in zip(q, online, offline):
        ax.text(qi + 0.25, 1.25, a + 3, str(a), ha="center", fontsize=9)
        ax.text(qi + 0.25, 0.25, b + 3, str(b), ha="center", fontsize=9)
    ax.set_xticks(q + 0.25, ["Q1", "Q2", "Q3", "Q4"])
    ax.set_yticks([])
    ax.set_zlabel("Заказы, тыс.")
    ax.set_title("Онлайн растёт, офлайн снижается, 2025", fontsize=13)
    ax.legend(handles=[Patch(color="#1b3a6b", label="Онлайн"), Patch(color="#fdae61", label="Офлайн")],
              loc="upper left")
    fig.text(0.01, 0.01, "Источник: учёт заказов, 2025", fontsize=8, color=GREY)
    fig.savefig(out("F19"), dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    make_f17()
    make_f18()
    make_f19()
