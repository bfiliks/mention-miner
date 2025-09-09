# scripts/export_csv.py
import json
import argparse
from pathlib import Path

import pandas as pd
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

from mention_miner.graph import build_comention_graph


def load_mentions(input_path: Path) -> list:
    if input_path.exists():
        return json.loads(input_path.read_text(encoding="utf-8"))
    # Fallback: try the "all files" path
    alt = Path("data/processed/mentions.json")
    if alt.exists():
        print(f"[info] {input_path} not found; using {alt}")
        return json.loads(alt.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        f"Could not find mentions JSON at {input_path} or {alt}. "
        "Run the extractor first."
    )


def to_nodes_edges(G: nx.Graph) -> tuple[pd.DataFrame, pd.DataFrame]:
    if G.number_of_nodes() == 0:
        nodes = pd.DataFrame(columns=["name", "degree", "strength", "betweenness", "community"])
        edges = pd.DataFrame(columns=["source", "target", "weight"])
        return nodes, edges

    deg = dict(G.degree())
    strength = {n: sum(G[n][nbr].get("weight", 1) for nbr in G.neighbors(n)) for n in G}
    btw = nx.betweenness_centrality(G, weight="weight", normalized=True)

    # Communities (greedy modularity)
    try:
        coms = list(greedy_modularity_communities(G, weight="weight"))
    except Exception:
        coms = []
    cid = {}
    for i, c in enumerate(coms):
        for n in c:
            cid[n] = i

    nodes = pd.DataFrame({
        "name": list(G.nodes()),
        "degree": [deg[n] for n in G],
        "strength": [strength[n] for n in G],
        "betweenness": [btw[n] for n in G],
        "community": [cid.get(n, -1) for n in G],
    }).sort_values("strength", ascending=False)

    edges = pd.DataFrame(
        [(u, v, d.get("weight", 1)) for u, v, d in G.edges(data=True)],
        columns=["source", "target", "weight"]
    )

    return nodes, edges


def main():
    parser = argparse.ArgumentParser(description="Export nodes/edges CSV from mentions.json")
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=Path("data/kirilloff/mentions.json"),
        help="Path to mentions.json (default: data/kirilloff/mentions.json; "
             "fallback to data/processed/mentions.json)"
    )
    parser.add_argument(
        "-o", "--outdir",
        type=Path,
        default=None,
        help="Output directory (default: same folder as input JSON)"
    )
    args = parser.parse_args()

    mentions = load_mentions(args.input)
    G = build_comention_graph(mentions)

    outdir = args.outdir or args.input.parent
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = to_nodes_edges(G)
    nodes_path = outdir / "nodes.csv"
    edges_path = outdir / "edges.csv"
    nodes.to_csv(nodes_path, index=False)
    edges.to_csv(edges_path, index=False)

    print(f"Wrote: {nodes_path}")
    print(f"Wrote: {edges_path}")


if __name__ == "__main__":
    main()
