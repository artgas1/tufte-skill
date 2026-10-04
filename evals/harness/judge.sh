#!/bin/bash
# Blind judging: put chart.png, defects.md, the generator and audits renamed to audit_<random>.md
# (skill names masked) into one directory, then run:
# usage: evals/harness/judge.sh <batch-dir> <fixture-id: F1..F6> <model>
set -u
D=$1; FX=$2; M=$3
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
SET=dev
case $FX in
 F1) LF='LF: если аудит называет числом lie factor (или отношение «эффект графика / эффект данных») для D1 (обрезанная ось столбцов) и/или D2 (иконки) — запиши число в lf_D1/lf_D2 и оцени верность по правилу из defects.md (D1: 35…47 по крайним столбцам либо иное сравнение с верной арифметикой; D2: 3,5 или эквивалент). Не назван числом — null.';;
 F2|F3) LF='LF: в этой фикстуре эталонных lie factor нет — поставь lf_D1, lf_D1_ok, lf_D2, lf_D2_ok = null; но любые числовые коэффициенты искажения из аудита проверь и неверные внеси в false_claims.';;
 F4) SET=dev2; LF='для ЛЕВОЙ панели: аудит должен назвать ЧИСЛО LF; lf_ok=true, если число верно в пределах ±10% для той пары, которую аудит указал (LF = r + 1, r = большее/меньшее значение; 10→80 = 9,0). Только слова без числа LF («×64 по площади») — lf_ok=null. Неверное число — false. Для правой (честной) панели LF ≠ 1 (±10%) — ложное утверждение.';;
 F5) SET=dev2; LF='значения не читаются. lf_ok=true, если аудит прямо говорит, что LF вычислить нельзя (или даёт только корректную границу с объяснением, не придумывая значений); lf_ok=false, если называет число LF или считает его на «примерных» значениях; null, если LF вообще не обсуждается. Любые конкретные значения/проценты/отношения столбцов — ложные утверждения.';;
 F6) SET=dev2; LF='эталона нет: lf и lf_ok = null, если аудит не трактует подписанную обрезку как дефект; если трактует — внеси это в false_claims (lf_ok=false).';;
esac
P="$(cat "$ROOT/evals/$SET/judge_prompt.txt")"; P="${P//\{FX\}/$FX}"; P="${P//\{LF_RULE\}/$LF}"
cd "$D" || exit 1
claude -p "$P" --model "$M" --setting-sources project --output-format json \
  --allowedTools "Read,Glob,Bash(python3:*),Bash(ls:*)" --max-turns 30 > "judge.$M.json"
