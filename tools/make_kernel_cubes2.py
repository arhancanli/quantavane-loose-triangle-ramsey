"""make_kernel_cubes2.py: Kaggle kernel for the K11 cubes with time limits and splitting. Embeds tools/hyp.py,
tools/cube_lib.py, tools/cube_run.py and the cube file (zlib+base64, SHA-256 checked); regenerates the base CNF and
asserts its body SHA-256 (d4ab1fce...); builds CaDiCaL (c6073042) and drat-trim (2e3b2dc) from source and march_cu from the embedded
sources of our local copy (tar.gz, SHA-256 checked), asserting all three binaries exist before the run; runs cube_run.py on a slice of the shuffled order with os.cpu_count() workers, logging nproc and memory.
Usage: python3 -I make_kernel_cubes2.py SLUG RANGE [--gpu|--tpu] [--reverse] [--tl 300] [--hours 11.3]
"""
import base64, hashlib, json, os, sys, zlib
HERE = os.path.dirname(os.path.abspath(__file__)); LANE = os.path.dirname(HERE)
slug, rng = sys.argv[1], sys.argv[2]
gpu, tpu, rev = "--gpu" in sys.argv, "--tpu" in sys.argv, "--reverse" in sys.argv
tl = sys.argv[sys.argv.index("--tl") + 1] if "--tl" in sys.argv else "300"
hours = sys.argv[sys.argv.index("--hours") + 1] if "--hours" in sys.argv else "11.3"
src = {f: open(os.path.join(HERE, f)).read() for f in ("hyp.py", "cube_lib.py", "cube_run.py")}
import io, tarfile
MSRC = os.path.expanduser("<tools>/CnC/march_cu")
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tf:
    for fn in sorted(os.listdir(MSRC)):
        if fn == "Makefile" or fn.endswith(".c") or fn.endswith(".h"):
            tf.add(os.path.join(MSRC, fn), arcname=fn)
march_b64 = base64.b64encode(buf.getvalue()).decode()
march_sha = hashlib.sha256(buf.getvalue()).hexdigest()
raw = open(os.path.join(LANE, "runs", "cubes11", "cubes.icnf"), "rb").read()
b64, csha = base64.b64encode(zlib.compress(raw, 9)).decode(), hashlib.sha256(raw).hexdigest()
out = os.path.join(LANE, "kaggle", slug); os.makedirs(out, exist_ok=True)
run = f'''# Kaggle kernel {slug}: K11 cubes (R_5(C3;3) = 11), range {rng}, reverse={rev}, tl={tl}, with splitting.
import base64, hashlib, json, os, subprocess, sys, time, zlib
W = "/kaggle/working"; T = W + "/tools"; os.makedirs(T, exist_ok=True)
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True)
log = open(W + "/run.log", "a")
def say(s):
    line = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) + " " + s
    print(line, flush=True); log.write(line + "\\n"); log.flush()
say("NPROC " + str(os.cpu_count()) + " | " + sh("nproc; free -g | head -2; grep 'model name' /proc/cpuinfo | head -1").stdout.replace("\\n", " | "))
for f, s in json.loads({json.dumps(src)!r}).items(): open(T + "/" + f, "w").write(s)
r = sh(sys.executable + " -I " + T + "/hyp.py 11 C3L/C3L/C3L/C3L/C3L " + W + "/base.cnf --colswap --nonstar --hall 6,7,8,9")
bsha = hashlib.sha256(open(W + "/base.cnf").read().split("\\n", 1)[1].encode()).hexdigest()
say("base " + r.stdout.strip() + " body_sha256 " + bsha)
assert bsha == "d4ab1fce5ad2f39b0a0198f411926f3bee17f1a53e7b70d9a052e6992bf03204"
raw = zlib.decompress(base64.b64decode({b64!r}))
assert hashlib.sha256(raw).hexdigest() == "{csha}"
open(W + "/cubes.icnf", "wb").write(raw)
say("cadical " + sh("cd /tmp && git clone -q https://github.com/arminbiere/cadical && cd cadical && git checkout -q c60730422e758ef1cebe7aeddf2dda31c996bf04 && ./configure > /dev/null && make -j8 > /dev/null && ./build/cadical --version").stdout.strip())
say("drat-trim " + sh("cd /tmp && git clone -q https://github.com/marijnheule/drat-trim && cd drat-trim && git checkout -q 2e3b2dc0ecf938addbd779d42877b6ed69d9a985 && make > /dev/null && ls drat-trim").stdout.strip())
import io, tarfile
mt = base64.b64decode({march_b64!r})
assert hashlib.sha256(mt).hexdigest() == "{march_sha}"
os.makedirs("/tmp/march_src", exist_ok=True)
tarfile.open(fileobj=io.BytesIO(mt), mode="r:gz").extractall("/tmp/march_src")
mk = sh("cd /tmp/march_src && make CFLAGS='-O3 -fno-strict-aliasing -Wall -DNDEBUG -fcommon' 2>&1 | tail -3")
say("march_cu build: " + mk.stdout.strip()[-300:])
for b in ("/tmp/cadical/build/cadical", "/tmp/drat-trim/drat-trim", "/tmp/march_src/march_cu"):
    assert os.path.exists(b), "missing binary " + b
open("/tmp/tiny.cnf", "w").write("p cnf 3 4\\n1 2 0\\n-1 2 0\\n1 -2 0\\n-1 -2 3 0\\n")
say("march_cu self-test: " + sh("/tmp/march_src/march_cu /tmp/tiny.cnf -o /tmp/tiny.icnf; echo rc=$?").stdout.strip()[-200:])
os.makedirs("/tmp/cubes", exist_ok=True)
cmd = [sys.executable, "-I", T + "/cube_run.py", W + "/base.cnf", W + "/cubes.icnf", W + "/run", str(os.cpu_count()),
       "--range", "{rng}", "--tl", "{tl}", "--tmp", "/tmp/cubes", "--cad", "/tmp/cadical/build/cadical",
       "--dt", "/tmp/drat-trim/drat-trim", "--march", "/tmp/march_src/march_cu", "--hours", "{hours}", "--nonice"]
if {rev}: cmd.append("--reverse")
say("RUN " + " ".join(cmd))
r = subprocess.run(cmd, capture_output=True, text=True)
say("cube_run rc=" + str(r.returncode) + " " + r.stderr[-500:])
say(open(W + "/run/progress.log").read()[-2000:])
say("END")
'''
open(os.path.join(out, "run.py"), "w").write(run)
meta = {"id": f"arhancanli12/{slug}", "title": slug.replace("-", " "), "code_file": "run.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": gpu, "enable_tpu": tpu, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [], "kernel_sources": []}
if tpu: meta["machine_shape"] = "TpuV5E8"
json.dump(meta, open(os.path.join(out, "kernel-metadata.json"), "w"))
print("wrote", out, os.path.getsize(os.path.join(out, "run.py")))
