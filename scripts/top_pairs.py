import json, pathlib
from mention_miner.graph import build_comention_graph
p = pathlib.Path("data/kirilloff/mentions.json")
m = json.loads(p.read_text(encoding="utf-8"))
G = build_comention_graph(m)
pairs = sorted(((u,v,d["weight"]) for u,v,d in G.edges(data=True)), key=lambda x: -x[2])
print("Top co-mention pairs:")
for u,v,w in pairs[:30]:
    print(f"{w:3}  {u}  —  {v}")
