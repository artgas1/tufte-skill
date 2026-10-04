# Planted defects — dev set 2 (written 2026-10-04 08:53 UTC+3, BEFORE the generator was written or run)

Scoring as in `evals/dev/fixtures/defects.md`: caught = 1, partial = 0.5, missed = 0. A false statement is a
claimed defect or fact that is not on the chart or is arithmetically wrong (checked against the picture and the
generator). Real side issues listed at the end are not false statements.

## F4 — proportional circles: one panel scaled by radius, one by area (`F4/chart.png`)

Data. Left panel "Выручка, млн ₽": Самара 10, Казань 20, Санкт-Петербург 40, Москва 80 — circle RADIUS ∝ value.
Right panel "Клиенты, тыс.": Самара 15, Казань 30, Санкт-Петербург 45, Москва 60 — circle AREA ∝ value (honest).
Every circle carries its city name and value. Title "Выручка и клиенты по городам, 2025". Source line present.

| ID | Defect | Counts as caught |
|---|---|---|
| F4-D1 | Left panel: radius ∝ value, so area ∝ value². For a pair with data ratio r (smaller→larger), LF = r + 1: 10→80 → **LF = 9.0**; 20→80 → 5.0; 40→80 → 3.0; 10→20 → 3.0 | named that circle size (area) grows faster than the value / radius-proportional scaling |
| F4-D2 | The two panels use different size rules (radius vs area) for the same visual variable, without saying so | named that the panels are scaled differently / inconsistent encoding between panels |

LF metric F4: a number for the left panel, correct within ±10% for the pair the audit states (LF = r + 1).
Not a number (words only, e.g. "×64 by area") → lf_ok = null, not true.
The RIGHT panel is honest (LF = 1.0): calling it distorted, or giving it an LF ≠ 1 (±10%), is a false statement.

## F5 — 3-D columns without any readable values (`F5/chart.png`)

Data (in the generator only; NOT printed on the chart): Север 34, Юг 51, Запад 27, Восток 46, Центр 63.
The value axis has no numbers, bars carry no labels. Perspective 3-D view. Title "Продажи по регионам".

| ID | Defect | Counts as caught |
|---|---|---|
| F5-D1 | 3-D / perspective for one-dimensional data — depth carries no data and distorts apparent heights | named 3-D / perspective / extra dimension as distortion |
| F5-D2 | No numbers on the value axis and no value labels — the values cannot be read at all | named that values cannot be read / no scale / no labels |
| F5-D3 | No units and no source | named either |
| F5-D4 | Each bar a different colour, the colours carry no meaning (one series) | named meaningless / decorative per-bar colours |

LF metric F5: the correct behaviour is to say that the Lie Factor cannot be computed because values are not
readable (lf_ok = true). Any LF number (lf_ok = false) and any concrete value, percentage or ratio attributed to
the bars ("Центр ≈ 60", "Юг is about twice Запад") is a false statement — the chart does not show them.

## F6 — a deliberately clean chart with labelled choices (`F6/chart.png`)

Data: 2015 412, 2016 430, 2017 455, 2018 468, 2019 497 (thousand units). Bars, each labelled with its value.
The y-axis starts at 400; this is LABELLED on the chart (axis-break marks and the note "Ось Y начинается с 400").
Title "Продажи выросли на 21% за 2015–2019" (412→497 = +20.6%, correct). Units on the axis. Footer:
"Данные условные (иллюстрация). Источник: внутренний учёт, 2019". Light grid behind bars, no legend, no frame.

Planted defects: **none**.

False statements on F6 include: treating the labelled truncation as a defect or violation (mentioning it as a
labelled, acknowledged choice — with or without its LF — is fine); claiming there is no source or that
"данные условные" is a documentation failure; treating the age of the data (2019) or the business conclusion as
a defect; claiming the title's 21% is wrong; any misread value.

## Side issues (not false statements if mentioned)
- F4-I1: circles of the left panel touch or overlap labels at the largest size.
- F5-I1: category labels on the 3-D floor are slanted and small.
- F6-I1: a bar chart of a 5-point time series could equally be a line or dots.
