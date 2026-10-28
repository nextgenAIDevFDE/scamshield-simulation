"""Diagrams for the conceptual ScamShield paper (v2): larger type for print legibility,
OPRF-based pseudonyms P(.) and query-only token interface."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({"font.family": "DejaVu Serif"})
INK = "#1f2937"; TEL = "#dbeafe"; TELE = "#1d4ed8"; BNK = "#dcfce7"; BNKE = "#15803d"
SHR = "#fef3c7"; SHRE = "#b45309"; RED = "#fee2e2"; REDE = "#b91c1c"; GRY = "#f3f4f6"; FB = "#4b5563"

def box(ax, x, y, w, h, text, fc="white", ec=INK, fs=7, bold=False, lw=1.0, r=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.004,rounding_size={r}", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
            fontweight="bold" if bold else "normal", linespacing=1.2)

def arrow(ax, x1, y1, x2, y2, color=INK, lw=1.0, ls="-", cs="arc3", ms=9):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=ms, color=color,
                                 lw=lw, ls=ls, connectionstyle=cs))

def save(fig, path):
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.03); plt.close(fig)

# ------------------------------------------------ Fig. 1: visibility gap (single column)
def fig_problem(path):
    fig, ax = plt.subplots(figsize=(3.4, 2.35)); ax.set_xlim(-0.02, 1.02); ax.set_ylim(0, 1); ax.axis("off")
    box(ax, 0.00, 0.70, 0.24, 0.17, "Scammer", fc=RED, ec=REDE, bold=True, fs=7.5)
    box(ax, 0.38, 0.70, 0.24, 0.17, "Customer", fc=GRY, bold=True, fs=7.5)
    box(ax, 0.76, 0.70, 0.24, 0.17, "Mule\naccount", fc=RED, ec=REDE, bold=True, fs=7.5)
    arrow(ax, 0.24, 0.785, 0.38, 0.785, color=TELE)
    ax.text(0.31, 0.93, "call / SMS", ha="center", fontsize=7, color=TELE)
    arrow(ax, 0.62, 0.785, 0.76, 0.785, color=BNKE)
    ax.text(0.69, 0.93, "payment", ha="center", fontsize=7, color=BNKE)
    box(ax, 0.00, 0.02, 0.48, 0.56,
        "TELECOM sees\n\nrisky caller\nscam words\nnamed account\n\nnot the payment", fc=TEL, ec=TELE, fs=7)
    box(ax, 0.52, 0.02, 0.48, 0.56,
        "BANK sees\n\ngenuine login\nnew payee\nlarger amount\n\nnot the scam call", fc=BNK, ec=BNKE, fs=7)
    ax.plot([0.30, 0.24], [0.70, 0.58], color=TELE, lw=0.8, ls=":")
    ax.plot([0.70, 0.76], [0.70, 0.58], color=BNKE, lw=0.8, ls=":")
    save(fig, path)

# ------------------------------------------------ Fig. 2: architecture (full width)
def fig_arch(path):
    fig, ax = plt.subplots(figsize=(7.2, 4.5)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    F = 6.6
    def lane(x, w, fc, ec, title):
        ax.add_patch(FancyBboxPatch((x, 0.12), w, 0.86, boxstyle="round,pad=0.003,rounding_size=0.012", fc=fc, ec=ec, lw=1.3))
        ax.text(x + w / 2, 0.945, title, ha="center", va="center", fontsize=7.6, fontweight="bold", color=ec, linespacing=1.0)
    lane(0.005, 0.335, "#f8fbff", TELE, "TELECOM AI")
    lane(0.36, 0.235, "#fffbeb", SHRE, "COMMON LAYER")
    lane(0.615, 0.38, "#f7fdf9", BNKE, "BANK AI")
    # telecom
    box(ax, 0.02, 0.80, 0.305, 0.11, "Inputs: call metadata,\nSMS text, call speech*", fc=TEL, ec=TELE, fs=F)
    box(ax, 0.02, 0.645, 0.095, 0.12, "Caller\nreputa-\ntion", fc="white", ec=TELE, fs=F)
    box(ax, 0.125, 0.645, 0.095, 0.12, "SMS\nNLP", fc="white", ec=TELE, fs=F)
    box(ax, 0.23, 0.645, 0.095, 0.12, "Speech\nNLP*", fc="white", ec=TELE, fs=F)
    box(ax, 0.02, 0.50, 0.305, 0.105, "Risk fusion:\nflag if risk ≥ τ", fc=TEL, ec=TELE, fs=F)
    box(ax, 0.02, 0.355, 0.145, 0.105, "Scam\ntype", fc="white", ec=TELE, fs=F)
    box(ax, 0.18, 0.355, 0.145, 0.105, "Beneficiary\nextraction", fc="white", ec=TELE, fs=F)
    box(ax, 0.02, 0.195, 0.305, 0.12, "Token issuer:\nOPRF pseudonyms,\nlive call state", fc=TEL, ec=TELE, fs=F)
    for x in (0.0675, 0.1725, 0.2775):
        arrow(ax, x, 0.80, x, 0.765, color=TELE); arrow(ax, x, 0.645, x, 0.605, color=TELE)
    for x in (0.0925, 0.2525):
        arrow(ax, x, 0.50, x, 0.46, color=TELE); arrow(ax, x, 0.355, x, 0.315, color=TELE)
    ax.text(0.172, 0.145, "* where lawful; on-device preferred", ha="center", fontsize=6.1, style="italic", color=TELE)
    # common layer
    box(ax, 0.375, 0.45, 0.205, 0.42,
        "Token store\n\nP(phone)\nP(beneficiaries)\ncall active?\nconfidence\nscam type\nexpiry\n\nno audio,\nno text",
        fc=SHR, ec=SHRE, fs=F)
    box(ax, 0.375, 0.29, 0.205, 0.12, "Mule registry\nP(mule IDs)", fc=SHR, ec=SHRE, fs=F)
    box(ax, 0.375, 0.155, 0.205, 0.095, "OPRF service,\naudit log", fc="white", ec=SHRE, fs=F)
    arrow(ax, 0.325, 0.255, 0.375, 0.53, color=SHRE, lw=1.5, cs="arc3,rad=-0.2")
    ax.text(0.318, 0.36, "push", fontsize=6.2, color=SHRE, ha="center", bbox=dict(fc="white", ec="none", pad=0.4))
    # bank
    box(ax, 0.63, 0.80, 0.35, 0.11, "Add payee / pay from any\nchannel (app, web, branch...)", fc=BNK, ec=BNKE, fs=F)
    box(ax, 0.63, 0.645, 0.165, 0.12, "Query:\nP(phone),\nP(payee)", fc="white", ec=BNKE, fs=F)
    box(ax, 0.815, 0.645, 0.165, 0.12, "Bank\nfeatures", fc="white", ec=BNKE, fs=F)
    box(ax, 0.63, 0.50, 0.35, 0.105, "Joint risk model\n+ active-call rule", fc=BNK, ec=BNKE, fs=F)
    box(ax, 0.63, 0.195, 0.35, 0.265,
        "Tiered intervention\n\nT1: scam warning\nT2: pause + question\nT3: hold + call-back\n+ guardian alert",
        fc="white", ec=BNKE, fs=F)
    for x in (0.7125, 0.8975):
        arrow(ax, x, 0.80, x, 0.765, color=BNKE); arrow(ax, x, 0.645, x, 0.605, color=BNKE)
    arrow(ax, 0.805, 0.50, 0.805, 0.46, color=BNKE)
    arrow(ax, 0.63, 0.72, 0.58, 0.72, color=SHRE, lw=1.3)
    arrow(ax, 0.58, 0.675, 0.63, 0.675, color=SHRE, lw=1.3)
    # feedback
    ax.plot([0.805, 0.805], [0.195, 0.07], color=FB, lw=1.0, ls="--")
    ax.plot([0.805, 0.172], [0.07, 0.07], color=FB, lw=1.0, ls="--")
    arrow(ax, 0.172, 0.07, 0.172, 0.12, color=FB, ls="--")
    ax.text(0.49, 0.035, "feedback: confirmed outcomes retrain both sides and update the mule registry",
            ha="center", fontsize=6.4, color=FB, style="italic")
    save(fig, path)

# ------------------------------------------------ Fig. 3: real-time sequence (single column)
def fig_seq(path):
    fig, ax = plt.subplots(figsize=(3.4, 4.9)); ax.set_xlim(-0.03, 1.03); ax.set_ylim(0, 1); ax.axis("off")
    L = [("Scammer", 0.09, REDE), ("Customer", 0.29, INK), ("Telco AI", 0.50, TELE),
         ("Common\nlayer", 0.71, SHRE), ("Bank AI", 0.91, BNKE)]
    for name, x, c in L:
        box(ax, x - 0.088, 0.93, 0.176, 0.06, name, fc="white", ec=c, fs=5.9, bold=True)
        ax.plot([x, x], [0.02, 0.93], color=c, lw=0.6, ls=(0, (3, 2)))
    X = {n.split()[0]: x for n, x, _ in L}
    ys = np.linspace(0.875, 0.05, 12)
    steps = [
        ("Scammer", "Customer", "1. scam call", REDE),
        (None, "Telco", "2. AI flags\nthe call", TELE),
        ("Telco", "Common", "3. token", TELE),
        ("Scammer", "Customer", "4. 'add payee'", REDE),
        ("Customer", "Bank", "5. add payee + pay", INK),
        ("Bank", "Common", "6. query", BNKE),
        ("Common", "Bank", "7. active + match", SHRE),
        (None, "Bank", "8. rule:\nT3", BNKE),
        ("Bank", "Customer", "9. HOLD + warning", BNKE),
        ("Customer", "Bank", "10. cancels payment", INK),
        ("Telco", "Common", "11. call ended", TELE),
        ("Bank", "Telco", "12. feedback", FB),
    ]
    for y, (a, b, t, c) in zip(ys, steps):
        if a is None:
            xb = X[b]
            ax.add_patch(FancyBboxPatch((xb - 0.013, y - 0.022), 0.026, 0.044, boxstyle="round,pad=0.002", fc=c, ec=c))
            ax.text(xb - 0.03, y, t, ha="right", va="center", fontsize=6.6, color=c, linespacing=1.05,
                    bbox=dict(fc="white", ec="none", pad=0.4))
            continue
        xa, xb = X[a], X[b]
        ax.add_patch(FancyArrowPatch((xa, y - 0.018), (xb, y - 0.018), arrowstyle="-|>", mutation_scale=7,
                                     color=c, lw=0.9, ls="--" if c == FB else "-"))
        ax.text((xa + xb) / 2, y - 0.009, t, ha="center", va="bottom", fontsize=6.6, color=c,
                bbox=dict(fc="white", ec="none", pad=0.25))
    y0, y1 = ys[0] + 0.03, ys[8] - 0.035
    ax.add_patch(FancyBboxPatch((-0.02, y1), 1.04, y0 - y1, boxstyle="round,pad=0.002", fc="none", ec="#9ca3af", lw=0.6, ls=":"))
    ax.text(-0.01, y1 + 0.006, "call still\nlive", ha="left", va="bottom", fontsize=6.0, color="#6b7280",
            style="italic", linespacing=1.0)
    save(fig, path)

if __name__ == "__main__":
    os.makedirs("figs", exist_ok=True)
    fig_problem("figs/c_fig1_problem.png"); fig_arch("figs/c_fig2_arch.png"); fig_seq("figs/c_fig3_seq.png")
