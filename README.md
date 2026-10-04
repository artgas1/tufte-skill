# tufte-skill

A Claude Code plugin with one skill, `tufte`. It audits charts for honesty and clarity, and builds
them with honest defaults, following Edward Tufte's principles: Lie Factor, zero baselines, dual
axes, area scaling, time axes, context, chartjunk and data-ink.

The skill is small on purpose: a ~2,200-word procedure, a deterministic checker script, and a
reference file of quotes verified against the books. It complements palette and chart-type
skills rather than replacing them.

## What it does

**Audit** (an image, a screenshot, a matplotlib script, a Vega-Lite spec or a Plotly figure):

1. Computes what can be computed with `scripts/tufte_check.py`.
2. Transcribes the chart before judging it — axes, baselines, which series is which and *how
   that is known*, time labels, every printed number. Most wrong statements in chart audits come
   from misreading (taking one line for another, trusting a legend that covers only one panel),
   so the skill treats axis colours and legends as claims to check, not facts.
3. Computes the Lie Factor and other arithmetic instead of estimating it. Every LF number in a
   report comes from the checker, with the command quoted; when values cannot be read, the report
   says so (or gives a proven bound) instead of guessing.
4. Judges against a compact rubric and reports findings in four levels: misrepresents the data,
   misleads by omission or claim, obstructs reading, non-data ink. Choices the chart labels openly
   (an annotated axis break, "illustrative data") and opinions outside the rubric are not findings.

**Build**: honest defaults (bars from zero, area-scaled bubbles, one y-axis, real time axis,
real money, no smoothing through sparse points, light chrome), then runs the checker on the
script before rendering.

## The checker

`skills/tufte/scripts/tufte_check.py` — Python, no network.

| Command | What it checks |
|---|---|
| `lf --data A B [--baseline X \| --encoding radius \| --measured D1 D2 --measure diameter]` | Lie Factor (VDQI p. 57) for truncated axes and size encodings; prints a "Quote this result as" line |
| `lf --bound [--baseline B --axis-max T \| --encoding radius]` | When values are unreadable: LF ≥ T/(T−B) for bars from a non-zero baseline (for bars LF = v/(v−B), v the smaller value); LF ≥ 2 when linear size ∝ value; otherwise "cannot be computed" |
| `blobs chart.png` | Measures coloured shapes (circles, icons, bubbles) in pixels |
| `scaling --values … --sizes …` | Fits the rule that maps values to measured sizes (radius ∝ value vs area ∝ value), robust to anti-aliasing on small shapes, and gives the LF for smallest→largest |
| `time LABEL...` | Time labels drawn evenly but uneven in time; missing periods |
| `image chart.png` | What pixels can tell: aspect ratio, colour-coded axes, colour sets of repeated panels. Says plainly that integrity cannot be computed from pixels |
| `figure plot.py` | Runs a matplotlib script (show/close disabled) and checks bar baselines (with Lie Factor; downgraded to a note when the chart's text labels the truncation), dual-axis colour swaps, one category in two colours, time spacing, pies (count, explode, labels summing to 100), dark or on-top grid, 3-D, smoothing, fills to arbitrary levels, icons scaled in both dimensions, shouting or causal titles, false precision, aspect and banking |
| `spec chart.json` | The same checks for Vega-Lite specs and Plotly figure JSON where the spec allows (incl. Plotly's default `sizemode='diameter'`) |

`figure` **executes** the script you give it. Run it on plotting code you trust.

Several commands run in one process with `--then`
(`image chart.png --then lf --data 410 520 --baseline 400`).

Tests: `python3 -m pytest skills/tufte/scripts/test_tufte_check.py` (41 tests) — every check has a
negative control (silent on a clean chart, fires on a broken one). Lint: `ruff check .` and
`pyright skills/tufte/scripts evals` are clean.

## Install

**As a plugin (recommended)**
```
/plugin marketplace add artgas1/tufte-skill
/plugin install tufte-skill@tufte-skill
```
or in `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "tufte-skill": { "source": { "source": "github", "repo": "artgas1/tufte-skill" } }
  },
  "enabledPlugins": { "tufte-skill@tufte-skill": true }
}
```

To pin a release, add `"ref": "tufte-skill--v1.0.0"` next to `"repo"`. Settings alone register
the marketplace; run `claude plugin install tufte-skill@tufte-skill` once to install the plugin.

**As a plain skill**: copy `skills/tufte/` to `~/.claude/skills/tufte/`.

Requirements: Python ≥ 3.9 with numpy and matplotlib for the `image`, `blobs` and `figure` commands
(Pillow comes with matplotlib). `lf`, `time` and `spec` need only the standard library plus
matplotlib's colour helpers (`scaling` needs only the standard library). Tested with Python 3.13.9, numpy 2.3.5, matplotlib 3.10.9. Plotly
is not required: `spec` reads the figure JSON (`fig.to_json()`).

## Use

The skill loads by itself on requests such as "audit this chart", "is this graph misleading?",
"проверь график перед отправкой". You can also call it explicitly: `/tufte-skill:tufte`.

## How it was evaluated

**Protocol.** The same audit prompt ("list every design and data-honesty problem in chart.png:
what, why, fix") is run with and without the skill. The charts are synthetic fixtures with
**planted defects written down before the charts were generated**. A blind judge (audits
relabelled with random codes, skill names masked) marks each planted defect caught / partial /
missed and lists every false statement about the chart; cost comes from the CLI's reported
`total_cost_usd`. Acceptance criteria were fixed in [`ACCEPTANCE.md`](ACCEPTANCE.md) before the
first run.

**Development set 1** (`evals/dev/`, three charts, 32 planted defects). The skill was tuned on
these, so the numbers below show behaviour on charts it was fitted to — not generalisation. The
tables are for version 0.1.0; a 1.0.0 regression run (Sonnet, one run per chart) found
10/10, 11/11 and 11/11 planted defects with 0 false statements and LF = 41 on the truncated bars.

<!-- DEV-RESULTS-START -->
Three arms, all on the same prompt (which does not mention any skill), fixtures and judge:
**this skill** (loaded by the agent's own decision), **no skill** (the agent's normal
environment, which includes a built-in palette/form skill), and **jpoindexter `/tufte`** (that
collection's router, invoked explicitly). Runs of 2026-10-04; version 0.1.0.

| Sonnet | n (F1/F2/F3) | defects found | false statements / audit | Lie Factor correct (bars / icons) | swapped axis colours caught | pie colours reassigned caught | cost vs no skill |
|---|---|---|---|---|---|---|---|
| this skill | 3/3/3 | 98.5% | 0.33 | 3/3 · 2/3 | 2 + 1 partial / 3 | 2 + 1 partial / 3 | ×1.16 |
| no skill | 6/3/3 | 92.4% | 4.39 | 1/6 · 1/6 | 0/3 | 0/3 | ×1.00 |
| jpoindexter `/tufte` | 6/3/3 | 93.4% | 4.56 | 6/6 · 4/6 | 0/3 | 0/3 | ×1.9 |

| Opus | n (F1/F2/F3) | defects found | false statements / audit | Lie Factor correct (bars / icons) | swapped axis colours caught | pie colours reassigned caught | cost vs no skill |
|---|---|---|---|---|---|---|---|
| this skill | 2/2/2 | 99.2% | 0.17 | 2/2 · 2/2 | 2/2 | 1 + 1 partial / 2 | ×1.08 |
| no skill | 3/3/3 | 93.4% | 5.00 | 3/3 · 1/3 | 0/3 | 0 + 1 partial / 3 | ×1.00 |
| jpoindexter `/tufte` | 3/3/3 | 93.4% | 5.33 | 3/3 · 2/3 | 0/3 | 0 + 1 partial / 3 | ×1.8 |

Differences (bootstrap stratified by fixture, 95% CI):

| | Sonnet | Opus |
|---|---|---|
| **This skill − no skill** | | |
| defects found | +6.1 pp (+4.5…+7.6) | +5.8 pp (+3.8…+7.6) |
| false statements per audit | −4.06 (−4.56…−3.56) | −4.83 (−5.56…−4.17) |
| cost | ×1.16 | ×1.08 |
| **This skill − jpoindexter** | | |
| defects found | +5.1 pp (+3.5…+6.6) | +5.8 pp (+4.5…+7.1) |
| false statements per audit | −4.22 (−4.78…−3.56) | −5.17 (−5.67…−4.61) |
| cost | ×0.61 | ×0.61 |

The cells hold few runs, so read the CIs as the direction on these charts, not as precise
effect sizes.

Most of the gain is in **false statements**. Without the skill, agents on F2/F3 read one series
or category as another: they trusted axis colours and a legend that covered only one pie, and
then built several wrong claims on that. The skill's reading protocol targets exactly this.

**Auto-loading:**
- The skill was invoked without being named in 24 of 24 audit runs (both models, both versions).
- It loaded on 4 of 4 differently phrased requests in English and Russian.
- It did not load on 2 of 2 near-miss requests: converting the PNG to JPEG, and an unrelated SQL
  task.

**First draft vs this version:**

| | Sonnet: defects found / false statements | Opus: defects found / false statements |
|---|---|---|
| first draft | 94.7% / 3.0 | 98.5% / 0.67 |
| this version | 98.5% / 0.33 | 99.2% / 0.17 |

The changes:
- one `python3 …` call with `--then`, because `cd` and shell variables were refused by
  permission allowlists and wasted turns;
- the axis colour no longer counts as evidence for itself;
- split evidence is reported as a self-contradiction;
- unverified marks are named by value, not by an inferred name.

**Judging.**
- The no-skill and jpoindexter audits were judged earlier. To check that the two judgings agree,
  each new batch re-judged two earlier no-skill audits as anchors. Their defect scores matched
  within ±0.5.
- On those anchors, false-statement counts came out 0–3 higher than in the earlier judging. If
  this bias exists, it works against the skill.

Per-run data: [`evals/dev-results/runs.csv`](evals/dev-results/runs.csv). Fixtures, prompts and
the harness are in `evals/`.
Regenerating the fixtures (`evals/*/fixtures/make_fixtures.py`) additionally needs SciPy; the
prompts and judge rules in `evals/` are in Russian, as the runs were.
<!-- DEV-RESULTS-END -->

**Held-out set — version 0.1.0 did not pass.** The acceptance run, on charts the author has not
seen (criteria in `ACCEPTANCE.md`):

| | Result |
|---|---|
| A3, numeric Lie Factor within ±10% | **Failed**: Sonnet 61% of runs (no skill: 0%), Opus 67%; threshold 80% |
| A1 / A2 on Opus | **Failed** at n = 1–2 per fixture: defects −0.5 pp, false statements +0.5 — within noise |
| A4, swapped axis colours caught | Passed (always caught) |
| A5, cost ×1.12–1.13 | Passed |
| A6, auto-loading 45/45 | Passed |

On the same held-out set (Sonnet), jpoindexter `/tufte` found no more defects than no skill
(+0.0 pp vs +1.6 pp for this skill), stated a correct Lie Factor in 8/18 runs (this skill:
11/18) and cost ×1.7 of this skill per audit. That set was retired after its failure analysis
was read, because the analysis exposed its contents.

The failures fell into four classes:
1. a Lie Factor worked out by hand instead of with the checker;
2. size encodings described only in words ("≈16× by area");
3. invented "approximate" values on charts whose values cannot be read;
4. labelled, deliberate choices reported as defects.

**Version 1.0.0** targets these four classes:
- every LF is quoted from the checker;
- `blobs` and `scaling` measure size encodings;
- `lf --bound` and the "cannot be computed" rule cover unreadable values;
- labelled choices and opinions outside the rubric are excluded from findings.

**Development set 2** (`evals/dev2/`) has one chart per class, with defects written down before
rendering:
- F4: circles scaled by radius next to circles scaled by area;
- F5: 3-D columns with no readable values;
- F6: a clean chart with an annotated axis break and an "illustrative data" note.

The same blind judge scored all three arms in one batch per chart. Runs per cell: 2 (0.1.0 on
Opus: 1).

| Class (chart) | Metric | no skill | 0.1.0 | 1.0.0 |
|---|---|---|---|---|
| 2: size encoding (F4) | LF correct ±10% — Sonnet / Opus | 0/2 · 0/2 | 2/2 · 1/1 | 2/2 · 2/2 |
| 1: LF from the checker (F4–F6) | LF numbers quoted from the tool | 0/5 | 7/7 (one computed on invented values) | 8/8 |
| 3: unreadable values (F5) | says "cannot be computed", no invented values — Sonnet / Opus | 0/2 · 0/2 | 2/2 · 0/1 | 2/2 · 2/2 |
| 3: unreadable values (F5) | false statements / audit — Sonnet / Opus | 0 · 1.5 | 0 · 3.0 | 0 · 0 |
| 4: clean chart (F6) | false statements / audit — Sonnet / Opus | 5.0 · 5.0 | 4.0 · 5.0 | 0 · 0 |
| all | planted defects found (F4, F5) | 100% | 100% | 100% |
| all | cost vs no skill — Sonnet / Opus | ×1.00 · ×1.00 | ≈×1.1 · ≈×1.1 | ≈×1.2 · ≈×0.9 |

Development set 2 was used to tune 1.0.0, so these numbers are optimistic too.

**Held-out set 2 — version 1.0.0.** A new set prepared independently, never seen by the skill
author: 8 charts with 54 planted defects (5 with a reference Lie Factor, one of them on purpose
"cannot be computed"), 3 clean charts carrying labelled deliberate choices (annotated axis break,
labelled log scale, "illustrative data", dated past-year data) and 2 build tasks. Defect lists and
reference values were written before rendering; the set and the candidate were checksummed and
did not change during the runs. `ACCEPTANCE.md` was verified byte-identical to its pre-rework copy.
126 runs, none invalid.

| Criterion | Sonnet (3 runs per chart) | Opus (2 runs per chart) |
|---|---|---|
| A1 defects found, skill / no skill | 99.0% / 96.1% (+2.9 pp, CI 0…+6.3) — met | 100% / 100% — met |
| A2 false statements on clean charts | 2.0 / 5.3 (−3.3, CI −4.3…−2.3) — met | 1.0 / 4.0 (−3.0, CI −4.0…−2.2) — met |
| A3 Lie Factor within ±10% (numeric references) | 9/12 = 75% (no skill 0/12) — **not met** | 6/8 = 75% (no skill 1/8) — **not met** |
| A3 incl. the "cannot be computed" reference | 12/15 = 80% (no skill 0/15) | 8/10 = 80% (no skill 3/10) |
| A4 swapped axis colours caught | 6/6 — met | 4/4 — met |
| A5 cost vs no skill | ×1.07 — met | ×1.13 — met |
| A6 auto-loading | 33/33 — met | 22/22 — met |

A3 per chart: on four of the five Lie Factor charts the skill was right in every run; on the
fifth — a truncated axis with several series — it was right in none (0/5), so the per-chart
condition of A3 is not met. There it computed a correct LF for each series, but not for the
extreme pair across series that the reference uses. **By the letter of `ACCEPTANCE.md`, 1.0.0
does not pass A3; it is released with this result stated.** Opus had 2 runs per chart, not the 3
that `ACCEPTANCE.md` asks for.

Also on this set:
- every Lie Factor the skill stated was quoted from the checker's output: 20/20 (no skill: 0/11);
- one category drawn in two colours: Sonnet 6/6 vs 3/6 without the skill; Opus 4/4 vs 4/4;
- false statements on charts with planted defects: no detectable difference (Sonnet −0.38,
  CI −0.92…+0.17; Opus +0.38, CI −0.19…+1.06);
- build tasks, rubric score: Sonnet 1.00 vs 0.925; Opus 1.00 vs 0.975.

**Judging.** A blind judge (Sonnet) scored all runs; audits were relabelled and skill names
masked. Opus re-judged the Lie Factor charts as a cross-check: 264/264 defect verdicts agreed,
36/40 Lie Factor verdicts agreed (all four disagreements in no-skill runs). Differences are
bootstrap estimates over chart × run with 95% CIs.

**Known limitations.**
- Truncated axis with several series: the LF is computed per series, not for the most extreme
  pair across series. Planned for 1.1.
- Some labelled, deliberate choices still draw comments ("illustrative data" called unfit for
  decisions, a labelled log scale called misleading): 1–2 false statements per clean chart.
- Values misread from images (segment sizes, gauge thresholds) still produce wrong statements;
  they do not affect the Lie Factor, which needs readable or measured values.
- On one clean dot plot, Opus took the guide lines for a length encoding and computed an LF where
  none applies (2 of 2 Opus runs; Sonnet: "LF not applicable").
- Synthetic charts, few runs per cell, one primary judge model.

**Script and spec inputs.** Besides the unit tests, the `figure` and `spec` paths were exercised in
8 agent runs (Sonnet) on three development inputs — a matplotlib script, a Vega-Lite spec and a
Plotly figure: the skill loaded and called the right command in 8/8 runs and every planted defect
was found. These inputs are not part of a held-out set.

## Relationship to jpoindexter/tufte-skills

[jpoindexter/tufte-skills](https://github.com/jpoindexter/tufte-skills) (MIT) is a much larger
collection (38 skills and a router) covering all of Tufte's books. We fact-checked it and kept the
verified claims we needed; see [`NOTICE`](NOTICE) for what was derived. This plugin takes a
different design: one compact skill, deterministic checks first, and a reading protocol aimed at
the errors we measured agents making.

## License

MIT — see [`LICENSE`](LICENSE). Tufte's books are © their copyright holders; this project is not
affiliated with or endorsed by Edward Tufte or Graphics Press. See [`NOTICE`](NOTICE).
