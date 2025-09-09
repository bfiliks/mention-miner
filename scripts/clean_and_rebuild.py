# scripts/clean_and_rebuild.py
"""
Clean mentions to remove non-people and list-like cliques, then rebuild outputs.

Key fixes:
- Single-token names are kept ONLY if is_person_verified=True
- Drop common work/character titles (e.g., "Moby Dick", "Jane Eyre", "Uncle Tom")
  and names in sentences that contain strong work-context hints (e.g., "novel",
  "Project Gutenberg", "character"), unless verified.
- Still removes jumbo list-like sentences (> MAX_SENT_FANOUT names).

Writes next to your latest mentions.json (kirilloff_big -> kirilloff -> processed):
  - mentions_clean.json
  - mentions_network_clean.html
  - nodes_clean.csv, edges_clean.csv
  - reading_list_clean.md
"""

from __future__ import annotations
import json, re, itertools, textwrap
from pathlib import Path
from typing import Dict, List, Tuple
import networkx as nx

# ---------- config ----------
TARGET_DIRS = [Path("data/kirilloff_big"), Path("data/kirilloff"), Path("data/processed")]
MAX_SENT_FANOUT = 8

# Hard blacklists (you can extend via file: data/dictionaries/non_person_blacklist.txt)
NONPERSON_EXACT = {
    "Digital Humanities",
    "Moby Dick",
    "Jane Eyre",
    "Uncle Tom",
    "Frankenstein",
}
WORK_HINTS = {
    "novel", "novels", "fiction", "character", "characters",
    "project gutenberg", "gutenberg",
}

STOP_SINGLE = {
    "In","On","For","This","That","The","A","An","And","But","Or",
    "Year","Digital","Humanities","Computation","Context"
}
GOOD_TOKEN = re.compile(r"^[A-Z][a-z\-'.]*$")   # allows J., O'Neil, Jean-Paul
HAS_DIGIT = re.compile(r"\d")

def load_blacklist() -> set[str]:
    p = Path("data/dictionaries/non_person_blacklist.txt")
    if p.exists():
        items = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        return NONPERSON_EXACT.union(items)
    return NONPERSON_EXACT

def sentence_key(m: dict) -> Tuple[str, str]:
    return (m.get("doc_id",""), (m.get("sentence_text") or "").strip())

def looks_like_nonperson_by_context(name: str, sentence: str, verified: bool, blacklist: set[str]) -> bool:
    if verified:
        return False
    if name in blacklist:
        return True
    s = (sentence or "").lower()
    if any(h in s for h in WORK_HINTS):
        toks = name.split()
        # treat 1-3 all-TitleCase tokens as likely work/character titles
        if 1 <= len(toks) <= 3 and all(t[:1].isupper() for t in toks):
            return True
    return False

def looks_like_person(name: str, verified: bool) -> bool:
    if not name:
        return False
    if HAS_DIGIT.search(name):
        return False
    if len(name) > 80:
        return False
    if name.isupper():
        return False

    toks = name.split()

    # ---- Single-token rule: require verification
    if len(toks) == 1:
        return bool(verified)  # ONLY keep single-token names if verified (e.g., "Liu" but verified)

    # ---- Multi-token: require most tokens to look like names/initials
    good = 0
    for t in toks:
        if re.fullmatch(r"[A-Z]\.", t):            # initials like "J."
            good += 1
        elif GOOD_TOKEN.match(t):                  # Title-case words
            good += 1
        elif t.lower() in {"de","van","von","da","dos","del","la","le","di","and","of"}:
            good += 1
    return good / len(toks) >= 0.6

def pick_input_dir() -> Path:
    for d in TARGET_DIRS:
        if (d / "mentions_linked.json").exists(): return d
        if (d / "mentions_verified.json").exists(): return d
        if (d / "mentions.json").exists(): return d
    raise SystemExit("No mentions.json found in data/kirilloff_big, data/kirilloff, or data/processed")

def load_mentions(base: Path) -> List[dict]:
    for name in ["mentions_linked.json", "mentions_verified.json", "mentions.json"]:
        p = base / name
        if p.exists():
            print("[info] using", p.as_posix())
            return json.loads(p.read_text(encoding="utf-8"))
    raise SystemExit("No mentions*.json present.")

def clean_mentions(ms: List[dict]) -> List[dict]:
    blacklist = load_blacklist()

    # preliminary pass: keep only person-type + name-like + not work/character by context
    kept = []
    for m in ms:
        if m.get("mention_type") != "person":
            continue
        nm = (m.get("norm_name") or m.get("span_text") or "").strip()
        if not nm:
            continue
        verified = bool(m.get("is_person_verified"))
        sent = (m.get("sentence_text") or "").strip()

        # drop single-token unless verified
        toks = nm.split()
        if len(toks) == 1 and not verified:
            continue

        # generic person-ish shape
        if not looks_like_person(nm, verified):
            continue

        # drop obvious non-persons by context/blacklist
        if looks_like_nonperson_by_context(nm, sent, verified, blacklist):
            continue

        # drop trivial capitalized function words (paranoia)
        if len(toks) == 1 and toks[0] in STOP_SINGLE:
            continue

        m["norm_name"] = nm
        kept.append(m)

    # group per sentence to drop jumbo list-like cliques
    by_sent: Dict[Tuple[str,str], List[dict]] = {}
    for m in kept:
        by_sent.setdefault(sentence_key(m), []).append(m)

    out = []
    for k, group in by_sent.items():
        uniq_names = sorted({g["norm_name"] for g in group})
        if len(uniq_names) > MAX_SENT_FANOUT:
            # skip entire sentence (e.g., bibliography-like enumerations)
            continue
        out.extend(group)
    return out

def build_graph_from_mentions(ms: List[dict]) -> nx.Graph:
    G = nx.Graph()
    ms = [m for m in ms if m.get("mention_type")=="person"]
    # group per sentence, connect unique names in that sentence
    for (_, _sent), group in itertools.groupby(sorted(ms, key=sentence_key), key=sentence_key):
        ppl = sorted({g["norm_name"] for g in group})
        if len(ppl) < 2:
            continue
        for i in range(len(ppl)):
            for j in range(i+1, len(ppl)):
                u, v = ppl[i], ppl[j]
                w = G[u][v]["weight"] + 1 if G.has_edge(u, v) else 1
                G.add_edge(u, v, weight=w)
    return G

def export_csvs(G: nx.Graph, outdir: Path):
    import pandas as pd
    deg = dict(G.degree())
    strength = {n: sum(G[n][nbr].get("weight",1) for nbr in G.neighbors(n)) for n in G}
    btw = nx.betweenness_centrality(G, weight="weight", normalized=True) if G.number_of_edges() else {n:0.0 for n in G}
    try:
        from networkx.algorithms.community import greedy_modularity_communities
        coms = list(greedy_modularity_communities(G, weight="weight"))
        cid = {n:i for i,c in enumerate(coms) for n in c}
    except Exception:
        cid = {n:-1 for n in G}
    nodes = pd.DataFrame({
        "name": list(G.nodes()),
        "degree": [deg[n] for n in G],
        "strength": [strength[n] for n in G],
        "betweenness": [btw[n] for n in G],
        "community": [cid.get(n,-1) for n in G],
    }).sort_values("strength", ascending=False)
    edges = pd.DataFrame([(u,v,d.get("weight",1)) for u,v,d in G.edges(data=True)],
                         columns=["source","target","weight"])
    nodes.to_csv(outdir/"nodes_clean.csv", index=False)
    edges.to_csv(outdir/"edges_clean.csv", index=False)

def write_html(G: nx.Graph, out_html: Path):
    from mention_miner.visualize import to_pyvis
    to_pyvis(G, str(out_html))

def write_reading_list(G: nx.Graph, mentions: List[dict], out_md: Path, top: int = 25):
    deg = dict(G.degree())
    strength = {n: sum(G[n][nbr].get("weight",1) for nbr in G.neighbors(n)) for n in G}
    ranking = sorted(G.nodes(), key=lambda n: (-strength[n], -deg[n], n.lower()))
    # contexts
    ctx = {}
    for m in mentions:
        nm = m.get("norm_name"); s = (m.get("sentence_text") or "").strip()
        if not nm or not s: continue
        ctx.setdefault(nm, [])
        s = " ".join(s.split())
        if s not in ctx[nm]:
            ctx[nm].append(s)

    lines = ["# Starter Reading List (CLEANED)", ""]
    for i, n in enumerate(ranking[:top], 1):
        s, d = strength[n], deg[n]
        lines.append(f"## {i}. {n}")
        lines.append(f"- **strength**: {s}  |  **degree**: {d}")
        for snip in ctx.get(n, [])[:3]:
            lines.append(f"- Context: {textwrap.fill(snip, width=100)}")
        lines.append("- Key works: _add 2–3_")
        lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")

def main():
    base = pick_input_dir()
    mentions = load_mentions(base)
    cleaned = clean_mentions(mentions)
    (base/"mentions_clean.json").write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[done] wrote", (base/"mentions_clean.json").as_posix(), f"({len(cleaned)} mentions)")

    G = build_graph_from_mentions(cleaned)
    write_html(G, base/"mentions_network_clean.html")
    print("[done] wrote", (base/"mentions_network_clean.html").as_posix())

    export_csvs(G, base)
    print("[done] wrote nodes_clean.csv and edges_clean.csv in", base.as_posix())

    write_reading_list(G, cleaned, base/"reading_list_clean.md", top=25)
    print("[done] wrote", (base/"reading_list_clean.md").as_posix())

if __name__ == "__main__":
    main()
