import io

import pandas as pd
import streamlit as st

from triage import process

st.set_page_config(page_title="Lead Triage", layout="wide", initial_sidebar_state="collapsed")


@st.cache_data(show_spinner=False)
def load_and_score(file_bytes: bytes) -> pd.DataFrame:
    # ponytail: Streamlit reruns the whole script on every click (row toggle,
    # filter, search keystroke) — without caching, all 500+ rows get re-parsed
    # and re-scored from scratch every single time. Cache key is the file's own
    # bytes, so it only recomputes when a genuinely different file is uploaded.
    raw = pd.read_csv(io.BytesIO(file_bytes))
    return process(raw)

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
    .stApp { color: var(--ink); }

    h1.page-title {
        font-family: 'Newsreader', Georgia, serif;
        font-weight: 500; font-size: 2.3rem; letter-spacing: -0.02em;
        margin: 0 0 0.3rem 0; color: var(--ink);
    }
    .page-caption { color: var(--muted); font-size: 0.95rem; margin-bottom: 1.5rem; width: 100%; }

    [data-testid="stFileUploaderDropzone"] {
        background: var(--surface); border: 1px solid var(--ink); border-radius: 4px;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] svg { display: none; }
    /* Streamlit's text input / selectbox wrappers use an invisible border at rest
       that snaps to solid black on focus -- same border in both states instead. */
    div[data-testid="stTextInputRootElement"],
    div[data-testid="stTextInputRootElement"]:focus-within,
    div[data-testid="stSelectbox"] div:has(> input),
    div[data-testid="stSelectbox"] div:has(> input):focus-within {
        border-color: transparent !important;
    }
    [data-testid="stFileUploaderFile"] {
        border: 1px solid var(--border); border-radius: 4px; padding: 0.4rem 0.7rem;
        background: var(--surface); margin-top: 0.5rem;
    }

    /* stat tiles */
    .stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px;
        background: var(--border); border: 1px solid var(--border); border-radius: 4px;
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

    .header-cell { color: var(--muted); font-size: 0.74rem; text-transform: uppercase;
        letter-spacing: 0.03em; padding-bottom: 0.5rem; border-bottom: 1px solid var(--ink); }

    /* each data row is a keyed container -> stable class we can target for hover + the
       full-row click overlay, without hardcoding one CSS rule per row. */
    div[class*="st-key-row-"] {
        position: relative; border-bottom: 1px solid var(--border); padding: 0.55rem 0.6rem;
    }
    div[class*="st-key-row-"]:hover { background: var(--row-hover); cursor: pointer; }
    /* Full-row click overlay: inset:0 alone stretches an absolutely positioned element to
       its positioned ancestor's edges. Adding width/height:100% on top of that breaks it —
       percentage height doesn't resolve against an auto-height ancestor, so don't mix the two. */
    div[class*="st-key-row-"] button {
        position: absolute !important; inset: 0 !important;
        opacity: 0 !important; cursor: pointer !important; border: none !important;
        padding: 0 !important; margin: 0 !important;
    }
    /* Streamlit sets position:relative on the button's own wrapper div, which becomes
       its containing block instead of our row -- neutralize it so inset:0 above
       resolves against the full row, not that tiny wrapper. */
    div[class*="st-key-row-"] div[data-testid="stElementContainer"]:has(button) {
        position: static !important;
    }
    .lead-name { font-weight: 600; font-size: 0.9rem; }
    .lead-title { color: var(--muted); font-size: 0.78rem; }
    .lead-notes { color: var(--muted); font-size: 0.82rem; overflow: hidden; text-overflow: ellipsis;
        white-space: nowrap; }
    .score-cell { display: flex; flex-direction: column; gap: 0.3rem; }
    .score-text { font-family: 'Newsreader', Georgia, serif; font-size: 0.95rem; }
    .bar-track { width: 56px; height: 3px; border-radius: 2px; background: var(--border); }
    .bar-fill { height: 3px; border-radius: 2px; background: var(--ink); }
    .capped-note { color: var(--muted); font-size: 0.68rem; margin-top: 0.2rem; }

    .detail-card { background: var(--row-hover); border: 1px solid var(--border); border-radius: 4px;
        padding: 1.1rem 1.4rem; margin: 0.25rem 0 0.9rem 0; }
    .detail-meta { color: var(--muted); font-size: 0.82rem; margin-bottom: 0.3rem; }
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
    'normalized. Each lead is scored for intent and fit from the notes, title, and email fields. '
    'The ranked list comes back with a Contact Now / Nurture / Disqualify call and the reasons behind it.</div>',
    unsafe_allow_html=True,
)

uploaded = st.file_uploader("Lead export CSV", type="csv", label_visibility="collapsed")

PILL_CLASS = {"Contact Now": "pill-contact", "Nurture": "pill-nurture", "Disqualify": "pill-disqualify"}

SCORING_EXPLAINER = """
**Guardrails first.** Non-buyers (students, recruiters, investors, spam/vendor pitches) and junk
rows get screened out before scoring starts: score 0, always Disqualify.

**Intent**, from the notes: buying language vs. hesitation, and whether a real budget number was
given (TBD, $0, and a stated number all mean something different).

**Fit**: decision-maker title, employee count in the target band, budget above the floor, and a
valid email on file. No valid email caps a lead at Nurture; you can't recommend contacting someone
you have no way to reach, however good the rest of the score looks.

**Score** = intent + fit, scaled to /100. 70+ is Contact Now, 30-69 is Nurture, below 30 is Disqualify.
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
    result = load_and_score(uploaded.getvalue()).copy()
    result["score_100"] = (result["total_score"] * 10).astype(int)

    counts = result["recommendation"].value_counts()
    source_rows = result.attrs.get("source_rows", len(result))
    duplicates_merged = result.attrs.get("duplicates_merged", 0)
    st.markdown('<div class="stat-row">', unsafe_allow_html=True)
    tiles = st.columns(4, gap="small")
    stat_tile(tiles[0], source_rows, "every row inspected")
    stat_tile(tiles[1], int(counts.get("Contact Now", 0)), "worth contacting now", highlight=True)
    stat_tile(tiles[2], int(counts.get("Nurture", 0)), "promising, not ready")
    stat_tile(tiles[3], int(counts.get("Disqualify", 0)), "junk, non-buyers, or low fit")
    st.markdown("</div>", unsafe_allow_html=True)
    if duplicates_merged:
        st.caption(f"{duplicates_merged} resubmitted duplicate{'s' if duplicates_merged != 1 else ''} merged before scoring, {len(result)} unique leads evaluated.")

    head_l, head_r = st.columns([3, 2])
    head_l.markdown('<h2 class="section-title">Lead queue</h2>', unsafe_allow_html=True)
    with head_r:
        c1, c2 = st.columns([3, 1])
        search = c1.text_input("Search", placeholder="Search name, company, notes...", label_visibility="collapsed")
        with c2:
            with st.popover("Scoring"):
                st.markdown(SCORING_EXPLAINER)

    filter_col, download_col = st.columns([3, 1], vertical_alignment="center")
    with filter_col:
        choice = st.segmented_control(
            "Filter", ["All", "Contact Now", "Nurture", "Disqualify"], default="All", label_visibility="collapsed",
        )
    with download_col:
        st.download_button(
            "Download ranked CSV",
            result.to_csv(index=False).encode("utf-8"),
            "leads_ranked.csv",
            "text/csv",
            type="primary",
            use_container_width=True,
        )

    view = result if choice in (None, "All") else result[result["recommendation"] == choice]
    if search:
        q = search.lower()
        # filters the full matching set, not just whatever page happens to be showing
        haystack = (view["name"].fillna("") + " " + view["company"].fillna("") + " "
                    + view["notes"].fillna("") + " " + view["title"].fillna("")).str.lower()
        view = view[haystack.str.contains(q, regex=False)]
    view = view.reset_index(drop=True)

    if "page_num" not in st.session_state:
        st.session_state.page_num = 1
    if "open_lead" not in st.session_state:
        st.session_state.open_lead = None

    count_col, size_col = st.columns([3, 1])
    count_col.caption(f"{len(view)} lead{'s' if len(view) != 1 else ''}")
    with size_col:
        page_size = st.selectbox(
            "Per page", [10, 20, 30], index=0, key="page_size_select", label_visibility="collapsed",
        )

    # any change to what's being viewed snaps back to page 1, never stranding you
    # on page 6 of a filtered set that only has 2 results.
    query_sig = (choice, search, page_size)
    if st.session_state.get("_query_sig") != query_sig:
        st.session_state.page_num = 1
        st.session_state._query_sig = query_sig

    total_pages = max(1, -(-len(view) // page_size))  # ceil division
    st.session_state.page_num = min(max(1, st.session_state.page_num), total_pages)
    start = (st.session_state.page_num - 1) * page_size

    COLS = [1.5, 1.1, 2.8, 0.7, 1.1]  # Lead, Company, Notes, Score, Recommendation
    header_cols = st.columns(COLS, gap="small")
    for c, label in zip(header_cols, ["Lead", "Company", "Notes", "Score", "Recommendation"]):
        c.markdown(f'<div class="header-cell">{label}</div>', unsafe_allow_html=True)

    shown = view.iloc[start:start + page_size]
    for idx, r in shown.iterrows():
        name = cell(r["name"]) or "(no name)"
        initial = name[0].upper() if name != "(no name)" else "?"
        pill = PILL_CLASS.get(r["recommendation"], "pill-nurture")
        is_open = st.session_state.open_lead == idx

        with st.container(key=f"row-{idx}"):
            row_cols = st.columns(COLS, gap="small", vertical_alignment="center")
            row_cols[0].markdown(
                f'<div style="display:flex;align-items:center;gap:0.55rem">'
                f'<div class="avatar">{initial}</div><div><div class="lead-name">{name}</div>'
                f'<div class="lead-title">{cell(r["title"]) or "Not listed"}</div></div></div>',
                unsafe_allow_html=True,
            )
            row_cols[1].markdown(f'<div class="lead-title">{cell(r["company"]) or "Not listed"}</div>', unsafe_allow_html=True)
            row_cols[2].markdown(f'<div class="lead-notes">{cell(r["notes"])}</div>', unsafe_allow_html=True)
            row_cols[3].markdown(
                f'<div class="score-cell"><span class="score-text">{int(r["score_100"])}/100</span>'
                f'<span class="bar-track"><span class="bar-fill" '
                f'style="width:{r["score_100"] * 0.56}px;display:block"></span></span></div>',
                unsafe_allow_html=True,
            )
            capped = r["total_score"] >= 7 and r["recommendation"] == "Nurture" and not r["email_valid"]
            capped_note = '<div class="capped-note">capped: no valid email</div>' if capped else ""
            row_cols[4].markdown(
                f'<div><span class="pill {pill}">{r["recommendation"]}</span>{capped_note}</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Toggle details for {name}", key=f"tog-{idx}"):
                st.session_state.open_lead = None if is_open else idx
                st.rerun()

        if is_open:
            reasons = [x.strip() for x in str(r["reasons"]).split(";") if x.strip()]
            reason_html = "".join(
                f'<div class="reason-row"><span>{x.lstrip("+-").strip()}</span>'
                f'<span class="{"reason-plus" if x.strip().startswith("+") else "reason-minus"}">'
                f'{"+" if x.strip().startswith("+") else "-"}</span></div>'
                for x in reasons
            ) or '<div class="reason-row"><span>No notable signals either way</span></div>'
            emp = cell(r["employees_clean"])
            emp_txt = f"{int(float(emp))} employees" if emp else "employee count unknown"
            budget = cell(r["budget_clean"])
            budget_txt = f"${int(float(budget)):,}/mo" if budget else "budget unknown"
            st.markdown(
                f"""<div class="detail-card">
                    <div class="detail-notes">&ldquo;{cell(r['notes'])}&rdquo;</div>
                    <div class="detail-meta">{cell(r['email']) or 'no email on file'} &middot; {emp_txt} &middot; {budget_txt}</div>
                    {reason_html}
                </div>""",
                unsafe_allow_html=True,
            )

    if total_pages > 1:
        prev_col, mid_col, next_col = st.columns([1, 3, 1])
        with prev_col:
            if st.button("< Prev", disabled=st.session_state.page_num <= 1, use_container_width=True):
                st.session_state.page_num -= 1
                st.rerun()
        mid_col.markdown(
            f'<div style="text-align:center;color:var(--muted);padding-top:0.4rem">'
            f'Page {st.session_state.page_num} of {total_pages}</div>',
            unsafe_allow_html=True,
        )
        with next_col:
            if st.button("Next >", disabled=st.session_state.page_num >= total_pages, use_container_width=True):
                st.session_state.page_num += 1
                st.rerun()
else:
    st.info("Waiting for a CSV upload.")
