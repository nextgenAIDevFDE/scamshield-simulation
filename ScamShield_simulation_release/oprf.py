"""Minimal 2HashDH OPRF over NIST P-256 with a 2-of-3 threshold key, used only to measure the
cost of computing pseudonyms. Pure Python (no constant-time guarantees); an upper bound on latency."""
import hashlib, secrets

p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
a = p - 3
b = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
n = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551

def inv(x, m): return pow(x, -1, m)

def add(P, Q):
    if P is None: return Q
    if Q is None: return P
    (x1, y1), (x2, y2) = P, Q
    if x1 == x2 and (y1 + y2) % p == 0: return None
    if P == Q: l = (3 * x1 * x1 + a) * inv(2 * y1, p) % p
    else: l = (y2 - y1) * inv(x2 - x1, p) % p
    x3 = (l * l - x1 - x2) % p
    return (x3, (l * (x1 - x3) - y1) % p)

def mul(k, P):
    R = None
    while k:
        if k & 1: R = add(R, P)
        P = add(P, P); k >>= 1
    return R

def hash_to_curve(msg: bytes):
    """Try-and-increment (illustrative; RFC 9380 would be used in practice)."""
    ctr = 0
    while True:
        x = int.from_bytes(hashlib.sha256(msg + ctr.to_bytes(4, "big")).digest(), "big") % p
        y2 = (pow(x, 3, p) + a * x + b) % p
        y = pow(y2, (p + 1) // 4, p)
        if y * y % p == y2: return (x, y)
        ctr += 1

def keygen_shares(t=2, nsrv=3):
    k = secrets.randbelow(n - 1) + 1
    coef = [k] + [secrets.randbelow(n) for _ in range(t - 1)]
    shares = {i: sum(c * pow(i, j, n) for j, c in enumerate(coef)) % n for i in range(1, nsrv + 1)}
    return k, shares

def lagrange(ids):
    lam = {}
    for i in ids:
        num = den = 1
        for j in ids:
            if j != i: num = num * (-j) % n; den = den * (i - j) % n
        lam[i] = num * inv(den, n) % n
    return lam

def pseudonym(x: str, shares, ids=(1, 2)):
    H1 = hash_to_curve(x.encode())
    rb = secrets.randbelow(n - 1) + 1
    B = mul(rb, H1)                                   # client blinds
    resp = {i: mul(shares[i], B) for i in ids}        # each server evaluates its share
    lam = lagrange(list(ids)); Z = None
    for i in ids: Z = add(Z, mul(lam[i], resp[i]))    # client combines
    Z = mul(inv(rb, n), Z)                            # unblind -> k*H1(x)
    return hashlib.sha256(x.encode() + Z[0].to_bytes(32, "big")).hexdigest()[:32]

def direct(x: str, k):
    Z = mul(k, hash_to_curve(x.encode()))
    return hashlib.sha256(x.encode() + Z[0].to_bytes(32, "big")).hexdigest()[:32]

if __name__ == "__main__":
    import time
    k, sh = keygen_shares()
    assert pseudonym("GB29NWBK60161331926819", sh) == direct("GB29NWBK60161331926819", k) == pseudonym("GB29NWBK60161331926819", sh, (2, 3))
    t0 = time.perf_counter(); N = 50
    for i in range(N): pseudonym(f"4477009{i:05d}", sh)
    print("ms per threshold OPRF evaluation:", (time.perf_counter() - t0) / N * 1000)
