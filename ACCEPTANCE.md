# Acceptance criteria

Written 2026-10-04 05:45 (UTC+3), **before** the first evaluation run of this skill. The criteria
are judged on a **held-out** fixture set that the skill author has not seen. The development
fixtures (`dev`, three charts) are used for debugging only and do not count towards acceptance.

## Setup that every number refers to

- **Task.** The same audit prompt for every run: a chart image is in the working folder and the
  agent is asked to list design and data-honesty problems, with what/why/fix for each.
- **Arms.**
  - `base` — the agent with its normal environment (including any built-in palette/form skill),
    no Tufte skill.
  - `skill` — the same environment plus this plugin. The prompt does **not** name the skill;
    loading it is the agent's own decision.
- **Models.** Sonnet and Opus, at least 3 repetitions per fixture × arm × model.
- **Scoring.** A blind judge (the audits are relabelled with random codes, skill names masked)
  marks each planted defect `caught` (1), `partial` (0.5) or `missed` (0) against a defect list
  written before the charts were generated, and lists every false statement about the chart or
  its data. Cost is the `total_cost_usd` reported by the CLI for the audit run.

## Criteria (all must hold, per model)

| # | Criterion | Pass condition |
|---|---|---|
| A1 | Defects found | Mean share of planted defects caught, `skill` ≥ `base` (point estimate). The 95% bootstrap CI of the difference is reported alongside. |
| A2 | False positives on clean charts | On fixtures with no planted defects: mean false statements per audit, `skill` ≤ `base`. |
| A3 | Lie Factor is numerically correct | On every fixture whose defect list gives a Lie Factor: the audit states a number within ±10% of the true value in ≥ 80% of `skill` runs. |
| A4 | Swapped axis colours are caught | On fixtures with a dual axis whose colours are swapped: `caught` in ≥ 2/3 of `skill` runs. |
| A5 | Cost | Mean cost per audit, `skill` ≤ 1.3 × `base`. |
| A6 | Auto-loading | On audit prompts that do not name the skill, the skill is invoked in ≥ 2/3 of `skill` runs (counted from the run transcript: a `Skill` call for it, or a read of its `SKILL.md`). |

A criterion that cannot be measured on the held-out set (for example, no fixture contains the
relevant defect) is reported as **not measured**, never as passed.

## What does not count

- Development results (`evals/dev-results/`) — the skill was tuned on those fixtures.
- Scores from a judge that saw which arm produced an audit.
