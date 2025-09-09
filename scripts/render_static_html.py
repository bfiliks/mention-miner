import json, pathlib, networkx as nx
from pyvis.network import Network
from mention_miner.graph import build_comention_graph

out = pathlib.Path("data/kirilloff")
m = json.loads((out/"mentions.json").read_text(encoding="utf-8"))

G = build_comention_graph(m)

# Precompute positions (static)
pos = nx.spring_layout(G, seed=42, k=0.7, iterations=200)
scale = 800

net = Network(height="700px", width="100%", notebook=False, directed=False)
for n in G.nodes():
    strength = sum(G[n][nbr].get("weight", 1) for nbr in G.neighbors(n))
    x, y = pos[n]
    net.add_node(
        n, label=n, value=max(1, strength), title=f"Strength: {strength}",
        x=int(x*scale), y=int(y*scale), physics=False, fixed=True
    )
for u, v, d in G.edges(data=True):
    net.add_edge(u, v, value=d.get("weight", 1), physics=False)

# Hard-disable physics globally
net.set_options('{"physics":{"enabled":false},"interaction":{"hover":true,"zoomView":true,"dragView":true}}')
net.write_html(str(out/"mentions_network.html"), notebook=False)
print("Wrote:", out/"mentions_network.html"))
