#!/bin/sh
# One command:  sh check.sh        (a few minutes; needs cc and python3, standard library only)
# With cadical and drat-trim on PATH it also re-solves R_4(C3;3) <= 9 and checks the DRAT proof (seconds).
# Re-solving all 18,129 leaves of R_5(C3;3) <= 11 takes about 49 CPU-hours: see README.md.
set -eu
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
fail() { echo "CHECK FAILED: $*"; exit 1; }
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
sha() { "$PY" -c 'import hashlib,sys; h=hashlib.sha256(); f=open(sys.argv[1],"rb"); [h.update(c) for c in iter(lambda: f.read(1<<20), b"")]; print(h.hexdigest())' "$1"; }
body() { sed -n '/^p cnf/,$p' "$1" > "$1.body"; sha "$1.body"; }
cc -O2 -o "$T/hypenc" checks/hypenc.c

echo "1. Lower bounds: colourings with no monochromatic loose triangle (two checkers each)"
for w in "witnesses/R4_C3L_3unif_n8.col C3L/C3L/C3L/C3L" "witnesses/R5_C3L_3unif_n10.col C3L/C3L/C3L/C3L/C3L" \
         "witnesses/R5_C3L_3unif_n10_midpoint.col C3L/C3L/C3L/C3L/C3L" \
         "witnesses/R12_C3L_3unif_n18.col C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L" \
         "witnesses/R14_C3L_3unif_n20.col C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L/C3L"; do
  set -- $w
  "$T/hypenc" check "$1" "$2" | grep -q "^PASS" || fail "hypenc check $1"
  "$PY" -I checks/hcheck_char.py "$1" "$2" | grep -q "^PASS" || fail "hcheck_char $1"
  echo "   $1: PASS (both)"
done
for c in runs/ctl_h4c3_n8_c0.col runs/ctl_h4c3_n8_c1.col runs/ctl_h4c3_n8_c2.col runs/ctl_h4c3_n8_c3.col; do
  "$T/hypenc" check $c C3L/C3L/C3L/C3L | grep -q "^PASS" && fail "hypenc accepted red control $c"
  "$PY" -I checks/hcheck_char.py $c C3L/C3L/C3L/C3L | grep -q "^PASS" && fail "hcheck_char accepted red control $c"
done
for c in runs/ctl_hk5c3_n10_c0.col runs/ctl_hk5c3_n10_c1.col runs/ctl_hk5c3_n10_c2.col runs/ctl_hk5c3_n10_c3.col runs/ctl_hk5c3_n10_c4.col; do
  "$T/hypenc" check $c C3L/C3L/C3L/C3L/C3L | grep -q "^PASS" && fail "hypenc accepted red control $c"
  "$PY" -I checks/hcheck_char.py $c C3L/C3L/C3L/C3L/C3L | grep -q "^PASS" && fail "hcheck_char accepted red control $c"
done
echo "   9 red controls (a planted loose triangle in one colour) refused by both"

echo "2. Upper-bound formulas, built by two separately written generators (Python and C)"
"$PY" -I tools/hyp.py 9 C3L/C3L/C3L/C3L "$T/n9.cnf" --colswap > /dev/null
"$T/hypenc" enc 9 C3L/C3L/C3L/C3L "$T/n9c.cnf" all 1 > /dev/null 2>&1
[ "$(sha "$T/n9.cnf")" = 6a44c615d3677191d08dfcc305a595d259fe13dc9ed80909964e7a72fec82198 ] || fail "R_4 formula hash"
[ "$(body "$T/n9.cnf")" = "$(body "$T/n9c.cnf")" ] || fail "the two R_4 generators differ"
"$PY" -I tools/hyp.py 11 C3L/C3L/C3L/C3L/C3L "$T/n11.cnf" --colswap --nonstar --hall 6,7,8,9 > /dev/null
"$T/hypenc" enc 11 C3L/C3L/C3L/C3L/C3L "$T/n11c.cnf" all 1 nonstar hall=6,7,8,9 > /dev/null 2>&1
[ "$(body "$T/n11.cnf")" = d4ab1fce5ad2f39b0a0198f411926f3bee17f1a53e7b70d9a052e6992bf03204 ] || fail "R_5 formula hash"
[ "$(body "$T/n11c.cnf")" = d4ab1fce5ad2f39b0a0198f411926f3bee17f1a53e7b70d9a052e6992bf03204 ] || fail "the two R_5 generators differ"
echo "   R_4 (n = 9) and R_5 (n = 11) formulas: identical from both generators, hashes as recorded"

echo "3. R_5 cube and conquer: the 14,905 cubes and the records of all 18,129 refuted leaves and 53 splits"
[ "$(sha runs/cubes11/cubes.icnf)" = ff3d794c348e77d13252649c6de616091fd6f9c70ba7c4f0aff85219a36b9bb8 ] || fail "cube file hash"
"$PY" -I tools/cube_merge.py "$T/n11.cnf" runs/cubes11/cubes.icnf runs/cubes11/run/results.jsonl runs/cubes11/imported/c11.jsonl runs/cubes11/imported/c11mc_crash1.jsonl > "$T/merge.txt" 2>&1 || { tail -5 "$T/merge.txt"; fail "cube merge"; }
grep -q "covered=14905 missing=0" "$T/merge.txt" && grep -q "problems=0" "$T/merge.txt" || { tail -5 "$T/merge.txt"; fail "cube coverage"; }
grep -E "covered=" "$T/merge.txt" | tail -1 | sed 's/^/   /'

if command -v cadical > /dev/null && command -v drat-trim > /dev/null; then
  echo "4. R_4(C3;3) <= 9: CaDiCaL refutes the n = 9 formula; drat-trim checks the proof"
  set +e; cadical -q "$T/n9.cnf" "$T/n9.drat" > "$T/cad.txt"; rc=$?; set -e
  [ $rc = 20 ] || fail "CaDiCaL did not report UNSAT (rc $rc)"
  drat-trim "$T/n9.cnf" "$T/n9.drat" | grep -q "s VERIFIED" || fail "drat-trim"
  echo "   UNSAT, proof VERIFIED"
else
  echo "4. (skipped: put cadical and drat-trim on PATH to re-solve R_4 <= 9 here)"
fi
echo "ALL CHECKS PASSED: R_4(C3;3) = 9 and R_5(C3;3) = 11 (lower bounds checked; formulas and cube cover as recorded)."
