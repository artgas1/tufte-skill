# Planted defects — dev set 7, colour statements (written 2026-10-05 19:22 UTC+3, BEFORE the generator was written or run)

Purpose: measure colour statements, the class 1.4 failed on held-out charts (described there only as classes:
`colours` took the neighbouring line or an anti-aliased edge; statements about paleness, merging, grayscale
or colour-vision deficiency without a number).

**Metric.** Every statement in an audit about colours separating — text vs background, pale / faded /
low-contrast, merging, grayscale, colour-vision deficiency (CVD) — is one *colour statement*. It is
*numbered and correct* when it quotes a ratio or ΔE from the tool AND that number matches the reference
below within 5% AND its conclusion follows from the number (contrast: text fails below 4.5:1, marks or
series in grayscale below 3:1; CVD: confused only below ΔE 10). Share reported: numbered-and-correct /
all colour statements. Statements that a colour carries meaning or not (e.g. "colour carries no data")
are not colour statements.

Reference values (WCAG 2.x contrast; CVD = Machado 2009 at full severity, CIE76 ΔE, worst of protan /
deutan / tritan):

| Pair | Contrast | CVD worst ΔE |
|---|---|---|
| #b2182b vs #1b5e9e (two lines, F20) | 1.03:1 | 57.2 (protan) |
| #555555 on white (footnote, F20) | 7.46:1 | — |
| #999999 on white (footnote, F21) | 2.85:1 | — |
| #d62728 vs #2ca02c (two categories, F21) | 1.48:1 | 7.3 (deutan) |
| #1b3a6b vs #fdae61 (two categories, F21) | 6.12:1 | 76.0 (tritan) |
| gradient base #eef3f9 on white (F21) | 1.12:1 | — |

## F20 — two lines with direct labels next to the line ends, grey footnote (`F20/chart.png`)

Data, monthly active customers, thousand, Jan–Dec 2025: Онлайн 41, 43, 44, 47, 49, 52, 53, 55, 58, 60, 62, 65 in
#1b5e9e; Офлайн 38, 39, 39, 41, 42, 42, 44, 45, 45, 47, 48, 49 in #b2182b. Each line labelled at its end, the
label touching the line. Footnote «Источник: CRM, 2025» in #555555. Y axis from 0.

| ID | Defect | Counts as caught |
|---|---|---|
| F20-D1 | The two lines have nearly the same lightness (1.03:1): in grayscale print they are told apart only by their labels | named it WITH a ratio |

Not defects: the footnote contrast (7.46:1 passes AA); CVD (ΔE 57 — distinct); calling either a problem is
a false colour statement.

## F21 — bars with a gradient fill, four categories identified by a legend only, light-grey footnote (`F21/chart.png`)

Data, revenue share by channel, %, 2025: Сайт 38, Маркетплейсы 27, Розница 21, Партнёры 14 — bars in #1b3a6b,
#fdae61, #d62728, #2ca02c, each bar filled with a vertical gradient that fades to #eef3f9 at its base. Legend
only (no direct labels). Footnote «Источник: учёт продаж» in #999999.

| ID | Defect | Counts as caught |
|---|---|---|
| F21-D1 | Gradient fill: decoration, and the base of each bar fades into the background (1.12:1) | named the gradient (a ratio needed only for the "fades" part) |
| F21-D2 | Legend instead of direct labels | named |
| F21-D3 | Розница (#d62728) and Партнёры (#2ca02c) are confusable for deutan readers (ΔE 7.3) and in grayscale (1.48:1) | named WITH ΔE or ratio |
| F21-D4 | Footnote #999999 on white is 2.85:1 — below AA | named WITH a ratio |
