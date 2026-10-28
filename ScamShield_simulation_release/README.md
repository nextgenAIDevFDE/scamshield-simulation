# ScamShield: simulation study (code, parameters, seeds, raw outputs)

Anonymised artefact for the paper "ScamShield: A Privacy-Preserving Telecom–Bank Intelligence
Framework for Real-Time Prevention of Call-Induced Authorised Scam Payments".

Real bank and telecom records are confidential and cannot be disclosed, so the paper is evaluated
with an agent-based simulation. This repository contains everything needed to regenerate every
simulation number, table and figure in the paper.

## Reproduce
1. Python 3.10+ with numpy, pandas, scikit-learn and matplotlib.
2. Download the UCI SMS Spam Collection (Almeida et al., 2011; https://archive.ics.uci.edu/dataset/228/sms+spam+collection)
   and save it as `data/sms.tsv` (tab-separated: `label<TAB>text`, labels `ham`/`spam`).
3. Run `bash reproduce.sh` (about 2–3 minutes per seed on 2 CPU cores).
4. Check the result: `python3 verify.py results/results_v3.json expected/results_v3.json`
   prints `REPRODUCED EXACTLY` when every value matches the shipped outputs (timing fields excluded).
   `python3 make_tables.py` prints Tables XI and XII exactly as in the paper; compare with `expected/tables.txt`.

## Contents
| File | Purpose |
|---|---|
| `sim2.py` | Agent-based simulation, bank-side models, Algorithm 1, baselines, metrics (seeds given on the command line) |
| `telco_models.py` | Telecom-side models: caller reputation, SMS and speech classifiers, risk fusion, flag thresholds |
| `textgen.py` | Template generator for scam and benign SMS and call transcripts (hand-written phrase banks; no language model) |
| `bene.py` | Valid IBANs, spoken rendering with recognition errors, canonicalising extractor, bounded candidate expansion |
| `oprf.py` | 2HashDH OPRF over P-256 with a 2-of-3 threshold key (used only to measure latency) |
| `aggregate_v3.py` | Mean ± SD across runs -> `results/agg_v3.json`, Fig. 4 |
| `make_tables.py` | Prints Tables XI and XII from `results/agg_v3.json` |
| `figs_concept.py` | Framework diagrams (Figs. 1–3) |
| `verify.py` | Compares a fresh run with the shipped raw outputs |
| `expected/` | Raw per-seed outputs, aggregated values and printed tables used in the paper |
| `PARAMETERS.md` | All simulation parameters and where they are set |

Seeds: 0, 1, 2, 3, 4. Runs are deterministic: the same seed gives identical results on rerun.
Latency figures depend on the machine and are excluded from verification.
