#!/bin/bash
# Run one audit with or without the plugin, in a fresh directory that holds only the chart.
# usage: evals/harness/run_audit.sh <chart.png> <out-dir> <model> [skill|base]
# Run from the repository root. Requires the `claude` CLI.
set -u
CHART=$1; OUT=$2; MODEL=$3; ARM=${4:-skill}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
cp "$CHART" "$OUT/chart.png"
PROMPT="$(cat "$ROOT/evals/dev/audit_prompt.txt")"
EXTRA=()
if [ "$ARM" = "skill" ]; then EXTRA=(--plugin-dir "$ROOT"); fi  # macOS bash 3.2: guard the empty array below
cd "$OUT" || exit 1
claude -p "$PROMPT" --model "$MODEL" --setting-sources project ${EXTRA[@]+"${EXTRA[@]}"} \
  --output-format stream-json --verbose \
  --allowedTools "Read,Write,Skill,Glob,Bash(ls:*),Bash(python3:*)" --max-turns 20 \
  > "$OUT/log.jsonl" 2> "$OUT/log.err"
# audit.md is written by the agent; cost is in the last line of log.jsonl ("total_cost_usd")
