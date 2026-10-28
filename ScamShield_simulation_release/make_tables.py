"""Print Tables XI and XII of the paper exactly as they appear, from results/agg.json.
Usage: python make_tables.py   (run aggregate.py first)"""
import json

A = json.load(open("results/agg.json")); R = A["results"]
f = lambda m, k, s=100, d=1: f"{R[m][k][0]*s:.{d}f}±{R[m][k][1]*s:.{d}f}"

print("TABLE XI  Simulation results over five runs (%, mean ± SD; genuine held per 10,000)")
rows = [("Bank ML", "Bank ML"), ("Call-status rule", "Call status, simple"), ("Call-status + risk", "Call status + risk"),
        ("Mule risk feed", "Mule risk feed"), ("ScamShield (metadata)", "ScamShield, metadata"),
        ("ScamShield (message)", "ScamShield, message"), ("ScamShield (full)", "ScamShield, full")]
print(f"{'System':24s}{'Intercepted':>14s}{'Elderly':>14s}{'Held':>14s}{'Gen. int.':>14s}{'Gen. held/10k':>16s}{'Loss prev.':>14s}")
for m, lab in rows:
    print(f"{lab:24s}{f(m,'intercepted'):>14s}{f(m,'intercepted_elderly'):>14s}{f(m,'held'):>14s}"
          f"{f(m,'gen_any',100,2):>14s}{f(m,'gen_t3',1e4):>16s}{f(m,'loss_prev_base'):>14s}")

print("\nTABLE XII  Beneficiary matching and ablation (%, mean ± SD)")
B = A["benef"]
rows = [("Full, exact raw match", "Exact match on raw text", "raw"), ("Full, canonical, no expansion", "Canonicalised, no variants", "canon"),
        ("ScamShield (full)", "Canonicalised + variants", "exp"), ("Full, no active-call rule", "Full, no active-call rule", "exp")]
print(f"{'Variant':30s}{'Matched':>14s}{'Held':>14s}{'Loss prev.':>14s}{'Gen. held/10k':>16s}")
for m, lab, k in rows:
    mt = f"{B[k]['any'][0]*100:.1f}±{B[k]['any'][1]*100:.1f}"
    print(f"{lab:30s}{mt:>14s}{f(m,'held'):>14s}{f(m,'loss_prev_base'):>14s}{f(m,'gen_t3',1e4):>16s}")
