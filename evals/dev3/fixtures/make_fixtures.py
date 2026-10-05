"""Generate dev set 3 (F7, F8, F9): several series on one value axis. Defects are listed in defects.md,
written before this script."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
CONV = {
    "Email": [3.9, 4.0, 4.1, 4.2],
    "Партнёры": [2.6, 2.8, 2.9, 3.0],
    "Реклама": [2.6, 2.25, 2.5, 2.7],
}
COLOURS = {"Email": "#4c72b0", "Партнёры": "#dd8452", "Реклама": "#55a868"}


def out(name):
    d = os.path.join(HERE, name)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "chart.png")


def grouped(ax, honest: bool):
    x = np.arange(len(QUARTERS))
    w = 0.26
    for k, (name, vals) in enumerate(CONV.items()):
        bars = ax.bar(x + (k - 1) * w, vals, w, color=COLOURS[name], label=name, zorder=2)
        ax.bar_label(bars, labels=[f"{v:g}" for v in vals], fontsize=8, padding=2)
    ax.set_xticks(x, QUARTERS)
    return x, w


def make_f7():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    grouped(ax, honest=False)
    ax.set_ylim(2.0, 4.5)                                   # D1: truncated, no note
    ax.grid(True, color="#333333", linewidth=1.0, zorder=3)  # D5: dark grid over the bars
    ax.set_title("Реклама догнала партнёров", fontsize=14)   # D2: false claim; D3: no unit
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=True)  # D6: boxed legend far away
    fig.tight_layout()                                      # D4: no source line
    fig.savefig(out("F7"), dpi=110)
    plt.close(fig)


def make_f8():
    regions = ["А", "Б", "В", "Г", "Д"]
    y24 = [62, 58, 71, 66, 54]
    y25 = [68, 55, 75, 70, 60]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    y = np.arange(len(regions))
    h = 0.38
    b24 = ax.barh(y - h / 2, y24, h, color="#8172b3", label="2024")   # 2024 drawn on top in each group
    b25 = ax.barh(y + h / 2, y25, h, color="#c44e52", label="2025")
    ax.invert_yaxis()
    for bars, vals in ((b24, y24), (b25, y25)):
        ax.bar_label(bars, labels=[f"{v:.3f}" for v in vals], fontsize=8, padding=2)  # D2: 3 decimals
    ax.set_yticks(y, regions)
    ax.set_xlim(50, 80)                                     # D1: truncated, no note
    ax.set_xlabel("Заказы, тыс.")
    ax.set_title("Заказы по регионам, 2024 и 2025", fontsize=14)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="lower right")  # D3: legend order reversed
    fig.tight_layout()                                      # D4: no source
    fig.savefig(out("F8"), dpi=110)
    plt.close(fig)


def make_f9():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x, w = grouped(ax, honest=True)
    ax.set_ylim(0, 4.8)
    ax.grid(True, axis="y", color="#e6e6e6", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    last = len(QUARTERS) - 1
    for k, (name, vals) in enumerate(CONV.items()):
        ax.annotate(name, (x[last] + (k - 1) * w, vals[last]), xytext=(18, 0), textcoords="offset points",
                    color=COLOURS[name], fontsize=9, va="center")
    ax.set_xlim(-0.5, last + 0.9)
    ax.set_title("Email конвертирует лучше всего во всех кварталах (конверсия, %)", fontsize=13)
    fig.text(0.01, 0.01, "Источник: CRM, выгрузка 01.10.2025", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out("F9"), dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    make_f7()
    make_f8()
    make_f9()
