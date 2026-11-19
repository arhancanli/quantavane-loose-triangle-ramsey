"""cube_sample.py: Knuth-style size estimate for cube-and-conquer (playbook point 4). Picks S uniformly random cubes
from a march_cu cube file, solves BASE.cnf + cube units with CaDiCaL (time limit TL each), and reports
N_cubes * mean(time) as the estimated total, counting timeouts at TL (so the estimate is a lower bound if any time
out). Search side only; the real run must check every cube with a proof and check that the cubes cover the space.
Usage: python3 -I cube_sample.py BASE.cnf CUBES.icnf S TL [seed]
"""
import random, subprocess, sys, tempfile, time, os

base, cubes, S, TL = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
seed = int(sys.argv[5]) if len(sys.argv) > 5 else 1
CAD = os.path.expanduser("<tools>/cadical/src/build/cadical")
cl = [l for l in open(cubes) if l.startswith("a ")]
N = len(cl)
lines = open(base).read().split("\n")
hdr = lines[1].split() if lines[0].startswith("c") else lines[0].split()
start = 2 if lines[0].startswith("c") else 1
nv, nc = int(hdr[2]), int(hdr[3])
body = "\n".join(lines[start:]).rstrip("\n") + "\n"
rnd = random.Random(seed)
times, res = [], []
for idx in rnd.sample(range(N), min(S, N)):
    lits = [int(x) for x in cl[idx].split()[1:] if x != "0"]
    with tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False) as f:
        f.write(f"p cnf {nv} {nc + len(lits)}\n" + body + "".join(f"{l} 0\n" for l in lits))
        fn = f.name
    t0 = time.time()
    r = subprocess.run(["nice", "-n", "10", CAD, "-q", "-t", str(TL), fn], capture_output=True, text=True)
    dt = time.time() - t0
    os.remove(fn)
    st = "UNSAT" if r.returncode == 20 else ("SAT" if r.returncode == 10 else "TIMEOUT")
    times.append(min(dt, TL)); res.append(st)
    print(f"cube {idx} len={len(lits)} {st} {dt:.1f}s", flush=True)
    if st == "SAT":
        print("SAT CUBE FOUND", flush=True)
        break
mean = sum(times) / len(times)
print(f"N_cubes={N} sampled={len(times)} timeouts={res.count('TIMEOUT')} mean={mean:.1f}s "
      f"estimate_total={N*mean/3600:.1f} CPU-h ({'lower bound' if 'TIMEOUT' in res else 'estimate'})")
