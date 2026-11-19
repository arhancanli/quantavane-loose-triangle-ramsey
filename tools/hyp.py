"""hyp.py (encoder A, hypergraphs): full CNF for "k-colouring of the triples of [n] with no colour-c copy of H_c".

Variables x_{t,c} = t*k + c + 1 (k >= 3) or x_t = t + 1 (k = 2, true = colour 0), triples t in lexicographic order.
Clauses, in this order:
  (1) one-hot (k >= 3): for each t: (x_{t,0} v ... v x_{t,k-1}), then (-x_{t,a} v -x_{t,b}) for a < b;
  (2) lex-leader symmetry breaking x <=_lex sigma(x) for the variable permutation sigma of each vertex
      transposition (i j), i < j in lexicographic order ('all') or j = i+1 ('adj'), then each colour transposition
      (a b), a < b, whose two patterns are equal (--colswap); positions 1..V, fixed positions skipped;
  (3) for each colour c, for each copy of H_c (a set of triples), sorted copies: (-x_{t,c} for t in copy)
      (k = 2: colour 1 copies give (x_t for t in copy));
  (4) only with --nonstar (k >= 3): for each colour c, for each vertex v: (x_{t,c} for t not containing v), i.e.
      no colour class lies inside the star of a vertex. Sound when R_{k-1}(H;3) <= n-1 is already proved: a
      class inside the star of v would leave a (k-1)-colouring of the triples of [n] minus v.
  (4b) only with --firstuse a,b,c/d,e,f/... (used with --sb none): colours of the listed triples appear in order of
      first use: triple 1 has colour 0, and triple i has colour <= 1 + max(colours of triples 1..i-1). For i = 2:
      (-x_{T2,c}) for c >= 2; for i = 3: (-x_{T3,c}) for c >= 3 and (-x_{T2,0} v -x_{T3,2}). Sound for equal patterns:
      relabel the colours of any good colouring in order of first appearance along the list.
  (5) only with --hall R1,R2,...,R_{k-1} (R_j = the proved value of R_j(H;3)): for j = 1..k-1 with
      s = n - R_{k-j} >= 1, for each s-set S of vertices (lexicographic) and each j-set J of colours (lexicographic):
      (x_{t,c} for c in J, for t in lexicographic order of the triples avoiding S), i.e. some colour of J appears off
      S. Sound: otherwise the triples off S (n - s = R_{k-j} points) use at most k-j colours.
Patterns (3-uniform): C3L (loose triangle: abx, bcy, caz; 6 vertices), P3L (loose path of 3 triples, 7 vertices),
K4 (4 points, 4 triples), K4-t (4 points, 3 triples), K5 (5 points, 10 triples).
Usage: python -I hyp.py N PATS OUT.cnf [--sb all|adj|none] [--colswap]     PATS like C3L/C3L/C3L/C3L
"""
import sys
from itertools import combinations, permutations


def pattern(name):
    if name == "C3L":
        # vertices a=0 b=1 c=2 (junctions), x=3 y=4 z=5
        return 6, [(0, 1, 3), (1, 2, 4), (2, 0, 5)]
    if name == "P3L":
        # loose path: 012, 234, 456
        return 7, [(0, 1, 2), (2, 3, 4), (4, 5, 6)]
    if name == "K4":
        return 4, list(combinations(range(4), 3))
    if name == "K4-t":
        return 4, [(0, 1, 2), (0, 1, 3), (0, 2, 3)]
    if name == "K5":
        return 5, list(combinations(range(5), 3))
    raise ValueError(name)


def copies(n, name, tidx):
    h, E = pattern(name)
    seen = set()
    for vs in combinations(range(n), h):
        for perm in permutations(vs):
            key = frozenset(tidx[tuple(sorted((perm[a], perm[b], perm[c])))] for a, b, c in E)
            seen.add(key)
    return sorted(tuple(sorted(s)) for s in seen)


def main():
    n = int(sys.argv[1])
    names = sys.argv[2].split("/")
    out = sys.argv[3]
    sb = "all"
    colswap = "--colswap" in sys.argv
    nonstar = "--nonstar" in sys.argv
    firstuse = None
    if "--firstuse" in sys.argv:
        firstuse = [tuple(sorted(int(x) for x in t.split(","))) for t in sys.argv[sys.argv.index("--firstuse") + 1].split("/")]
        if len(firstuse) != 3 or len(set(names)) != 1 or len(names) < 3:
            sys.exit("--firstuse needs exactly three triples, k >= 3 and one pattern")
    hall = None
    if "--hall" in sys.argv:
        hall = [int(x) for x in sys.argv[sys.argv.index("--hall") + 1].split(",")]
        if len(hall) != len(names) - 1 or hall != sorted(hall) or len(set(names)) != 1:
            sys.exit("--hall needs k-1 increasing values R_1..R_{k-1} and one pattern for all colours")
    if "--sb" in sys.argv:
        sb = sys.argv[sys.argv.index("--sb") + 1]
        if sb not in ("all", "adj", "none"):
            sys.exit("--sb must be all, adj or none")
    k = len(names)
    T = list(combinations(range(n), 3))
    tidx = {t: i for i, t in enumerate(T)}
    V = len(T) * (k if k >= 3 else 1)

    def var(t, c):
        return t * k + c + 1 if k >= 3 else t + 1

    top = V
    cls = []
    if k >= 3:
        for t in range(len(T)):
            cls.append([var(t, c) for c in range(k)])
            for a, b in combinations(range(k), 2):
                cls.append([-var(t, a), -var(t, b)])

    def lexleader(s):
        nonlocal top
        pos = [p for p in range(1, V + 1) if s[p] != p]
        y = None
        for i, p in enumerate(pos):
            a, b = p, s[p]
            pre = [] if y is None else [-y]
            cls.append(pre + [-a, b])
            if i == len(pos) - 1:
                break
            top += 1
            cls.append(pre + [-a, -b, top])
            cls.append(pre + [a, b, top])
            y = top

    if sb != "none":
        pairs = list(combinations(range(n), 2)) if sb == "all" else [(i, i + 1) for i in range(n - 1)]
        for i, j in pairs:
            sw = lambda x: j if x == i else (i if x == j else x)
            s = [0] * (V + 1)
            for t, tr in enumerate(T):
                img = tidx[tuple(sorted(sw(x) for x in tr))]
                for c in range(k if k >= 3 else 1):
                    s[var(t, c)] = var(img, c)
            lexleader(s)
    if colswap and k >= 3:
        for a, b in combinations(range(k), 2):
            if names[a] != names[b]:
                continue
            s = [0] * (V + 1)
            for t in range(len(T)):
                for c in range(k):
                    cc = b if c == a else (a if c == b else c)
                    s[var(t, c)] = var(t, cc)
            lexleader(s)
    nbase = len(cls)
    cache = {}
    for c, name in enumerate(names):
        if name not in cache:
            cache[name] = copies(n, name, tidx)
        for cp in cache[name]:
            if k >= 3:
                cls.append([-var(t, c) for t in cp])
            else:
                cls.append([-var(t, 0) for t in cp] if c == 0 else [var(t, 0) for t in cp])
    if nonstar and k >= 3:
        for c in range(k):
            for v in range(n):
                cls.append([var(t, c) for t in range(len(T)) if v not in T[t]])
    if firstuse:
        t1, t2, t3 = (tidx[t] for t in firstuse)
        cls.append([var(t1, 0)])
        for c in range(2, k):
            cls.append([-var(t2, c)])
        for c in range(3, k):
            cls.append([-var(t3, c)])
        cls.append([-var(t2, 0), -var(t3, 2)])
    if hall and k >= 3:
        for j in range(1, k):
            s_ = n - hall[k - j - 1]
            if s_ < 1:
                continue
            for S in combinations(range(n), s_):
                off = [t for t in range(len(T)) if not set(T[t]) & set(S)]
                for J in combinations(range(k), j):
                    cls.append([var(t, c) for c in J for t in off])
    with open(out, "w") as f:
        f.write(f"c ramsey-exact hyp.py n={n} pats={'/'.join(names)} sb={sb} colswap={colswap} base={nbase}\n")
        f.write(f"p cnf {top} {len(cls)}\n")
        for cl in cls:
            f.write(" ".join(map(str, cl)) + " 0\n")
    print(f"wrote {out}: vars={top} clauses={len(cls)} base={nbase}")


if __name__ == "__main__":
    main()
