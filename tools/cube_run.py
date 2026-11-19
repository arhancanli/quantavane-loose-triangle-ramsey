"""cube_run.py: cube-and-conquer driver with checked proofs, time limits and splitting (R_5(C3;3) = 11 route).
Takes the cubes of a march_cu file in a fixed shuffled order (seed), optionally a slice of that order (--range a:b as
fractions) and optionally reversed; runs each node with tools/cube_lib.run_node (CaDiCaL with time limit + DRAT +
drat-trim; on timeout a march_cu split with a checked cover proof, children queued at the end). Resumable: nodes
already in OUTDIR/results.jsonl are skipped, and children of recorded splits that lack a record are re-queued.
A SAT node stops the run. Progress (every 100 records): OUTDIR/progress.log.
Usage: python3 -I cube_run.py BASE.cnf CUBES.icnf OUTDIR WORKERS [--seed 2026] [--range 0:1] [--reverse] [--tl 300]
       [--depth 6] [--tmp DIR] [--cad P] [--dt P] [--march P] [--hours H] [--nonice]
"""
import argparse, json, os, random, sys, time
from collections import deque
from concurrent.futures import ProcessPoolExecutor, FIRST_COMPLETED, wait

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cube_lib  # noqa: E402

BASE = TOOLS = None


def init(base_path, tools):
    global BASE, TOOLS
    BASE, TOOLS = cube_lib.load_base(base_path), tools


def job(node, tl, depth, tmp, nice):
    return cube_lib.run_node(node, BASE, TOOLS, tl, depth, tmp, nice)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("cubes"); ap.add_argument("out"); ap.add_argument("workers", type=int)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--range", default="0:1")
    ap.add_argument("--reverse", action="store_true")
    ap.add_argument("--tl", type=int, default=300)
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--tmp", default="<archive>/qv-ramsey-exact-proofs/cubes11")
    ap.add_argument("--cad", default=os.path.expanduser("<tools>/cadical/src/build/cadical"))
    ap.add_argument("--dt", default=os.path.expanduser("<tools>/drat-trim/src/drat-trim"))
    ap.add_argument("--march", default=os.path.expanduser("<tools>/CnC/march_cu/march_cu"))
    ap.add_argument("--hours", type=float, default=1e9)
    ap.add_argument("--nonice", action="store_true")
    ap.add_argument("--skip", nargs="*", default=[], help="other results.jsonl files: their VERIFIED UNSAT root nodes are skipped")
    a = ap.parse_args()
    os.makedirs(a.tmp, exist_ok=True); os.makedirs(a.out, exist_ok=True)
    cl = [l for l in open(a.cubes) if l.startswith("a ")]
    order = list(range(len(cl)))
    random.Random(a.seed).shuffle(order)
    lo, hi = (float(x) for x in a.range.split(":"))
    order = order[int(lo * len(order)):int(hi * len(order))]
    if a.reverse:
        order = order[::-1]
    resf = os.path.join(a.out, "results.jsonl")
    recs = [json.loads(l) for l in open(resf)] if os.path.exists(resf) else []
    done = {(r["cube"], tuple(r.get("path", []))) for r in recs}
    for sf in a.skip:
        for l in open(sf):
            r = json.loads(l)
            if r.get("rc") == 20 and r.get("drat_trim") == ["s VERIFIED"] and not r.get("path"):
                done.add((r["cube"], ()))
    queue = deque()
    for j in order:
        if (j, ()) not in done:
            queue.append((j, [], [int(x) for x in cl[j].split()[1:] if x != "0"]))
    for r in recs:
        sp = r.get("split")
        if sp and sp.get("cover_drat") == ["s VERIFIED"]:
            for s, sub in enumerate(sp["subs"]):
                if (r["cube"], tuple(r.get("path", [])) + (s,)) not in done:
                    queue.append((r["cube"], r.get("path", []) + [s], r["lits"] + sub))
    prog = open(os.path.join(a.out, "progress.log"), "a")
    print(f"START {time.strftime('%F %T')} range={a.range} reverse={a.reverse} tl={a.tl} queued={len(queue)} "
          f"already={len(done)} workers={a.workers}", file=prog, flush=True)
    tools = (a.cad, a.dt, a.march)
    T0, n, tot, mx, bad, splits = time.time(), 0, 0.0, 0.0, 0, 0
    stop = False
    with ProcessPoolExecutor(a.workers, initializer=init, initargs=(a.base, tools)) as ex, open(resf, "a") as rf:
        running = set()
        while (queue or running) and not stop:
            while queue and len(running) < a.workers and time.time() - T0 < a.hours * 3600:
                running.add(ex.submit(job, queue.popleft(), a.tl, a.depth, a.tmp, not a.nonice))
            if not running:
                break
            fin, running = wait(running, return_when=FIRST_COMPLETED)
            for f in fin:
                rec, children = f.result()
                rf.write(json.dumps(rec) + "\n"); rf.flush()
                n += 1
                t = rec["solve_s"] + rec.get("check_s", 0)
                tot += t; mx = max(mx, t)
                if "split" in rec:
                    splits += 1
                    sp = rec["split"]
                    print(f"SPLIT cube {rec['cube']} path {rec.get('path')} n_sub={sp['n_sub']} cover_rc={sp.get('cover_rc')} "
                          f"cover_drat={sp.get('cover_drat')}", file=prog, flush=True)
                    queue.extend(children)
                elif rec["rc"] == 20 and rec.get("drat_trim") != ["s VERIFIED"]:
                    bad += 1
                    print(f"NOT-VERIFIED cube {rec['cube']} path {rec.get('path')} {rec.get('drat_trim')}", file=prog, flush=True)
                if rec["rc"] == 10:
                    print(f"SAT NODE cube {rec['cube']} path {rec.get('path')}: stopping", file=prog, flush=True)
                    stop = True
                if n % 100 == 0:
                    print(f"{time.strftime('%F %T')} records={n} queue={len(queue)} mean_s={tot/n:.2f} max_s={mx:.1f} "
                          f"splits={splits} not_verified={bad}", file=prog, flush=True)
        if stop:
            for f in running:
                f.cancel()
    print(f"END {time.strftime('%F %T')} records={n} queue_left={len(queue)} splits={splits} not_verified={bad}",
          file=prog, flush=True)


if __name__ == "__main__":
    main()
