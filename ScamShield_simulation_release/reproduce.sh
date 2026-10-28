#!/usr/bin/env bash
# Reproduce every simulation number, table and figure in the ScamShield paper.
# Requires: Python 3.10+ with numpy, pandas, scikit-learn, matplotlib; the UCI SMS Spam Collection at data/sms.tsv.
set -euo pipefail
mkdir -p results figs
[ -f data/sms.tsv ] || { echo "Missing data/sms.tsv (UCI SMS Spam Collection, tab-separated: label<TAB>text)"; exit 1; }
python3 sim2.py 0 1 2 3 4        # five independent runs (seeds 0-4); about 3 minutes each on 2 cores
python3 aggregate_v3.py          # mean ± SD across runs -> results/agg_v3.json, figs/c_fig4_sim.png
python3 verify.py results/results_v3.json expected/results_v3.json
python3 make_tables.py           # prints Tables XI and XII exactly as in the paper
python3 figs_concept.py          # framework diagrams (Figs. 1-3)
