"""Aggregate the five runs in results/results_v3.json (mean ± SD across runs) and draw Fig. 4.
Every simulation number in the paper is read from the output of this script (results/agg_v3.json)."""
import json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = json.load(open("results/results_v3.json")); seeds = sorted(R)
def ms(get):
    v = np.array([get(R[s]) for s in seeds], float); return [float(v.mean()), float(v.std(ddof=1) if len(v) > 1 else 0.0)]
first = R[seeds[0]]
methods = list(first["results"]); keys = list(first["results"][methods[0]])
A = {"seeds": [int(s) for s in seeds],
     "results": {m: {k: ms(lambda d, m=m, k=k: d["results"][m][k]) for k in keys} for m in methods},
     "friction": {k: ms(lambda d, k=k: d["friction"][k]) for k in first["friction"]},
     "benef": {m: {k: ms(lambda d, m=m, k=k: d["benef"][m][k]) for k in ["exact", "any"]} for m in ["raw", "canon", "exp"]},
     "genuine_matches": {k: ms(lambda d, k=k: d["benef"][k]) for k in ["genuine_variant_matches", "genuine_exact_matches", "genuine_n"]},
     "flags": {p: {k: ms(lambda d, p=p, k=k: d["meta"]["flags"][p][k]) for k in first["meta"]["flags"][p]} for p in first["meta"]["flags"]},
     "cs_sweep": {x: {k: ms(lambda d, x=x, k=k: d["meta"]["cs_sweep"][x][k]) for k in first["meta"]["cs_sweep"][x]} for x in first["meta"]["cs_sweep"]},
     "meta": {k: ms(lambda d, k=k: d["meta"][k]) for k in ["n_payments", "n_scam", "n_test", "n_scam_test", "n_genuine_test", "share_elderly_scam", "mule_hit_scam"]},
     "ctx": {k: ms(lambda d, k=k: d["meta"]["ctx_scam"].get(k, 0)) for k in ["active_scam", "recent_scam", "ott", "unlinked"]},
     "lat": {k: ms(lambda d, k=k: d["latency"][k]) for k in ["bank_decision_ms", "oprf_ms", "telco_scoring_ms"]},
     "telco": {
        "sms_real": {k: ms(lambda d, k=k: d["telco"]["sms_eval"]["uci_real_test"][k]) for k in ["precision", "recall", "f1"]},
        "sms_real_n": ms(lambda d: d["telco"]["sms_eval"]["uci_real_test"]["n"]),
        "sms_scamlike": {k: ms(lambda d, k=k: d["telco"]["sms_eval"]["uci_scamlike"][k]) for k in ["n", "share_of_test", "share_of_spam", "recall"]},
        "sms_synth": {k: ms(lambda d, k=k: d["telco"]["sms_eval"]["synthetic_scam_test"][k]) for k in ["precision", "recall", "f1"]},
        "call_in": {k: ms(lambda d, k=k: d["telco"]["call_eval"][k]) for k in ["precision", "recall", "f1"]},
        "call_loso_recall": ms(lambda d: np.mean([v["recall"] for v in d["telco"]["call_loso"].values()])),
        "call_loso_precision": ms(lambda d: np.mean([v["precision"] for v in d["telco"]["call_loso"].values()])),
        "call_loso_min": ms(lambda d: min(v["recall"] for v in d["telco"]["call_loso"].values())),
        "rep_auc": ms(lambda d: d["telco"]["rep_eval"]["auc"])}}
json.dump(A, open("results/agg_v3.json", "w"), indent=1)

# ------------------------------------------------------------ Fig. 4
plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 7, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e"})
order = ["Bank ML", "Call-status rule", "Call-status + risk", "Mule risk feed", "ScamShield (full)"]
label = {"Bank ML": "Bank ML", "Call-status rule": "Call status (simple)", "Call-status + risk": "Call status + risk",
         "Mule risk feed": "Mule risk feed", "ScamShield (full)": "ScamShield"}
col = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
groups = [("intercepted", "Scam payments\nintercepted"), ("intercepted_elderly", "Intercepted\n(elderly)"), ("loss_prev_base", "Scam loss\nprevented")]
fig, ax = plt.subplots(figsize=(3.4, 2.3)); w = 0.16
for i, m in enumerate(order):
    v = [A["results"][m][k][0] * 100 for k, _ in groups]; e = [A["results"][m][k][1] * 100 for k, _ in groups]
    x = np.arange(len(groups)) + (i - 2) * w
    ax.bar(x, v, w * 0.9, yerr=e, color=col[i], label=label[m], capsize=1.0, error_kw={"lw": 0.5, "ecolor": "#52514e"},
           edgecolor="#fcfcfb", linewidth=0.6)
    for xx, vv in zip(x, v): ax.text(xx, vv + 1.5, f"{vv:.0f}", ha="center", va="bottom", fontsize=5.0, color="#0b0b0b")
ax.set_xticks(range(len(groups))); ax.set_xticklabels([g for _, g in groups])
ax.set_ylabel("% of scam payments / value"); ax.set_ylim(0, 112)
ax.yaxis.grid(True, color="#e5e4e0", lw=0.5); ax.set_axisbelow(True)
ax.legend(ncol=3, fontsize=5.8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.2), handlelength=1.0, columnspacing=0.8)
fig.savefig("figs/c_fig4_sim.png", dpi=300, bbox_inches="tight", pad_inches=0.02); plt.close(fig)

if __name__ == "__main__":
    for m in methods:
        d = A["results"][m]
        print(f"{m:32s} int {d['intercepted'][0]*100:5.1f}±{d['intercepted'][1]*100:.1f} held {d['held'][0]*100:5.1f} eld {d['intercepted_elderly'][0]*100:5.1f} "
              f"gen_any {d['gen_any'][0]*100:.2f} gen_t3/10k {d['gen_t3'][0]*1e4:.1f}±{d['gen_t3'][1]*1e4:.1f} loss {d['loss_prev_base'][0]*100:5.1f} prec {d['hold_precision'][0]*100:.1f}")
    print(json.dumps(A["flags"], indent=0)); print(json.dumps(A["cs_sweep"], indent=0)); print(A["telco"])
