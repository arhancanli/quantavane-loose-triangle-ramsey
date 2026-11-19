"""cube_lib.py: one cube-and-conquer node with a time limit and splitting (used by tools/cube_run.py and the Kaggle
cube kernels). A node is (cube index, path, literals); its CNF is BASE + the literals as units.
- CaDiCaL with a time limit TL writes a binary DRAT proof; UNSAT -> drat-trim checks it; SAT -> model kept.
- On timeout the node is SPLIT: march_cu (depth D) cubes the node's CNF; the split's cover formula (node CNF + the
  negation of every sub-cube) is refuted by CaDiCaL with a DRAT proof checked by drat-trim; the sub-cubes become child
  nodes (path + [s], literals = node literals + sub-cube literals), returned for queueing.
Every record keeps the SHA-256 of the CNF it is about (node CNF, or cover CNF) and of the proof; files are removed with
os.remove on the per-process paths after use.
"""
import hashlib, os, subprocess, time


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_base(path):
    lines = open(path).read().split("\n")
    i = 0
    while lines[i].startswith("c"):
        i += 1
    nv, nc = int(lines[i].split()[2]), int(lines[i].split()[3])
    return nv, nc, "\n".join(lines[i + 1:]).rstrip("\n") + "\n"


def _drat(DT, cnf, prf):
    t = time.time()
    d = subprocess.run([DT, cnf, prf, "-t", "20000"], capture_output=True, text=True)
    return [l for l in d.stdout.replace("\r", "\n").splitlines() if l.startswith("s ")], round(time.time() - t, 2)


def run_node(node, base, tools, tl, depth, tmpdir, nice=True):
    """node = (cube, path, lits); base = (nv, nc, body); tools = (CAD, DT, MARCH). Returns (record, children)."""
    cube, path, lits = node
    nv, nc, body = base
    CAD, DT, MARCH = tools
    pre = ["nice", "-n", "10"] if nice else []
    pid = os.getpid()
    cnf, prf = os.path.join(tmpdir, f"w{pid}.cnf"), os.path.join(tmpdir, f"w{pid}.drat")
    with open(cnf, "w") as f:
        f.write(f"p cnf {nv} {nc + len(lits)}\n")
        f.write(body)
        f.write("".join(f"{l} 0\n" for l in lits))
    rec = dict(cube=cube, path=path, lits=lits, cnf_sha256=sha_file(cnf))
    t0 = time.time()
    r = subprocess.run(pre + [CAD, "-q", "-t", str(tl), cnf, prf], capture_output=True, text=True)
    rec["rc"], rec["solve_s"] = r.returncode, round(time.time() - t0, 2)
    children = []
    if r.returncode == 20:
        rec["proof_bytes"], rec["proof_sha256"] = os.path.getsize(prf), sha_file(prf)
        rec["drat_trim"], rec["check_s"] = _drat(DT, cnf, prf)
    elif r.returncode == 10:
        rec["model"] = [l for l in r.stdout.splitlines() if l.startswith("v")]
    else:
        # split this node
        cub = os.path.join(tmpdir, f"w{pid}.icnf")
        t1 = time.time()
        subprocess.run(pre + [MARCH, cnf, "-d", str(depth), "-o", cub], capture_output=True, text=True)
        subs = [[int(x) for x in l.split()[1:] if x != "0"] for l in open(cub) if l.startswith("a ")] \
            if os.path.exists(cub) else []
        sp = dict(depth=depth, n_sub=len(subs), subs=subs, march_s=round(time.time() - t1, 2))
        cov = os.path.join(tmpdir, f"w{pid}.cover.cnf")
        with open(cov, "w") as f:
            f.write(f"p cnf {nv} {nc + len(lits) + len(subs)}\n")
            f.write(body)
            f.write("".join(f"{l} 0\n" for l in lits))
            f.write("".join(" ".join(str(-l) for l in s) + " 0\n" for s in subs))
        sp["cover_cnf_sha256"] = sha_file(cov)
        t2 = time.time()
        rc = subprocess.run(pre + [CAD, "-q", "-t", str(4 * tl), cov, prf], capture_output=True, text=True).returncode
        sp["cover_rc"], sp["cover_s"] = rc, round(time.time() - t2, 2)
        if rc == 20:
            sp["cover_proof_bytes"], sp["cover_proof_sha256"] = os.path.getsize(prf), sha_file(prf)
            sp["cover_drat"], sp["cover_check_s"] = _drat(DT, cov, prf)
            if sp["cover_drat"] == ["s VERIFIED"] and subs:
                children = [(cube, path + [s], lits + sub) for s, sub in enumerate(subs)]
        rec["split"] = sp
        for p in (cub, cov):
            if os.path.exists(p):
                os.remove(p)
    for p in (cnf, prf):
        if os.path.exists(p):
            os.remove(p)
    return rec, children
