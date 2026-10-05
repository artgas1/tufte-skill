---
name: tufte
description: >-
  Audit, critique or build charts for honesty and clarity using Edward Tufte's principles: Lie
  Factor, zero baselines, dual axes, icon/bubble area scaling, uneven time axes, missing context,
  chartjunk and data-ink. Use this skill whenever the user asks to check, review, audit, critique,
  fact-check or fix a chart, graph, plot, infographic or dashboard figure (an image, a screenshot
  or plotting code), asks whether a chart is misleading, or prepares a chart for management,
  clients or publication — even if Tufte is never mentioned. Works in any language ("проверь
  график", "аудит графика", "is this chart misleading?"). Complements palette and chart-type
  skills: this one owns integrity and evidence.
---

# Tufte: chart integrity — audit and build

An audit fails in two ways: it misses a distortion, or it **misreads the chart** (takes one line
for another, trusts a legend that does not apply) and then reasons confidently from the misreading.
In practice the second failure produces most of the wrong statements. So this procedure computes
what can be computed, transcribes what has to be read, and only then judges.

Order of importance: (1) does the chart misrepresent the data, (2) does it mislead by omission or
by its claims, (3) does it obstruct reading, (4) non-data ink. If another skill in the environment
governs palette, chart type or interaction, follow it for those; this skill does not repeat them.

## Tool

`scripts/tufte_check.py` inside this skill's base directory (python3 + numpy + matplotlib, no
network). Call it as **one command that starts with `python3` and the full absolute path** — no
`cd`, no shell variables, no `&&`/`;`: restricted environments allow only commands that start with
`python3`, and every refused call costs a turn. Chain several checks in one call with `--then`:

```
python3 /abs/path/to/skill/scripts/tufte_check.py image chart.png --then lf --data 120 150 --baseline 100 --then time 2000 2005 2010 2011
```

| Command | Use |
|---|---|
| `image chart.png` | Image only. Aspect ratio, colour-coded axes, colour sets of the left/right halves. It cannot compute integrity from pixels. |
| `blobs chart.png` | Measures coloured shapes (circles, icons, bubbles) in pixels: box width/height, area. |
| `scaling --values … --sizes …` | Fits which rule maps values to measured sizes (radius ∝ value or area ∝ value) and gives the LF for smallest→largest. |
| `figure plot.py` | Runs a matplotlib script (show/close disabled) and checks every figure: bar baselines with Lie Factor (per series and chart-wide), dual-axis colours, category colours across panels, time spacing, pies, grid, 3-D, smoothing, area fills, icon scaling, titles. |
| `spec chart.json` | Vega-Lite spec or Plotly figure JSON: the same checks where the spec allows. |
| `lf --data A B --baseline X` | Lie Factor from two values you read. `--encoding both-dims`/`radius` when linear size ∝ value, `volume` for 3-D; `--measured D1 D2 --measure diameter` for sizes measured in pixels. |
| `lfmax --series NAME=v1,v2,… --series … --baseline X` | Several series on one axis: the chart Lie Factor — the strongest distortion over every pair of marks, across series too — plus each series' own LF. |
| `lf --bound …` | Values unreadable: `--baseline B --axis-max T` gives LF ≥ T/(T−B) for bars from B; `--encoding radius` gives LF ≥ 2, but only when you know linear size ∝ value (a legend says so) — growing width and height alone do not prove it; bare `--bound` tells you to report "cannot be computed". |
| `time L1 L2 …` | Are labels drawn evenly also even in time? `--positions` if the spacing is not even. |

An ERROR from `figure`/`spec` is computed from the chart's own objects — report it (check it
against the picture once). WARN is a candidate that needs your judgement.

## Audit

### 1. Compute what can be computed
Source available (script, notebook cell, JSON spec) → `figure` or `spec`. Only an image → look at
it, then make one call: `image` (plus `blobs` if sizes encode values) chained with the `lf`/`time`
checks for the values you read (step 3).

### 2. Transcribe before judging
Write a compact **Reading** block, then judge only from it:
- panels and what each shows;
- each axis: title, unit, range, where it starts, linear/log, label colour;
- each series or category: name → colour → axis/panel, and **how you know the name** (legend,
  direct label, title, or inference);
- time labels exactly as printed, in order;
- every number printed on the chart, including numbers in titles and annotations.

Three rules make the reading trustworthy:

- **Identity before values.** Axis colours and legends are claims made by the chart; checking them
  is part of the audit. On a dual-axis chart, decide which line belongs to which axis from
  independent evidence only — a legend or direct label, a number stated in the title or an
  annotation (which pairing reproduces "tripled"?), the plausibility of each line's values on each
  scale. The axis colour is the claim under test, so it never counts as evidence for itself. If the
  evidence supports the pairing that the axis colours contradict, the axis colours are swapped —
  a top-severity finding, since readers will read each line on the wrong scale. If the evidence
  splits (the title fits only the pairing the colours contradict), the chart contradicts itself:
  report "either the axis colours are swapped or the headline is false" as a top finding, and do
  not quote values that depend on the pairing.
- **A legend covers only what it says it covers.** For repeated panels (two pies, small
  multiples), build category → colour for each panel. When categories are identified only by
  colour and the legend is scoped to one panel (e.g. titled "2024"), test whether identities hold:
  the same order of values with different colours, or a colour whose value jumps implausibly
  (4% → 30%), means the colours were reassigned. Panels may be rotated: compare the order of
  values around the circle or along the axis, not absolute positions. In a panel the legend does
  not cover, refer to marks by value and position ("the 25% slice"), never by an inferred name —
  in the findings and in the Reading. Report that categories cannot be matched across panels,
  and do not compute per-category changes from colour.
- **Unreadable is a finding, not a guess.** If text is too small, a colour is ambiguous, or you
  cannot tell where two lines cross, write "unreadable" and build nothing on it.

### 3. Compute from the reading
- **Lie Factor** for every magnitude that is not a plain length from zero — truncated bars, icons,
  bubbles, areas, 3-D, pictograms. LF = (size of effect shown) / (size of effect in data), effect =
  (second − first) / first (VDQI p. 57). Distortion starts outside 0.95–1.05.
  - **Every LF number comes from the tool.** Run `lf` (or `scaling`/`lf --bound`), and in the
    finding quote the command and the line it printed. An LF you worked out in your head, a ratio
    of ratios, or "≈16× by area, ≈4× by diameter" is not an LF: if you did not run the tool, state
    no LF number.
  - **Truncated bars:** `lf --data V1 V2 --baseline B`. For bars LF = v/(v − B) with v the smaller
    value, so the exact value of the larger bar barely matters.
  - **Several series on one truncated axis:** readers compare bars across series, not only within
    one. Run `lfmax` with every value of every series (`--series Email=3.9,4.2 --series Ads=2.4,2.8
    --baseline 2`). The **headline LF is the chart LF it prints** (the smallest bar against any larger
    one); per-series LFs go after it as detail. Same for bubbles or icons of several series: pass all
    shapes of the panel to `scaling` at once. `figure`/`spec` print the chart LF themselves
    (`lie-factor-max`).
  - **Circles, bubbles, icons:** read the printed values, measure the shapes with `blobs` (box width
    = diameter), then `scaling --values v1 v2 … --sizes d1 d2 …` (all shapes of one panel, same
    order). It fits the rule — radius ∝ value means area ∝ value² — and prints one LF; small shapes
    carry 1–2 px of anti-aliasing error, so prefer `scaling` over a two-shape `lf --measured`.
    Report that one number.
  - **Values not readable** (no numbers on the axis and no labels; 3-D or perspective that hides
    the baseline): do not estimate values — not even "about 60" or "roughly twice". Write "LF cannot
    be computed: the values are not readable". If the axis range is readable for bars from a
    non-zero baseline, `lf --bound --baseline B --axis-max T` gives a lower bound you may quote.
- **Time axis:** run `time` on the printed labels. Equal spacing for unequal intervals, or a
  silently missing period, is a finding.
- **Every other number you state** (growth multiples, sums of percentages, differences): compute
  it, do not estimate it. Percent labels of one pie must sum to 100.

### 4. Judge with the rubric
List only rows that actually fail. Page numbers point to `references/canon.md`.

**Not findings:**
- **Choices the chart labels openly.** Tufte's second principle: clear labelling defeats
  distortion (VDQI p. 56). Examples:
  - an axis that starts above zero with a break mark or a note ("axis starts at 400");
  - a labelled log scale;
  - "illustrative / hypothetical data" or "данные условные" — this is a disclosure and counts
    as documentation;
  - a stated deflator or a stated sampling note.

  At most mention them as acknowledged choices (with the `lf` output for reference), never as
  defects.
- **Judgments outside this rubric**: the data are old, the topic or the business conclusion, what
  else the author "should" have shown, personal taste. If no row fails, the verdict is "no" and
  the findings list is empty or holds only minor ink notes.

| Area | Question | Fails when |
|---|---|---|
| Proportion | Is every magnitude drawn proportionally? | LF outside 0.95–1.05 (VDQI p. 57) |
| Baseline | Do bars and filled areas start at zero on a linear axis? | Non-zero start or log scale under bars |
| Area | Do icons, bubbles and circles scale by area? | Width and height both ∝ value; radius ∝ value; Plotly default `sizemode='diameter'` |
| Dimensions | Does depth carry data? | 3-D, perspective or extrusion for 1-D/2-D data (VDQI p. 71) |
| Time | Is distance proportional to elapsed time? | Uneven intervals drawn evenly; a period silently missing |
| Money | Are long money series in real units? | Nominal prices over many years without saying so (VDQI p. 68) |
| Consistency | Do panels share scales, units, colours and order? | Same category in two colours; different scales without notice (VDQI p. 61) |
| Two axes | Is a second y-scale avoided? | Two y-scales: their alignment is arbitrary, so crossings and relative slopes mean nothing. Axis colour ≠ its series is worse |
| Interpolation | Are values between observations real? | Smoothed curves through few points; area filled to an arbitrary level |
| Context | Compared to what? | No baseline period, comparison group or whole (VDQI p. 74) |
| Claims | Does the text say only what the data show? | Number in the title that the data contradict; causal claim without a mechanism; shouting title |
| Labels | Can a reader decode it without guessing? | Missing units; legend instead of direct labels; legend for one series; legend order ≠ data order |
| Documentation | Who made it, from what? | No source, date or definition (BE p. 132) |
| Precision | Do digits match the data? | Three decimals on shares |
| Pies | Is a pie the right form at all? | > ~6 slices, unsorted, exploded slice, several pies compared (VDQI p. 178) |
| Shape | Is the aspect ratio fair to slopes? | Line chart taller than wide; Tufte: ~50% wider than tall (VDQI p. 190); bank to 45° |
| Data-ink | Is every drop of ink data? | Dark, dense or on-top grid (VDQI p. 113); gradients, textures, shadows, frames, hatching (moiré); heavy markers and thick lines hiding values; decoration that takes over ("duck", VDQI p. 116) |

### 5. Report
Reply in the user's language.
1. **Verdict** in one line: does the chart misrepresent the data (yes / no / can't tell), and its
   single biggest problem.
2. **Findings**, most severe first, grouped by the four levels above. Each: *what* (with the
   evidence — the value you read, or the tool command and its output line for any LF), *why it
   matters* (one line, cite the principle), *fix* (concrete: what to draw instead).
3. **Could not verify** — what was unreadable or ambiguous.
4. **Reading** — the transcription from step 2, compact.

Do not pad. A clean chart gets a short report; an invented problem is as wrong as a missed one.

## Build

When you draw or redraw a chart:
1. Name the comparison it must make ("compared to what?") and pick the form (follow a chart-type
   skill if the environment has one).
2. Integrity defaults: bars and areas from zero; magnitude by position or length; if size encodes
   a value, area ∝ value (matplotlib `s` is already an area; Plotly `sizemode='area'`); one y-axis —
   two measures go to two aligned panels or an index (=100 at the start); a real time axis
   (numbers or datetimes, never strings); real money for long spans; straight segments between
   observations; about 1.5:1 width:height for lines unless the data suggest otherwise.
3. Ink: light grid behind data or none; no 3-D, shadows, gradients or textures; direct labels
   over legends; a title that states the finding the data support; units; a source line.
4. Run `tufte_check.py figure <script>` (or `spec`), fix every ERROR, decide on every WARN, then
   render and look at the image.

Code idioms for these fixes: `references/build-recipes.md`.

## References
- `references/canon.md` — verified quotes with book and page; cite from it, not from memory.
- `references/build-recipes.md` — matplotlib, Plotly and Vega-Lite snippets for honest defaults.
