import pandas as pd
import streamlit as st

from triage import process

st.set_page_config(page_title="Lead Triage", layout="wide", initial_sidebar_state="collapsed")

# ---------- design system ----------
# Plain black-on-white, no accent hue. Verdicts are told apart by weight/fill
# (solid / outline / muted), not color-coding, on purpose.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,500&display=swap');

    :root {
        --bg: #ffffff;
        --surface: #ffffff;
        --ink: #111111;
        --muted: #6b6b66;
        --border: #e4e4e0;
        --row-hover: #fafafa;
        --fill: #111111;
        --fill-ink: #ffffff;
        --muted-bg: #f1f1ee;
    }

    .stApp { background: var(--bg); }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; max-width: 1320px; }
    body, .stApp, p, span, div, label { color: var(--ink); }

    h1.page-title {
        font-family: 'Newsreader', Georgia, serif;
        font-weight: 500; font-size: 2.3rem; letter-spacing: -0.02em;
        margin: 0 0 0.3rem 0; color: var(--ink);
    }
    .page-caption { color: var(--muted); font-size: 0.95rem; margin-bottom: 1.5rem; width: 100%; }

    [data-testid="stFileUploaderDropzone"] {
        background: var(--surface); border: 1px solid var(--ink); border-radius: 8px;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] svg { display: none; }

    /* stat tiles */
    .stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px;
        background: var(--border); border: 1px solid var(--border); border-radius: 8px;
        overflow: hidden; margin: 1.75rem 0 2.25rem 0; width: 100%; }
    .stat-tile { background: var(--surface); padding: 1.15rem 1.4rem; }
    .stat-tile.highlight { background: var(--fill); }
    .stat-tile.highlight .stat-num, .stat-tile.highlight .stat-label { color: var(--fill-ink); }
    .stat-num { font-family: 'Newsreader', Georgia, serif; font-weight: 500; font-size: 2.1rem;
        line-height: 1; color: var(--ink); font-variant-numeric: oldstyle-nums; }
    .stat-label { color: var(--muted); font-size: 0.82rem; margin-top: 0.35rem; }

    h2.section-title {
        font-family: 'Newsreader', Georgia, serif; font-weight: 500; font-size: 1.5rem;
        letter-spacing: -0.01em; margin: 0;
    }

    /* verdict pills: told apart by fill, not hue */
    .pill { display: inline-block; padding: 0.2rem 0.65rem; border-radius: 999px;
        font-size: 0.74rem; font-weight: 600; letter-spacing: 0.02em; white-space: nowrap; }
    .pill-contact { background: var(--fill); color: var(--fill-ink); }
    .pill-nurture { background: var(--surface); color: var(--ink); border: 1px solid var(--ink); }
    .pill-disqualify { background: var(--muted-bg); color: var(--muted); }

    .avatar { flex: none; width: 26px; height: 26px; border-radius: 999px; background: var(--muted-bg);
        color: var(--ink); font-size: 0.72rem; font-weight: 600; display: flex;
        align-items: center; justify-content: center; }

    .lead-row { display: grid; grid-template-columns: 2fr 1.6fr 1.4fr 1fr auto; gap: 0.75rem;
        align-items: center; padding: 0.65rem 0.25rem; border-bottom: 1px solid var(--border); }
    .lead-row.header { color: var(--muted); font-size: 0.74rem; text-transform: uppercase;
        letter-spacing: 0.03em; padding-bottom: 0.5rem; }
    .lead-name { font-weight: 600; font-size: 0.9rem; }
    .lead-title { color: var(--muted); font-size: 0.78rem; }
    .lead-notes { color: var(--muted); font-size: 0.82rem; overflow: hidden; text-overflow: ellipsis;
        white-space: nowrap; }
    .score-text { font-family: 'Newsreader', Georgia, serif; font-size: 0.95rem; }
    .bar-track { width: 46px; height: 3px; border-radius: 2px; background: var(--border); display: inline-block; margin-right: 0.4rem; }
    .bar-fill { height: 3px; border-radius: 2px; background: var(--ink); }

    .detail-card { background: var(--row-hover); border: 1px solid var(--border); border-radius: 8px;
        padding: 1.1rem 1.4rem; margin: 0.25rem 0 0.9rem 0; }
    .detail-notes { font-family: 'Newsreader', Georgia, serif; font-style: italic; font-size: 1rem;
        margin: 0.5rem 0 0.9rem 0; line-height: 1.5; }
    .reason-row { display: flex; justify-content: space-between; padding: 0.3rem 0;
        border-bottom: 1px solid var(--border); font-size: 0.85rem; }
    .reason-row:last-child { border-bottom: none; }
    .reason-plus { color: var(--ink); font-weight: 700; }
    .reason-minus { color: var(--muted); font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 class="page-title">Lead Triage</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-caption">Upload a lead export CSV. Dates, employee counts, and budget get '
    'normalized; each lead is scored for intent and fit from the notes, title, and email fields; '
    'the ranked list comes back with a Contact Now / Nurture / Disqualify call and the reasons behind it.</div>',
    unsafe_allow_html=True,
)

uploaded = st.file_uploader("Lead export CSV", type="csv", label_visibility="collapsed")

PILL_CLASS = {"Contact Now": "pill-contact", "Nurture": "pill-nurture", "Disqualify": "pill-disqualify"}
PAGE_SIZE = 50

SCORING_EXPLAINER = """
**Guardrails first.** Non-buyers (students, recruiters, investors, spam/vendor pitches) and junk
rows are screened out before scoring even starts — score 0, always Disqualify.

**Intent** — from the notes: buying language vs. hesitation, and whether a real budget number
was given (TBD, $0, and a stated number all mean something different).

**Fit** — decision-maker title, employee count in the target band, budget above the floor, and a
valid email on file. No valid email caps a lead at Nurture — you can't recommend contacting
someone you have no way to reach, however good the rest of the score looks.

**Score** = intent + fit, scaled to /100. 70+ → Contact Now, 30–69 → Nurture, below 30 → Disqualify.
"""


def stat_tile(container, number, label, highlight=False):
    cls = "stat-tile highlight" if highlight else "stat-tile"
    container.markdown(
        f'<div class="{cls}"><div class="stat-num">{number}</div>'
        f'<div class="stat-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def cell(v):
    return "" if pd.isna(v) else str(v)


if uploaded:
    raw = pd.read_csv(uploaded)
    result = process(raw)
    result["score_100"] = (result["total_score"] * 10).astype(int)

    counts = result["recommendation"].value_counts()
    st.markdown('<div class="stat-row">', unsafe_allow_html=True)
    tiles = st.columns(4, gap="small")
    stat_tile(tiles[0], len(result), "every row inspected")
    stat_tile(tiles[1], int(counts.get("Contact Now", 0)), "worth contacting now", highlight=True)
    stat_tile(tiles[2], int(counts.get("Nurture", 0)), "promising, not ready")
    stat_tile(tiles[3], int(counts.get("Disqualify", 0)), "junk, non-buyers, or low fit")
    st.markdown("</div>", unsafe_allow_html=True)

    head_l, head_r = st.columns([3, 2])
    head_l.markdown('<h2 class="section-title">Lead queue</h2>', unsafe_allow_html=True)
    with head_r:
        c1, c2 = st.columns([3, 1])
        search = c1.text_input("Search", placeholder="Search name, company, notes…", label_visibility="collapsed")
        with c2:
            with st.popover("Scoring ↴"):
                st.markdown(SCORING_EXPLAINER)

    choice = st.segmented_control(
        "Filter", ["All", "Contact Now", "Nurture", "Disqualify"], default="All", label_visibility="collapsed",
    )
    view = result if choice in (None, "All") else result[result["recommendation"] == choice]
    if search:
        q = search.lower()
        haystack = (view["name"].fillna("") + " " + view["company"].fillna("") + " "
                    + view["notes"].fillna("") + " " + view["title"].fillna("")).str.lower()
        view = view[haystack.str.contains(q, regex=False)]
    view = view.reset_index(drop=True)

    if "page_size" not in st.session_state:
        st.session_state.page_size = PAGE_SIZE
    if "open_lead" not in st.session_state:
        st.session_state.open_lead = None

    st.caption(f"{len(view)} lead{'s' if len(view) != 1 else ''}")

    st.markdown(
        '<div class="lead-row header"><div>Lead</div><div>Company</div><div>Notes</div>'
        '<div>Score</div><div>Verdict</div></div>',
        unsafe_allow_html=True,
    )

    shown = view.head(st.session_state.page_size)
    for _, r in shown.iterrows():
        name = cell(r["name"]) or "(no name)"
        initial = name[0].upper() if name != "(no name)" else "?"
        pill = PILL_CLASS.get(r["recommendation"], "pill-nurture")
        row_cols = st.columns([2, 1.6, 1.4, 1, 1, 0.4], gap="small", vertical_alignment="center")
        row_cols[0].markdown(
            f'<div style="display:flex;align-items:center;gap:0.55rem">'
            f'<div class="avatar">{initial}</div><div><div class="lead-name">{name}</div>'
            f'<div class="lead-title">{cell(r["title"]) or "&mdash;"}</div></div></div>',
            unsafe_allow_html=True,
        )
        row_cols[1].markdown(f'<div class="lead-title">{cell(r["company"]) or "&mdash;"}</div>', unsafe_allow_html=True)
        row_cols[2].markdown(f'<div class="lead-notes">{cell(r["notes"])}</div>', unsafe_allow_html=True)
        row_cols[3].markdown(
            f'<span class="bar-track"><span class="bar-fill" style="width:{r["score_100"] * 0.46}px;display:block"></span></span>'
            f'<span class="score-text">{int(r["score_100"])}/100</span>',
            unsafe_allow_html=True,
        )
        row_cols[4].markdown(f'<span class="pill {pill}">{r["recommendation"]}</span>', unsafe_allow_html=True)
        is_open = st.session_state.open_lead == r["lead_id"]
        if row_cols[5].button("▾" if not is_open else "▴", key=f"tog-{r['lead_id']}", type="secondary"):
            st.session_state.open_lead = None if is_open else r["lead_id"]
            st.rerun()

        if is_open:
            reasons = [x.strip() for x in str(r["reasons"]).split(";") if x.strip()]
            reason_html = "".join(
                f'<div class="reason-row"><span>{x.lstrip("+-").strip()}</span>'
                f'<span class="{"reason-plus" if x.strip().startswith("+") else "reason-minus"}">'
                f'{"+" if x.strip().startswith("+") else "&minus;"}</span></div>'
                for x in reasons
            ) or '<div class="reason-row"><span>No notable signals either way</span></div>'
            st.markdown(
                f"""<div class="detail-card">
                    <div class="detail-notes">&ldquo;{cell(r['notes'])}&rdquo;</div>
                    <div class="lead-title">{cell(r['email']) or 'no email on file'}</div>
                    {reason_html}
                </div>""",
                unsafe_allow_html=True,
            )

    if len(view) > st.session_state.page_size:
        if st.button(f"Show {min(PAGE_SIZE, len(view) - st.session_state.page_size)} more", type="primary"):
            st.session_state.page_size += PAGE_SIZE
            st.rerun()

    st.write("")
    st.download_button(
        "Download ranked CSV",
        result.to_csv(index=False).encode("utf-8"),
        "leads_ranked.csv",
        "text/csv",
        type="primary",
    )
else:
    st.info("Waiting for a CSV upload.")
