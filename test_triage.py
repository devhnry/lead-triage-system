"""Smallest possible self-check: fails loudly if scoring logic breaks."""
import pandas as pd
from triage import parse_budget, parse_employees, parse_date, score_lead, recommend, dedupe

assert parse_budget("$8,000/mo") == 8000
assert parse_budget("12k/mo") == 12000
assert parse_budget("TBD") is None
assert parse_budget("0") == 0
assert parse_budget("") is None

assert parse_employees("71+") == 71
assert parse_employees("7-27") == 17
assert parse_employees("") is None

assert parse_date("06/28/2024") is not None
assert parse_date("Jun 7 2024") is not None
assert parse_date("2024-6-20") is not None
assert parse_date("") is None

student_row = {"notes": "CS student, love what you do, not looking to buy", "monthly_budget": "", "employees": ""}
intent, fit, dq, reasons = score_lead(student_row)
assert dq is True
assert recommend(intent, fit, dq) == "Disqualify"

hot_row = {
    "notes": "We're a marketing agency, 22 people. Budget approved, want to start ASAP.",
    "monthly_budget": "$12,000/mo",
    "employees": "22",
}
intent, fit, dq, reasons = score_lead(hot_row)
assert dq is False
assert recommend(intent, fit, dq) == "Contact Now"

dupe_df = pd.DataFrame([
    {"lead_id": "L-1", "name": "Obi", "email": "obi@x.com", "notes": "hello, interested"},
    {"lead_id": "L-1-dup", "name": "Obi", "email": "obi@x.com", "notes": "(duplicate submission) hello, interested"},
    {"lead_id": "L-2", "name": "Ada", "email": "ada@x.com", "notes": "unrelated lead"},
])
deduped, merged = dedupe(dupe_df)
assert merged == 1
assert len(deduped) == 2
assert deduped[deduped["lead_id"] == "L-1"]["notes"].iloc[0] == "hello, interested"  # kept the untagged copy

print("all checks passed")
