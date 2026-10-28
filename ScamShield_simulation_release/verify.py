"""Check that a fresh run reproduces the shipped raw results exactly (timing fields excluded).
Usage: python verify.py results/results.json expected/results.json"""
import json, sys
new, ref = (json.load(open(p)) for p in sys.argv[1:3])
bad = 0
def cmp(a, b, path):
    global bad
    if isinstance(b, dict):
        for k in b:
            if k == "latency": continue
            if k not in a: print("missing", path + "/" + k); bad += 1; continue
            cmp(a[k], b[k], path + "/" + k)
    elif isinstance(b, (int, float)):
        if abs(float(a) - float(b)) > 1e-12: print("differs", path, a, b); bad += 1
    elif a != b: print("differs", path); bad += 1
for seed in new:
    if seed not in ref: print("seed not in reference:", seed); bad += 1; continue
    cmp(new[seed], ref[seed], "seed" + seed)
print("REPRODUCED EXACTLY" if bad == 0 else f"{bad} differences")
sys.exit(1 if bad else 0)
