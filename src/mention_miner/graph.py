
import itertools, json
from typing import List, Dict, Any
import networkx as nx

def build_comention_graph(all_mentions: List[Dict[str, Any]], window: str="sentence"):
    G = nx.Graph()
    for m in all_mentions:
        if m["mention_type"] == "person":
            G.add_node(m["norm_name"], type="person")
    by_doc_sent = {}
    for m in all_mentions:
        if m["mention_type"]!="person":
            continue
        key = (m["doc_id"], m.get("sentence_text","") if window=="sentence" else "")
        by_doc_sent.setdefault(key, []).append(m["norm_name"])
    for _, names in by_doc_sent.items():
        for a,b in itertools.combinations(sorted(set(names)), 2):
            w = G.get_edge_data(a,b,default={"weight":0})["weight"]+1
            G.add_edge(a,b, weight=w)
    return G

def export_json(all_mentions, out_json_path):
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(all_mentions, f, indent=2, ensure_ascii=False)
