# scripts/make_reading_list.py
"""
Generate a Starter Reading List from co-mentions.

Usage:
  python scripts/make_reading_list.py
  python scripts/make_reading_list.py -i data/kirilloff/mentions.json -o data/kirilloff/reading_list.md
  python scripts/make_reading_list.py --verified-only --top 30 --contexts-per 4
"""
from __future__ import annotations
import argparse, json, textwrap
from pathlib import Path
from typing import Dict, List
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities
from mention_miner.graph import build_comention_graph

def load_mentions(preferred: Path | None) -> tuple[List[dict], Path]:
    candidates = []
    if preferred:
        candidates.append(preferred)
    candidates += [
        Path("data/kirilloff_big/mentions.json"),
        Path("data/kirilloff/mentions.json"),
        Path("data/processed/mentions.json"),
    ]
    for p in candidates:
        if p and p.exists():
            return json.loads(p.read_text(encoding="utf-8")), p
    raise FileNotFoundError("Could not find mentions.json. Run the extractor first.")

def unique_keep_order(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def collect_contexts(mentions: List[dict]) -> Dict[str, List[str]]:
    by = {}
    for m in mentions:
        if m.get("mention_type") != "person": continue
        nm = m.get("norm_name") or m.get("span_text","")
        if not nm: continue
        sent = (m.get("sentence_text") or "").strip()
        if sent:
            by.setdefault(nm, []).append(" ".join(sent.split()))
    for k, v in by.items():
        by[k] = unique_keep_order(v)
    return by

def rank_nodes(G: nx.Graph):
    if G.number_of_nodes() == 0:
        return [], {}, {}, {"betweenness": {}, "community": {}}
    degree = dict(G.degree())
    strength = {n: sum(G[n][nbr].get("weight",1) for nbr in G.neighbors(n)) for n in G}
    betw = nx.betweenness_centrality(G, weight="weight", normalized=True) if G.number_of_edges() else {n:0.0 for n in G}
    try:
        coms = list(greedy_modularity_communities(G, weight="weight"))
        comm = {n:i for i,c in enumerate(coms) for n in c}
    except Exception:
        comm = {n:-1 for n in G}
    ranking = sorted(G.nodes(), key=lambda n: (-strength[n], -degree[n], n.lower()))
    return ranking, strength, degree, {"betweenness": betw, "community": comm}

def make_markdown(ranking, strength, degree, extras, contexts, top_n, contexts_per, source_path: Path) -> str:
    betw, comm = extras["betweenness"], extras["community"]
    total_nodes = len(ranking)
    header = f"""# Starter Reading List (from co-mentions)

_Source:_ `{source_path.as_posix()}`
_Nodes:_ **{total_nodes}** — showing top **{min(top_n, total_nodes)}**

**How to read:** Higher **strength** = stronger presence via repeated co-mentions;  
**degree** = breadth of connections; **betweenness** = bridge role; **community** = cluster ID.
"""
    lines = [header.strip(), ""]
    for i, name in enumerate(ranking[:top_n], start=1):
        s, d, b, c = strength.get(name,0), degree.get(name,0), betw.get(name,0.0), comm.get(name,-1)
        lines.append(f"## {i}. {name}")
        lines.append(f"- **strength**: {s}  |  **degree**: {d}  |  **betweenness**: {b:.3f}  |  **community**: {c}")
        cx = contexts.get(name, [])[:contexts_per]
        if cx:
            lines.append("- **Contexts:**")
            for sent in cx:
                lines.append(f"  - {textwrap.fill(sent, width=100)}")
        lines.append("- **Key works to check:** _(add 2–3 works)_")
        lines.append("")
    lines.append("---\n### Communities overview")
    by_comm = {}
    for n in ranking:
        by_comm.setdefault(comm.get(n,-1), []).append(n)
    for cid, names in sorted(by_comm.items()):
        if cid == -1: continue
        top = ", ".join(names[:10])
        lines.append(f"- **Community {cid}**: {top}" + ("..." if len(names) > 10 else ""))
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description="Generate a Starter Reading List from co-mentions.")
    ap.add_argument("-i","--input", type=Path, default=None, help="Path to mentions.json (defaults to kirilloff_big/kirilloff/processed lookup)")
    ap.add_argument("-o","--output", type=Path, default=None, help="Output Markdown path (default: reading_list.md next to input)")
    ap.add_argument("--verified-only", action="store_true", help="Use only mentions with is_person_verified=True")
    ap.add_argument("--top", type=int, default=25, help="How many scholars to include")
    ap.add_argument("--contexts-per", type=int, default=3, help="How many context sentences per scholar")
    args = ap.parse_args()

    mentions, src = load_mentions(args.input)
    if args.verified_only:
        mentions = [m for m in mentions if m.get("mention_type")=="person" and m.get("is_person_verified")]
    else:
        mentions = [m for m in mentions if m.get("mention_type")=="person"]

    G = build_comention_graph(mentions)
    ranking, strength, degree, extras = rank_nodes(G)
    contexts = collect_contexts(mentions)

    out = args.output or (src.parent / "reading_list.md")
    out.write_text(make_markdown(ranking, strength, degree, extras, contexts, args.top, args.contexts_per, src),
                   encoding="utf-8")
    print("Wrote:", out)

if __name__ == "__main__":
    main()
