"""make_kernel_cubes.py: Kaggle kernel that runs K11 cubes from the END of the shuffled cube order (the local run
tools/cube_run.py goes from the start with the same seed), each with CaDiCaL + DRAT + drat-trim, writing results.jsonl
in the same format. Embeds tools/hyp.py (regenerates hk5c3_n11_h.cnf; its body SHA-256 must be d4ab1fce...) and the
cube file (zlib + base64; SHA-256 checked).
Usage: python3 -I make_kernel_cubes.py SLUG [--tpu]
"""
import base64, hashlib, json, os, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
LANE = os.path.dirname(HERE)
slug = sys.argv[1]
tpu = "--tpu" in sys.argv
hyp = open(os.path.join(HERE, "hyp.py")).read()
cubes_raw = open(os.path.join(LANE, "runs", "cubes11", "cubes.icnf"), "rb").read()
cubes_b64 = base64.b64encode(zlib.compress(cubes_raw, 9)).decode()
cubes_sha = hashlib.sha256(cubes_raw).hexdigest()
out = os.path.join(LANE, "kaggle", slug)
os.makedirs(out, exist_ok=True)
run = f'''# Kaggle kernel {slug}: K11 cubes for R_5(C3;3) = 11, from the end of the shuffled order (seed 2026).
import base64, hashlib, json, os, random, subprocess, sys, time, zlib
from multiprocessing import Pool
W = "/kaggle/working"
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True)
def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
log = open(W + "/run.log", "a")
def say(s):
    line = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) + " " + s
    print(line, flush=True); log.write(line + "\\n"); log.flush()
say("NPROC " + str(os.cpu_count()) + " | " + sh("free -g | head -2").stdout.replace("\\n", " | "))
open(W + "/hyp.py", "w").write({hyp!r})
r = sh(sys.executable + " -I " + W + "/hyp.py 11 C3L/C3L/C3L/C3L/C3L " + W + "/base.cnf --colswap --nonstar --hall 6,7,8,9")
body = open(W + "/base.cnf").read().split("\\n", 1)[1]
bsha = hashlib.sha256(body.encode()).hexdigest()
say("base " + r.stdout.strip() + " body_sha256 " + bsha)
assert bsha == "d4ab1fce5ad2f39b0a0198f411926f3bee17f1a53e7b70d9a052e6992bf03204"
raw = zlib.decompress(base64.b64decode({cubes_b64!r}))
assert hashlib.sha256(raw).hexdigest() == "{cubes_sha}"
cl = [l for l in raw.decode().split("\\n") if l.startswith("a ")]
tasks = [(i, [int(x) for x in c.split()[1:] if x != "0"]) for i, c in enumerate(cl)]
random.Random(2026).shuffle(tasks)
tasks = tasks[::-1]
say("cubes " + str(len(tasks)))
r = sh("cd /tmp && git clone -q https://github.com/arminbiere/cadical && cd cadical && git checkout -q c60730422e758ef1cebe7aeddf2dda31c996bf04 && ./configure > /dev/null && make -j8 > /dev/null && ./build/cadical --version")
say("cadical " + r.stdout.strip())
r = sh("cd /tmp && git clone -q https://github.com/marijnheule/drat-trim && cd drat-trim && git checkout -q 2e3b2dc0ecf938addbd779d42877b6ed69d9a985 && make > /dev/null && ls drat-trim")
say("drat-trim " + r.stdout.strip())
CAD, DT = "/tmp/cadical/build/cadical", "/tmp/drat-trim/drat-trim"
lines = open(W + "/base.cnf").read().split("\\n")
i = 0
while lines[i].startswith("c"): i += 1
NV, NC = int(lines[i].split()[2]), int(lines[i].split()[3])
BODY = "\\n".join(lines[i + 1:]).rstrip("\\n") + "\\n"
def work(task):
    idx, lits = task
    wid = os.getpid(); cnf = f"/tmp/w{{wid}}.cnf"; prf = f"/tmp/w{{wid}}.drat"
    with open(cnf, "w") as f:
        f.write(f"p cnf {{NV}} {{NC + len(lits)}}\\n"); f.write(BODY); f.write("".join(f"{{l}} 0\\n" for l in lits))
    rec = dict(cube=idx, lits=lits, cnf_sha256=sha_file(cnf), where="{slug}")
    t0 = time.time(); r = subprocess.run([CAD, "-q", cnf, prf], capture_output=True, text=True)
    rec["rc"], rec["solve_s"] = r.returncode, round(time.time() - t0, 2)
    if r.returncode == 20:
        rec["proof_bytes"], rec["proof_sha256"] = os.path.getsize(prf), sha_file(prf)
        t1 = time.time(); d = subprocess.run([DT, cnf, prf, "-t", "20000"], capture_output=True, text=True)
        rec["drat_trim"] = [l for l in d.stdout.replace("\\r", "\\n").splitlines() if l.startswith("s ")]
        rec["check_s"] = round(time.time() - t1, 2)
    elif r.returncode == 10:
        rec["model"] = [l for l in r.stdout.splitlines() if l.startswith("v")]
    for p in (cnf, prf):
        if os.path.exists(p): os.remove(p)
    return rec
T0 = time.time(); n = 0
with Pool(os.cpu_count()) as pool, open(W + "/results.jsonl", "a") as rf:
    for rec in pool.imap_unordered(work, tasks):
        rf.write(json.dumps(rec) + "\\n"); rf.flush(); n += 1
        if rec["rc"] != 20 or rec.get("drat_trim") != ["s VERIFIED"]: say("NOT-OK " + json.dumps(rec)[:300])
        if n % 200 == 0: say(f"done {{n}}")
        if time.time() - T0 > 11.3 * 3600:
            say("time limit reached"); pool.terminate(); break
say("END done " + str(n))
'''
open(os.path.join(out, "run.py"), "w").write(run)
meta = {"id": f"arhancanli12/{slug}", "title": slug.replace("-", " "), "code_file": "run.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": False, "enable_tpu": tpu, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [], "kernel_sources": []}
if tpu:
    meta["machine_shape"] = "TpuV5E8"
json.dump(meta, open(os.path.join(out, "kernel-metadata.json"), "w"))
print("wrote", out, "run.py bytes", os.path.getsize(os.path.join(out, "run.py")))
