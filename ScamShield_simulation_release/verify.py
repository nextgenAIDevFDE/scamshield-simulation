"""Compare a fresh run with the shipped raw outputs (timing fields excluded).

Exact check (pinned versions in requirements.txt, Python 3.13):
    python3 verify.py results/results.json expected/results.json
Headline check for other Python or library versions (compares the paper's main results, averaged over
the five runs, within a tolerance in percentage points):
    python3 verify.py --summary results/agg.json expected/agg.json --tol 1
"""
import json, sys

if "--summary" in sys.argv:
    files = [a for a in sys.argv[1:] if a.endswith(".json")]
    tol = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 1.0
    new, ref = (json.load(open(p))["results"] for p in files[:2])
    keys = [("loss_prev_base", 100, "loss prevented %"), ("held", 100, "scams held %"),
            ("intercepted", 100, "any intervention %"), ("gen_t3", 1e4, "genuine held /10k")]
    worst, bad = 0.0, 0
    print(f"{'System':30s}" + "".join(f"{lab:>22s}" for _, _, lab in keys))
    for m in ref:
        if m not in new: print("missing", m); bad += 1; continue
        cells = []
        for k, sc, _ in keys:
            a, b = new[m][k][0] * sc, ref[m][k][0] * sc
            d = abs(a - b); worst = max(worst, d); bad += d > tol
            cells.append(f"{a:8.1f} vs {b:6.1f}")
        print(f"{m:30s}" + "".join(f"{c:>22s}" for c in cells))
    print(f"\nLargest difference: {worst:.2f}; " + (f"ALL HEADLINE RESULTS WITHIN {tol}" if not bad else f"{bad} values differ by more than {tol}"))
    sys.exit(1 if bad else 0)

args = [a for a in sys.argv[1:] if not a.startswith("--")]
tol = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 0.0
if "--tol" in sys.argv: args = [a for a in args if a != sys.argv[sys.argv.index("--tol") + 1]]
new, ref = (json.load(open(p)) for p in args[:2])
bad, worst, n = 0, (0.0, ""), 0

def cmp(a, b, path):
    global bad, worst, n
    if isinstance(b, dict):
        for k in b:
            if k == "latency": continue
            if not isinstance(a, dict) or k not in a: print("missing", path + "/" + k); bad += 1; continue
            cmp(a[k], b[k], path + "/" + k)
    elif isinstance(b, (int, float)) and not isinstance(b, bool):
        n += 1
        d = abs(float(a) - float(b))
        # counts (sample sizes, integers > 1) are compared relative to their size
        if isinstance(b, int) and abs(b) > 1: d = d / abs(b)
        if d > worst[0]: worst = (d, path)
        if d > tol + 1e-12: bad += 1
    elif a != b: bad += 1

for seed in new:
    if seed not in ref: print("seed not in reference:", seed); bad += 1; continue
    cmp(new[seed], ref[seed], "seed" + seed)
if tol == 0:
    print("REPRODUCED EXACTLY" if bad == 0 else f"{bad} of {n} values differ; largest difference {worst[0]:.4g} at {worst[1]}"
          "\n(different Python or library versions? Install requirements.txt on Python 3.13 for an exact match, or compare"
          " the headline results: python3 verify.py --summary results/agg.json expected/agg.json --tol 1)")
else:
    print(f"WITHIN TOLERANCE {tol}" if bad == 0 else f"{bad} of {n} values exceed tolerance {tol}; largest {worst[0]:.4g} at {worst[1]}")
sys.exit(1 if bad else 0)
