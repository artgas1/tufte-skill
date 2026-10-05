"""Write the `claude plugin eval` suite (evals/cases/<id>/) for the dev fixtures F1–F9.

Re-run after editing the defect lists or rubrics below: python3 evals/cases/make_cases.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
with open(os.path.join(ROOT, "evals/dev/audit_prompt.txt"), encoding="utf-8") as _f:
    PROMPT = _f.read().strip()

SET = {"F1": "dev", "F2": "dev", "F3": "dev", "F4": "dev2", "F5": "dev2", "F6": "dev2",
       "F7": "dev3", "F8": "dev3", "F9": "dev3", "F10": "dev4", "F11": "dev4", "F12": "dev4",
       "F13": "dev5", "F14": "dev5", "F15": "dev5", "F16": "dev5",
       "F17": "dev6", "F18": "dev6", "F19": "dev6", "F20": "dev7", "F21": "dev7"}

DEFECTS = {
    "F1": (8, ["value axis of the bars starts at 400 (truncated, no break mark)",
               "icons scaled in both width and height, so their area grows with the square of the value",
               "gradient fill on the bars", "decorative noise texture in the background",
               "year 2022 silently missing on an evenly spaced axis", "shouting headline «ВЗРЫВНОЙ РОСТ!»",
               "legend for a single series", "dark dense grid drawn over the bars",
               "the two panels order the years in opposite directions", "no units or no source"]),
    "F2": (8, ["pseudo-3-D tilt that enlarges front slices", "two pies used to compare years",
               "the same category has different colours in the two pies", "too many / tiny slices (9 slices)",
               "the 2025 labels sum to 107.7%, not 100%", "an exploded slice", "legend instead of direct labels",
               "spurious precision (three decimals)", "slices not sorted by size", "no source / vague title",
               "drop shadow under the pies"]),
    "F3": (8, ["two y-axes with arbitrary scales and a false crossing", "uneven time intervals drawn evenly",
               "nominal money over 24 years without deflation", "spline smoothing between sparse points",
               "tall, narrow aspect ratio exaggerating slopes", "heavy markers and thick lines",
               "area filled to an arbitrary level (1500)",
               "axis colours swapped: each axis is coloured like the OTHER line",
               "causal annotation «Рост цен вызвал отток клиентов!» without evidence",
               "rotated year labels or dense dotted grid", "no source or no unit on the right axis"]),
    "F4": (2, ["left panel: circle radius ∝ value, so area grows with value²",
               "the two panels use different size rules (radius vs area)"]),
    "F5": (3, ["3-D / perspective columns for one-dimensional data", "values cannot be read: no axis numbers, no labels",
               "no units or no source", "meaningless per-bar colours"]),
    "F7": (5, ["value axis starts at 2.0 under bars (truncated)", "headline «Реклама догнала партнёров» contradicted by Q4 (2.7 < 3.0)",
               "no unit (%)", "no source", "dark grid drawn over the bars", "boxed legend instead of direct labels"]),
    "F10": (1, ["circle radius ∝ value, so area grows with value²", "no key for how size maps to value",
                "circles in unrelated colours that carry no data"]),
    "F12": (1, ["value axis starts at 60 under bars (truncated)", "no source"]),
    "F8": (3, ["value axis starts at 50 under bars (truncated)", "three decimals on thousands of orders («62.000»)",
               "legend order is the reverse of the bar order", "no source"]),
}

LF_REGEX = {
    # reference Lie Factor values, matched near an "LF"/"Lie Factor" mention in the final answer
    "F1": r"(?:LF|[Ll]ie [Ff]actor)[^\n]{0,40}?(?:3[5-9]|4[0-7])(?:[.,]\d+)?\b",
    "F4": r"(?:LF|[Ll]ie [Ff]actor)[^\n]{0,40}?(?:8[.,][1-9]|9(?:[.,]\d+)?|9[.,]9)\b",
    "F7": r"(?:LF|[Ll]ie [Ff]actor)[^\n]{0,40}?(?:8[.,][1-9]\d*|9(?:[.,]\d+)?)\b",
    "F8": r"(?:LF|[Ll]ie [Ff]actor)[^\n]{0,40}?(?:1[23][.,]\d+|13|14(?:[.,][0-8]\d*)?)\b",
    "F10": r"(?:LF|[Ll]ie [Ff]actor)[^\n]{0,40}?(?:8[.,][1-9]\d*|9(?:[.,]\d+)?)\b",
    "F12": r"(?:LF|[Ll]ie [Ff]actor)[^\n]{0,40}?(?:1[67][.,]\d+|1[89](?:[.,]\d+)?)\b",
    "F5": r"(?:не (?:может быть )?вычисл|нельзя (?:вы)?числ|невозможно (?:вы|по)счит|cannot be computed|not computable)",
}

ONE_LF = {
    "F10": "The audit must state exactly ONE Lie Factor for the circles, about 9 (8.1–9.9). PASS if it does. FAIL if "
           "it states two or more different LF numbers for the circles (for example one from fitting all circles and "
           "another from two diameters), or its headline LF for the circles is outside 8.1–9.9.",
    "F11": "The chart shows two LINES on a value axis that starts at 60, and the chart says so. Lines encode by "
           "position, so the Lie Factor does not apply. PASS if the audit states no Lie Factor number and no "
           "'exaggerated N times' for this chart (saying 'LF not applicable' is a pass). FAIL if it states any LF "
           "number or a distortion multiple, or calls the labelled axis start a defect.",
}

CONTROL = {
    # Controls target the integrity false positive; comments on style or documentation do not decide them.
    "F6": "The chart's value axis starts at 400 and the chart SAYS so (a visible note and a break mark). "
          "PASS if the audit does not count this labelled truncation as a defect: describing it as an "
          "acknowledged / disclosed choice, even with its Lie Factor for reference, is a pass. FAIL if the audit "
          "lists the truncation among the defects or problems to fix, or says the chart misrepresents the data.",
    "F9": "The chart's bars start at zero on a linear axis and the headline is true. PASS if the audit does not "
          "claim that the chart misrepresents the data (no truncation, no Lie Factor other than 1, no false "
          "headline). Remarks on documentation (for example that an export dated 01.10.2025 cannot contain Q4 — "
          "that is correct) or on styling do not decide the verdict. FAIL if it claims a distortion of the data.",
    "F13": "Two LINES on a value axis that starts at 3.4; the chart states it. PASS if the audit makes no "
           "quantitative claim that the chart exaggerates or stretches change — no Lie Factor, no 'N times', no "
           "'looks several times larger' — and does not call the stated axis start a defect. FAIL otherwise.",
    "F14": "A DUMBBELL chart (two dots per region) on a value axis that starts at 60; the chart states it. PASS if "
           "the audit makes no quantitative claim that the chart exaggerates change (no Lie Factor, no 'N times', no "
           "'looks several times larger') and does not call the stated axis start a defect. Mentioning that the "
           "subtitle bullets are black rather than coloured is correct and does not decide the verdict. FAIL "
           "otherwise.",
    "F15": "Bars from zero; the footer says 'Источник: учебный набор данных. Данные условные, для иллюстрации'. "
           "PASS if the audit does not treat the 'illustrative data' note as a defect, a contradiction with the "
           "source, or a reason the chart is unfit. FAIL if it does, or if it claims the data are distorted.",
    "F16": "Annotation and source text are #555555 on white (7.46:1) and tick labels #666666 (5.74:1); both pass "
           "WCAG AA. PASS if the audit does not call any of this text low-contrast, too light or hard to read. "
           "FAIL if it does, or if it claims the data are distorted.",
    "F17": "Two LINES on a value axis that starts at 70; nothing marks it (no break symbol, no note; the tick reads "
           "70.0). PASS if the audit names that the axis start is not marked (a tick label is not a mark) AND makes no "
           "quantitative distortion claim for these lines (no Lie Factor, no 'N times', no 'looks like a doubling'). "
           "FAIL if it accepts the start as a labelled / open choice, or makes such a claim.",
    "F18": "A DOT plot on an x axis from 40, with a drawn axis-break symbol and the note 'Шкала начинается с 40%'. "
           "PASS if the audit does not call the axis start a defect and makes no quantitative distortion claim (no "
           "Lie Factor, no 'N times'). FAIL otherwise.",
    "F19": "3-D bars of two series, dark blue #1b3a6b and light orange #fdae61 (contrast about 6:1 between them). "
           "PASS if the audit names the 3-D as a defect and makes no claim about colours separating badly (faces "
           "merging with the background, series hard to tell apart, grayscale) unless it quotes a contrast ratio "
           "from a tool. FAIL if it makes such a claim without a ratio, or misses the 3-D.",
    "F20": "Two lines (#1b5e9e, #b2182b; contrast between them 1.03:1, CVD worst ΔE 57) and a footnote in #555555 "
           "(7.46:1). PASS if every statement about colours separating (pale, low-contrast, merging, grayscale, "
           "colour-blind readers) quotes a number and the number fits: the lines ARE close in grayscale (about 1:1), "
           "they are NOT confused for colour-blind readers, the footnote is NOT low-contrast. FAIL if any such "
           "statement has no number, or contradicts these values.",
    "F21": "Gradient bars in #1b3a6b, #fdae61, #d62728, #2ca02c with a legend only; footnote #999999 (2.85:1). PASS if "
           "the audit names the gradient as decoration, and every statement about colours separating quotes a "
           "number that fits: red #d62728 vs green #2ca02c ARE confusable (deutan ΔE about 7, grayscale 1.48:1); "
           "the footnote IS below AA (2.85:1). FAIL if a colour statement has no number or contradicts these values.",
}


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


for fx, s in SET.items():
    d = os.path.join(ROOT, "evals/cases", fx)
    write(os.path.join(d, "prompt.md"),
          "---\n"
          f"description: Audit of dev fixture {fx} (evals/{s}/fixtures/defects.md lists what is planted)\n"
          f"tags: [audit, {s}]\n"
          "runs: 3\n"
          "max_turns: 25\n"
          "timeout_seconds: 600\n"
          "allowed_tools: [Read, Write, Glob, Skill, Bash]\n"
          "---\n\n" + PROMPT + "\n")
    write(os.path.join(d, "case.yaml"),
          'schema_version: "1.1"\n'
          f"name: {fx}\n"
          "context:\n"
          "  scaffold_script: setup.sh\n")
    write(os.path.join(d, "setup.sh"),
          "#!/bin/bash\n"
          "# Copy the fixture chart into the empty workspace (runs only with --scaffold).\n"
          "set -e\n"
          f'cp "$(dirname "$0")/../../{s}/fixtures/{fx}/chart.png" chart.png\n')
    os.chmod(os.path.join(d, "setup.sh"), 0o755)
    g = os.path.join(d, "graders")
    write(os.path.join(g, "skill-fired.md"),
          "---\ntype: tool_used\ntool: Skill\ninput_match: '\"skill\"\\s*:\\s*\"(?:[\\w-]+:)?tufte\"'\n---\n")
    write(os.path.join(g, "tool-ran.md"),
          "---\ntype: tool_used\ntool: Bash\ninput_match: 'tufte_check\\.py'\narm: with-only\n---\n")
    if fx in DEFECTS:
        need, items = DEFECTS[fx]
        lst = "\n".join(f"- {x}" for x in items)
        write(os.path.join(g, "defects.md"),
              "---\ntype: llm\nfocus: last_message\n---\n\n"
              f"The chart has these planted defects:\n{lst}\n\n"
              f"PASS if the audit names at least {need} of them (any wording; a defect counts when the audit "
              "identifies the same problem). FAIL if it names fewer.\n")
    if fx in LF_REGEX:
        write(os.path.join(g, "lie-factor.md"),
              "---\ntype: regex\ntarget: last_message\n"
              f"pattern: '{LF_REGEX[fx]}'\n---\n")
    if fx in ONE_LF:
        write(os.path.join(g, "one-lie-factor.md"),
              "---\ntype: llm\nfocus: last_message\n---\n\n" + ONE_LF[fx] + "\n")
    if fx in CONTROL:
        write(os.path.join(g, "no-false-defects.md"),
              "---\ntype: llm\nfocus: last_message\n---\n\n" + CONTROL[fx] + "\n")
print("wrote", len(SET), "cases")
