import json, pathlib, networkx as nx, matplotlib.pyplot as plt
from mention_miner.graph import build_comention_graph

out = pathlib.Path("data/kirilloff")
m = json.loads((out/"mentions.json").read_text(encoding="utf-8"))
G = build_comention_graph(m)

plt.figure()
pos = nx.spring_layout(G, seed=42, k=0.7)
nx.draw_networkx(G, pos, with_labels=True, node_size=400, font_size=8)
plt.axis("off")
png = out/"mentions_network.png"
plt.savefig(png, dpi=200, bbox_inches="tight")
print("Wrote:", png)
