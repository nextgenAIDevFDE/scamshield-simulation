"""Telecom-side AI models: SMS scam classifier, call-transcript scam classifier,
caller-reputation model, and telco risk fusion. Returns trained models and evaluation metrics."""
import random, numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, make_union
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score, accuracy_score
import textgen as tg

def text_clf():
    return make_pipeline(
        make_union(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                   TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True)),
        LogisticRegression(C=4.0, max_iter=2000, class_weight="balanced"))

def prf(y, p, s):
    P, R, F, _ = precision_recall_fscore_support(y, p, average="binary", zero_division=0)
    return dict(precision=P, recall=R, f1=F, accuracy=accuracy_score(y, p), auc=roc_auc_score(y, s))

def caller_features(r, scam, n):
    """Synthetic caller metadata. Scam callers: young numbers, many distinct callees, short calls,
    skew to elderly callees, more spoof/intl flags. Large overlap on purpose."""
    rs = np.random.default_rng(r.randint(0, 10**9))
    if scam:
        age = rs.gamma(1.3, 180, n)             # days since number activation (incl. hijacked numbers)
        callees = rs.lognormal(2.4, 1.3, n)     # distinct callees / day
        dur = rs.lognormal(5.3, 1.0, n)         # mean call duration (s)
        eld = rs.beta(3, 4, n)                  # share of callees aged 65+
        spoof = rs.random(n) < 0.20
        intl = rs.random(n) < 0.20
        rep = rs.poisson(0.7, n)                # spam reports last 30d
    else:
        age = rs.gamma(2.0, 600, n)
        callees = rs.lognormal(1.4, 1.4, n)     # includes businesses / call centres
        dur = rs.lognormal(5.0, 1.0, n)
        eld = rs.beta(2, 4, n)
        spoof = rs.random(n) < 0.03
        intl = rs.random(n) < 0.08
        rep = rs.poisson(0.25, n)
    return np.c_[age, callees, dur, eld, spoof, intl, rep].astype(float)

def train(seed=0, sms_path="data/sms.tsv"):
    r = random.Random(seed)
    M = {}
    # ---------- SMS classifier: real UCI SMS Spam Collection + synthetic scam-intent SMS ----------
    d = pd.read_csv(sms_path, sep="\t", header=None, names=["l", "t"], quoting=3)
    d["y"] = (d.l == "spam").astype(int)
    tr, te = train_test_split(d, test_size=0.3, random_state=seed, stratify=d.y)
    syn = []
    for _ in range(2500):
        st = r.choice(tg.SCAM_TYPES)
        syn.append((tg.scam_sms(r, st, tg.rand_benef(r) if r.random() < 0.6 else None), 1))
        syn.append((tg.benign_sms(r), 0))
    syn = pd.DataFrame(syn, columns=["t", "y"])
    syn_tr, syn_te = train_test_split(syn, test_size=0.3, random_state=seed, stratify=syn.y)
    Xtr = pd.concat([tr[["t", "y"]], syn_tr])
    sms = text_clf().fit(Xtr.t, Xtr.y)
    M["sms"] = sms
    res = {}
    for name, df in [("uci_real_test", te), ("synthetic_scam_test", syn_te)]:
        s = sms.predict_proba(df.t)[:, 1]; res[name] = prf(df.y, (s >= .5).astype(int), s)
        res[name]["n"] = len(df)
    # scam-like subset of the real spam test messages (prize/claim, payment, account or urgency language)
    import re as _re
    rx = _re.compile(r"(?:won|win|winner|prize|claim|award|selected|cash|urgent|account|bank|refund|guarantee|pay|£|\$)", _re.I)
    sl = te[(te.y == 1) & te.t.str.contains(rx)]
    ps = sms.predict_proba(sl.t)[:, 1]
    res["uci_scamlike"] = dict(n=len(sl), share_of_test=len(sl) / len(te), share_of_spam=len(sl) / int(te.y.sum()),
                               recall=float((ps >= .5).mean()))
    M["sms_eval"] = res

    # ---------- Call transcript classifier (synthetic ASR-style transcripts) ----------
    rows = []
    for _ in range(6000):
        st = r.choice(tg.SCAM_TYPES)
        rows.append((tg.scam_call(r, st, tg.rand_benef(r) if r.random() < .65 else None), 1, st))
        rows.append((tg.benign_call(r, tg.rand_benef(r) if r.random() < .3 else None), 0, "benign"))
    cd = pd.DataFrame(rows, columns=["t", "y", "st"])
    ctr, cte = train_test_split(cd, test_size=0.3, random_state=seed, stratify=cd.y)
    call = text_clf().fit(ctr.t, ctr.y)
    s = call.predict_proba(cte.t)[:, 1]
    M["call"] = call
    M["call_eval"] = prf(cte.y, (s >= .5).astype(int), s) | {"n": len(cte)}
    # generalisation to an unseen scam type (leave-one-scam-type-out), threshold 0.5
    loso = {}
    for st in tg.SCAM_TYPES:
        trn = cd[(cd.st != st)]; tst = cd[(cd.st == st) | (cd.y == 0)].sample(frac=1, random_state=seed)
        tst = pd.concat([tst[tst.y == 1], tst[tst.y == 0].iloc[:(tst.y == 1).sum()]])
        trn = trn.drop(tst[tst.y == 0].index, errors="ignore")
        mdl = text_clf().fit(trn.t, trn.y); s = mdl.predict_proba(tst.t)[:, 1]
        loso[st] = prf(tst.y, (s >= .5).astype(int), s)
    M["call_loso"] = loso
    # scam-type classifier (for token's scam_type field)
    sc = cd[cd.y == 1]
    s_tr, s_te = train_test_split(sc, test_size=0.3, random_state=seed, stratify=sc.st)
    stype = text_clf().fit(s_tr.t, s_tr.st)
    M["stype"] = stype
    M["stype_acc"] = accuracy_score(s_te.st, stype.predict(s_te.t))

    # ---------- Caller reputation ----------
    Xs, Xb = caller_features(r, True, 8000), caller_features(r, False, 40000)
    X = np.r_[Xs, Xb]; y = np.r_[np.ones(len(Xs)), np.zeros(len(Xb))]
    a, b, ya, yb = train_test_split(X, y, test_size=.3, random_state=seed, stratify=y)
    rep = HistGradientBoostingClassifier(max_iter=200, random_state=seed).fit(a, ya)
    s = rep.predict_proba(b)[:, 1]
    M["rep"] = rep
    M["rep_eval"] = prf(yb, (s >= .5).astype(int), s)

    # ---------- Telco fusion (stacking) on independent synthetic calls ----------
    F, Y = [], []
    for i in range(6000):
        scam = i % 2 == 0
        st = r.choice(tg.SCAM_TYPES)
        optin = r.random() < 0.45
        has_sms = r.random() < (0.5 if scam else 0.3)
        sms_t = (tg.scam_sms(r, st) if scam else tg.benign_sms(r)) if has_sms else None
        tr_t = (tg.scam_call(r, st) if scam else tg.benign_call(r)) if optin else None
        F.append(fusion_vec(M, sms_t, tr_t, caller_features(r, scam, 1)[0])); Y.append(int(scam))
    F, Y = np.array(F), np.array(Y)
    fa, fb, ya, yb = train_test_split(F, Y, test_size=.3, random_state=seed, stratify=Y)
    fus = LogisticRegression(max_iter=1000).fit(fa, ya)
    s = fus.predict_proba(fb)[:, 1]
    # flag threshold: 1% false-flag rate on benign calls
    tau = float(np.quantile(s[yb == 0], 0.99))
    M["tau_m"] = float(np.quantile(s[yb == 0], 0.97))   # medium-confidence threshold (3% false flags)
    M["fusion"], M["tau"] = fus, tau
    M["fusion_eval"] = prf(yb, (s >= tau).astype(int), s) | {"tau": tau,
                        "false_flag_rate": float((s[yb == 0] >= tau).mean())}
    # recall by content availability
    has_tr = fb[:, 3] == 1
    M["fusion_eval"]["recall_with_transcript"] = float((s[(yb == 1) & has_tr] >= tau).mean())
    M["fusion_eval"]["recall_metadata_only"] = float((s[(yb == 1) & ~has_tr & (fb[:, 1] == 0)] >= tau).mean())
    return M

def fusion_vec(M, sms_t, tr_t, cf):
    ss = M["sms"].predict_proba([sms_t])[0, 1] if sms_t else 0.0
    ts = M["call"].predict_proba([tr_t])[0, 1] if tr_t else 0.0
    rs = M["rep"].predict_proba(cf.reshape(1, -1))[0, 1]
    return [ss, float(sms_t is not None), ts, float(tr_t is not None), rs]

def fusion_batch(M, sms_list, tr_list, CF):
    n = len(sms_list)
    ss = np.zeros(n); ts = np.zeros(n)
    i_s = [i for i, t in enumerate(sms_list) if t]; i_t = [i for i, t in enumerate(tr_list) if t]
    if i_s: ss[i_s] = M["sms"].predict_proba([sms_list[i] for i in i_s])[:, 1]
    if i_t: ts[i_t] = M["call"].predict_proba([tr_list[i] for i in i_t])[:, 1]
    rs = M["rep"].predict_proba(CF)[:, 1]
    hs = np.array([1.0 if t else 0.0 for t in sms_list]); ht = np.array([1.0 if t else 0.0 for t in tr_list])
    F = np.c_[ss, hs, ts, ht, rs]
    return M["fusion"].predict_proba(F)[:, 1], F
