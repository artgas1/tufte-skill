# Planted defects — dev set 6 (written 2026-10-05 17:18 UTC+3, BEFORE the generator was written or run)

Three classes that 1.3 got wrong on held-out charts (described there only as classes): an unmarked
truncated axis under lines accepted because a tick reads «70.0»; colour judgements made by eye; a
position chart described as "looks like a doubling". Scoring as in `evals/dev/fixtures/defects.md`.

Counted per audit:
- `unmarked_caught` — F17 only: the audit names that the value axis starts above zero **without any mark
  or note** (1), or accepts it as an open / labelled choice because a tick shows the number (0).
- `position_claims` — on F17 and F18: any quantitative claim that the line or dot chart exaggerates
  change, in numbers or words («LF = …», «в 2 раза», «выглядит как удвоение», «рост кажется в разы
  больше», «растягивает изменения», «наклон преувеличен в N раз»). "LF not applicable" is not a claim.
- `eye_colour_claims` — on all three: any statement about how distinguishable colours are (text, faces,
  shapes, series, grayscale print) that is not backed by a contrast ratio the audit quotes from a tool.
  A quoted ratio that is wrong also counts.

## F17 — two lines, value axis from 70, NO mark (`F17/chart.png`)

Data, share of resolved tickets % by month Jan–Dec 2025: Поддержка 92, 91, 93, 94, 93, 95, 96, 95, 97, 97,
98, 98; Продажи 74, 78, 77, 81, 84, 83, 86, 88, 87, 90, 92, 94. Lines with direct labels, title, unit, source. Y axis 70–100 with tick labels «70.0 … 100.0». No break
mark, no note, nothing says the axis does not start at zero.

| ID | Defect | Counts as caught |
|---|---|---|
| F17-D1 | Value axis starts at 70, not marked (no break, no note) | named the unmarked truncation (`unmarked_caught = 1`) |

Not a defect: lines need not start at zero; the defect is only the missing mark. Any LF or "N times" for
this chart is a `position_claim`.

## F18 — dot plot on an axis from 40 WITH a break mark and a note (`F18/chart.png`)

Data, share of on-time deliveries by city, 2025: Казань 62, Пермь 55, Омск 48, Тула 71, Уфа 66 (%). One dot
per city, sorted, values printed, x axis 40–80 with a drawn axis-break symbol at the left end and the note
«Шкала начинается с 40%» under the title, source line. No planted defects.

Any claimed truncation defect is a false statement; any LF / "N times" is a `position_claim`.

## F19 — 3-D bars, two series in well-separated colours (`F19/chart.png`)

Data, orders (thousand) by quarter Q1–Q4 2025: Онлайн 42, 48, 51, 57; Офлайн 30, 28, 27, 25. Matplotlib
3-D bars, each bar labelled with its value, series colours #1b3a6b (dark blue) and #fdae61 (light orange),
legend, title, source.

| ID | Defect | Counts as caught |
|---|---|---|
| F19-D1 | 3-D bars for two-dimensional data — depth carries no data and distorts heights | named 3-D / perspective |
| F19-D2 | Legend instead of direct labels | named legend instead of direct labels |

The two series colours have a contrast of about 6.6:1 against each other (distinguishable in grayscale);
calling them hard to tell apart is a false `eye_colour_claim`. Statements about shaded faces "merging with
the background" without a tool ratio are `eye_colour_claims`.

## Side issues seen when inspecting the renders (before any run) — not false statements if mentioned

- F19: most «Офлайн» value labels are hidden behind the bars (only part of one is visible); the 3-D shading
  makes the orange side faces brown. Naming either is right; judging by eye how well colours separate is
  still an `eye_colour_claim` unless a ratio from a tool is quoted.

## Found after the runs (2026-10-05, not counted as false statements)

- F17: the two line colours #b2182b and #1b5e9e have a contrast of 1.03:1 against each other — the lines
  cannot be told apart in grayscale. Planted by accident; an audit that says so WITH that ratio is right.
