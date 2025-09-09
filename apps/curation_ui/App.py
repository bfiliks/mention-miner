
import json
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Mention Miner – Curation", layout="wide")
st.title("Mention Miner – Curation UI")

processed_dir = Path("data/processed")
processed_dir.mkdir(parents=True, exist_ok=True)
json_path = processed_dir / "mentions.json"
curated_path = processed_dir / "mentions_curated.csv"

if json_path.exists():
    data = json.loads(json_path.read_text(encoding="utf-8"))
    df = pd.DataFrame(data)
else:
    st.info("No data found. Run the extractor first.")
    st.stop()

st.sidebar.header("Filters")
doc_ids = sorted(df["doc_id"].unique())
doc_sel = st.sidebar.multiselect("Documents", doc_ids, default=doc_ids)
type_sel = st.sidebar.multiselect("Mention type", sorted(df["mention_type"].unique()), default=["person"])

view = df[df["doc_id"].isin(doc_sel) & df["mention_type"].isin(type_sel)].copy()
view["decision"] = ""
view["new_norm_name"] = view["norm_name"]

st.write("### Mentions")
st.dataframe(view[["doc_id","span_text","norm_name","mention_type","source_type","sentence_text","decision","new_norm_name"]], use_container_width=True)

st.write("---")
st.write("### Export")
if st.button("Save curation CSV"):
    out = view[["doc_id","span_text","norm_name","new_norm_name","mention_type","source_type","sentence_text","confidence"]].copy()
    out.rename(columns={"new_norm_name":"curated_norm_name"}, inplace=True)
    out.to_csv(curated_path, index=False)
    st.success(f"Saved to {curated_path}")
