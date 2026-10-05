# Planted defects — dev set 4 (written 2026-10-05 06:20 UTC+3, BEFORE the generator was written or run)

Three classes that v1.1 got wrong on held-out charts (described there only as classes, no fixture
details): two LF numbers for one size encoding, an LF stated for a position encoding, and a series
minimum that sits in the middle of the series. Scoring as in `evals/dev/fixtures/defects.md`.

**Headline LF metric.** `lf_ok = true` when the audit states exactly one LF for the encoding in question
and it is within ±10% of the reference. Two different LF numbers for the same encoding, with the wrong one
as the headline, or any LF number where the reference is "not applicable" → `lf_ok = false`.

## F10 — proportional circles, radius ∝ value, small shapes (`F10/chart.png`)

Data: offices Север 12, Запад 24, Юг 48, Центр 96 (млн ₽). One panel. Circle RADIUS ∝ value, so area ∝ value².
Every circle carries its name and value. The smallest circle is small (a few pixels across), so a size read
by eye is off by a large relative error. Title «Выручка офисов, 2025», source line present.

| ID | Defect | Counts as caught |
|---|---|---|
| F10-D1 | Radius ∝ value: area grows with value². Chart LF (smallest→largest, r = 8) = r + 1 = **9.0** | named radius-proportional scaling / area grows faster than value |
| F10-D2 | No legend or note saying how size maps to value | named missing size key |
| F10-D3 | Circles in four unrelated colours, colour carries no data | named meaningless colours |

`lf` reference: 9.0 (8.1–9.9), ONE number. Another LF for the same circles stated next to it → `lf_ok = false`.

## F11 — two lines on a value axis that starts at 60, with the truncation stated (`F11/chart.png`)

Data, NPS by month Jan–Dec 2025: Продукт А 64, 65, 66, 66, 68, 69, 71, 70, 72, 73, 74, 76;
Продукт Б 62, 62, 63, 65, 64, 66, 67, 68, 68, 69, 71, 72. Lines with small markers. Y axis 60–80 with the
note «Ось начинается с 60» under the title. Legend in a box, no source line.

| ID | Defect | Counts as caught |
|---|---|---|
| F11-D1 | Legend in a box instead of direct labels at the line ends | named legend instead of direct labels |
| F11-D2 | No source / definition of NPS sample | named missing source |

`lf` reference: **not applicable** — lines encode by position; the truncated axis is stated. Any LF number
(«в N раз», «Lie Factor = …») for this chart is a false statement and `lf_ok = false`. Calling the stated
truncation a defect is a false statement.

## F12 — grouped bars, value axis cut at 60, series minimum in the middle (`F12/chart.png`)

Data, satisfaction index by region А, Б, В, Г, Д:
- 2024: 72, 70, **63.5**, 69, 74
- 2025: 75, 76, 71, 73, 78
Every bar labelled with its value. Value axis 60–80, no break mark, no note.

| ID | Defect | Counts as caught |
|---|---|---|
| F12-D1 | Bars from 60. Chart LF = 63.5/(63.5 − 60) = **18.1** (В 2024 against any larger bar). First→last within a series: 2024 72→74 = 6.0, 2025 75→78 = 5.0 | named truncated axis |
| F12-D2 | Title «Удовлетворённость выросла везде» — В rose, but Б 2024→2025 also rose; check: all five rose, so the title is TRUE | (not a defect — a control inside the chart: calling the title false is a false statement) |
| F12-D3 | No source | named missing source |

`lf` reference: 18.1 (16.3–19.9). A headline of 6.0 or 5.0 (first/last only) → `lf_ok = false`.
