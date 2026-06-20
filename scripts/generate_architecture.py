"""
Architecture & Workflow diagram for the
AI Agent Ticket Triage & Auto-Routing System.

Run   : python scripts/generate_architecture.py
Output: architecture_diagram.png  (project root, ~3600x2520 px)
"""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(20, 14))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis("off")
fig.patch.set_facecolor("#F0F2F5")

C = dict(
    navy="#001529", blue="#1677FF", lblue="#E6F4FF",
    green="#52C41A", lgreen="#F6FFED",
    orange="#FA8C16", lorange="#FFF7E6",
    red="#F5222D", lred="#FFF1F0",
    purple="#722ED1", lpurple="#F9F0FF",
    teal="#08979C", white="#FFFFFF",
    grey="#8C8C8C", dark="#262626",
    bg="#F0F2F5", border="#D9D9D9",
)


def box(ax, x, y, w, h, face, edge, r=0.2, lw=1.5):
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        linewidth=lw, edgecolor=edge, facecolor=face, zorder=3,
    ))


def txt(ax, x, y, t, sz=9, c="#262626", w="normal", ha="center", va="center"):
    ax.text(x, y, t, fontsize=sz, color=c, fontweight=w,
            ha=ha, va=va, zorder=4, multialignment="center")


def arr(ax, x1, y1, x2, y2, c="#595959", lw=2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=c, lw=lw,
                                connectionstyle="arc3,rad=0",
                                mutation_scale=14),
                zorder=2)


def sec(ax, x, y, w, h, face, edge, lbl, lc):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.3",
        linewidth=1.5, edgecolor=edge,
        facecolor=face, alpha=0.4, zorder=1,
    ))
    ax.text(x + 0.18, y + h - 0.18, lbl,
            fontsize=8, color=lc, fontweight="bold",
            va="top", ha="left", zorder=5, style="italic")


# ── Title ─────────────────────────────────────────────────────────────────────
txt(ax, 10, 13.55, "AI Agent Ticket Triage & Auto-Routing System",
    17, C["navy"], "bold")
txt(ax, 10, 13.12, "Architecture & Workflow Diagram", 11, C["grey"])
ax.plot([0.5, 19.5], [12.82, 12.82], color=C["border"], lw=1.5, zorder=2)


# ── LAYER 1: INPUT ────────────────────────────────────────────────────────────
sec(ax, 0.5, 11.05, 19.0, 1.6, C["lblue"], C["blue"], "LAYER 1 — INPUT", C["blue"])

box(ax, 3.8, 11.85, 3.2, 0.9, C["lblue"], C["blue"], lw=2)
txt(ax, 3.8, 12.0,  "Excel File",           10, C["blue"],  "bold")
txt(ax, 3.8, 11.72, "sample_tickets.xlsx",   8.5, C["grey"])

arr(ax, 5.4, 11.85, 7.2, 11.85, C["blue"], 2)
txt(ax, 6.3, 12.05, "Upload", 8, C["grey"])

box(ax, 10.0, 11.85, 4.2, 0.9, C["blue"], C["navy"], lw=2)
txt(ax, 10.0, 12.0,  "React Web Portal",              10, C["white"], "bold")
txt(ax, 10.0, 11.72, "Ant Design 5  |  Vite  |  :5173", 8,  "#BAE0FF")

arr(ax, 12.1, 11.85, 14.2, 11.85, C["blue"], 2)
txt(ax, 13.15, 12.05, "REST API", 8, C["grey"])

box(ax, 16.8, 11.85, 4.0, 0.9, C["navy"], C["blue"], lw=2)
txt(ax, 16.8, 12.0,  "FastAPI Backend",                10, C["white"], "bold")
txt(ax, 16.8, 11.72, "Python 3.13  |  uvicorn  |  :8000", 8,  "#BAE0FF")

arr(ax, 16.8, 11.4, 16.8, 10.42, C["navy"], 2.5)
txt(ax, 17.6, 10.9, "Trigger\nPipeline", 8, C["grey"])


# ── LAYER 2: AI BRAIN ─────────────────────────────────────────────────────────
sec(ax, 0.5, 9.35, 19.0, 1.6, C["lpurple"], C["purple"],
    "LAYER 2 — AI BRAIN & DATA", C["purple"])

box(ax, 5.5, 10.15, 3.5, 1.0, C["lpurple"], C["purple"], lw=2)
txt(ax, 5.5, 10.38, "ML Classifier",              9.5, C["purple"], "bold")
txt(ax, 5.5, 10.13, "TF-IDF + Logistic Regression", 8,  C["dark"])
txt(ax, 5.5,  9.88, "scikit-learn  |  classifier.pkl", 7.5, C["grey"])

txt(ax, 8.1, 10.15, "OR", 10, C["grey"], "bold")

box(ax, 10.8, 10.15, 3.8, 1.0, C["lpurple"], C["purple"], lw=2)
txt(ax, 10.8, 10.38, "Ollama LLM  (Fallback)",       9.5, C["purple"], "bold")
txt(ax, 10.8, 10.13, "gpt-oss:120b-cloud",             8,  C["dark"])
txt(ax, 10.8,  9.88, "localhost:11434  |  temp=0.1", 7.5, C["grey"])

box(ax, 15.0, 10.15, 3.0, 1.0, C["lorange"], C["orange"], lw=2)
txt(ax, 15.0, 10.38, "routing_config.xlsx",       9.5, C["orange"], "bold")
txt(ax, 15.0, 10.13, "Teams  |  Leads  |  Members", 8,  C["dark"])
txt(ax, 15.0,  9.88, "No code change required",  7.5, C["grey"])

box(ax, 18.4, 10.15, 2.4, 1.0, C["lblue"], C["teal"], lw=2)
txt(ax, 18.4, 10.38, "SQLite DB",          9.5, C["teal"],  "bold")
txt(ax, 18.4, 10.13, "Tickets | Feedback",  8,   C["dark"])
txt(ax, 18.4,  9.88, "Metrics | Audit",    7.5,  C["grey"])

arr(ax, 8.5, 9.35, 8.5, 8.32, C["purple"], 2.5)
txt(ax, 9.3, 8.83, "Per-ticket\nclassification", 8, C["grey"])


# ── LAYER 3: AGENT PIPELINE ───────────────────────────────────────────────────
sec(ax, 0.5, 6.9, 19.0, 2.2, "#E8F4FD", C["blue"],
    "LAYER 3 — MULTI-AGENT PIPELINE", C["blue"])

agents = [
    (2.2,  C["blue"],   C["lblue"],   "1. Classifier\nAgent",  "What type?",   "ML primary\nOllama fallback"),
    (5.6,  C["orange"], C["lorange"], "2. Priority\nAgent",    "How urgent?",  "P1 keywords first\nOllama for P2-P4"),
    (9.0,  C["green"],  C["lgreen"],  "3. Routing\nAgent",     "Who handles?", "config.xlsx\nP1/P2 → Lead"),
    (12.4, C["navy"],   C["lblue"],   "4. Confidence\nAgent",  "Sure enough?", "ML*0.5+LLM*0.3\n+Priority*0.2"),
    (15.8, C["purple"], C["lpurple"], "5. Feedback\nAgent",    "Remember?",    "Save corrections\nTrigger retrain"),
]

for i, (cx, edge, face, title, question, detail) in enumerate(agents):
    box(ax, cx, 8.0, 2.9, 1.85, face, edge, lw=2, r=0.22)
    ax.plot([cx - 1.45, cx + 1.45], [8.65, 8.65], color=edge, lw=2, zorder=4)
    txt(ax, cx, 8.83, title,    9,   edge,      "bold")
    txt(ax, cx, 8.42, question, 9,   C["dark"], "bold")
    txt(ax, cx, 8.07, detail,   8,   C["grey"])
    if i < 4:
        arr(ax, cx + 1.45, 8.0, cx + 1.8, 8.0, edge, 1.8)

arr(ax, 9.0, 7.08, 9.0, 6.2, C["navy"], 2.5)
txt(ax, 9.8, 6.63, "Final\nScore", 8, C["grey"])


# ── LAYER 4: DECISION GATE ────────────────────────────────────────────────────
sec(ax, 0.5, 5.5, 19.0, 1.3, "#FFFBE6", C["orange"],
    "LAYER 4 — CONFIDENCE DECISION GATE", C["orange"])

box(ax, 9.0, 5.95, 5.5, 0.85, "#FFFBE6", C["orange"], lw=2.5)
txt(ax, 9.0, 6.1,  "Confidence Threshold Check",                     10,  C["orange"], "bold")
txt(ax, 9.0, 5.83, "Weighted Score  =  ML × 0.5  +  LLM × 0.3  +  Priority × 0.2", 8.5, C["dark"])

arr(ax,  6.8, 5.62,  4.5, 4.65, C["green"],  2.2)
arr(ax,  9.0, 5.62,  9.0, 4.65, C["orange"], 2.2)
arr(ax, 11.2, 5.62, 13.5, 4.65, C["red"],    2.2)

txt(ax,  4.5, 5.25, "> 85%",    9, C["green"],  "bold")
txt(ax,  9.0, 5.25, "65 – 85%", 9, C["orange"], "bold")
txt(ax, 13.5, 5.25, "< 65%",    9, C["red"],    "bold")


# ── LAYER 5: OUTCOMES ─────────────────────────────────────────────────────────
sec(ax, 0.5, 2.95, 19.0, 2.3, C["bg"], C["border"], "LAYER 5 — OUTCOMES", C["dark"])

box(ax, 4.5, 3.95, 5.6, 1.7, C["lgreen"],  C["green"],  lw=2.5)
txt(ax, 4.5, 4.65, "AUTO-ROUTED",                    11, C["green"],  "bold")
txt(ax, 4.5, 4.37, "Assignee confirmed from config",  8.5, C["dark"])
txt(ax, 4.5, 4.12, "Gmail SMTP email sent instantly", 8.5, C["dark"])
txt(ax, 4.5, 3.87, "Enriched Excel downloaded",       8.5, C["dark"])
txt(ax, 4.5, 3.42, "Status: Auto-Routed",              8,  C["green"])

box(ax, 9.0, 3.95, 5.6, 1.7, C["lorange"], C["orange"], lw=2.5)
txt(ax, 9.0, 4.65, "FLAGGED",                            11, C["orange"], "bold")
txt(ax, 9.0, 4.37, "Placed in Review Queue (React UI)",  8.5, C["dark"])
txt(ax, 9.0, 4.12, "Human approves or overrides",        8.5, C["dark"])
txt(ax, 9.0, 3.87, "Correction saved for retraining",    8.5, C["dark"])
txt(ax, 9.0, 3.42, "Status: Flagged",                     8,  C["orange"])

box(ax, 13.5, 3.95, 5.6, 1.7, C["lred"],   C["red"],   lw=2.5)
txt(ax, 13.5, 4.65, "HELD",                               11, C["red"],    "bold")
txt(ax, 13.5, 4.37, "Manual classification required",     8.5, C["dark"])
txt(ax, 13.5, 4.12, "Analyst routes ticket in the UI",    8.5, C["dark"])
txt(ax, 13.5, 3.87, "Correction saved for retraining",    8.5, C["dark"])
txt(ax, 13.5, 3.42, "Status: Held",                        8,  C["red"])


# ── LAYER 6: NOTIFICATIONS ───────────────────────────────────────────────────
sec(ax, 0.5, 1.38, 19.0, 1.5, C["lblue"], C["navy"],
    "LAYER 6 — NOTIFICATIONS & PERSISTENCE", C["navy"])

box(ax, 4.5, 2.1, 5.2, 0.9, C["lblue"],  C["blue"],   lw=2)
txt(ax, 4.5, 2.28, "Gmail SMTP Notification",                    9.5, C["blue"],   "bold")
txt(ax, 4.5, 2.02, "HTML email to assignee  |  smtp.gmail.com:587", 8, C["grey"])

box(ax, 9.0, 2.1, 5.2, 0.9, C["lblue"],  C["navy"],   lw=2)
txt(ax, 9.0, 2.28, "Enriched Excel Download",              9.5, C["navy"],   "bold")
txt(ax, 9.0, 2.02, "+8 AI columns  |  triage_results.xlsx",  8, C["grey"])

box(ax, 13.5, 2.1, 5.2, 0.9, C["lorange"], C["orange"], lw=2)
txt(ax, 13.5, 2.28, "Audit Trail — SQLite",                      9.5, C["orange"], "bold")
txt(ax, 13.5, 2.02, "All tickets  |  Feedback  |  Model Metrics",  8, C["grey"])

arr(ax,  4.5, 3.1,  4.5, 2.55, C["green"],  1.8)
arr(ax,  9.0, 3.1,  9.0, 2.55, C["orange"], 1.8)
arr(ax, 13.5, 3.1, 13.5, 2.55, C["red"],    1.8)


# ── Feedback loop spine ───────────────────────────────────────────────────────
ax.plot([1.05, 1.05], [2.1, 9.9],  color=C["purple"], lw=1.8, linestyle="dashed", zorder=2)
ax.plot([1.05, 2.65], [2.1, 2.1],  color=C["purple"], lw=1.8, linestyle="dashed", zorder=2)
arr(ax, 1.05, 9.9, 2.2, 9.9, C["purple"], 1.8)
ax.text(0.65, 6.0, "Feedback\nLoop",
        fontsize=8.5, color=C["purple"], fontweight="bold",
        ha="center", va="center", rotation=90, zorder=5)


# ── Legend ────────────────────────────────────────────────────────────────────
legend_items = [
    (C["blue"],   "Frontend / API"),
    (C["purple"], "AI / ML Layer"),
    (C["green"],  "Auto-Routed (>85%)"),
    (C["orange"], "Flagged (65-85%)"),
    (C["red"],    "Held (<65%)"),
    (C["teal"],   "Config / Storage"),
]
for i, (color, label) in enumerate(legend_items):
    bx = 1.4 + i * 3.05
    box(ax, bx, 0.88, 0.32, 0.32, color, color)
    ax.text(bx + 0.25, 0.88, label,
            fontsize=8, color=C["dark"], va="center", ha="left", zorder=5)

ax.plot([0.5, 19.5], [0.58, 0.58], color=C["border"], lw=1)
ax.text(10.0, 0.3,
        "Python · FastAPI · React · Ollama · scikit-learn · SQLite · Gmail SMTP",
        fontsize=7.5, color=C["grey"], ha="center", va="center", zorder=5)


# ── Save ──────────────────────────────────────────────────────────────────────
out = pathlib.Path(__file__).resolve().parent.parent / "architecture_diagram.png"
plt.tight_layout(pad=0)
plt.savefig(str(out), dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"Saved -> {out}")
