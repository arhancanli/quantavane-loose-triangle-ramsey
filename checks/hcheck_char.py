"""hcheck_char.py: second checker for 3-uniform colourings (written apart from checks/hypenc.c and tools/hyp.py).
Characterisations used:
  C3L  three triples of one colour, pairwise meeting in exactly one vertex, with no vertex common to all three
  P3L  triples e1, e2, e3 with |e1 & e2| = |e2 & e3| = 1, e1 & e3 empty, e1 & e2 != e2 & e3
  K4-t four points spanning at least three triples of the colour
  K4   four points whose four triples all have the colour
  K5   five points whose ten triples all have the colour
Usage: python3 -I hcheck_char.py COLFILE PATS     (COLFILE: "n k", then "a b c col" per triple)
"""
import sys
from itertools import combinations


def main():
    path, pats = sys.argv[1], sys.argv[2]
    names = pats.split("/")
    data = open(path).read().split()
    n, k = int(data[0]), int(data[1])
    assert k == len(names)
    col = {}
    vals = list(map(int, data[2:]))
    for i in range(0, len(vals), 4):
        a, b, c, x = vals[i:i + 4]
        t = frozenset((a, b, c))
        assert len(t) == 3 and max(t) < n and min(t) >= 0 and 0 <= x < k and t not in col
        col[t] = x
    assert len(col) == n * (n - 1) * (n - 2) // 6
    bad = False
    for c, name in enumerate(names):
        E = [t for t, x in col.items() if x == c]
        hit = None
        if name == "C3L":
            for e1, e2, e3 in combinations(E, 3):
                if len(e1 & e2) == 1 and len(e2 & e3) == 1 and len(e1 & e3) == 1 and not (e1 & e2 & e3):
                    hit = (e1, e2, e3)
                    break
        elif name == "P3L":
            for e2 in E:
                for e1 in E:
                    if len(e1 & e2) != 1:
                        continue
                    for e3 in E:
                        if len(e3 & e2) == 1 and not (e1 & e3) and (e1 & e2) != (e3 & e2):
                            hit = (e1, e2, e3)
                            break
                    if hit:
                        break
                if hit:
                    break
        elif name in ("K4-t", "K4", "K5"):
            s = 5 if name == "K5" else 4
            need = 3 if name == "K4-t" else (4 if name == "K4" else 10)
            for Q in combinations(range(n), s):
                if sum(1 for t in combinations(Q, 3) if col[frozenset(t)] == c) >= need:
                    hit = Q
                    break
        else:
            raise ValueError(name)
        if hit:
            print(f"colour {c}: CONTAINS {name}: {[sorted(e) for e in hit] if name in ('C3L', 'P3L') else hit}")
            bad = True
        else:
            print(f"colour {c} ({len(E)} triples): no {name}")
    print("FAIL" if bad else f"PASS n={n}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
