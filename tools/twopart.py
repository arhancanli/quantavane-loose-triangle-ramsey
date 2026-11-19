"""twopart.py: the two-part construction (search side; outputs go to the checkers).
Input: a good k2-colouring of the triples of an m-set (m even), file BASE ("m k2", then "a b c col").
Output: a colouring of the triples of 2m points P = {0..m-1}, Q = {m..2m-1} with (m-1) + k2 colours:
  - a triple with two points a, b in one part and one point in the other part gets colour c, where c is the index of
    the perfect matching containing {a, b} in the round-robin 1-factorization of K_m (applied to each part);
  - a triple inside one part gets (m-1) + its colour in BASE (the same base colouring on P and on Q).
Usage: python3 -I twopart.py BASE OUT
"""
import sys
from itertools import combinations


def one_factor_index(m):
    """round-robin 1-factorization of K_m (m even): vertex m-1 fixed; matching r pairs (r, m-1) and
    ((r+i) mod (m-1), (r-i) mod (m-1)) for i = 1..(m-2)/2."""
    idx = {}
    for r in range(m - 1):
        idx[frozenset((r, m - 1))] = r
        for i in range(1, (m - 2) // 2 + 1):
            idx[frozenset(((r + i) % (m - 1), (r - i) % (m - 1)))] = r
    assert len(idx) == m * (m - 1) // 2
    return idx


def main():
    base, out = sys.argv[1], sys.argv[2]
    data = open(base).read().split()
    m, k2 = int(data[0]), int(data[1])
    assert m % 2 == 0
    vals = list(map(int, data[2:]))
    bc = {frozenset(vals[i:i + 3]): vals[i + 3] for i in range(0, len(vals), 4)}
    idx = one_factor_index(m)
    n, k = 2 * m, (m - 1) + k2
    with open(out, "w") as f:
        f.write(f"{n} {k}\n")
        for t in combinations(range(n), 3):
            side = [v // m for v in t]
            loc = [v % m for v in t]
            if side[0] == side[1] == side[2]:
                c = (m - 1) + bc[frozenset(loc)]
            else:
                maj = 0 if side.count(0) == 2 else 1
                a, b = [loc[i] for i in range(3) if side[i] == maj]
                c = idx[frozenset((a, b))]
            f.write(f"{t[0]} {t[1]} {t[2]} {c}\n")
    print(f"wrote {out}: n={n} k={k}")


if __name__ == "__main__":
    main()
