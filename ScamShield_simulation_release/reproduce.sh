#!/usr/bin/env bash
# Reproduce every simulation number, table and figure in the ScamShield paper.
# Requires: Python 3.13 with the packages in requirements.txt; the UCI SMS Spam Collection at data/sms.tsv.
set -euo pipefail
mkdir -p results figs
[ -f data/sms.tsv ] || { echo "Missing data/sms.tsv (UCI SMS Spam Collection, tab-separated: label<TAB>text)"; exit 1; }
python3 simulate.py 0 1 2 3 4    # five independent runs (seeds 0-4) incl. sensitivity sweeps; about 7 minutes each on 2 cores
python3 aggregate.py             # mean ± SD across runs -> results/agg.json, figs/c_fig4_sim.png
python3 verify.py results/results.json expected/results.json   # prints REPRODUCED EXACTLY
python3 make_tables.py           # prints Tables XI and XII exactly as in the paper
python3 figs_concept.py          # framework diagrams (Figs. 1-3)
