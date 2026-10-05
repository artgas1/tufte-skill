"""Generate dev set 5 (F13–F16): clean controls. Defects (none planted) are described in defects.md,
written before this script."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GREY = "#555555"


def out(name):
    d = os.path.join(HERE, name)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "chart.png")


def clean(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def make_f13():
    months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
    app = [3.6, 3.7, 3.7, 3.8, 3.9, 4.0, 4.0, 4.1, 4.2, 4.3, 4.4, 4.5]
    web = [3.5, 3.5, 3.6, 3.6, 3.7, 3.7, 3.8, 3.8, 3.9, 3.9, 4.0, 4.1]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    x = np.arange(12)
    ax.plot(x, app, color="#1b5e9e", linewidth=1.8)
    ax.plot(x, web, color="#d95f02", linewidth=1.8)
    ax.annotate("Приложение", (11, app[-1]), xytext=(6, 0), textcoords="offset points", color="#1b5e9e", va="center")
    ax.annotate("Сайт", (11, web[-1]), xytext=(6, 0), textcoords="offset points", color="#d95f02", va="center")
    ax.set_xticks(x, months)
    ax.set_xlim(-0.3, 12.6)
    ax.set_ylim(3.4, 4.8)
    ax.set_ylabel("Средняя оценка, 1–5")
    ax.set_title("Оценка приложения растёт быстрее, чем сайта, 2025\nОсь начинается с 3,4", fontsize=12)
    ax.grid(True, axis="y", color="#eeeeee", linewidth=0.6)
    clean(ax)
    fig.text(0.01, 0.01, "Источник: отзывы в сторах и на сайте, 2025", fontsize=8, color=GREY)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out("F13"), dpi=110)
    plt.close(fig)


def make_f14():
    regions = ["А", "Б", "В", "Г", "Д"]
    a = [66, 70, 63, 68, 72]
    b = [71, 72, 70, 69, 77]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    y = np.arange(len(regions))
    for yi, v1, v2 in zip(y, a, b):
        ax.plot([v1, v2], [yi, yi], color="#bbbbbb", linewidth=1.5, zorder=1)
        ax.scatter([v1], [yi], color="#9ebcda", s=60, zorder=2)
        ax.scatter([v2], [yi], color="#1b5e9e", s=60, zorder=2)
        ax.annotate(f"{v1}", (float(v1), float(yi)), xytext=(-8, 0), textcoords="offset points", ha="right", va="center", fontsize=9)
        ax.annotate(f"{v2}", (float(v2), float(yi)), xytext=(8, 0), textcoords="offset points", ha="left", va="center", fontsize=9)
    ax.set_yticks(y, regions)
    ax.invert_yaxis()
    ax.set_xlim(60, 80)
    ax.set_xlabel("Индекс удовлетворённости")
    ax.set_title("Удовлетворённость выросла во всех регионах\n● 2024 (светлая)   ● 2025 (тёмная) · Ось начинается с 60",
                 fontsize=12)
    ax.grid(True, axis="x", color="#eeeeee", linewidth=0.6)
    clean(ax)
    fig.text(0.01, 0.01, "Источник: опрос клиентов, 2024–2025", fontsize=8, color=GREY)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out("F14"), dpi=110)
    plt.close(fig)


def make_f15():
    ch = ["Чат", "Почта", "Телефон", "Форма"]
    v = [420, 310, 180, 95]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    y = np.arange(len(ch))
    bars = ax.barh(y, v, color="#1b5e9e", height=0.6)
    ax.bar_label(bars, labels=[str(x) for x in v], padding=3, fontsize=9)
    ax.set_yticks(y, ch)
    ax.invert_yaxis()
    ax.set_xlim(0, 480)
    ax.set_xlabel("Обращений за месяц")
    ax.set_title("Чат — главный канал обращений", fontsize=13)
    clean(ax)
    fig.text(0.01, 0.01, "Источник: учебный набор данных. Данные условные, для иллюстрации", fontsize=8, color=GREY)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out("F15"), dpi=110)
    plt.close(fig)


def make_f16():
    w = np.arange(1, 9)
    u = [12.1, 12.8, 13.0, 13.9, 14.2, 14.8, 15.5, 16.1]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(w, u, color="#1b5e9e", linewidth=2)
    ax.annotate("Активные пользователи", (8, u[-1]), xytext=(6, 0), textcoords="offset points", color="#1b5e9e",
                va="center", fontsize=9)
    ax.annotate("+33% за 8 недель", (4.5, 15.2), color=GREY, fontsize=10)
    ax.set_xlim(0.8, 9.6)
    ax.set_ylim(0, 18)
    ax.set_xticks(w, [f"нед. {i}" for i in w])
    ax.tick_params(colors="#666666")
    ax.set_ylabel("Тыс. пользователей в неделю", color="#666666")
    ax.set_title("Аудитория растёт каждую неделю", fontsize=13)
    clean(ax)
    fig.text(0.01, 0.01, "Источник: продуктовая аналитика, недели 1–8", fontsize=8, color=GREY)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out("F16"), dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    make_f13()
    make_f14()
    make_f15()
    make_f16()
