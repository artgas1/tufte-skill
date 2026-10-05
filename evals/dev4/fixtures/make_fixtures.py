"""Generate dev set 4 (F10, F11, F12). Defects are listed in defects.md, written before this script."""
import os

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


def make_f10():
    names = ["Север", "Запад", "Юг", "Центр"]
    vals = [12, 24, 48, 96]
    colours = ["#e377c2", "#17becf", "#bcbd22", "#8c564b"]   # D3: colour carries no data
    fig, ax = plt.subplots(figsize=(10, 4.6))
    xs = [0.8, 2.2, 4.4, 7.9]
    r_max = 0.55
    for x, n, v, c in zip(xs, names, vals, colours):
        r = r_max * v / max(vals)                             # D1: radius ∝ value
        ax.add_patch(Circle((x, 1.8), r, color=c))
        ax.text(x, 1.8 - r - 0.15, f"{n}\n{v}", ha="center", va="top", fontsize=10)
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.6, 3.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Выручка офисов, 2025", fontsize=14)        # D2: no size key
    fig.text(0.01, 0.01, "Источник: управленческая отчётность, млн ₽", fontsize=8, color="#555555")
    fig.savefig(out("F10"), dpi=110)
    plt.close(fig)


def make_f11():
    months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
    a = [64, 65, 66, 66, 68, 69, 71, 70, 72, 73, 74, 76]
    b = [62, 62, 63, 65, 64, 66, 67, 68, 68, 69, 71, 72]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    x = np.arange(12)
    ax.plot(x, a, marker="o", markersize=3, color="#4c72b0", label="Продукт А")
    ax.plot(x, b, marker="o", markersize=3, color="#dd8452", label="Продукт Б")
    ax.set_xticks(x, months)
    ax.set_ylim(60, 80)
    ax.set_ylabel("NPS")
    ax.set_title("NPS по месяцам, 2025\nОсь начинается с 60", fontsize=13)
    ax.legend(loc="upper left", frameon=True)                # D1: boxed legend; D2: no source
    ax.grid(True, axis="y", color="#e6e6e6", linewidth=0.6)
    fig.tight_layout()
    fig.savefig(out("F11"), dpi=110)
    plt.close(fig)


def make_f12():
    regions = ["А", "Б", "В", "Г", "Д"]
    y24 = [72, 70, 63.5, 69, 74]
    y25 = [75, 76, 71, 73, 78]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    x = np.arange(len(regions))
    w = 0.38
    b1 = ax.bar(x - w / 2, y24, w, color="#8da0cb", label="2024")
    b2 = ax.bar(x + w / 2, y25, w, color="#1b5e9e", label="2025")
    ax.bar_label(b1, labels=[f"{v:g}" for v in y24], fontsize=9, padding=2)
    ax.bar_label(b2, labels=[f"{v:g}" for v in y25], fontsize=9, padding=2)
    ax.set_xticks(x, regions)
    ax.set_ylim(60, 80)                                       # D1: truncated, no note
    ax.set_ylabel("Индекс удовлетворённости")
    ax.set_title("Удовлетворённость выросла везде", fontsize=14)
    ax.legend(loc="upper left")
    fig.tight_layout()                                        # D3: no source
    fig.savefig(out("F12"), dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    make_f10()
    make_f11()
    make_f12()
