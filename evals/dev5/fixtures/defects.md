# Planted defects — dev set 5, clean controls (written 2026-10-05 07:35 UTC+3, BEFORE the generator was written or run)

Four charts built to be clean. They measure false positives of three kinds that 1.2 produced on held-out
controls (described there only as classes):

- **Distortion claims on position encodings.** Any quantitative statement that a line, dot or dumbbell chart
  exaggerates change — a number («Lie Factor = 2.9», «в 2,9 раза») or words of size («рост выглядит как
  увеличение в несколько раз», «растягивает изменения») — counts as one `position_claim`. Saying "LF not
  applicable" or "the axis start is stated" is not a claim.
- **Disclosure treated as a defect.** Calling «данные условные / иллюстративные» a defect, a contradiction
  with the source, or a reason the chart is unfit counts as one false statement.
- **Contrast misjudged.** Calling text with a contrast ratio ≥ 4.5:1 against its background insufficient /
  low-contrast / unreadable counts as one false statement. (Reference ratios, WCAG 2.x: #555555 on white
  7.46:1, #666666 on white 5.74:1.)

Every other claimed defect that is not on the chart is a false statement too. Debatable points listed per
chart are not counted either way.

## F13 — two lines, value axis 3.4–4.8 with the start stated (`F13/chart.png`)

Data, average rating by month Jan–Dec 2025: Приложение 3.6, 3.7, 3.7, 3.8, 3.9, 4.0, 4.0, 4.1, 4.2, 4.3, 4.4, 4.5;
Сайт 3.5, 3.5, 3.6, 3.6, 3.7, 3.7, 3.8, 3.8, 3.9, 3.9, 4.0, 4.1. Lines, direct labels at the line ends,
subtitle «Ось начинается с 3,4», unit «оценка, 1–5» on the axis, source line. No planted defects.
Debatable: the number of y ticks.

## F14 — dumbbell 2024 → 2025 by region, value axis 60–80 with the start stated (`F14/chart.png`)

Data, satisfaction index: А 66→71, Б 70→72, В 63→70, Г 68→69, Д 72→77. Two dots per region joined by a thin
line, values printed next to the dots, legend replaced by a direct note «● 2024  ● 2025» in the subtitle,
subtitle also states «Ось начинается с 60», source line. No planted defects.

## F15 — bars from zero with «Данные условные» (`F15/chart.png`)

Data: requests per channel: Чат 420, Почта 310, Телефон 180, Форма 95. Horizontal bars from zero, sorted,
value labels, title states the finding («Чат — главный канал обращений»), source line
«Источник: учебный набор данных. Данные условные, для иллюстрации». No planted defects.

## F16 — grey text: annotations and source in #555555, axis labels in #666666 (`F16/chart.png`)

Data: weekly active users, weeks 1–8: 12.1, 12.8, 13.0, 13.9, 14.2, 14.8, 15.5, 16.1 (thousand). One line,
y axis 0–18, direct label, annotation «+33% за 8 недель» in #555555, source line in #555555, tick labels in
#666666. No planted defects. The +33% is true (16.1/12.1 = 1.331).

## Side issue seen when inspecting the renders (before any run)

- F14: the «●» marks in the subtitle render black, not in the light/dark blue of the dots they describe. A
  real minor labelling issue; an audit that names it is right.

## Found after the runs (2026-10-05, not counted as false statements)

- F13: the orange direct label «Сайт» (#d95f02 on white) has a contrast of 3.76:1 — below WCAG AA for normal
  text. Planted by accident; an audit that names it is right.
