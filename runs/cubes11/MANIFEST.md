# R_5(C3;3) <= 11 certificate manifest (19 Nov 2026 01:0x +04)

## Formula
base CNF runs/hk5c3_n11_h.cnf: aebdc881d01a726dfa6b0236f167af0e8b2a4cbeae989cfdfb51959487dcd50a (body from the p line: d4ab1fce5ad2f39b0a0198f411926f3bee17f1a53e7b70d9a052e6992bf03204; generated identically by tools/hyp.py '11 C3L/C3L/C3L/C3L/C3L --colswap --nonstar --hall 6,7,8,9' and checks/hypenc.c 'enc 11 ... all 1 nonstar hall=6,7,8,9')
tools/hyp.py a3d0b0ab0624ebebe8ab6a9fa26b342bccc66a9bb11a61a7c95f6e9c66a76cf5
checks/hypenc.c 0fc08ff5ea9cd60f72549fc2ee21a72352af967efe37c69ff98e060f24171539

## Cubes
runs/cubes11/cubes.icnf (march_cu -d 14, 14905 cubes): ff3d794c348e77d13252649c6de616091fd6f9c70ba7c4f0aff85219a36b9bb8

## Root cover (base + negation of every cube is UNSAT)
    PROVE-START cover11 2026-11-18 11:01:04 cnf_sha256=d859bdee0b0a397f96025753fb4c0917b7977555a688e4bc1712a76aaff18239
    CADICAL rc=20 solve_s=2 s UNSATISFIABLE
    PROOF bytes=5428467 sha256=5e2ae14fe099835603a9c8e74a5fdb5cf1c5d3770c3ce6899d5c691bbc6aa652
    DRAT-TRIM check_s=1 s VERIFIED
    PROOF-DELETED cover11
    PROVE-END cover11 2026-11-18 11:01:07

## Leaf and split records
runs/cubes11/run/results.jsonl: 13781 records, SHA-256 0ff2cf7e9b3a94a47094f568f0ab258bfa446a155897b6874f3f57e11b67230b
runs/cubes11/imported/c11.jsonl: 4401 records, SHA-256 c7b4d2565a2bd21774b5eaefda81bb9957479203f4852dab8ec4821d54b13310
runs/cubes11/imported/c11mc_crash1.jsonl: 49 records, SHA-256 a78348e52455c1fa2211917ec866eda4c2d49a955c43cd12fea63396b40a5d36

## Tools
tools/cube_lib.py de8a770003d77410b643de4a3cd5ad78743824feec7a8ed63a27a9c2409c4820
tools/cube_run.py ab2754a60a267d868088882d53b7457057b68821d8d9381a2226ac5c9b8a29ba
tools/cube_merge.py 84a847ece0540156036828dc5bd9918ec14a420ab74f33e7e96bd8c75e2c02c9
tools/make_kernel_cubes.py 5177759b7590b6965459fa3ad95295bb04f61cc9c9798a033b428e9684aa2bd0
tools/make_kernel_cubes2.py e4c3eba0d53e7943cfeea253425b517b08660be7639cff2524a2f85904630c6e
CaDiCaL 3.0.1 (local build; Kaggle: commit c6073042); drat-trim (local: 'Last edit April 21, 2024'; Kaggle: commit 2e3b2dc); march_cu (CnC, local sources)

## Merge (tools/cube_merge.py over the three results files)
    cubes=14905 covered=14905 missing=0 leaves=18129 splits=53 solve_h=48.78 check_h=25.97 proof_GB=125.25 problems=0

## Lemma clauses in the base formula
nonstar + hall=6,7,8,9 rest on R_1 = 6 (trivial), R_2 = 7, R_3 = 8 (GyRa; re-certified 18 Nov, runs/hk2c3_n7, runs/hk3c3_n8, drat-trim VERIFIED) and R_4 <= 9 (NOTES 2.1: two DRAT certificates, referee 1).

## Root-cover CNF provenance (19 Nov 01:2x, after referee 3)
runs/cover11.cnf was written as: one comment line "c cover check: hk5c3_n11_h.cnf + negations of all 14905 march cubes",
then "p cnf 23860 370680", then the base clauses (hk5c3_n11_h.cnf from its p line on), then for each cube line of
cubes.icnf in file order the clause of its negated literals. SHA-256 with the comment line: d859bdee0b0a397f96025753fb4c0917b7977555a688e4bc1712a76aaff18239;
from the p line on (what a rebuild without the comment gives, as referee 3 did): ce252fec634c8837dc7e6cfd88814b4a09b7ebe7dac99820c425df6c08fac889.
Both re-read from the file on disk. DRAT checkers ignore comments; referee 3's re-proof of the comment-free file gave a
byte-identical proof (SHA-256 5e2ae14f...).

## Referee 3 note: c11 cube 1953
Re-solving c11 cube 1953 gave a proof with different bytes from the recorded SHA-256 (the Kaggle run used CaDiCaL
built from commit c6073042 on Linux; the re-solve used the local build); the re-solved proof is drat-trim VERIFIED, so
the leaf stands. (As recorded by the lab lead: all 200 sampled leaves and 5 split covers were re-solved and
drat-trim VERIFIED; cube 1953 is the proof-hash mismatch the referee reported.)

## Formally verified checks with cake_lpr (19 Nov 01:3x)
cake_lpr (CakeML-verified LRAT/LPR checker; github tanyongkiam/cake_lpr commit 033aad5, sources verified against its
cake_lpr.sha256; built locally for arm64) checked fresh CaDiCaL 3.0.1 LRAT proofs (tools/lrat_check.sh, proofs deleted
after the check):
- root cover runs/cover11.cnf (SHA-256 d859bdee...): LRAT 8,778,522 bytes, SHA-256 6d1f8981b898e65b3fd8afbac610e9513a1f004b01848749ab543053a1113bf5, s VERIFIED UNSAT
- R_2 <= 7 (runs/hk2c3_n7.cnf): LRAT 608 bytes, SHA-256 2d74be59..., s VERIFIED UNSAT
- R_3 <= 8 (runs/hk3c3_n8.cnf): LRAT 22,949 bytes, SHA-256 4007f24b..., s VERIFIED UNSAT
- R_4 <= 9 (runs/h4c3_n9.cnf): LRAT 16,783,697 bytes, SHA-256 20eb742f..., s VERIFIED UNSAT

## Full LRAT re-verification with proofs kept (19 Nov 2026, finished 12:40 +04)
tools/reverify.py rebuilt the CNF of every leaf (18,129) and every split cover (53) of the merged tree, required its
SHA-256 to equal the hash in the original record, re-solved it with CaDiCaL 3.0.1 (--lrat=true --binary=true) and
checked the proof with cake_lpr (CakeML-verified, build 033aad5). Result: 18,182 / 18,182 items, all 18,182
cnf_matches_record = true, rc = 20, cake_lpr "s VERIFIED UNSAT"; 0 not OK. Solve 27.6 CPU-h, check 4.5 CPU-h.
Proofs kept: 155.1 GB of binary LRAT, stored gzip -1 as 92.1 GB under
"<archive>/qv-ramsey-exact-proofs/r5_lrat/" (one file per item; name and gz SHA-256 in each record).
runs/cubes11/reverify.jsonl: 18,182 records, SHA-256 c2a36b5cf7c9a9d12696e46045dfffa430f457e27f082fc9e55e23ebedabbec8
