"""ScamShield simulation study.
Agent-based simulation of call-induced authorised scam payments, evaluating the v2 design
(confidence-graded flags, canonicalised + expanded beneficiary matching, mule registry,
decision matrix / Algorithm 1) against a bank-only model and two deployed-style baselines
(call-status rule; number/mule risk feed)."""
import os, sys, json, time, random
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
import textgen as tg, telco_models as tm, bene, oprf

CHANNELS = ["app", "web", "branch", "phone_banking", "wallet"]
Q = {"base": {1: 0.3, 2: 0.6, 3: 0.9}, "low": {1: 0.15, 2: 0.4, 3: 0.8}, "high": {1: 0.5, 2: 0.8, 3: 0.95}}

def simulate(seed, M, N=20000, DAYS=30, EPISODES=1500, MULES=1200, P_CALL=0.70):
    r = random.Random(seed); g = np.random.default_rng(seed)
    elderly = g.random(N) < 0.30
    optin = np.where(elderly, g.random(N) < 0.60, g.random(N) < 0.30)      # on-device speech analysis opt-in
    rate = g.lognormal(-0.6, 0.6, N); med = g.lognormal(4.0, 0.8, N)
    chpref = [g.dirichlet([3, 2, 2, 1.5, 1]) if e else g.dirichlet([5, 2, .5, .5, 2.5]) for e in elderly]
    mules = [bene.make_benef(r) for _ in range(MULES)]
    mule_w = g.pareto(2.5, MULES) + 1; mule_w /= mule_w.sum()               # some mules reused often
    rows, ctxs = [], []

    def contact(kind, cust, stype=None, benef=None, genuine_payee=None):
        """Returns telecom-visible evidence for the contact linked to a payment."""
        d = dict(kind=kind, sms=None, tr=None, low=set(), cf=None, mins=np.nan, conveyed=False)
        if kind in ("ott", "none", "unlinked"): return d
        scam = kind in ("active_scam", "recent_scam", "ignored_scam")
        if scam:
            if r.random() < 0.5:                                              # scam SMS
                txt = tg.scam_sms(r, stype)
                if benef and r.random() < 0.6:
                    w, _ = bene.written(r, *benef); txt += " " + w; d["conveyed"] = True
                d["sms"] = txt
            if optin[cust]:                                                    # on-device speech
                tr = tg.scam_call(r, stype)
                if benef and r.random() < 0.65:
                    s, low = bene.spoken(r, *benef); tr += " . " + s; d["low"] = low; d["conveyed"] = True
                d["tr"] = tr
        else:
            if r.random() < 0.3: d["sms"] = tg.benign_sms(r)
            if optin[cust]:
                tr = tg.benign_call(r)
                if genuine_payee and r.random() < 0.5:
                    s, low = bene.spoken(r, *genuine_payee); tr += " . " + s; d["low"] = low
                d["tr"] = tr
        d["cf"] = tm.caller_features(r, scam, 1)[0]
        d["mins"] = 0.0 if kind.startswith("active") else (g.uniform(5, 180) if kind != "ignored_scam" else g.uniform(30, 1440))
        return d

    # ---------------- genuine payments ----------------
    n_pay = g.poisson(rate * DAYS)
    for c in np.where(n_pay > 0)[0]:
        known = [bene.make_benef(r) for _ in range(r.randint(2, 8))]
        for _ in range(n_pay[c]):
            new = r.random() < (0.05 if elderly[c] else 0.08)
            pb = bene.make_benef(r) if new else r.choice(known)
            business = r.random() < 0.4
            amt = med[c] * (g.lognormal(1.5, 0.8) if r.random() < 0.05 else g.lognormal(0.3 if new else 0, 0.8))
            age = g.lognormal(7.0, 1.0) if (not new or r.random() < .80) else g.uniform(1, 90)
            fanin = g.lognormal(2.5, 1.2) if business else g.poisson(1.0)
            name = r.choices([1.0, 0.5, 0.0], [.90, .07, .03])[0]
            ch = CHANNELS[g.choice(5, p=chpref[c])]
            p_active = (0.15 if new else (0.09 if elderly[c] else 0.06))
            u = r.random()
            if u < p_active: kind = "active_benign"
            elif u < p_active + 0.25: kind = "recent_benign"
            elif u < p_active + 0.25 + (0.015 if elderly[c] else 0.008): kind = "ignored_scam"
            else: kind = "none"
            ctx = contact(kind, c, stype=r.choice(tg.SCAM_TYPES), genuine_payee=pb if new else None)
            rows.append(dict(cust=c, elderly=elderly[c], label=0, ep=-1, k=0, t=g.uniform(0, DAYS * 1440),
                             amount=amt, amt_ratio=amt / med[c], new_payee=int(new), payee_age=age, payee_fanin=fanin,
                             name_match=name, channel=ch, session_s=g.lognormal(4.3, 0.6) * (1.3 if elderly[c] else 1.0),
                             hesitation=g.lognormal(1.0, 0.7) * (1.4 if elderly[c] else 1.0),
                             app_switches=g.poisson(0.4 + (0.8 if kind == "active_benign" else 0)),
                             pasted=int(r.random() < (0.25 if new else 0.05)), payee=pb[1], stype="none", mule=-1))
            ctxs.append(ctx)

    # ---------------- scam episodes ----------------
    w = np.where(elderly, 3.0, 1.0); w /= w.sum()
    victims = g.choice(N, EPISODES, p=w)
    ep_info = []
    for e, c in enumerate(victims):
        st = r.choices(tg.SCAM_TYPES, [3, 2, 3, 2, 2, 1] if elderly[c] else [2, 1, 1, 2, 1, 4])[0]
        mi = int(g.choice(MULES, p=mule_w)); benef = mules[mi]
        u = r.random()
        age = g.uniform(1, 30) if u < .35 else (g.uniform(30, 180) if u < .60 else g.lognormal(6.5, 1))
        fanin = g.uniform(3, 40) if r.random() < .45 else g.poisson(1.0)
        name = r.choices([0.0, 0.5, 1.0], [.45, .25, .30])[0]
        k = int(g.geometric(0.55))
        t0 = g.uniform(0, DAYS * 1440 - 3000)
        ep_info.append((e, mi, t0))
        for j in range(k):
            amt = med[c] * (g.lognormal(0.4 + 0.5 * j, 0.8) if st == "investment" else g.lognormal(0.9, 0.9))
            ch = CHANNELS[g.choice(5, p=chpref[c])] if r.random() < .5 else r.choice(["app", "web", "app"])
            ott = 0.35 if st == "investment" else 0.10
            act = (0.40 * P_CALL / 0.70) if st == "investment" else P_CALL   # share paid during the scam call
            u = r.random()
            kind = ("ott" if u < ott else "unlinked" if u < ott + 0.05 else
                    "active_scam" if u < ott + 0.05 + act else "recent_scam")
            ctx = contact(kind, c, stype=st, benef=benef)
            rows.append(dict(cust=c, elderly=elderly[c], label=1, ep=e, k=j, t=t0 + j * g.uniform(20, 1440),
                             amount=amt, amt_ratio=amt / med[c], new_payee=int(j == 0), payee_age=age + j, payee_fanin=fanin,
                             name_match=name, channel=ch, session_s=g.lognormal(4.45, 0.65) * (1.3 if elderly[c] else 1.0),
                             hesitation=g.lognormal(1.15, 0.75) * (1.4 if elderly[c] else 1.0),
                             app_switches=g.poisson(0.9 if kind == "active_scam" else 0.45),
                             pasted=int(r.random() < (0.30 if j == 0 else 0.1)), payee=benef[1], stype=st, mule=mi))
            ctxs.append(ctx)
    df = pd.DataFrame(rows)
    df["ctx"] = [x["kind"] for x in ctxs]
    df["call_active"] = df.ctx.isin(["active_scam", "active_benign"]).astype(int)
    df["mins_since"] = [x["mins"] for x in ctxs]
    df["conveyed"] = [int(x["conveyed"]) for x in ctxs]

    # ---------------- mule registry (confirmed reports with delay) ----------------
    reg = {}
    for e, mi, t0 in ep_info:
        if r.random() < 0.5:
            tr_ = t0 + g.uniform(1, 5) * 1440
            reg[mi] = min(reg.get(mi, 1e18), tr_)
    df["mule_hit_true"] = [int(m >= 0 and reg.get(m, 1e18) < t) for m, t in zip(df.mule, df.t)]
    # false reports: each genuine payee account gets a uniform draw u and a listing time; it is (wrongly)
    # listed in the registry if u < false-report rate (applied in evaluate). Separate RNG keeps other draws unchanged.
    gf = np.random.default_rng(seed + 1000)
    gp = df.loc[df.label == 0, "payee"].unique()
    fu = dict(zip(gp, gf.random(len(gp)))); ft = dict(zip(gp, gf.uniform(0, DAYS * 1440, len(gp))))
    df["fr_u"] = [fu.get(p, 1.0) if lab == 0 else 1.0 for p, lab in zip(df.payee, df.label)]
    df["fr_t"] = [ft.get(p, 1e18) if lab == 0 else 1e18 for p, lab in zip(df.payee, df.label)]

    # ---------------- telecom side, three profiles ----------------
    idx = [i for i, x in enumerate(ctxs) if x["cf"] is not None]
    CF = np.array([ctxs[i]["cf"] for i in idx])
    prof = {"meta": ([None] * len(idx), [None] * len(idx)),
            "msg": ([ctxs[i]["sms"] for i in idx], [None] * len(idx)),
            "full": ([ctxs[i]["sms"] for i in idx], [ctxs[i]["tr"] for i in idx])}
    payee = df.payee.values
    for pname, (S, TR) in prof.items():
        risk, _ = tm.fusion_batch(M, S, TR, CF)
        rr = np.zeros(len(df)); rr[idx] = risk
        conf = np.where(rr >= M["tau"], 2, np.where(rr >= M["tau_m"], 1, 0))
        conf[~np.isin(np.arange(len(df)), idx)] = 0
        within = df.mins_since.fillna(1e9).values <= 1440
        flag = np.where(conf > 0, np.where(df.call_active.values == 1, 2, np.where(within, 1, 0)), 0)
        conf = np.where(flag > 0, conf, 0)
        df[f"flag_{pname}"] = flag; df[f"conf_{pname}"] = conf
        df[f"rec_{pname}"] = np.where(flag == 0, 0, np.where(df.mins_since.fillna(1e9).values < 60, 1, 2))
        # beneficiary candidates by matching method
        for mname in (["raw", "canon", "exp"] if pname == "full" else (["exp"] if pname == "msg" else [])):
            match = np.zeros(len(df), int)
            for i in np.where(flag > 0)[0]:
                x = ctxs[i]; srcs = [(x["sms"], set())] + ([(x["tr"], x["low"])] if pname == "full" else [])
                ex, va = set(), set()
                for txt, low in srcs:
                    if not txt: continue
                    if mname == "raw":
                        ex |= set(bene.extract_raw(txt))
                    else:
                        for c in bene.extract(txt):
                            if mname == "canon":
                                if not (len(c) == 22 and c[:2].isalpha()) or bene.iban_valid(c): ex.add(c)
                            else:
                                for cc, lab in bene.expand(c, low if txt is x["tr"] else set()):
                                    (ex if lab == "exact" else va).add(cc)
                pv = payee[i] if "@" in payee[i] else payee[i].upper()
                match[i] = 2 if pv in ex else (1 if pv in va else 0)
            df[f"match_{pname}_{mname}"] = match
    return df

BANK = ["amount", "amt_ratio", "new_payee", "payee_age", "payee_fanin", "name_match", "ch_i",
        "session_s", "hesitation", "app_switches", "pasted"]

def ans_feats(df, p, mname):
    m = df[f"match_{p}_{mname}"] if mname else 0
    return pd.DataFrame({"a_flag": df[f"flag_{p}"], "a_conf": df[f"conf_{p}"], "a_rec": df[f"rec_{p}"],
                         "a_match": np.maximum(m, 2 * df.mule_hit)}, index=df.index)

def model(tr, feats):
    m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_leaf_nodes=31,
                                       class_weight={0: 1, 1: 5}, random_state=0)
    return m.fit(tr[feats], tr.label)

def model_tiers(m, cal, te, feats, f1=0.01, f2=0.003, return_cal=False):
    sc = m.predict_proba(cal[feats])[:, 1]; g0 = sc[cal.label.values == 0]
    t1, t2 = np.quantile(g0, 1 - f1), np.quantile(g0, 1 - f2)
    s = m.predict_proba(te[feats])[:, 1]
    t = np.where(s >= t2, 2, np.where(s >= t1, 1, 0))
    return (t, s, g0) if return_cal else (t, s)

def algorithm1(tm_, A, new):
    fl, cf, mt = A.a_flag.values, A.a_conf.values, A.a_match.values
    t = tm_.copy()
    act = fl == 2; end = fl == 1
    t = np.where(act, np.maximum(t, 1), t)
    t = np.where(end & (new == 1), np.maximum(t, 1), t)
    t = np.where(end & (mt == 1), np.maximum(t, 2), t)
    t = np.where(act & (new == 1) & (cf == 1), np.maximum(t, 2), t)
    t = np.where(act & (new == 1) & (cf == 2), 3, t)
    t = np.where(act & (mt == 1), 3, t)
    t = np.where(mt == 2, 3, t)
    return t

def losses(te, tier, q):
    """Expected share of scam value saved. Payments of an episode are walked in order; an
    intervention at tier t stops the episode with probability q[t] (the payment and all later
    ones are then saved); otherwise the payment is lost and the episode continues."""
    s = te[te.label == 1].assign(tier=tier[te.label.values == 1]).sort_values(["ep", "k"])
    lost = tot = lost_e = tot_e = 0.0
    for _, grp in s.groupby("ep"):
        S = 1.0; eld = bool(grp.elderly.iloc[0])
        for amt, tt in zip(grp.amount.values, grp.tier.values):
            qq = q[tt] if tt > 0 else 0.0
            tot += amt; tot_e += amt * eld
            lost += amt * S * (1 - qq); lost_e += amt * S * (1 - qq) * eld
            S *= (1 - qq)
    return 1 - lost / tot, 1 - lost_e / tot_e

def metrics(te, tier):
    y = te.label.values == 1; e = te.elderly.values
    d = dict(intercepted=(tier[y] > 0).mean(), held=(tier[y] == 3).mean(),
             intercepted_elderly=(tier[y & e] > 0).mean(), intercepted_nonelderly=(tier[y & ~e] > 0).mean(),
             gen_any=(tier[~y] > 0).mean(), gen_t2=(tier[~y] >= 2).mean(), gen_t3=(tier[~y] == 3).mean(),
             hold_precision=(tier[y] == 3).sum() / max((tier == 3).sum(), 1))
    for c in ["active_scam", "recent_scam", "ott", "unlinked"]:
        m = y & (te.ctx.values == c); d["int_" + c] = (tier[m] > 0).mean()
    for k, q in Q.items():
        lp, lpe = losses(te, tier, q); d[f"loss_prev_{k}"] = lp; d[f"loss_prev_elderly_{k}"] = lpe
    return d

FALSE_REPORT = 0.001   # share of genuine payee accounts wrongly listed in the mule registry

def apply_registry(df, fr):
    """Registry hit = confirmed mule listed before the payment, or a genuine payee wrongly listed before it.
    After a wrongly listed payee is held once and confirmed genuine, it is trusted for that customer."""
    false = (df.label.values == 0) & (df.fr_u.values < fr) & (df.fr_t.values < df.t.values)
    d = df.assign(_f=false.astype(int))
    first = d[d._f == 1].sort_values("t").groupby(["cust", "payee"]).head(1).index
    fh = np.zeros(len(df), int); fh[df.index.get_indexer(first)] = 1
    return np.maximum(df.mule_hit_true.values, fh)

LIGHT = ["Bank ML", "Call-status rule", "Call-status + risk", "Mule risk feed", "ScamShield (full)", "ScamShield (metadata)"]

def evaluate(df, fr=FALSE_REPORT, light=False):
    df = df.copy().reset_index(drop=True); df["ch_i"] = df.channel.map({c: i for i, c in enumerate(CHANNELS)})
    df["mule_hit"] = apply_registry(df, fr)
    custs = df.cust.unique(); rng = np.random.default_rng(7); rng.shuffle(custs)
    n = len(custs); trc, cac = set(custs[: int(.4 * n)]), set(custs[int(.4 * n): int(.6 * n)])
    tr = df[df.cust.isin(trc)]; ca = df[df.cust.isin(cac)]
    te = df[~df.cust.isin(trc | cac)].reset_index(drop=True)
    R = {}
    rs = np.random.default_rng(11)
    for rho in ((0.75, 0.5) if not light else ()):
        p = f"metaR{int(rho*100)}"
        keep = ~((df.label.values == 1) & (df.flag_meta.values > 0) & (rs.random(len(df)) > rho))
        for c in ("flag", "conf", "rec"): df[f"{c}_{p}"] = np.where(keep, df[f"{c}_meta"].values, 0)
    tr = df[df.cust.isin(trc)]; ca = df[df.cust.isin(cac)]
    te = df[~df.cust.isin(trc | cac)].reset_index(drop=True)
    # bank-only model
    mb = model(tr, BANK); tb, sb, g0 = model_tiers(mb, ca, te, BANK, return_cal=True)
    R["Bank ML"] = metrics(te, tb)
    # deployed-style baseline A (lower bound): call-status rule (any call in progress + new payee -> hold)
    oncall_new = (te.call_active.values == 1) & (te.new_payee.values == 1)
    ta = tb.copy(); ta[oncall_new] = 3
    R["Call-status rule"] = metrics(te, ta)
    # deployed-style baseline A' (fairer): call + new payee + bank risk score in the top x% of genuine payments
    cs_sweep = {}
    for x in (0.02, 0.05, 0.10, 0.20, 0.50):
        thr = np.quantile(g0, 1 - x); tx = tb.copy(); tx[oncall_new & (sb >= thr)] = 3
        mx = metrics(te, tx); cs_sweep[x] = {k: mx[k] for k in ["intercepted", "held", "gen_t3", "loss_prev_base", "intercepted_elderly"]}
        if x == 0.10: R["Call-status + risk"] = mx
    # deployed-style baseline B: number / mule risk feed (reported payee -> hold)
    tbb = tb.copy(); tbb[te.mule_hit.values == 1] = 3
    R["Mule risk feed"] = metrics(te, tbb)
    # ScamShield variants
    def ss(name, p, mname, rule=True):
        X = lambda d: pd.concat([d[BANK], ans_feats(d, p, mname)], axis=1).assign(label=d.label.values)
        Xtr, Xca, Xte = X(tr), X(ca), X(te); feats = BANK + ["a_flag", "a_conf", "a_rec", "a_match"]
        m = model(Xtr, feats); tmod, _ = model_tiers(m, Xca, Xte, feats)
        A = ans_feats(te, p, mname)
        t = algorithm1(tmod, A, te.new_payee.values) if rule else np.where(A.a_match.values == 2, 3, tmod)
        R[name] = metrics(te, t)
        return t, m, feats
    t_full, m_full, feats_full = ss("ScamShield (full)", "full", "exp")
    ss("ScamShield (metadata)", "meta", None)
    if light:
        return {k: R[k] for k in LIGHT}
    ss("ScamShield (message)", "msg", "exp")
    ss("Metadata, 75% of scam flags", "metaR75", None)
    ss("Metadata, 50% of scam flags", "metaR50", None)
    ss("Full, exact raw match", "full", "raw")
    ss("Full, canonical, no expansion", "full", "canon")
    ss("Full, no active-call rule", "full", "exp", rule=False)
    # friction check for the high-confidence active-call rule
    g = te[te.label == 0]
    linked = g[g.ctx.isin(["active_benign", "recent_benign", "ignored_scam"])]
    benign_c = g[g.ctx.isin(["active_benign", "recent_benign"])]
    f_hat = (benign_c.conf_full == 2).mean()
    q_call = (g.call_active == 1).mean(); q_new = (g.new_payee == 1).mean()
    rule_t3 = ((g.flag_full == 2) & (g.conf_full == 2) & (g.new_payee == 1) & (g.ctx == "active_benign")).mean()
    cs_t3 = ((g.call_active == 1) & (g.new_payee == 1)).mean()
    q_cn = ((g.call_active == 1) & (g.new_payee == 1)).mean()
    fric = dict(f_hat=f_hat, q_call=q_call, q_new=q_new, q_call_and_new=q_cn, predicted=f_hat * q_cn, measured=rule_t3,
                callstatus_measured=cs_t3)
    # beneficiary matching (scam payments with flagged contact where the scammer conveyed the beneficiary)
    s = te[(te.label == 1) & (te.flag_full > 0) & (te.conveyed == 1)]
    bm = {m: dict(exact=float((s[f"match_full_{m}"] == 2).mean()), any=float((s[f"match_full_{m}"] > 0).mean()))
          for m in ["raw", "canon", "exp"]}
    bm["n"] = len(s)
    gg = te[te.label == 0]
    bm["genuine_variant_matches"] = int((gg.match_full_exp == 1).sum()); bm["genuine_exact_matches"] = int((gg.match_full_exp == 2).sum())
    bm["genuine_n"] = len(gg)
    sc_c = df[(df.label == 1) & df.ctx.isin(["active_scam", "recent_scam"])]
    bn_c = df[(df.label == 0) & df.ctx.isin(["active_benign", "recent_benign"])]
    flags = {p: dict(scam_any=float((sc_c[f"conf_{p}"] > 0).mean()), scam_high=float((sc_c[f"conf_{p}"] == 2).mean()),
                     benign_any=float((bn_c[f"conf_{p}"] > 0).mean()), benign_high=float((bn_c[f"conf_{p}"] == 2).mean()))
             for p in ["meta", "msg", "full"]}
    meta = dict(flags=flags, cs_sweep=cs_sweep, n_test=len(te), n_scam_test=int(te.label.sum()), n_genuine_test=int((te.label == 0).sum()),
                tiers_full=pd.crosstab(t_full, te.label.values).to_dict())
    return R, fric, bm, meta, (m_full, feats_full, te)

def latency(M, mf, n=2000):
    m_full, feats, te = mf
    store = {f"c{i}": {"flag": 2, "conf": 2, "benef": {f"b{i}"}} for i in range(100000)}
    X = te.assign(**{k: 0 for k in ["a_flag", "a_conf", "a_rec", "a_match"]})[feats].head(n)
    t0 = time.perf_counter()
    for i in range(n):
        tok = store.get(f"c{i}"); _ = tok and (f"b{i}" in tok["benef"])
        m_full.predict_proba(X.iloc[[i]])
    bank_ms = (time.perf_counter() - t0) / n * 1000
    k, sh = oprf.keygen_shares(); t0 = time.perf_counter()
    for i in range(40): oprf.pseudonym(f"GB29NWBK601613319268{i:02d}", sh)
    oprf_ms = (time.perf_counter() - t0) / 40 * 1000
    rr = random.Random(1); t0 = time.perf_counter()
    for _ in range(300):
        tm.fusion_batch(M, [tg.scam_sms(rr, "bank_impersonation")], [tg.scam_call(rr, "bank_impersonation")],
                        tm.caller_features(rr, True, 1))
    telco_ms = (time.perf_counter() - t0) / 300 * 1000
    return dict(bank_decision_ms=bank_ms, oprf_ms=oprf_ms, telco_scoring_ms=telco_ms)

if __name__ == "__main__":
    seeds = [int(s) for s in sys.argv[1:]] or [0]
    out = {}
    for sd in seeds:
        t0 = time.time()
        M = tm.train(sd)
        df = simulate(sd, M)
        R, fric, bm, meta, mf = evaluate(df)
        # sensitivity: false-report rate of the mule registry
        fr_sens = {fr: evaluate(df, fr=fr, light=True) for fr in (0.0, 0.01)}
        meta["genuine_registry_hits"] = int(((df.label == 0).values & (apply_registry(df, FALSE_REPORT) == 1)).sum())
        meta.update(n_payments=len(df), n_scam=int(df.label.sum()), share_elderly_scam=float(df[df.label == 1].elderly.mean()),
                    ctx_scam=df[df.label == 1].ctx.value_counts(normalize=True).to_dict(),
                    mule_hit_scam=float(df[df.label == 1].mule_hit_true.mean()))
        # sweep: share of scam payments made during the scam call (input parameter P_CALL)
        pcall = {}
        for p in (0.5, 0.3):
            d2 = simulate(sd, M, P_CALL=p)
            pcall[p] = dict(results=evaluate(d2, light=True), ctx=d2[d2.label == 1].ctx.value_counts(normalize=True).to_dict())
        tele = {k: M[k] for k in ["sms_eval", "call_eval", "call_loso", "rep_eval", "fusion_eval"]}
        g = df[df.label == 0]
        meta["genuine_call_share"] = float(g.call_active.mean())
        out[sd] = dict(results=R, friction=fric, benef=bm, meta=meta, telco=tele, latency=latency(M, mf),
                       fr_sensitivity=fr_sens, pcall_sweep=pcall)
        print(f"seed {sd} done in {time.time()-t0:.0f}s", flush=True)
        print(pd.DataFrame(R).T[["intercepted", "held", "intercepted_elderly", "gen_any", "gen_t3", "loss_prev_base"]].round(4).to_string(), flush=True)
        print(fric, bm, flush=True)
        os.makedirs("results", exist_ok=True)
        json.dump(out, open("results/results.json", "w"), indent=1, default=float)
