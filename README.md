# Lead Triage System

Cleans a messy lead export, scores each lead for intent + fit from the notes/title/budget/employee
fields, and ranks them with a Contact Now / Nurture / Disqualify recommendation.

## Run it

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/streamlit run app.py
```

Upload a CSV with columns: `lead_id, created, name, email, company, employees, website, title, source, monthly_budget, notes`.

## How it works

1. **Clean** (`triage.py`) — normalizes inconsistent dates, employee counts (`"71+"`, `"7-27"`), and
   budgets (`"$8,000/mo"`, `"12k/mo"`, `"TBD"`) into real numbers/dates. `"TBD"` (unknown) and `"$0"`
   (confirmed no budget) are kept distinct on purpose.
2. **Score** (`triage.py: score_lead`) — keyword rules, not an ML model (notes are short and
   templated, so rules stay auditable). Hard disqualifiers (student/journalist/investor/job-seeker/
   spam language, junk title rows) short-circuit to score 0 regardless of budget or size. Everything
   else gets an intent score (buying language vs. hesitation, budget presence) and a fit score
   (decision-maker title, employee count band, budget floor), 0–5 each.
3. **Rank** (`triage.py: process`) — sorts by total score, labels Contact Now (≥7) / Nurture (3–6) /
   Disqualify (<3 or hard-disqualified).

Tunable constants live at the top of the scoring section in `triage.py`: `BUDGET_FLOOR`,
`EMPLOYEE_FIT_RANGE`, `DECISION_MAKER_TITLES` — these encode business assumptions, not facts, and
should be recalibrated against real deal data.

## Files

- `triage.py` — cleaning + scoring logic, no I/O, unit-testable
- `app.py` — Streamlit UI: upload, view, filter, download ranked CSV
- `test_triage.py` — smoke test for the parsing/scoring functions

## Tests

```bash
./.venv/bin/python test_triage.py
```
