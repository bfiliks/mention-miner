import json, pathlib, re
from mention_miner.graph import build_comention_graph
from mention_miner.visualize import to_pyvis

# --- lightweight cleanup so the graph looks sane ---
def clean_name(s):
    s = re.sub(r"[’']s\b", "", s)          # drop possessive "'s"
    s = re.sub(r"\becho\b", "", s)         # remove accidental "echo"
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s

p = pathlib.Path("data/processed/mentions.json")
mentions = json.loads(p.read_text(encoding="utf-8"))

for m in mentions:
    if m.get("mention_type") == "person":
        m["norm_name"] = clean_name(m.get("norm_name",""))

# Build & write HTML
G = build_comention_graph(mentions)
out = "data/processed/mentions_network.html"
to_pyvis(G, out)
print(f"Wrote {out}")
