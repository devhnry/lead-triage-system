import pandas as pd
import streamlit as st

from triage import process

st.set_page_config(page_title="Lead Triage", layout="wide", initial_sidebar_state="collapsed")

# ---------- design system ----------
# Editorial dashboard: warm paper ground, high-contrast serif for numbers/headings,
# system sans for UI chrome and body copy. Palette + type pinned to the reference
# screenshots the brief supplied — not a free-choice greenfield pick.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,500&display=swap');

    :root {
        --bg: oklch(97% 0.012 90);
        --surface: oklch(99% 0.004 90);
        --ink: oklch(20% 0.02 90);
        --muted: oklch(40% 0.02 90);
        --border: oklch(89% 0.012 90);
        --accent: oklch(33% 0.07 155);
        --accent-bg: oklch(91% 0.06 120);
        --nurture-bg: oklch(88% 0.06 60);
        --nurture-ink: oklch(32% 0.08 50);
        --disqualify-bg: oklch(90% 0.035 18);
        --disqualify-ink: oklch(38% 0.09 18);
        --bar: oklch(16% 0.01 90);
    }

    .stApp { background: var(--bg); }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; max-width: 1200px; }

    body, .stApp, p, span, div, label { color: var(--ink); }

    .topbar {
        height: 6px; margin: -2rem -1rem 2rem -1rem;
        background: var(--bar);
    }

    h1.page-title {
        font-family: 'Newsreader', Georgia, serif;
        font-weight: 500; font-size: 2.4rem; letter-spacing: -0.02em;
        margin: 0 0 0.15rem 0; color: var(--ink);
    }
    .page-caption { color: var(--muted); font-size: 0.95rem; margin-bottom: 1.75rem; max-width: 70ch; }

    /* stat tiles */
    .stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px;
        background: var(--border); border: 1px solid var(--border); border-radius: 10px;
        overflow: hidden; margin-bottom: 2.25rem; }
    .stat-tile { background: var(--surface); padding: 1.1rem 1.4rem; transition: background 150ms ease-out; }
    .stat-tile.highlight { background: var(--accent-bg); }
    .stat-num { font-family: 'Newsreader', Georgia, serif; font-weight: 500; font-size: 2.1rem;
        line-height: 1; color: var(--ink); font-variant-numeric: oldstyle-nums; }
    .stat-label { color: var(--muted); font-size: 0.82rem; margin-top: 0.35rem; }

    h2.section-title {
        font-family: 'Newsreader', Georgia, serif; font-weight: 500; font-size: 1.6rem;
        letter-spacing: -0.01em; margin: 0 0 1rem 0;
    }

    /* recommendation pills used in the detail panel */
    .pill { display: inline-block; padding: 0.2rem 0.7rem; border-radius: 999px;
        font-size: 0.78rem; font-weight: 600; letter-spacing: 0.01em; }
    .pill-contact { background: var(--accent-bg); color: var(--accent); }
    .pill-nurture { background: var(--nurture-bg); color: var(--nurture-ink); }
    .pill-disqualify { background: var(--disqualify-bg); color: var(--disqualify-ink); }

    .detail-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
        padding: 1.5rem 1.75rem; margin-top: 1rem; }
    .detail-name { font-family: 'Newsreader', Georgia, serif; font-size: 1.3rem; font-weight: 500; }
    .detail-meta { color: var(--muted); font-size: 0.85rem; margin-top: 0.1rem; }
    .detail-notes { font-family: 'Newsreader', Georgia, serif; font-style: italic; font-size: 1.05rem;
        margin: 1.1rem 0; line-height: 1.5; color: var(--ink); }
    .reason-row { display: flex; justify-content: space-between; padding: 0.35rem 0;
        border-bottom: 1px solid var(--border); font-size: 0.88rem; }
    .reason-row:last-child { border-bottom: none; }
    .reason-plus { color: var(--accent); font-weight: 600; }
    .reason-minus { color: var(--disqualify-ink); font-weight: 600; }

    /* lead table */
    .lead-table-wrap { border: 1px solid var(--border); border-radius: 10px; overflow: auto;
        max-height: 620px; background: var(--surface); }
    table.lead-table { width: 100%; border-collapse: collapse; font-size: 0.87rem; }
    table.lead-table thead th { position: sticky; top: 0; background: var(--surface);
        text-align: left; padding: 0.65rem 1rem; color: var(--muted); font-weight: 500;
        font-size: 0.78rem; border-bottom: 1px solid var(--border); z-index: 1; }
    table.lead-table td { padding: 0.6rem 1rem; border-bottom: 1px solid var(--border);
        vertical-align: middle; }
    table.lead-table tbody tr:last-child td { border-bottom: none; }
    table.lead-table tbody tr:hover { background: oklch(96% 0.012 90); }
    .lead-cell { display: flex; align-items: center; gap: 0.65rem; }
    .avatar { flex: none; width: 28px; height: 28px; border-radius: 999px; background: var(--accent-bg);
        color: var(--accent); font-size: 0.75rem; font-weight: 600; display: flex;
        align-items: center; justify-content: center; }
    .lead-name { font-weight: 600; line-height: 1.25; }
    .lead-title { color: var(--muted); font-size: 0.78rem; }
    .score-cell { display: flex; align-items: center; gap: 0.5rem; }
    .bar-track { width: 56px; height: 4px; border-radius: 2px; background: var(--border); }
    .bar-fill { height: 4px; border-radius: 2px; background: var(--accent); }
    .notes-cell { color: var(--muted); max-width: 340px; overflow: hidden; text-overflow: ellipsis;
        white-space: nowrap; }
    </style>
    <div class="topbar"></div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 class="page-title">Lead Triage</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-caption">Upload a lead export CSV. Dates, employee counts, and budget get '
    'normalized; each lead is scored for intent and fit from the notes and title fields; '
    'the ranked list comes back with a Contact Now / Nurture / Disqualify call and the reasons behind it.</div>',
    unsafe_allow_html=True,
)

uploaded = st.file_uploader("Lead export CSV", type="csv", label_visibility="collapsed")

PILL_CLASS = {"Contact Now": "pill-contact", "Nurture": "pill-nurture", "Disqualify": "pill-disqualify"}


def stat_tile(container, number, label, highlight=False):
    cls = "stat-tile highlight" if highlight else "stat-tile"
    container.markdown(
        f'<div class="{cls}"><div class="stat-num">{number}</div>'
        f'<div class="stat-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


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

    st.markdown('<h2 class="section-title">Lead queue</h2>', unsafe_allow_html=True)
    choice = st.segmented_control(
        "Filter",
        ["All", "Contact Now", "Nurture", "Disqualify"],
        default="All",
        label_visibility="collapsed",
    )
    view = result if choice in (None, "All") else result[result["recommendation"] == choice]
    view = view.reset_index(drop=True)

    def cell(v):
        return "" if pd.isna(v) else str(v)

    rows_html = []
    for _, r in view.iterrows():
        name = cell(r["name"]) or "(no name)"
        initial = name[0].upper() if name != "(no name)" else "?"
        pill = PILL_CLASS.get(r["recommendation"], "pill-nurture")
        rows_html.append(
            f"""<tr>
                <td><div class="lead-cell"><div class="avatar">{initial}</div>
                    <div><div class="lead-name">{name}</div><div class="lead-title">{cell(r['title']) or '&mdash;'}</div></div></div></td>
                <td>{cell(r['company']) or '&mdash;'}</td>
                <td><div class="score-cell"><div class="bar-track"><div class="bar-fill" style="width:{r['score_100']}%"></div></div>
                    <span>{int(r['score_100'])}/100</span></div></td>
                <td><span class="pill {pill}">{r['recommendation']}</span></td>
                <td class="notes-cell">{cell(r['notes'])}</td>
            </tr>"""
        )

    st.markdown(
        f"""<div class="lead-table-wrap"><table class="lead-table">
            <thead><tr><th>Lead</th><th>Company</th><th>Score</th><th>Verdict</th><th>Notes</th></tr></thead>
            <tbody>{''.join(rows_html)}</tbody>
        </table></div>""",
        unsafe_allow_html=True,
    )

    st.write("")
    options = ["Select a lead to inspect…"] + [
        f"{cell(r['name']) or '(no name)'} · {cell(r['company']) or 'no company'} · {r['recommendation']}"
        for _, r in view.iterrows()
    ]
    picked = st.selectbox("Inspect a lead", options, label_visibility="collapsed")

    if picked != options[0]:
        lead = view.iloc[options.index(picked) - 1]
        reasons = [r.strip() for r in str(lead["reasons"]).split(";") if r.strip()]
        reason_html = "".join(
            f'<div class="reason-row"><span>{r.lstrip("+-").strip()}</span>'
            f'<span class="{"reason-plus" if r.strip().startswith("+") else "reason-minus"}">'
            f'{"+" if r.strip().startswith("+") else "−"}</span></div>'
            for r in reasons
        ) or '<div class="reason-row"><span>No notable signals either way</span></div>'

        pill = PILL_CLASS.get(lead["recommendation"], "pill-nurture")
        st.markdown(
            f"""
            <div class="detail-card">
                <span class="pill {pill}">{lead['recommendation']}</span>
                <span style="float:right" class="detail-meta">{int(lead['score_100'])}/100</span>
                <div class="detail-name">{cell(lead['name']) or '(no name)'} &middot; {cell(lead['company']) or '(no company)'}</div>
                <div class="detail-meta">{cell(lead['title']) or 'Title unknown'} &middot; {cell(lead['email'])}</div>
                <div class="detail-notes">&ldquo;{cell(lead['notes'])}&rdquo;</div>
                {reason_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("Pick a lead above to see the score breakdown behind it.")

    st.download_button(
        "Download ranked CSV",
        result.to_csv(index=False).encode("utf-8"),
        "leads_ranked.csv",
        "text/csv",
    )
else:
    st.info("Waiting for a CSV upload.")
