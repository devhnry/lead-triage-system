"""Lead cleaning + scoring logic. Pure functions, no I/O — testable and reusable
against any future export with the same columns."""
import re
from datetime import datetime

import pandas as pd

# ---------- cleaning ----------

DATE_FORMATS = ["%m/%d/%Y", "%Y-%m-%d", "%b %d %Y", "%m-%d-%Y", "%Y-%m-%d", "%m/%d/%y"]


def parse_date(raw):
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip().replace(",", "")
    # normalize "2024-6-20" -> "2024-06-20" width so strptime doesn't need every variant
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # last resort: let pandas guess (handles "2024-6-20", "6/5/24", etc.)
    try:
        return pd.to_datetime(s, dayfirst=False).date()
    except (ValueError, TypeError):
        return None


def parse_employees(raw):
    """'71+' -> 71, '7-27' -> 17 (midpoint), '10' -> 10, '' -> None."""
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip().rstrip("+")
    if "-" in s:
        lo, hi = s.split("-", 1)
        try:
            return (int(lo) + int(hi)) / 2
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_budget(raw):
    """'$8,000/mo' / '12k/mo' / '18k' / 'TBD' / '0' -> monthly USD float or None."""
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip().lower()
    if s in ("tbd", "n/a", "na", "unknown", "?"):
        return None
    s = s.replace("/mo", "").replace("per month", "").replace("$", "").replace(",", "").strip()
    m = re.match(r"^([\d.]+)\s*k?$", s)
    if not m:
        return None
    val = float(m.group(1))
    if s.endswith("k"):
        val *= 1000
    return val


def valid_email(raw):
    return bool(raw) and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(raw).strip()) is not None


# ---------- scoring ----------

# ponytail: keyword rules, not an ML classifier — 520 rows of short notes don't
# justify embeddings/LLM scoring, and rules are auditable in a 1-page doc.
# Upgrade path: swap `score_notes` for an LLM-judge call if notes get longer/messier.

HARD_DISQUALIFY_PATTERNS = [
    r"\bstudent\b", r"\bjournalist\b", r"\bnot a client\b", r"\bnot looking to buy\b",
    r"\blooking for a role\b", r"\bcv\b", r"\bnot a direct buyer\b", r"\bjust learning\b",
    r"\bcan'?t really pay\b", r"\bintern(ship)?\b", r"\bportfolio compan",
    r"you have won", r"click here to claim",  # spam/phishing rows
]

POSITIVE_INTENT_PATTERNS = [
    r"budget approved", r"want(s)? to start (asap|this month|now)", r"ready to buy",
    r"want it automated end to end", r"decision in about a month", r"have some budget",
]

NEGATIVE_INTENT_PATTERNS = [
    r"comparing a few options", r"price sensitive", r"not sure what we need",
    r"not sure who signs off", r"would need to loop in the team", r"budget not locked",
]

# decision-maker titles = can actually approve a purchase, regardless of company type.
# ELI5: "agency" in the notes was a weak proxy for fit (271 non-agency leads describe the
# same automation pain points) — job title is a stronger, more defensible signal.
DECISION_MAKER_TITLES = [
    "owner", "founder", "ceo", "coo", "cto", "vp", "head of", "director",
    "managing partner", "managing director", "partner",
]
JUNK_TITLES = ["asdf", "test"]
# every Student/Recruiter-titled row in this dataset is a non-buyer (job-seeker,
# bootcamp grad, journalist, VC, recruiter pitching placements) — verified against
# all unique notes for these titles, no exceptions found.
NON_BUYER_TITLES = ["student", "recruiter"]

BUDGET_FLOOR = 2000  # ponytail: arbitrary min viable engagement size, tune per business
EMPLOYEE_FIT_RANGE = (5, 100)  # sweet spot: too small = no budget, too big = needs enterprise sale


def _matches_any(patterns, text):
    return any(re.search(p, text) for p in patterns)


def score_lead(row):
    """Returns (intent_score 0-5, fit_score 0-5, disqualified bool, reasons list)."""
    notes = str(row.get("notes") or "").lower()
    title = str(row.get("title") or "").strip().lower()
    reasons = []

    if _matches_any(HARD_DISQUALIFY_PATTERNS, notes):
        return 0, 0, True, ["notes indicate non-buyer (student/journalist/job-seeker/investor/spam/etc.)"]
    if title in JUNK_TITLES:
        return 0, 0, True, ["junk/test row (garbage title field)"]
    if title in NON_BUYER_TITLES:
        return 0, 0, True, [f"non-buyer title ({title})"]

    intent = 2  # neutral baseline
    if _matches_any(POSITIVE_INTENT_PATTERNS, notes):
        intent += 2
        reasons.append("+intent: buying signal in notes")
    if _matches_any(NEGATIVE_INTENT_PATTERNS, notes):
        intent -= 1
        reasons.append("-intent: hesitation/comparison signal in notes")
    budget = parse_budget(row.get("monthly_budget"))
    if budget is None:
        intent -= 1
        reasons.append("-intent: no budget stated")
    elif budget == 0:
        intent -= 2
        reasons.append("-intent: budget is $0")
    intent = max(0, min(5, intent))

    fit = 2  # neutral baseline
    if any(t in title for t in DECISION_MAKER_TITLES):
        fit += 1
        reasons.append("+fit: decision-maker title (can approve a purchase)")
    emp = parse_employees(row.get("employees"))
    if emp is not None and EMPLOYEE_FIT_RANGE[0] <= emp <= EMPLOYEE_FIT_RANGE[1]:
        fit += 1
        reasons.append("+fit: employee count in target range")
    if budget is not None and budget >= BUDGET_FLOOR:
        fit += 2
        reasons.append(f"+fit: budget >= ${BUDGET_FLOOR}/mo")
    fit = max(0, min(5, fit))

    return intent, fit, False, reasons


def recommend(intent, fit, disqualified):
    if disqualified:
        return "Disqualify"
    total = intent + fit
    if total >= 7:
        return "Contact Now"
    if total >= 3:
        return "Nurture"
    return "Disqualify"


# ---------- pipeline ----------

def process(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["created_clean"] = df["created"].apply(parse_date)
    df["employees_clean"] = df["employees"].apply(parse_employees)
    df["budget_clean"] = df["monthly_budget"].apply(parse_budget)
    df["email_valid"] = df["email"].apply(valid_email)

    scored = df.apply(lambda r: score_lead(r), axis=1, result_type="expand")
    scored.columns = ["intent_score", "fit_score", "disqualified", "reasons"]
    df = pd.concat([df, scored], axis=1)
    df["total_score"] = df["intent_score"] + df["fit_score"]
    df["recommendation"] = df.apply(
        lambda r: recommend(r["intent_score"], r["fit_score"], r["disqualified"]), axis=1
    )
    df["reasons"] = df["reasons"].apply(lambda rs: "; ".join(rs))

    df = df.sort_values("total_score", ascending=False).reset_index(drop=True)
    return df
