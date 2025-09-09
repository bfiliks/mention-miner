# scripts/export_csv.py
import json
from pathlib import Path
import pandas as pd
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities
from mention_miner.graph import build_comention_graph

def load_mentions(p: Path) -> list:
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    alt = Path("data/processed/mentions.json")
    if alt.exists():
        print(f"[info] {p} not found; using {alt}")
        return json.loads(alt.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"Missing {p} (and {alt}). Run the extractor first.")

def to_tables(G: nx.Graph):
    if G.number_of_nodes() == 0:
        return (pd.DataFrame(columns=["name","degree","strength","betweenness","community"]),
                pd.DataFrame(columns=["source","target","weight"]))
    deg = dict(G.degree())
    strength = {n: sum(G[n][nbr].get("weight",1) for nbr in G.neighbors(n)) for n in G}
    btw = nx.betweenness_centrality(G, weight="weight", normalized=True)
    try:
        coms = list(greedy_modularity_communities(G, weight="weight"))
    except Exception:
        coms = []
    cid = {n:i for i,c in enumerate(coms) for n in c}
    nodes = pd.DataFrame({
        "name": list(G.nodes()),
        "degree": [deg[n] for n in G],
        "strength": [strength[n] for n in G],
        "betweenness": [btw[n] for n in G],
        "community": [cid.get(n,-1) for n in G],
    }).sort_values("strength", ascending=False)
    edges = pd.DataFrame([(u,v,d.get("weight",1)) for u,v,d in G.edges(data=True)],
                         columns=["source","target","weight"])
    return nodes, edges

# --- main ---
inp = Path("data/kirilloff_big/mentions.json")  # change to data/kirilloff/mentions.json if needed
m = load_mentions(inp)
G = build_comention_graph(m)
outdir = inp.parent
outdir.mkdir(parents=True, exist_ok=True)
nodes, edges = to_tables(G)
nodes.to_csv(outdir/"nodes.csv", index=False)
edges.to_csv(outdir/"edges.csv", index=False)
print("Wrote:", outdir/"nodes.csv")
print("Wrote:", outdir/"edges.csv")
