#!/bin/zsh
# usage: tools/prove.sh TAG [TIMELIMIT_S]
# Fresh CaDiCaL 3.0.1 solve of runs/TAG.cnf with a binary DRAT proof written to the external SSD, then drat-trim
# (Heule et al.) checks it; the proof's size and SHA-256 are logged and the proof file is deleted after the check.
TAG=$1; TL=${2:-36000}
cd ~/our working repository/research/ramsey-exact
CAD=<tools>/cadical/src/build/cadical
DT=<tools>/drat-trim/src/drat-trim
PR="<archive>/qv-ramsey-exact-proofs/$TAG.drat"
echo "PROVE-START $TAG $(date '+%F %T') cnf_sha256=$(shasum -a 256 runs/$TAG.cnf | cut -c1-64)"
T0=$(date +%s)
$CAD -q -t $TL runs/$TAG.cnf "$PR" > runs/$TAG.cadical.out 2>&1
RC=$?; T1=$(date +%s)
echo "CADICAL rc=$RC solve_s=$((T1-T0)) $(grep -m1 '^s ' runs/$TAG.cadical.out)"
if [ $RC -eq 20 ]; then
  SZ=$(stat -f %z "$PR"); SH=$(shasum -a 256 "$PR" | cut -c1-64)
  echo "PROOF bytes=$SZ sha256=$SH"
  $DT runs/$TAG.cnf "$PR" -t 200000 > runs/$TAG.drattrim.out 2>&1
  T2=$(date +%s)
  echo "DRAT-TRIM check_s=$((T2-T1)) $(tr '\r' '\n' < runs/$TAG.drattrim.out | grep -E '^s ' | tail -1)"
  rm -f "<archive>/qv-ramsey-exact-proofs/$TAG.drat"
  echo "PROOF-DELETED $TAG"
fi
echo "PROVE-END $TAG $(date '+%F %T')"
