# ScamShield simulation

Code, parameters, seeds and raw outputs for the paper "ScamShield: A Privacy-Preserving Telecom–Bank
Intelligence Framework for Real-Time Prevention of Call-Induced Authorised Scam Payments".

Real bank and telecom records are confidential and cannot be disclosed, so the paper is evaluated with an
agent-based simulation. This repository regenerates every simulation number, table and figure in the paper.

## Reproduce
1. Install **Python 3.13** and the pinned packages: `pip install -r requirements.txt`
   (the pinned versions need Python 3.13; check with `python3 --version`).
2. Download the UCI SMS Spam Collection (Almeida et al., 2011): https://archive.ics.uci.edu/dataset/228/sms+spam+collection
   Unzip it and save the file `SMSSpamCollection` as `data/sms.tsv`.
3. Run `bash reproduce.sh` (about 7 minutes per seed on 2 CPU cores, including the sensitivity sweeps).
   On Windows, run the commands in `reproduce.sh` one by one with `python` instead of `python3`.

## Check the results
- **Exact check** (Python 3.13 with the pinned versions): `python3 verify.py results/results.json expected/results.json`
  prints `REPRODUCED EXACTLY` when every value matches the shipped outputs (timing fields excluded).
- **Headline check** (any other Python or library versions): small numerical differences between library versions
  change individual values slightly, so compare the paper's headline results instead:
  `python3 verify.py --summary results/agg.json expected/agg.json --tol 1`
  It prints each system's loss prevented, share held, share intercepted and genuine holds next to the paper's
  values and confirms they agree within 1 percentage point. (On Python 3.9 with numpy 2.0, pandas 2.3 and
  scikit-learn 1.6 the largest difference we observed was 0.6 points.)
- `python3 make_tables.py` prints the main results table; compare with `expected/tables.txt`.

Quick test with one seed (about 7 minutes):
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
| `verify.py` | Compares a fresh run with the shipped outputs: exact check, or `--summary` headline check |
| `expected/` | Raw per-seed outputs, aggregated values and printed tables used in the paper |
| `PARAMETERS.md` | All simulation parameters and where they are set |
| `requirements.txt` | Pinned package versions |

Seeds: 0, 1, 2, 3, 4. Runs are deterministic: the same seed gives identical results on rerun.
Latency figures depend on the machine and are excluded from verification.

## License
MIT (see `LICENSE`). The SMS Spam Collection is not redistributed here; download it from the link above.
