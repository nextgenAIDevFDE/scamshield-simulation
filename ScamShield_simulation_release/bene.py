"""Beneficiary identifiers for ScamShield v2: valid IBAN generation, spoken rendering with
speech-recognition errors, extraction, canonicalisation, and bounded candidate expansion."""
import re, string

DIG = string.digits

def iban_valid(s):
    s = s.upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", s): return False
    t = s[4:] + s[:4]
    n = "".join(str(int(ch, 36)) for ch in t)
    return int(n) % 97 == 1

def make_iban(r):
    cc = r.choice(["GB", "DE", "FR", "NL", "ES", "IT", "IE", "BE"])
    bban = "".join(r.choice(string.ascii_uppercase) for _ in range(4)) + "".join(r.choice(DIG) for _ in range(14))
    t = bban + cc + "00"
    n = int("".join(str(int(ch, 36)) for ch in t))
    chk = 98 - n % 97
    return f"{cc}{chk:02d}{bban}"

def make_acct(r):
    return "".join(r.choice(DIG) for _ in range(r.choice([10, 11, 12, 14])))

def make_wallet(r):
    h = "".join(r.choice(string.ascii_lowercase) for _ in range(r.randint(5, 9))) + str(r.randint(10, 999))
    return h + "@" + r.choice(["pay", "wallet", "bank", "upi", "paylink"])

def make_benef(r):
    k = r.random()
    if k < 0.40: return ("iban", make_iban(r))
    if k < 0.75: return ("acct", make_acct(r))
    return ("wallet", make_wallet(r))

# ------------------------------------------------------------------ rendering
KW = {"iban": ["iban", "the safe account iban", "account"], "acct": ["account number", "a/c", "account"],
      "wallet": ["wallet id", "pay to", "payment id"]}

def written(r, kind, val):
    """Identifier as typed in an SMS: exact, sometimes grouped with spaces."""
    v = val
    if kind != "wallet" and r.random() < 0.4: v = " ".join(val[i:i + 4] for i in range(0, len(val), 4))
    return r.choice(KW[kind]) + " " + v, set()

def spoken(r, kind, val, p_sub=0.25, p_swap=0.06):
    """Identifier as recognised from speech. Returns (text, low-confidence digit positions in canonical form).
    One digit may be misrecognised (substitution) or two adjacent digits swapped; digits are read in
    groups and repeated digits are sometimes said as 'double d'."""
    v = list(val.upper() if kind != "wallet" else val)
    digpos = [i for i, ch in enumerate(v) if ch.isdigit()]
    low = set()
    if kind != "wallet" and digpos:
        u = r.random()
        if u < p_sub:
            i = r.choice(digpos); v[i] = r.choice([d for d in DIG if d != v[i]])
            if r.random() < 0.8: low.add(i)
        elif u < p_sub + p_swap:
            pairs = [i for i in digpos if i + 1 < len(v) and v[i + 1].isdigit() and v[i] != v[i + 1]]
            if pairs:
                i = r.choice(pairs); v[i], v[i + 1] = v[i + 1], v[i]
                if r.random() < 0.8: low.add(i)
        if r.random() < 0.5: low.add(r.choice(digpos))   # an unrelated low-confidence digit
    s = "".join(v)
    if kind == "wallet": return r.choice(KW[kind]) + " " + s, set()
    g = r.choice([3, 4]) if r.random() < 0.7 else len(s)
    parts = [s[i:i + g] for i in range(0, len(s), g)]
    out = []
    for p in parts:
        p = p.lower()
        if r.random() < 0.3:
            p = re.sub(r"(\d)\1", lambda m: f" double {m.group(1)} ", p, count=1)
        out.append(p.strip())
    return r.choice(KW[kind]) + " " + " ".join(out), low

# ------------------------------------------------------------------ extraction
KWRX = re.compile(r"(?:safe account iban|iban|account number|a/c|acct no|account|wallet id|pay to|payment id|transfer to)\s+", re.I)

def _spoken_to_compact(seg):
    seg = re.sub(r"\bdouble\s+(\d)", r"\1\1", seg, flags=re.I)
    seg = re.sub(r"\btriple\s+(\d)", r"\1\1\1", seg, flags=re.I)
    toks = seg.split(); out = ""
    for t in toks:
        if "@" in t: return t if not out else out
        if not re.fullmatch(r"[a-z0-9]{1,34}", t, re.I): break
        if any(c.isdigit() for c in t) or (not out and len(t) == 2) or (len(out) == 4 and len(t) == 4):
            out += t
            if len(out) >= 34: break
            continue
        break
    return out

def canon(kind_hint, s):
    s = re.sub(r"[\s\-\.]", "", s)
    if "@" in s: return s.lower()
    return s.upper()

def extract(text):
    """Canonicalising extractor: handles grouped digits and 'double d' spoken forms."""
    if not text: return []
    out = []
    for m in KWRX.finditer(text):
        seg = text[m.end(): m.end() + 80]
        c = _spoken_to_compact(seg)
        if not c: continue
        c = canon(None, c)
        if "@" in c and re.fullmatch(r"[a-z0-9]{3,}@[a-z]+", c): out.append(c)
        elif re.fullmatch(r"[A-Z]{2}\d{2}[A-Z]{4}\d{14}", c): out.append(c)
        elif re.fullmatch(r"\d{10,14}", c): out.append(c)
    return list(dict.fromkeys(out))

RAW = [re.compile(r"\b([a-z]{2}\d{2}[a-z]{4}\d{14})\b", re.I), re.compile(r"\b([a-z0-9]{3,}@(?:pay|wallet|bank|upi|paylink))\b", re.I),
       re.compile(r"(?:account|a/c|acct no|acct|account number)\s*(?:number)?\s*(\d{10,14})\b", re.I)]

def extract_raw(text):
    """Baseline extractor without canonicalisation (exact contiguous strings only)."""
    out = []
    for rx in RAW:
        for m in rx.findall(text or ""): out.append(m.lower() if "@" in m else m.upper())
    return list(dict.fromkeys(out))

# ------------------------------------------------------------------ candidate expansion
def expand(c, low, kmax=20):
    """Return list of (candidate, label). Exact candidate first (if valid); then variants at
    low-confidence digit positions (single substitutions, adjacent transpositions).
    IBAN candidates must pass the mod-97 check; at most kmax candidates."""
    is_iban = bool(re.fullmatch(r"[A-Z]{2}\d{2}[A-Z]{4}\d{14}", c))
    ok = (lambda x: iban_valid(x)) if is_iban else (lambda x: True)
    out = []
    if ok(c): out.append((c, "exact"))
    if "@" in c: return out
    pos = sorted(p for p in low if p < len(c) and c[p].isdigit())
    # for an invalid IBAN without confidence hints, try every digit position
    if is_iban and not ok(c) and not pos: pos = [i for i, ch in enumerate(c) if ch.isdigit()]
    var = []
    for p in pos:
        for d in DIG:
            if d != c[p]: var.append(c[:p] + d + c[p + 1:])
        for q in (p - 1, p + 1):
            if 0 <= q < len(c) and c[q].isdigit() and c[q] != c[p]:
                a, b = sorted((p, q)); var.append(c[:a] + c[b] + c[a] + c[b + 1:])
    seen = {c}
    for v in var:
        if v in seen or not ok(v): continue
        seen.add(v); out.append((v, "variant"))
        if len(out) >= kmax: break
    return out
