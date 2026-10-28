"""Synthetic text generators for scam / benign SMS and call transcripts,
plus beneficiary identifier generation and extraction."""
import random, re, string

SCAM_TYPES = ["bank_impersonation", "authority_impersonation", "family_emergency",
              "prize_refund", "tech_support", "investment"]

ORGS = ["your bank", "the bank fraud department", "customer security team", "the card services unit",
        "head office", "the payments division"]
AUTH = ["the police", "the tax office", "customs", "the cyber crime unit", "the court", "immigration"]
REL = ["your grandson", "your son", "your daughter", "your nephew", "your granddaughter"]
PRIZE = ["a lottery", "a lucky draw", "an insurance refund", "a tax refund", "an electricity bill refund",
         "a pension bonus"]
TECH = ["your computer", "your phone", "your internet connection", "your banking app", "your router"]
INV = ["crypto trading", "a gold scheme", "a forex platform", "a guaranteed return fund", "a share tip group"]
URG = ["immediately", "right now", "within the next hour", "today itself", "before the account is frozen",
       "urgently", "without delay"]
SECRET = ["do not tell anyone", "keep this confidential", "do not inform your family",
          "do not disconnect the call", "stay on the line", "do not speak to bank staff"]

def rand_iban(r):
    cc = r.choice(["GB", "DE", "FR", "NL", "ES", "IT", "IE", "BE"])
    return cc + "".join(r.choice(string.digits) for _ in range(2)) + "".join(
        r.choice(string.ascii_uppercase) for _ in range(4)) + "".join(r.choice(string.digits) for _ in range(14))

def rand_acct(r):
    return "".join(r.choice(string.digits) for _ in range(r.choice([10, 11, 12, 14])))

def rand_wallet(r):
    h = "".join(r.choice(string.ascii_lowercase) for _ in range(r.randint(5, 9))) + str(r.randint(10, 999))
    return h + "@" + r.choice(["pay", "wallet", "bank", "upi", "paylink"])

def rand_benef(r):
    k = r.random()
    if k < 0.35: return ("iban", rand_iban(r))
    if k < 0.70: return ("acct", rand_acct(r))
    return ("wallet", rand_wallet(r))

def benef_phrase(r, kind, val):
    if kind == "iban": return r.choice(["IBAN ", "account ", "safe account IBAN "]) + val
    if kind == "acct": return r.choice(["account number ", "a/c ", "acct no ", "account "]) + val
    return r.choice(["wallet ID ", "pay to ", "payment ID ", "transfer to "]) + val

def scam_sms(r, stype, benef=None):
    b = (" " + benef_phrase(r, *benef)) if benef else ""
    T = {
        "bank_impersonation": [
            "Dear customer your account is suspended due to suspicious activity. Move funds to secure account{b} {u}.",
            "ALERT from {o}: unauthorised login detected. To protect savings transfer balance to safe account{b} {u}.",
            "{o}: your card is blocked. Verify KYC and transfer to holding account{b} {u} or lose access.",
            "Security notice: we are protecting your money. Transfer to the protected account{b} and {s}."],
        "authority_impersonation": [
            "This is {a}. A case is registered against your ID. Pay the security deposit{b} {u} to avoid arrest.",
            "{a} notice: unpaid penalty found. Settle{b} {u} else legal action. {s}.",
            "Final warning from {a}. Your parcel contains illegal items. Pay clearance fee{b} {u}."],
        "family_emergency": [
            "Hi Grandma its me, lost my phone this is my new number. I am in trouble please send money{b} {u}. {s}.",
            "Mum I had an accident and need to pay the hospital{b} {u}. Please dont call dad.",
            "Hello it's {rel_s}. Stuck abroad, wallet stolen. Send money{b} {u}, will explain later.",
            "Hi mum this is my new number, save it. Can you text me back when you are free?",
            "Hey dad its me, phone broke, using a friends phone. Can you help me with something today?"],
        "prize_refund": [
            "Congratulations! You have won {p}. Pay processing fee{b} {u} to claim your prize.",
            "You are eligible for {p}. To receive it pay small verification charge{b} {u}.",
            "WINNER! Claim {p} now. Transfer release fee{b}. Offer expires {u}."],
        "tech_support": [
            "Virus detected on {t}. Call support and install remote helper app. Refund charge{b} {u}.",
            "Your subscription will auto renew for 299. To cancel and get refund install support app and transfer{b} {u}.",
            "Microsoft-style support: {t} is hacked. Our engineer will connect remotely. Pay fix fee{b} {u}."],
        "investment": [
            "Earn 40% monthly guaranteed with {i}. Deposit{b} {u} to start, limited slots.",
            "Exclusive {i} invite. Minimum deposit to wallet{b}. Profits doubled {u}.",
            "Your {i} account shows profit. Pay tax to withdraw{b} {u}.",
            "Hi, nice chatting yesterday. My uncle's fund is doing well this month, want me to add you?"],
    }
    t = r.choice(T[stype])
    return t.format(b=b, u=r.choice(URG), s=r.choice(SECRET), o=r.choice(ORGS), a=r.choice(AUTH),
                    p=r.choice(PRIZE), t=r.choice(TECH), i=r.choice(INV),
                    rel_s=r.choice(REL).replace("your ", "your "))

BENIGN_SMS = [
    "Your OTP for login is {n}. Do not share it with anyone including bank staff.",
    "Rs/EUR {amt} debited from your account ending {n4} for electricity bill. Not you? Call your bank.",
    "Your parcel has been delivered. Thank you for shopping with us.",
    "Hi mum, landed safely, will call you tonight.",
    "Reminder: your doctor appointment is tomorrow at {h} am.",
    "Thanks for the lunch today, I transferred my share to your account.",
    "Dear customer, salary of {amt} credited to your account ending {n4}.",
    "Your pension of {amt} has been credited. Have a nice day.",
    "Can you send me the plumber's number? The kitchen tap is leaking again.",
    "Payment of {amt} received for invoice {n4}. Thank you for your business.",
    "Your monthly statement is ready to view in the app.",
    "Hey, can you pay the rent to the landlord account this week? I'll pay you back.",
    "Grandpa, happy birthday! Love you, see you on Sunday.",
    "Your card ending {n4} was used at the grocery store for {amt}.",
    "We noticed a login from a new device. If this was you, no action is needed.",
    "Please transfer the school fee {amt} to the school account before Friday.",
    "Your new card has been dispatched and will arrive in 5 working days.",
    "Fraud alert: did you attempt a payment of {amt} at an online store? Reply YES or NO. We will never ask you to move money.",
    "Your account security settings were updated. If this was not you call the number on the back of your card.",
    "Your tax refund of {amt} has been processed and will be credited within 5 days.",
    "Urgent: your water bill is overdue, please pay {amt} by Friday to avoid a late fee.",
    "Mum can you send me {amt} for the train ticket? I'll pay you back next week.",
]

def benign_sms(r):
    return r.choice(BENIGN_SMS).format(n=r.randint(100000, 999999), n4=r.randint(1000, 9999),
                                        amt=r.randint(10, 3000), h=r.randint(8, 11))

# ---------------- call transcripts (ASR-style, lowercase) ----------------
SCAM_CALL = {
    "bank_impersonation": [
        "hello i am calling from {o} we detected fraudulent transactions on your account",
        "your money is not safe someone inside the bank is involved",
        "to protect your savings you must move the funds to a safe account",
        "i will give you the safe account details {b}",
        "{s} this is a confidential investigation",
        "open your banking app and add the new payee now",
        "if the app asks you why you are paying choose paying family",
        "do not worry this is completely normal procedure"],
    "authority_impersonation": [
        "this is officer calling from {a} there is a warrant in your name",
        "your identity was used for money laundering",
        "to clear your name you must pay a refundable security deposit",
        "the deposit account is {b}", "{s} or you will be arrested today",
        "we are monitoring this call stay on the line", "pay {u} and you will get a clearance letter"],
    "family_emergency": [
        "grandma it is me i am in big trouble please do not tell mum",
        "i had an accident and the police are holding me", "i need money for the lawyer {u}",
        "send it to my friend's account {b}", "please {s} i am so scared",
        "the lawyer will speak to you now he will explain"],
    "prize_refund": [
        "congratulations you are selected for {p}", "to release the amount we need a small processing fee",
        "pay the fee to {b} and the prize will be credited", "this offer is valid {u}",
        "do not share this with anyone or the prize is cancelled"],
    "tech_support": [
        "we are calling about a security problem on {t}", "please install the remote support app so i can fix it",
        "now open your banking app i will guide you", "we accidentally refunded too much please send back the extra",
        "transfer the excess to {b}", "{s} while i fix the problem"],
    "investment": [
        "i am your personal investment manager for {i}", "you can double your money in one month guaranteed",
        "the opportunity closes {u}", "deposit to our trading wallet {b}",
        "your profit is waiting but you must pay the release tax first", "{s} because the bank will block profits"],
}
BENIGN_CALL = [
    ["hi dad how are you", "we are coming on sunday for lunch", "the kids want to see you",
     "did you take your medicine", "okay love you bye"],
    ["hello this is the clinic", "calling to confirm your appointment tomorrow", "please bring your reports",
     "thank you have a good day"],
    ["hi this is the plumber", "i finished fixing the tap", "the total is the same as the quote",
     "you can pay to my business account {b}", "thank you see you next time"],
    ["hello mum i paid the electricity bill for you", "you need to transfer the rent to the landlord",
     "his account is {b}", "call me if the app is confusing"],
    ["hello this is your bank calling about your new card", "we will never ask you to move money",
     "the card will arrive in five days", "is there anything else"],
    ["hey are we still meeting tomorrow", "yes at the cafe", "i will transfer you my half for the tickets",
     "great see you"],
    ["hello sir delivery for you", "i am outside the gate", "cash or online payment is fine", "thank you"],
    ["hi this is the school office", "the trip fee is due on friday", "you can pay through the parent portal",
     "thank you"],
    ["hello this is the fraud team at your bank", "we blocked a suspicious payment on your card",
     "can you confirm if you made a purchase today", "your money is safe we will never ask you to transfer it",
     "we will send you a new card thank you"],
    ["hi grandma it is me", "i am in a bit of trouble with my car", "can you lend me some money until friday",
     "i will send you my account details by message", "please do not tell mum she will worry"],
    ["hello i am calling about your investment account", "your pension fund statement is ready",
     "the returns this year were good", "you can review it online", "call us if you have questions"],
    ["hello this is the insurance company renewal reminder", "your policy expires next month",
     "you can renew online any time", "bye"],
    ["grandpa i got the job", "i am so happy", "thank you for the gift money", "we will celebrate"],
]

def asr_noise(r, s, p=0.08):
    w = s.split(); out = []
    for x in w:
        q = r.random()
        if q < p / 2: continue
        if q < p: x = x[:-1] if len(x) > 3 else x
        out.append(x)
    return " ".join(out)

def spoken_benef(r, kind, val, digit_err=0.10):
    v = list(val.lower())
    for i, c in enumerate(v):
        if c.isdigit() and r.random() < digit_err / max(1, sum(ch.isdigit() for ch in v)) * 3:
            v[i] = r.choice(string.digits)
    return benef_phrase(r, kind, "".join(v)).lower()

def scam_call(r, stype, benef=None):
    lines = list(SCAM_CALL[stype]); r.shuffle(lines)
    lines = lines[: r.randint(1, 4)]      # live analysis sees only part of the call
    filler = [x for b in BENIGN_CALL for x in b if "{b}" not in x]
    for _ in range(r.randint(1, 4)): lines.insert(r.randint(0, len(lines)), r.choice(filler))
    b = spoken_benef(r, *benef) if benef else "the account i will message you"
    t = " . ".join(lines).format(o=r.choice(ORGS), a=r.choice(AUTH), b=b, s=r.choice(SECRET), u=r.choice(URG),
                                  p=r.choice(PRIZE), t=r.choice(TECH), i=r.choice(INV))
    return asr_noise(r, t, 0.18)

def benign_call(r, benef=None):
    lines = list(r.choice(BENIGN_CALL))
    b = spoken_benef(r, *benef) if benef else "my usual account"
    t = " . ".join(lines).format(b=b)
    return asr_noise(r, t, 0.18)

# ---------------- beneficiary extraction ----------------
RX = [re.compile(r"\b([a-z]{2}\d{2}[a-z]{4}\d{14})\b", re.I),
      re.compile(r"\b([a-z0-9]{3,}@(?:pay|wallet|bank|upi|paylink))\b", re.I),
      re.compile(r"(?:account|a/c|acct no|acct|account number)\s*(?:number)?\s*(\d{10,14})\b", re.I)]

def extract_benef(text):
    out = set()
    for rx in RX:
        for m in rx.findall(text or ""):
            out.add(m.upper() if "@" not in m else m.lower())
    return out

def norm_benef(val):
    return val.lower() if "@" in val else val.upper()
