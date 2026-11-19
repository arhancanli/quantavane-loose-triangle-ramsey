# Multicolour Ramsey numbers of the 3-uniform loose triangle: R₄(C₃;3) = 9 and R₅(C₃;3) = 11

**Status: verified by two independent programs and an internal referee; not yet peer reviewed.**

Author: Arhan Canli (Quantavane, arhan@quantavane.com). On the use of AI, see
[Authorship and the role of AI](#authorship-and-the-role-of-ai).

## The results

The loose triangle C₃ (3-uniform) is three triples that pairwise meet in exactly one vertex and span six vertices.
R_r(C₃;3) is the least n such that every r-colouring of the triples of an n-set has a monochromatic loose triangle.

- **R₄(C₃;3) = 9.** The published bounds were 9 ≤ R₄ ≤ 12.
- **R₅(C₃;3) = 11.** The lower bound r + 5 = 10 fails at five colours.
- **R₁₂(C₃;3) ≥ 19**, and R_r(C₃;3) ≥ r + 6 + ⌊log₂(r/9)⌋ for every r ≥ 9, so R_r(C₃;3) − r is unbounded.

Gyárfás and Raeisi proved r + 5 ≤ R_r(C₃;3) ≤ 3r for r ≥ 3 and R₂ = 7, R₃ = 8, and wrote that they suspect the lower
bound r + 5 is the truth for all r; Mubayi and Suk's survey also says the lower bound appears more likely to be the
answer. The results above confirm the suspicion for four colours and show it fails for every r ≥ 5. The proofs are in
`paper/main.pdf` (draft).

## Earlier work

- A. Gyárfás and G. Raeisi, *The Ramsey number of loose triangles and quadrangles in hypergraphs*, Electron. J.
  Combin. 19(2) (2012), #P30: the bounds, R₂ = 7, R₃ = 8, the colouring giving r + 5, and the suspicion (end of
  Section 3).
- D. Mubayi and A. Suk, *A survey of hypergraph Ramsey problems* (arXiv:1707.04229), Section 9.
- M. Axenovich, A. Gyárfás, H. Liu and D. Mubayi, *Multicolor Ramsey numbers for triple systems*, Discrete Math. 322
  (2014), 69–77.
- S. Radziszowski, *Small Ramsey Numbers*, Electron. J. Combin. Dynamic Survey DS1, revision 18 (2026), item 7.2.2(a).
- Tools: lex-leader symmetry breaking (J. Crawford, M. Ginsberg, E. Luks and A. Roy, KR 1996); CaDiCaL 3.0.1 (A. Biere
  and coauthors); drat-trim (M. Heule and coauthors); cake_lpr (Y. K. Tan, M. Heule and M. Myreen); march_cu (cube and
  conquer, M. Heule and coauthors).

## How it was checked

- **Lower bounds.** Explicit colourings in `witnesses/` (one triple per line with its colour). Each is checked by two
  separately written checkers: `checks/hypenc.c check` (search over vertex maps, C) and `checks/hcheck_char.py`
  (characterisation: three triples pairwise meeting in one vertex with empty common part). Planted controls (one loose
  triangle in one colour, `checks/hplant.py`) are refused by both. The five-colour witness on 10 points has a short
  description: two copies P, Q of Z₅; a triple with two points a, b in one part and one in the other gets colour
  (a + b)/2 mod 5, a triple inside one part gets its middle term (`tools/midpoint.py`).
- **R₄ ≤ 9.** The formula for 4-colourings of the triples of a 9-set, with lex-leader constraints for point and colour
  transpositions (7,350 variables, 61,992 clauses, SHA-256 6a44c615…), is produced identically by `tools/hyp.py`
  and `checks/hypenc.c`; CaDiCaL 3.0.1 refutes it in seconds and its DRAT proof is verified by drat-trim; its LRAT
  proof was also verified by cake_lpr (a CakeML-verified checker). A second certificate uses no lex-leader argument
  (only the order of first use of colours): DRAT proof of 139 MB, verified.
- **R₅ ≤ 11.** The formula on 11 points with lex-leader constraints and two clause families implied by R₁–R₄ (23,860
  variables, 355,775 clauses) is produced identically by both generators. march_cu splits it into 14,905 cubes; the
  formula with the negations of all cubes is refuted (DRAT verified; LRAT verified by cake_lpr), and every cube was
  refuted with a checked proof, 53 of them after a further split: 18,129 leaves in all, about 49 hours of solving. On
  19 November 2026 every leaf and split was rebuilt, re-solved with LRAT output and checked by cake_lpr: 18,182 of
  18,182 VERIFIED (`runs/cubes11/reverify.jsonl`, hashes of every formula and proof). The proofs (92 GB gzipped) are
  kept by the lab and are not in this repository; `runs/cubes11/MANIFEST.md` lists the tools and hashes.
- Internal referees (fresh-context AI agents, not outside mathematicians) re-derived the encodings, checked the
  soundness of the symmetry breaking and of the implied clauses, re-proved R₂ = 7, R₃ = 8, R₄ ≤ 9 with their own
  encodings, and re-solved 200 random leaves and 5 split covers.

## Checking it: one command

    sh check.sh

It checks every colouring with both checkers and refuses the planted controls; regenerates the R₄ and R₅ formulas with
both generators and compares their hashes; checks that the cube records cover all 14,905 cubes with no problem; and,
if `cadical` and `drat-trim` are on PATH, re-solves R₄ ≤ 9 and verifies the proof. It needs `cc` and `python3`
(standard library). Re-solving the R₅ leaves: `python3 -I tools/reverify.py BASE.cnf OUT.jsonl KEEP_DIR WORKERS
runs/cubes11/run/results.jsonl runs/cubes11/imported/c11.jsonl runs/cubes11/imported/c11mc_crash1.jsonl` (needs
CaDiCaL and cake_lpr; about 49 CPU-hours).

The few files edited for this public copy (status sentences, local paths) are listed with their hashes in
`PUBLIC_COPY_CHANGES.md`.

## Not yet done

- Outside review: none yet. The paper is a draft.
- Lean 4: planned (the lower-bound colourings by `decide`; the upper bounds through the LRAT certificates).

## Authorship and the role of AI

Author and maintainer: Arhan Canli (Quantavane, https://quantavane.com), who takes responsibility for the results.

The searches, the encoders, the checkers, the runs and these documents were written and carried out by AI agents
(Claude, by Anthropic) working for Quantavane under Arhan Canli's direction. Programs described as written separately
share no code but were written with the same AI system. No mathematician outside Quantavane has reviewed this
repository; the colourings and the proofs can be checked by anyone with the programs here or with their own.

## Licence and citation

Colourings, cube files, records, the paper and the text are under CC BY 4.0 (`LICENSE`); the code is under the MIT
licence (`LICENSE-CODE`). Please cite as: Arhan Canli, *Multicolour Ramsey numbers of the 3-uniform loose triangle*,
https://github.com/arhancanli/quantavane-loose-triangle-ramsey (2026), together with Gyárfás and Raeisi.
