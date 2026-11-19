"""reverify.py: re-verify every leaf and every split cover of the R_5 cube tree with proofs KEPT.
Items = every distinct node used by the merge: leaves (rc = 20, drat-trim VERIFIED) and split covers (cover drat-trim
VERIFIED), from the given results files, deduplicated by (kind, cube, path). For each item (random order, fixed seed,
resumable): rebuild its CNF (BASE + literals, or BASE + literals + negated sub-cubes for a cover) and require its SHA-256
to equal the recorded one; CaDiCaL 3.0.1 writes a binary LRAT proof; cake_lpr (formally verified) checks it; the proof is
kept gzip -1 compressed under KEEP/ as <kind>_<cube>_<path>.lrat.gz; record (hashes of CNF, proof, compressed proof,
verdict, times) appended to OUT.jsonl. Proofs above --cap GB are checked but not kept (recorded as such).
Usage: python3 -I reverify.py BASE.cnf OUT.jsonl KEEP_DIR WORKERS RESULTS.jsonl [...] [--seed 7] [--cap 8] [--tmp DIR]
"""
import argparse, hashlib, json, os, random, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed

CAD = os.path.expanduser("<tools>/cadical/src/build/cadical")
CAKE = os.path.expanduser("<tools>/cake_lpr/cake_lpr")
BASE = None


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def init(base):
    global BASE
    lines = open(base).read().split("\n")
    i = 0
    while lines[i].startswith("c"):
        i += 1
    BASE = (int(lines[i].split()[2]), int(lines[i].split()[3]), "\n".join(lines[i + 1:]).rstrip("\n") + "\n")


def work(item, keep, tmp, cap_gb):
    nv, nc, body = BASE
    kind, cube, path, lits, subs, want = item
    name = f"{kind}_{cube}_{'-'.join(map(str, path)) or 'root'}"
    pid = os.getpid()
    cnf, prf = os.path.join(tmp, f"rv{pid}.cnf"), os.path.join(tmp, f"rv{pid}.lrat")
    with open(cnf, "w") as f:
        f.write(f"p cnf {nv} {nc + len(lits) + len(subs)}\n")
        f.write(body)
        f.write("".join(f"{l} 0\n" for l in lits))
        f.write("".join(" ".join(str(-l) for l in s) + " 0\n" for s in subs))
    rec = dict(item=name, kind=kind, cube=cube, path=path, cnf_sha256=sha_file(cnf))
    rec["cnf_matches_record"] = rec["cnf_sha256"] == want
    t0 = time.time()
    r = subprocess.run(["nice", "-n", "10", CAD, "-q", "--lrat=true", "--binary=true", cnf, prf], capture_output=True)
    rec["rc"], rec["solve_s"] = r.returncode, round(time.time() - t0, 2)
    if r.returncode == 20:
        rec["lrat_bytes"], rec["lrat_sha256"] = os.path.getsize(prf), sha_file(prf)
        t1 = time.time()
        c = subprocess.run(["nice", "-n", "10", CAKE, cnf, prf], capture_output=True, text=True)
        rec["cake_lpr"] = [l for l in c.stdout.splitlines() if l.startswith("s ")]
        rec["check_s"] = round(time.time() - t1, 2)
        if rec["lrat_bytes"] <= cap_gb * 1e9:
            gz = os.path.join(keep, name + ".lrat.gz")
            with open(gz, "wb") as gzf:
                subprocess.run(["nice", "-n", "10", "gzip", "-1", "-c", prf], stdout=gzf)
            rec["gz_file"], rec["gz_bytes"], rec["gz_sha256"] = os.path.basename(gz), os.path.getsize(gz), sha_file(gz)
        else:
            rec["kept"] = False
    for p in (cnf, prf):
        if os.path.exists(p):
            os.remove(p)
    return rec


def items_from(paths):
    seen, items = set(), []
    for p in paths:
        for l in open(p):
            r = json.loads(l)
            path = r.get("path", [])
            if r["rc"] == 20 and r.get("drat_trim") == ["s VERIFIED"]:
                key = ("leaf", r["cube"], tuple(path))
                if key not in seen:
                    seen.add(key); items.append(("leaf", r["cube"], path, r["lits"], [], r["cnf_sha256"]))
            sp = r.get("split")
            if sp and sp.get("cover_drat") == ["s VERIFIED"] and sp.get("subs"):
                key = ("cover", r["cube"], tuple(path))
                if key not in seen:
                    seen.add(key); items.append(("cover", r["cube"], path, r["lits"], sp["subs"], sp["cover_cnf_sha256"]))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("out"); ap.add_argument("keep"); ap.add_argument("workers", type=int)
    ap.add_argument("results", nargs="+")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--cap", type=float, default=8.0)
    ap.add_argument("--tmp", default="<archive>/qv-ramsey-exact-proofs/reverify_tmp")
    a = ap.parse_args()
    os.makedirs(a.keep, exist_ok=True); os.makedirs(a.tmp, exist_ok=True)
    items = items_from(a.results)
    random.Random(a.seed).shuffle(items)
    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            done.add(json.loads(l)["item"])
    todo = [it for it in items if f"{it[0]}_{it[1]}_{'-'.join(map(str, it[2])) or 'root'}" not in done]
    prog = open(a.out + ".progress", "a")
    print(f"START {time.strftime('%F %T')} items={len(items)} done={len(done)} todo={len(todo)} workers={a.workers}",
          file=prog, flush=True)
    n, bad, kept_gb = 0, 0, 0.0
    with ProcessPoolExecutor(a.workers, initializer=init, initargs=(a.base,)) as ex, open(a.out, "a") as f:
        futs = [ex.submit(work, it, a.keep, a.tmp, a.cap) for it in todo]
        for fu in as_completed(futs):
            rec = fu.result()
            f.write(json.dumps(rec) + "\n"); f.flush()
            n += 1
            kept_gb += rec.get("gz_bytes", 0) / 1e9
            if not (rec["cnf_matches_record"] and rec["rc"] == 20 and rec.get("cake_lpr") == ["s VERIFIED UNSAT"]):
                bad += 1
                print(f"NOT-OK {json.dumps(rec)[:300]}", file=prog, flush=True)
            if n % 100 == 0:
                print(f"{time.strftime('%F %T')} done={len(done) + n}/{len(items)} not_ok={bad} kept_gz_GB={kept_gb:.1f}",
                      file=prog, flush=True)
    print(f"END {time.strftime('%F %T')} done={len(done) + n}/{len(items)} not_ok={bad}", file=prog, flush=True)


if __name__ == "__main__":
    main()
