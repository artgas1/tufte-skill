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
| `lfmax --mark bar --series NAME=v1,v2,… --series … --baseline X` | Several series on one axis: the chart-wide LF — the strongest distortion over every pair of marks, across series too (for bars from a baseline B: the smallest bar against any larger one, v_min/(v_min−B)) — plus each series' own LF. It echoes how many values it received per series and warns when series lengths differ. `--mark line\|point` (position encodings) answers "not applicable" and prints no number |
| `lf --bound [--baseline B --axis-max T \| --encoding radius]` | When values are unreadable: LF ≥ T/(T−B) for bars from a non-zero baseline (for bars LF = v/(v−B), v the smaller value); LF ≥ 2 when linear size ∝ value; otherwise "cannot be computed" |
| `blobs chart.png` | Measures coloured shapes (circles, icons, bubbles) in pixels |
| `scaling --values … --sizes …` | Fits the rule that maps values to measured sizes (radius ∝ value vs area ∝ value), robust to anti-aliasing on small shapes, and gives the LF for smallest→largest |
| `pick chart.png --box X0 Y0 X1 Y1 --element text\|line\|fill` | The colour of one element in a pixel box — its solid core, not its anti-aliased edges, and not other ink in the box — with its contrast against the box background, or "not determined" |
| `colours chart.png [--box …]` | The solid colours drawn in an image (edge mixtures removed); does not say which element has which |
| `cvd A B` | Two colours as protan, deutan and tritan readers see them (Machado 2009, full severity): CIE76 ΔE and "likely confused" below 10 |
| `contrast FG BG [--size large]` | WCAG 2.x contrast ratio of a text colour on its background with AA/AAA verdicts; the skill makes no contrast claim without it |
| `time LABEL...` | Time labels drawn evenly but uneven in time; missing periods |
| `image chart.png` | What pixels can tell: aspect ratio, colour-coded axes, colour sets of repeated panels. Says plainly that integrity cannot be computed from pixels |
| `figure plot.py` | Runs a matplotlib script (show/close disabled) and checks bar baselines (with Lie Factor per series and chart-wide; downgraded to a note when the chart's text labels the truncation), dual-axis colour swaps, one category in two colours, time spacing, pies (count, explode, labels summing to 100), dark or on-top grid, 3-D, smoothing, fills to arbitrary levels, icons scaled in both dimensions, shouting or causal titles, false precision, aspect and banking |
| `spec chart.json` | The same checks for Vega-Lite specs and Plotly figure JSON where the spec allows (incl. Plotly's default `sizemode='diameter'`, and the chart-wide LF for Plotly bars on a truncated axis; Vega-Lite bars get the baseline check without an LF) |

`figure` **executes** the script you give it. Run it on plotting code you trust.

Several commands run in one process with `--then`
(`image chart.png --then lf --data 410 520 --baseline 400`).

Tests: `python3 -m pytest skills/tufte/scripts/test_tufte_check.py` (79 tests) — every check has a
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

To pin a release, add `"ref": "tufte-skill--v1.4.1"` (or another release tag) next to `"repo"`. Settings alone register
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

**`claude plugin eval` suite.** `evals/cases/` holds development charts F1–F9 as a
[`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals) suite: one case per chart with
the same audit prompt, a scaffold that copies the chart into the workspace, an LLM grader for the
planted defects, a regex grader for the reference Lie Factor where there is one, a control grader
on the two clean charts, an "one LF" grader on F10 and F11, and `skill-fired` / `tool-ran` as
plugin-fired indicators. The eval's sandbox cannot read a Python installed under your home directory
(pyenv, uv, conda) or a symlink that points outside the plugin, so create a real one inside the
plugin directory and put it first on `PATH`:
```
/usr/bin/python3 -m venv .venv-eval && .venv-eval/bin/pip install numpy matplotlib
PATH="$PWD/.venv-eval/bin:$PATH" claude plugin eval . --scaffold --allow-tools Write 'Bash(python3:*)' --judge-model sonnet
```
It reports a coarse pass/fail per grader with a no-plugin baseline arm. The per-defect numbers in
this README (each planted defect caught / partial / missed, false statements counted one by one,
blind cross-judging) come from the harness in `evals/harness/`, and acceptance uses held-out
charts; `plugin eval` replaces neither. `python3 evals/cases/make_cases.py` regenerates the cases.

First pass (1 run per arm, Sonnet agent, Sonnet judge): with the skill all 9 cases scored 1.0; without
it the mean was 0.61 — the Lie Factor grader failed without the skill on all five charts that have a
reference LF, the defect graders passed in both arms, and the F6 control (a disclosed truncation)
failed without the skill. The two control rubrics were retargeted after a first attempt in which both
arms failed: the F9 chart carries a real, unplanned inconsistency (an export dated 01.10.2025 showing
Q4), and the rubric counted minor remarks as false findings. One run per arm is a smoke test, not a
measurement.
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
- Truncated axis with several series (1.0): the LF was computed per series, not for the most
  extreme pair across series. Addressed in 1.1 by `lfmax` and the headline rule (see
  [Version 1.1](#version-11)); held-out acceptance of 1.1 is reported there.
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

## Version 1.1

**What changed.** A reader of a grouped or multi-series bar chart compares bars across series, so
the distortion that matters is the most extreme pair on the whole chart. For bars from a baseline
B that is the smallest bar against any larger one, LF = v_min/(v_min − B). 1.1 adds `lfmax`, which
computes it over every pair of marks (and per series as detail), makes `figure` and Plotly `spec`
print it as `lie-factor-max`, and tells the audit to lead with this chart LF. All 1.0 rules stay:
every LF from the tool, "cannot be computed" for unreadable values, disclosed choices are not
defects.

**Development check** (`evals/dev3/`: F7 three channels on an axis cut at 2.0, chart LF 9.0; F8 two
years on an axis cut at 50, chart LF 13.5; F9 a clean control; defects written before rendering;
2 runs per cell):

| | Headline LF = chart maximum |
|---|---|
| 1.1 | 6/6 (Sonnet 4/4, Opus 2/2), each from `lfmax` |
| 1.0 | 2/6 — the maximum was among the LFs it listed in 6/6, but 4 audits led with a list or a range |
| no skill | no LF number in 4/4 |

On these two charts 1.0's own pairs happened to include the smallest bar, so they do not reproduce
the held-out failure of 1.0; they show the headline rule working, not that the failure is fixed.
Regression on F1–F6 (Sonnet, 1 run each): LF 41 and 9.0 correct, "cannot be computed" on F5, the
labelled truncation on F6 kept as a disclosed choice, the axis-colour contradiction on F3 flagged.

**Held-out acceptance of 1.1: not passed.** The chart-wide LF was right in 80% of Sonnet runs and
93% of Opus runs, and on multi-series charts the share of correct LFs rose from 5/15 (1.0) to 12/15.
Auto-loading 60/60, cost ×1.13–1.20 of no skill. Three failure classes, reported without fixture
details: (1) for radius- or area-scaled shapes Sonnet stated two LFs — one from `scaling`, one from
`lf --measured` with sizes read by eye — and led with the wrong one, where 1.0 had stated one correct
number; (2) the new chart-wide rule spilled over to lines and dots on a labelled truncated axis, where
an LF does not apply and 1.0 had answered correctly; (3) a series minimum in the middle of a series
was missed because not every value was passed to `lfmax`. 1.2 addresses these.

## Version 1.2

**What changed.**
- **One LF per encoding.** `blobs` now points to `scaling` with all shapes; `scaling` says its LF is
  the one number for those shapes; in a call that chains `scaling` with `lf` for a size encoding, the
  `lf` result is printed as a cross-check without a "Quote this result" line. The audit procedure
  names the precedence (`scaling` over `lf --measured` over an assumed `--encoding radius`) and forbids
  sizes estimated by eye.
- **No LF for position encodings.** `lfmax` requires `--mark`; `--mark line|point|dot|scatter|slope`
  (also accepted by `lf`) returns "LF not applicable (position encoding)" and no number. `figure` and
  `spec` compute the chart-wide LF for bars only, as before (now covered by a test with lines).
- **Every value.** `lfmax` echoes how many values it received per series and warns when series
  lengths differ; the procedure asks for every value of every series in drawing order.

**Tests.** 56, eight of them new for 1.2. Run against the 1.1 script, five of the new tests fail (one
LF per size encoding in both chain orders, the position-mark guard in the API and the CLI, the
series-length warning); the other three pin behaviour 1.1 already had (a series minimum in the middle
found when all values are passed, no LF from `figure` for lines, a bar LF kept next to `scaling`).

**Development check** (`evals/dev4/`: F10 circles with radius ∝ value, reference LF 9.0, smallest
circle 13 px; F11 two lines on an axis starting at 60 with the start stated, reference "not
applicable"; F12 grouped bars from 60 with a series minimum in the middle, reference chart LF 18.1;
defects written before rendering):

| Headline LF correct (one number within ±10%, or none where none applies) | F10 | F11 | F12 |
|---|---|---|---|
| 1.2, Sonnet / Opus (2 runs each) | 2/2 / 2/2 | 2/2 / 2/2 | 2/2 / 2/2 |
| 1.1, Sonnet / Opus | 2/2 / — | 2/2 / 1/1 | 2/2 / 1/1 |
| 1.0, Sonnet | 2/2 | 2/2 | 0/2 (a range "5–18×" or a list as the headline) |
| no skill, Sonnet (1 run) | no LF | no LF (correct) | no LF |

These charts **did not reproduce** the held-out failures of 1.1: 1.1 itself was right on all three.
The 1.2 changes are guards proven by the unit tests above, not by these runs; whether they fix the
held-out classes is for the held-out acceptance of 1.2.

**`claude plugin eval` on 1.2** (with-skill arm only, 1 run per case, Sonnet): the first pass ran the
skill's script with a Python under the home directory, which the eval sandbox blocks — the agent
reported "the script did not run" and stated no LF, so the six LF graders failed for an environmental
reason, not a skill one. With a virtualenv inside the plugin directory (instructions above), F10
passed all five graders (one LF of 9.00). The remaining cases were not re-run within the development
budget. Pass/fail of the first pass: defects 9/9, F11 "no LF on lines" passed, F9 control passed, F6
control failed (the audit called the disclosed truncation its "main problem").

**Held-out acceptance of 1.2: passed on Opus; on Sonnet three kinds of false statements on clean
controls remained.** Passed on both models: LF for truncated lengths 100% (1.0: 42%, 1.1: 88%), radius
and area encodings 100%, "cannot be computed" 3/3, swapped axis colours 3/3, cost ×1.09–1.16 of no skill,
auto-loading 66/66. Sonnet's false statements on clean controls: (1) on position encodings with a
labelled truncated axis the script said "not applicable", yet the audit described a distortion in words
("the 3.4–4.8 axis stretches the changes about 2.9 times"); (2) an "illustrative data" note was called a
contradiction with the source; (3) #555 text on white was judged insufficient by eye (it is 7.46:1). 1.3
addresses these.

## Version 1.3

**What changed.**
- **No distortion estimate for position encodings, in numbers or in words.** The procedure forbids any
  quantitative claim of exaggeration for lines, dots, scatter, slope and dumbbell charts; a labelled axis
  start on them is not a finding, an unlabelled one is a single "axis start not marked" note. `dumbbell`
  and `range` join the position marks of `lf`/`lfmax`, and the "not applicable" message says outright:
  no number, no "N times".
- **Disclosures.** "Illustrative / example data" next to a source line is documentation, not a
  contradiction with the source — now stated with an example.
- **`contrast FG BG`.** WCAG 2.x ratio with AA/AAA verdicts for normal and large text; the procedure
  allows a contrast claim only from its output and none when the colours are known only from an image.

**Tests.** 63, seven of them new for 1.3; all seven fail against the 1.2 script (contrast values
#555/#fff 7.46 → AA pass, #aaa/#fff 2.32 → fail, the 4.5 threshold at #767676/#777777, input formats,
the CLI, and three position marks).

**Development check** (`evals/dev5/`: four clean controls written before rendering — F13 two lines on an
axis from 3.4, F14 a dumbbell on an axis from 60, both with the start stated; F15 bars with «Данные
условные, для иллюстрации»; F16 grey #555/#666 text):

| False statements of the three classes | runs | position claims (F13, F14) | "illustrative" as a defect (F15) | contrast misjudged (F16 and others) |
|---|---|---|---|---|
| 1.3, Sonnet | 12 | 0 | 0 | 0 |
| 1.3, Opus | 4 | 0 | 0 | 0 |
| 1.2, Sonnet | 8 | 1 («63→70 выглядит как рост в несколько раз») | 0 | 1 (#555 footnote «плохо читается») |
| 1.0, Sonnet | 4 | 0 | 0 | 0 |

Small numbers: 1.2 produced two such statements in eight runs here, so "0 of 12" for 1.3 is consistent
with the fix but does not prove it. The "illustrative" class did not reproduce in this set. One run of
1.2 called the orange label on F13 low-contrast; that is correct (#d95f02 on white is 3.76:1) and is
not counted.

**`claude plugin eval` regression on 1.3** (with-skill arm, 1 run per case, Sonnet; F1, F4, F5, F7,
F11, F12): all graders passed — LF 41, 9.00 (radius), "cannot be computed", 9.00 (several series), no LF
on lines, 18.14 (minimum in the middle). F4 first failed because the virtualenv was a symlink to a
directory outside the plugin, which the sandbox blocks; with a real virtualenv inside the plugin it
passed.

**Held-out acceptance of 1.3: not passed.** Against 1.0 on Sonnet it lowered false statements on clean
controls from 1.22 to 0.39 per chart, "N times" on position encodings from 11/15 to 1/15, and kept the LF
at 100% (1.0: 78%); cost ×1.07–1.11, auto-loading 66/66. Failure classes, without fixture details:
(1) over-correction on Opus — lines on an axis cut without any mark were accepted 3 times of 3 because a
tick read «70.0» ("it is visible from the label, so it is an open choice"); (2) Sonnet judged colours by
eye ("the dark side faces almost merge with the background"); (3) one position chart described as
"looks like a doubling".

## Version 1.4

**What changed.**
- **A tick is not a mark.** An axis start above zero counts as marked only with a drawn break symbol, a
  note or subtitle («шкала от 70», "axis starts at 70") or an annotation; a tick label showing the start
  value does not count. Unmarked → one finding, "axis start not marked" — with the LF on bars, without
  any number on lines and points. `figure` now reports `axis-start` / `axis-start-unmarked` for lines and
  points (break symbols drawn in axes coordinates are detected; a break also labels a bar truncation),
  and Plotly `spec` does the same from the title and annotations. The truncation-note pattern now also
  reads «шкала от N», «шкала начинается», «не от нуля».
- **No colour judgement by eye.** Any statement about how well colours separate — text, shapes, shaded
  faces, series, grayscale print — needs a `contrast` ratio quoted in the finding. New `colours`
  subcommand reads the colours actually drawn in a PNG (optionally in a pixel box) so the ratio can be
  computed without the source.
- **Forbidden phrases** for position encodings are listed in both languages ("looks like a doubling",
  «рост кажется в разы больше», …).

**Tests.** 73, ten of them new for 1.4 (as parametrised cases); against the 1.3 script nine fail — the
unmarked/marked truncation on lines (tick, note, subtitle, break symbol), the dot plot on x, a break
mark labelling bars, Plotly line truncation, the note pattern and `colours` — and one, lines from zero,
passes on both by design.

**Development check** (`evals/dev6/`, written before rendering: F17 lines on an axis from 70 with no
mark and ticks «70.0»; F18 a dot plot from 40 with a break symbol and a note; F19 3-D bars in two
colours):

| | runs (Sonnet / Opus) | F17 unmarked start named | position claims, F17+F18 | colour statements without a ratio |
|---|---|---|---|---|
| 1.4 | 9 / 9 | 3/3 / 3/3 | 0 / 0 | 1 / 0 |
| 1.3 | 6 / 6 | 0/2 / 0/2 | 0 / 0 | 2 / 0 |
| 1.0 | 3 / — | 1/1 | 0 | 1 |

The one 1.4 statement without a ratio was "black text on white has enough contrast" — true, but not
backed. Every other colour finding of 1.4 quoted a ratio from `contrast` or `colours` (for example the
two line colours of F17 at 1.03:1 — an accidental real issue of that chart — or label text on shaded
faces at 1.51:1). 1.3 reproduced class (1) here on both models; class (3) did not reproduce in this set.
F18 drew no false truncation finding from any version. Plugin-eval regression (F7, F17): all graders
passed.

**Held-out acceptance of 1.4: one criterion short.** On both models: defects found, LF 16/16, "N times"
on position encodings 0/19, cost; on Sonnet 0.57 fewer false statements than 1.0; auto-loading 96/96. The
miss: colour statements on Sonnet that carry a number and are right — 0.895 against a threshold of 0.90.
Classes, without fixture details: (1) `colours` on an image took a neighbouring line instead of the text
(3.76 instead of 4.87) and an anti-aliased edge pixel (6.04 instead of the true value); (2) colour
statements without a number — "the base of the gradient merges", "the footnote is pale", "small and
grey", "A and D are easy to confuse in grey", and on both models "the lines will merge for readers with
impaired colour vision"; (3) on Opus, a typography nit ("18% without a space") outside the rubric.

## Version 1.4.1

**What changed.**
- **`pick`** returns the colour of one element in a pixel box — text, line or fill — from its solid core,
  ignores other ink in the box, and answers "not determined" (with no number) when the box holds no such
  element, two of them, or no uniform core.
- **`colours`** lists only solid colours: exact colours that repeat, with anti-aliased edge mixtures
  removed by a spatial test (a mixture hugs a farther colour of the same edge); a light tint fill is kept.
- **`cvd A B`** simulates protan, deutan and tritan vision (Machado, Oliveira & Fernandes 2009, full
  severity, linear sRGB) and reports the CIE76 ΔE between the two simulated colours.
- **SKILL.md**: any statement about paleness, merging, grayscale or colour-vision deficiency needs a
  number from `contrast`, `pick` or `cvd`; the unnumbered phrases above are listed as forbidden. An
  element's colour comes from the source or `pick`, never from the `colours` list. Typography conventions
  are outside the rubric.

**Tests.** 79, six of them new for 1.4.1; five fail against the 1.4 script (edge mixtures in `colours`,
`pick` on a label next to a line, "not determined", a fill core, CVD), one — a light tint kept — passes on
both by design.

**Development check** (`evals/dev7/`, written before rendering: F20 two lines of equal lightness —
1.03:1 between them, distinct for colour-blind readers, ΔE 57 — and a #555555 footnote; F21 gradient
bars with red and green categories — deutan ΔE 7.3 — and a #999999 footnote at 2.85:1). Every
statement about colours separating was judged by hand: numbered with a value within 5% of the
reference and a conclusion that follows from it, or not.

| Colour statements numbered and right | Sonnet (5 runs per chart) | Opus (2 runs per chart) |
|---|---|---|
| 1.4.1 | 7/10 = 0.70 | 6/8 = 0.75 |
| 1.4 | 12/22 = 0.55 | 8/9 = 0.89 |

1.4's misses were mostly unnumbered claims about colour-blind readers ("the lines will merge" — false
here, ΔE 57) and "the gradient base merges"; 1.4.1 made far fewer colour statements and its misses were
unnumbered *positive* claims ("the colours are distinct", "contrasting colours") and grayscale asides
in "why it matters" lines. Opus's drop is two such asides in eight statements — small numbers. After
these runs the rule was extended to positive claims and "why it matters" lines; two further Sonnet runs
on F20 made only numbered statements (2/2), but one of them reused the example ratio printed in the
skill after `pick` could not separate the footnote, so that example was removed. Those two runs are a
spot check, not a measurement; the extended rule is not measured beyond them.

## Changelog

**1.4.1**
- `pick`: the colour of one element (text, line, fill) from its solid core, or "not determined".
- `colours`: solid colours only, anti-aliased edge mixtures removed.
- `cvd`: protan/deutan/tritan simulation with ΔE.
- Colour statements (pale, merging, grayscale, colour-vision deficiency) only with a number; typography
  conventions are outside the rubric.
- `evals/dev7/` and plugin-eval cases F20–F21.

**1.4.0**
- A tick label is not a truncation mark: unmarked starts are a finding (with LF on bars, without any
  number on lines and points); `figure`/Plotly `spec` report `axis-start` / `axis-start-unmarked`; a drawn
  break symbol labels a truncation.
- No colour judgement by eye: any statement about colours separating needs a `contrast` ratio; new
  `colours` reads the colours drawn in a PNG or a pixel box.
- Forbidden distortion phrases for position encodings listed in English and Russian.
- `evals/dev6/` and plugin-eval cases F17–F19.

**1.3.0**
- No quantitative distortion claim, in numbers or words, for position encodings (lines, dots, scatter,
  slope, dumbbell); `dumbbell` and `range` added to the position marks.
- "Illustrative data" next to a source is documentation, not a contradiction — rule with an example.
- `contrast FG BG`: WCAG 2.x ratio with AA/AAA verdicts; contrast claims only from it.
- `evals/dev5/` (four clean controls) and plugin-eval cases F13–F16.

**1.2.0**
- One Lie Factor per encoding: `scaling` is the number to quote for shapes; `lf` chained with
  `scaling` prints a cross-check; sizes only from `blobs`.
- `lfmax --mark` (required) and `lf --mark`: lines, points, dots, scatter and slope charts get "LF not
  applicable (position encoding)".
- `lfmax` echoes values per series and warns when series lengths differ; the procedure asks for every
  value of every series.
- `evals/dev4/` and plugin-eval cases F10–F12.

**1.1.0**
- `lfmax`: chart-wide Lie Factor over all marks of several series, with per-series detail.
- `figure` and Plotly `spec`: `lie-factor-max` for bars of several series on a truncated axis.
- Audit procedure: with several series on one truncated axis, the headline LF is the chart LF.
- `evals/cases/`: the development charts as a `claude plugin eval` suite; development set 3.

**1.0.0** — first release.

## Relationship to jpoindexter/tufte-skills

[jpoindexter/tufte-skills](https://github.com/jpoindexter/tufte-skills) (MIT) is a much larger
collection (38 skills and a router) covering all of Tufte's books. We fact-checked it and kept the
verified claims we needed; see [`NOTICE`](NOTICE) for what was derived. This plugin takes a
different design: one compact skill, deterministic checks first, and a reading protocol aimed at
the errors we measured agents making.

## License

MIT — see [`LICENSE`](LICENSE). Tufte's books are © their copyright holders; this project is not
affiliated with or endorsed by Edward Tufte or Graphics Press. See [`NOTICE`](NOTICE).
