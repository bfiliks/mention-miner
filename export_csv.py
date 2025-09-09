import json, pathlib, pandas as pd, networkx as nx
from mention_miner.graph import build_comention_graph

p = pathlib.Path("data/processed/mentions.json")
mentions = json.loads(p.read_text(encoding="utf-8"))
G = build_comention_graph(mentions)

# centralities & communities
deg = dict(G.degree())
strength = {n: sum(G[n][nbr]["weight"] for nbr in G.neighbors(n)) for n in G}
btw = nx.betweenness_centrality(G, weight="weight", normalized=True)

from networkx.algorithms.community import greedy_modularity_communities
coms = list(greedy_modularity_communities(G, weight="weight")) if G.number_of_nodes() else []
cid = {}
for i, c in enumerate(coms):
    for n in c: cid[n] = i

nodes = pd.DataFrame({
    "name": list(G.nodes()),
    "degree": [deg[n] for n in G],
    "strength": [strength[n] for n in G],
    "betweenness": [btw[n] for n in G],
    "community": [cid.get(n, -1) for n in G],
}).sort_values("strength", ascending=False)

edges = pd.DataFrame([(u, v, d.get("weight", 1)) for u, v, d in G.edges(data=True)],
                     columns=["source", "target", "weight"])

outdir = pathlib.Path("data/processed"); outdir.mkdir(parents=True, exist_ok=True)
nodes.to_csv(outdir / "nodes.csv", index=False)
edges.to_csv(outdir / "edges.csv", index=False)
print("Wrote data/processed/nodes.csv and data/processed/edges.csv")
