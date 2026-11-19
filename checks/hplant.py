"""hplant.py: red controls for 3-uniform colourings: for each colour c, plant a loose triangle (abx, bcy, caz) of
colour c on random points. Usage: python3 -I hplant.py COLFILE OUTPREFIX [seed] -> OUTPREFIX_c<c>.col"""
import random, sys
path, outp = sys.argv[1], sys.argv[2]
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
lines = open(path).read().split("\n")
n, k = map(int, lines[0].split())
rows = [list(map(int, l.split())) for l in lines[1:] if l.strip()]
rnd = random.Random(seed)
for c in range(k):
    a, b, cc, x, y, z = rnd.sample(range(n), 6)
    plant = {frozenset(t) for t in ((a, b, x), (b, cc, y), (cc, a, z))}
    with open(f"{outp}_c{c}.col", "w") as f:
        f.write(f"{n} {k}\n")
        for r in rows:
            col = c if frozenset(r[:3]) in plant else r[3]
            f.write(f"{r[0]} {r[1]} {r[2]} {col}\n")
    print(f"control c{c}: loose triangle on {(a, b, cc, x, y, z)}")
