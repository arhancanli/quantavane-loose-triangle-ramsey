#!/bin/zsh
# usage: tools/lrat_check.sh TAG CNF   CaDiCaL 3.0.1 writes an LRAT proof (text) to the external SSD; cake_lpr (CakeML,
# formally verified; build 033aad5, sources checked against cake_lpr.sha256) checks it; size and SHA-256 logged; proof
# deleted after the check (literal directory, per-tag file name).
TAG=$1; CNF=$2
CAD=<tools>/cadical/src/build/cadical
CAKE=<tools>/cake_lpr/cake_lpr
PR="<archive>/qv-ramsey-exact-proofs/lrat_$TAG.lrat"
echo "LRAT-START $TAG $(date '+%F %T') cnf_sha256=$(shasum -a 256 $CNF | cut -c1-64)"
T0=$(date +%s); $CAD -q --lrat=true --binary=false $CNF "$PR" > /dev/null 2>&1; RC=$?; T1=$(date +%s)
echo "CADICAL rc=$RC solve_s=$((T1-T0))"
if [ $RC -eq 20 ]; then
  echo "LRAT bytes=$(stat -f %z "$PR") sha256=$(shasum -a 256 "$PR" | cut -c1-64)"
  OUT=$($CAKE $CNF "$PR" 2>&1 | tail -2 | tr '\n' ' '); T2=$(date +%s)
  echo "CAKE_LPR check_s=$((T2-T1)) $OUT"
fi
rm -f "<archive>/qv-ramsey-exact-proofs/lrat_$TAG.lrat"
echo "LRAT-END $TAG $(date '+%F %T')"
