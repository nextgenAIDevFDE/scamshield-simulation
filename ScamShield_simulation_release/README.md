# ScamShield simulation

Code, parameters, seeds and raw outputs for the paper "ScamShield: A Privacy-Preserving Telecom–Bank
Intelligence Framework for Real-Time Prevention of Call-Induced Authorised Scam Payments".

Real bank and telecom records are confidential and cannot be disclosed, so the paper is evaluated with an
agent-based simulation. This repository regenerates every simulation number, table and figure in the paper.

## Reproduce
1. Python 3.13 and the pinned packages: `pip install -r requirements.txt`
2. Download the UCI SMS Spam Collection (Almeida et al., 2011): https://archive.ics.uci.edu/dataset/228/sms+spam+collection
   Unzip it and save the file `SMSSpamCollection` as `data/sms.tsv`.
3. Run `bash reproduce.sh` (about 7 minutes per seed on 2 CPU cores, including the sensitivity sweeps).
   On Windows, run the commands in `reproduce.sh` one by one with `python` instead of `python3`.
4. `verify.py` prints `REPRODUCED EXACTLY` when every value matches the shipped outputs in `expected/`
   (timing fields excluded). Exact agreement assumes the pinned package versions.
   `make_tables.py` prints Tables XI and XII exactly as in the paper; compare with `expected/tables.txt`.

Quick check with one seed (about 7 minutes):
```
mkdir -p results figs
python3 simulate.py 0
python3 verify.py results/results.json expected/results.json
```

## Contents
| File | Purpose |
|---|---|
| `simulate.py` | Agent-based simulation, bank-side models, Algorithm 1, baselines, metrics, sensitivity sweeps |
| `telco_models.py` | Telecom-side models: gradient-boosted caller reputation, TF-IDF + logistic regression for SMS and transcripts, logistic-regression fusion, flag thresholds |
| `textgen.py` | Template generator for scam and benign SMS and call transcripts (hand-written phrase banks; no language model, no speech recogniser) |
| `bene.py` | Valid IBANs, spoken rendering with digit errors, canonicalising extractor, bounded candidate expansion |
| `oprf.py` | 2HashDH OPRF over P-256 with a 2-of-3 threshold key, used only to measure latency (matching compares canonical identifiers, which is equivalent because the OPRF is deterministic) |
| `aggregate.py` | Mean ± SD across runs -> `results/agg.json`, Fig. 4 |
| `make_tables.py` | Prints Tables XI and XII from `results/agg.json` |
| `figs_concept.py` | Framework diagrams (Figs. 1–3) |
| `verify.py` | Compares a fresh run with the shipped raw outputs |
| `expected/` | Raw per-seed outputs, aggregated values and printed tables used in the paper |
| `PARAMETERS.md` | All simulation parameters and where they are set |
| `requirements.txt` | Pinned package versions |

Seeds: 0, 1, 2, 3, 4. Runs are deterministic: the same seed gives identical results on rerun.
Latency figures depend on the machine and are excluded from verification.

## License
MIT (see `LICENSE`). The SMS Spam Collection is not redistributed here; download it from the link above.
