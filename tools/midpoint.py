"""midpoint.py: the 'midpoint' colouring of the triples of two copies of Z_k (k odd), search side.
Points (p, a), p in {0,1}, a in Z_k. A triple with exactly two points (p,a), (p,b) in one part gets colour
(a+b)/2 mod k; a triple inside one part gets colour given by --inside: 'middle' (the middle term of a 3-term
arithmetic progression, k = 5 only), or 'free' (left to SAT: writes a CNF with the cross triples fixed by units).
Usage: python -I midpoint.py K OUT.col                      (inside = middle, k = 5)
       python -I midpoint.py K OUT.cnf --free               (CNF: hyp.py variable numbering, cross triples fixed)
"""
import sys
from itertools import combinations


def main():
    k, out = int(sys.argv[1]), sys.argv[2]
    free = "--free" in sys.argv
    inv2 = pow(2, -1, k)
    n = 2 * k
    pts = [(p, a) for p in range(2) for a in range(k)]
    T = list(combinations(range(n), 3))
    col = {}
    for t in T:
        P = [pts[v] for v in t]
        parts = [q[0] for q in P]
        if len(set(parts)) == 2:
            maj = max(set(parts), key=parts.count)
            a, b = [q[1] for q in P if q[0] == maj]
            col[t] = (a + b) * inv2 % k
        else:
            xs = sorted(q[1] for q in P)
            if free:
                col[t] = None
            else:
                mid = [m for m in xs if (2 * m - sum(xs) + m) % k == 0]
                assert len(mid) == 1, (xs, mid)
                col[t] = mid[0]
    if not free:
        with open(out, "w") as f:
            f.write(f"{n} {k}\n")
            for t in T:
                f.write(f"{t[0]} {t[1]} {t[2]} {col[t]}\n")
        print("wrote", out)
    else:
        units = []
        for i, t in enumerate(T):
            if col[t] is not None:
                units.append([i * k + col[t] + 1])
        open(out, "w").write("\n".join(" ".join(map(str, u)) + " 0" for u in units) + "\n")
        print("wrote units", out, len(units), "free triples", sum(1 for t in T if col[t] is None))


if __name__ == "__main__":
    main()
