"""Generate dev set 7 (F20, F21): colour statements. Defects are listed in defects.md, written before this
script."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))


def out(name):
    d = os.path.join(HERE, name)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "chart.png")


def clean(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def make_f20():
    months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
    online = [41, 43, 44, 47, 49, 52, 53, 55, 58, 60, 62, 65]
    offline = [38, 39, 39, 41, 42, 42, 44, 45, 45, 47, 48, 49]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    x = np.arange(12)
    ax.plot(x, online, color="#1b5e9e", linewidth=2)
    ax.plot(x, offline, color="#b2182b", linewidth=2)
    ax.annotate("Онлайн", (11.0, 65.0), xytext=(2, 0), textcoords="offset points", color="#1b5e9e", va="center")
    ax.annotate("Офлайн", (11.0, 49.0), xytext=(2, 0), textcoords="offset points", color="#b2182b", va="center")
    ax.set_xticks(x, months)
    ax.set_xlim(-0.3, 12.6)
    ax.set_ylim(0, 72)
    ax.set_ylabel("Активные клиенты, тыс.")
    ax.set_title("Онлайн растёт быстрее офлайна, 2025", fontsize=13)
    clean(ax)
    fig.text(0.01, 0.01, "Источник: CRM, 2025", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out("F20"), dpi=110)
    plt.close(fig)


def make_f21():
    names = ["Сайт", "Маркетплейсы", "Розница", "Партнёры"]
    vals = [38, 27, 21, 14]
    cols = ["#1b3a6b", "#fdae61", "#d62728", "#2ca02c"]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    x = np.arange(4)
    w = 0.6
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    for xi, v, c in zip(x, vals, cols):
        cmap = LinearSegmentedColormap.from_list("g", ["#eef3f9", c])
        ax.imshow(grad, extent=(xi - w / 2, xi + w / 2, 0, v), origin="lower", aspect="auto", cmap=cmap, zorder=2)
    ax.set_xlim(-0.6, 3.6)
    ax.set_ylim(0, 42)
    ax.set_xticks(x, ["", "", "", ""])
    ax.set_ylabel("Доля выручки, %")
    ax.set_title("Каналы продаж, 2025", fontsize=13)
    ax.legend(handles=[Patch(color=c, label=n) for n, c in zip(names, cols)], loc="upper right")
    clean(ax)
    fig.text(0.01, 0.01, "Источник: учёт продаж", fontsize=8, color="#999999")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out("F21"), dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    make_f20()
    make_f21()
