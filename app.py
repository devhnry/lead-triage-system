import pandas as pd
import streamlit as st

from triage import process

st.set_page_config(page_title="Lead Triage", layout="wide")
st.title("Lead Triage System")
st.caption(
    "Upload a lead export CSV. The system cleans dates/employees/budget, "
    "scores intent + fit from the notes field, and ranks leads with a "
    "Contact Now / Nurture / Disqualify recommendation."
)

uploaded = st.file_uploader("Lead export CSV", type="csv")

if uploaded:
    raw = pd.read_csv(uploaded)
    result = process(raw)

    counts = result["recommendation"].value_counts()
    c1, c2, c3 = st.columns(3)
    c1.metric("Contact Now", int(counts.get("Contact Now", 0)))
    c2.metric("Nurture", int(counts.get("Nurture", 0)))
    c3.metric("Disqualify", int(counts.get("Disqualify", 0)))

    tab = st.selectbox("Filter", ["All", "Contact Now", "Nurture", "Disqualify"])
    view = result if tab == "All" else result[result["recommendation"] == tab]

    st.dataframe(
        view[
            [
                "lead_id", "name", "company", "title", "total_score", "intent_score",
                "fit_score", "recommendation", "budget_clean", "employees_clean",
                "reasons", "notes",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download ranked CSV",
        result.to_csv(index=False).encode("utf-8"),
        "leads_ranked.csv",
        "text/csv",
    )
else:
    st.info("Waiting for a CSV upload.")
