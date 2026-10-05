# Planted defects — dev set 3, several series on one axis (written 2026-10-05 05:06 UTC+3, BEFORE the generator was written or run)

Scoring as in `evals/dev/fixtures/defects.md`: caught = 1, partial = 0.5, missed = 0. A false statement is a
claimed defect or fact that is not on the chart or is arithmetically wrong.

**Chart LF metric (the v1.1 target).** For bars drawn from a baseline B, LF of a pair = v/(v − B) with v the
first (smaller) value, so the strongest distortion on the chart is the smallest bar of ANY series against any
larger bar. `lf_chart_ok = true` when the audit's headline LF for the truncated axis is the chart maximum, within
±10%. A number that is right for some within-series pair but is not the chart maximum → `lf_chart_ok = false`
(that is the v1.0 failure mode), not a false statement. No LF number at all → `null`.

## F7 — grouped columns, three channels, value axis cut at 2.0 (`F7/chart.png`)

Data, conversion in %, quarters Q1–Q4 2025:
- Email 3.9, 4.0, 4.1, 4.2
- Партнёры 2.6, 2.8, 2.9, 3.0
- Реклама 2.6, **2.25**, 2.5, 2.7 (dip in Q2)

Every bar carries its value label. Value axis from 2.0 to 4.5, no break mark, no note.

| ID | Defect | Counts as caught |
|---|---|---|
| F7-D1 | Value axis starts at 2.0 under bars. Chart LF = 2.25/(2.25 − 2) = **9.0** (Реклама Q2 against any larger bar). Within-series first→last: Email 2.05, Партнёры 4.33, Реклама 4.33 | named truncated axis / bars not from zero |
| F7-D2 | Title «Реклама догнала партнёров» — the data contradict it (Q4: Реклама 2.7 < Партнёры 3.0) | named the false headline claim |
| F7-D3 | No unit on the value axis or in the title (the numbers are %) | named missing unit |
| F7-D4 | No source / date line | named missing source |
| F7-D5 | Dark, dense grid drawn over the bars | named heavy grid / grid on top |
| F7-D6 | Legend in a box far from the bars instead of direct labels | named legend instead of direct labels (partial if only "legend") |

`lf_chart` reference: 9.0 (8.1–9.9).

## F8 — horizontal grouped bars, two years, value axis cut at 50 (`F8/chart.png`)

Data, orders in thousands, regions А, Б, В, Г, Д:
- 2024: 62, 58, 71, 66, **54**
- 2025: 68, 55, 75, 70, 60

Bars carry value labels. Value axis from 50 to 80, no break mark, no note.

| ID | Defect | Counts as caught |
|---|---|---|
| F8-D1 | Value axis starts at 50 under bars. Chart LF = 54/(54 − 50) = **13.5** (Д 2024 against any larger bar). Region А 2024→2025: 62/12 = 5.17 | named truncated axis |
| F8-D2 | Value labels with three decimals («62.000») for thousands of orders | named spurious precision |
| F8-D3 | Legend order (2025 above 2024) is the reverse of the bar order inside each group (2024 above 2025) | named legend order ≠ data order |
| F8-D4 | No source / date | named missing source |

`lf_chart` reference: 13.5 (12.15–14.85).

## F9 — control: grouped columns from zero, clean (`F9/chart.png`)

Data: same as F7 but honest: value axis from 0, unit «конверсия, %» in the title, direct labels at the end of
each group instead of a legend, light grid behind the bars, source line «Источник: CRM, выгрузка 01.10.2025».
Title «Email конвертирует лучше всего во всех кварталах» (true).

No planted defects. Any claimed defect is a false statement, except the listed debatable point.
An LF ≠ 1 (±10%) for any pair is a false statement.

Debatable (not counted either way): three colours could be argued to be unnecessary when labels are direct.

## Found after the runs (2026-10-05, not counted as false statements)

- F9: the source line says «выгрузка 01.10.2025», but the chart shows Q4 2025 — an export from 1 October cannot
  hold the fourth quarter. A real inconsistency planted by accident; an audit that names it is right.
