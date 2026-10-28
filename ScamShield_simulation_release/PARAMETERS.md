# Simulation parameters (defaults used in the paper)

| Parameter | Value | Set in |
|---|---|---|
| Customers / share aged 65+ | 20,000 / 30% | `sim2.simulate(N=20000)`, `elderly` |
| Simulated period | 30 days | `simulate(DAYS=30)` |
| Scam episodes | 1,500 (elderly targeted 3x as often) | `simulate(EPISODES=1500)`, victim weights |
| Mule pool | 1,200 accounts, Pareto(2.5) reuse weights | `simulate(MULES=1200)` |
| Mule reporting | 50% of episodes reported, 1–5 day delay | mule registry block in `simulate` |
| Scam payment context | OTT 10% (investment 35%), unlinked line 5%, during call 70% (investment 40%), rest after call | episode loop in `simulate` |
| Genuine payments during a call | 15% for new payees; 6% / 9% (non-elderly / elderly) otherwise | genuine loop in `simulate` |
| On-device speech opt-in | 60% (65+) / 30% (others) | `optin` |
| Beneficiary conveyed | SMS 50% of scam contacts, ID included 60%; speech (opt-in) ID included 65% | `contact()` |
| Spoken digit errors | substitution 25%, adjacent transposition 6%; low-confidence marking 80% | `bene.spoken` |
| Candidate cap k_max | 20 | `bene.expand` |
| Flag thresholds | medium: 3% false flags, high: 1% false flags (telecom training data) | `telco_models.train` (`tau_m`, `tau`) |
| Bank model tiers | T1 riskiest 1%, T2 riskiest 0.3% of genuine payments (calibration set) | `sim2.model_tiers` |
| Call status + risk cut-off | riskiest 10% of genuine payments; sweep 2%, 5%, 10%, 20%, 50% | `sim2.evaluate` |
| Stop probability T1 / T2 / T3 | base 0.3 / 0.6 / 0.9; low 0.15 / 0.4 / 0.8; high 0.5 / 0.8 / 0.95 | `sim2.Q` |
| Metadata flag-rate sensitivity | keep 75% and 50% of scam flags | `sim2.evaluate` |
| Split | 40% train / 20% calibration / 40% test, by customer | `sim2.evaluate` |
| Seeds | 0–4 | command line |
