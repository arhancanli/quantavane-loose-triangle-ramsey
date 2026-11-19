"""cube_merge.py: merge cube-and-conquer records (local and Kaggle results.jsonl files) and decide coverage.
v2 (19 Nov 2026, after referee 3): memo keyed by the node's literal list; a node with two DIFFERENT split records is
rejected as a split (it can still be covered by a verified leaf record); children are derived only from a node's
unique valid split.
A node (cube, path) with expected literals L is COVERED if it has a record with literals L, rc = 20, drat-trim
's VERIFIED' and CNF SHA-256 = SHA-256(BASE + L as units); or it has exactly one distinct valid split record (literals
L, cover drat-trim 's VERIFIED', cover CNF SHA-256 = SHA-256(BASE + L + negated sub-cubes)) and every child
(cube, path + [s]) with literals L + sub-cube s is covered. Exit 0 iff every cube of the cube file is covered and no
problem was found.
Usage: python3 -I cube_merge.py BASE.cnf CUBES.icnf RESULTS.jsonl [RESULTS2.jsonl ...]
"""
import hashlib, json, sys
from collections import defaultdict


def load(base, cubes):
    lines = open(base).read().split("\n")
    i = 0
    while lines[i].startswith("c"):
        i += 1
    nv, nc = int(lines[i].split()[2]), int(lines[i].split()[3])
    body = "\n".join(lines[i + 1:]).rstrip("\n") + "\n"
    cl = [[int(x) for x in l.split()[1:] if x != "0"] for l in open(cubes) if l.startswith("a ")]
    return nv, nc, body, cl


def merge(nv, nc, body, cl, record_lists):
    def node_sha(lits):
        return hashlib.sha256((f"p cnf {nv} {nc + len(lits)}\n" + body + "".join(f"{l} 0\n" for l in lits)).encode()).hexdigest()

    def cover_sha(lits, subs):
        s = (f"p cnf {nv} {nc + len(lits) + len(subs)}\n" + body + "".join(f"{l} 0\n" for l in lits) +
             "".join(" ".join(str(-l) for l in sub) + " 0\n" for sub in subs))
        return hashlib.sha256(s.encode()).hexdigest()

    recs = defaultdict(list)
    for rl in record_lists:
        for r in rl:
            recs[(r["cube"], tuple(r.get("path", [])))].append(r)
    problems, memo = [], {}
    stats = dict(leaves=0, splits=0, solve_s=0.0, check_s=0.0, proof_bytes=0)

    def unique_split(key, lits):
        """the node's unique valid split (sub-cube list) or None; records a problem if two differ."""
        found = {}
        for r in recs.get(key, []):
            sp = r.get("split")
            if r["lits"] != lits or not sp or sp.get("cover_drat") != ["s VERIFIED"] or not sp.get("subs"):
                continue
            if cover_sha(lits, sp["subs"]) != sp.get("cover_cnf_sha256"):
                problems.append((key, "cover CNF hash mismatch")); continue
            found[json.dumps(sp["subs"])] = sp
        if len(found) > 1:
            problems.append((key, "two different split records")); return None
        return next(iter(found.values())) if found else None

    def covered(cube, path, lits):
        mk = (cube, tuple(path), tuple(lits))
        if mk in memo:
            return memo[mk]
        memo[mk] = False
        key = (cube, tuple(path))
        for r in recs.get(key, []):
            if r["lits"] != lits:
                if r["rc"] == 20:
                    problems.append((key, "leaf literals do not match the cube tree"))
                continue
            if r["rc"] == 20 and r.get("drat_trim") == ["s VERIFIED"]:
                if node_sha(lits) != r["cnf_sha256"]:
                    problems.append((key, "node CNF hash mismatch")); continue
                stats["leaves"] += 1; stats["solve_s"] += r["solve_s"]; stats["check_s"] += r.get("check_s", 0)
                stats["proof_bytes"] += r.get("proof_bytes", 0)
                memo[mk] = True
                return True
        sp = unique_split(key, lits)
        if sp is not None and all(covered(cube, list(path) + [s], lits + sub) for s, sub in enumerate(sp["subs"])):
            stats["splits"] += 1; stats["proof_bytes"] += sp.get("cover_proof_bytes", 0)
            memo[mk] = True
            return True
        return False

    missing = [j for j in range(len(cl)) if not covered(j, [], list(cl[j]))]
    return missing, problems, stats


def main():
    nv, nc, body, cl = load(sys.argv[1], sys.argv[2])
    lists = [[json.loads(l) for l in open(p)] for p in sys.argv[3:]]
    missing, problems, st = merge(nv, nc, body, cl, lists)
    print(f"cubes={len(cl)} covered={len(cl) - len(missing)} missing={len(missing)} leaves={st['leaves']} "
          f"splits={st['splits']} solve_h={st['solve_s']/3600:.2f} check_h={st['check_s']/3600:.2f} "
          f"proof_GB={st['proof_bytes']/1e9:.2f} problems={len(problems)}")
    if problems:
        print("problems (first 10):", problems[:10])
    if missing:
        print("missing (first 10):", missing[:10])
    sys.exit(0 if not missing and not problems else 1)


if __name__ == "__main__":
    main()
