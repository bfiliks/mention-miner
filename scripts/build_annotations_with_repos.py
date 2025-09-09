# scripts/build_annotations_with_repos.py
"""
Build per-scholar annotation pages with (optional) GitHub repository lookups for:
  - "digital humanities"
  - "cultural analytics"
  - "computational text analytics"
plus a per-scholar query.

Usage (from repo root, venv active):
  python scripts/build_annotations_with_repos.py --include-repos
  python scripts/build_annotations_with_repos.py -i data/kirilloff/mentions.json -o notes --include-repos
  python scripts/build_annotations_with_repos.py --verified-only --include-repos --repos-per 5 --global-repos-per 12

Environment:
  GITHUB_TOKEN  (optional) – increases rate limits and avoids abuse detection
"""

from __future__ import annotations
import argparse, json, os, re, textwrap, time
from pathlib import Path
from typing import Dict, List, Tuple
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

import requests
try:
    from tqdm import tqdm
except Exception:
    tqdm = None

from mention_miner.graph import build_comention_graph

# -------------------------- data loading --------------------------
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

def metrics(G: nx.Graph):
    deg = dict(G.degree())
    strength = {n: sum(G[n][nbr].get("weight", 1) for nbr in G.neighbors(n)) for n in G}
    betw = nx.betweenness_centrality(G, weight="weight", normalized=True) if G.number_of_edges() else {n: 0.0 for n in G}
    try:
        coms = list(greedy_modularity_communities(G, weight="weight"))
        comm = {n: i for i, c in enumerate(coms) for n in c}
    except Exception:
        comm = {n: -1 for n in G}
    return deg, strength, betw, comm

def top_partners(G: nx.Graph, name: str, k: int = 10):
    if name not in G:
        return []
    rows = [(nbr, G[name][nbr].get("weight", 1)) for nbr in G.neighbors(name)]
    rows.sort(key=lambda x: (-x[1], x[0].lower()))
    return rows[:k]

def collect_contexts(mentions: List[dict]) -> Dict[str, List[str]]:
    by = {}
    for m in mentions:
        if m.get("mention_type") != "person": continue
        nm = m.get("norm_name") or m.get("span_text","")
        sent = (m.get("sentence_text") or "").strip()
        if not nm or not sent: continue
        sent = " ".join(sent.split())
        by.setdefault(nm, [])
        if sent not in by[nm]:
            by[nm].append(sent)
    return by

# -------------------------- GitHub search --------------------------
GITHUB_API = "https://api.github.com/search/repositories"
GH_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if os.getenv("GITHUB_TOKEN"):
    GH_HEADERS["Authorization"] = f"Bearer {os.getenv('GITHUB_TOKEN')}"

GLOBAL_QUERIES = [
    'topic:"digital-humanities"',
    '"digital humanities" in:name,description,readme',
    '"cultural analytics" in:name,description,readme',
    '"computational text analytics" in:name,description,readme',
]

def gh_search(q: str, per_page: int = 30, pages: int = 2):
    """Search GitHub repos; returns list of repo dicts (deduped)."""
    seen, out = set(), []
    for page in range(1, pages + 1):
        params = {"q": q, "sort": "stars", "order": "desc", "per_page": per_page, "page": page}
        r = requests.get(GITHUB_API, params=params, headers=GH_HEADERS, timeout=20)
        if r.status_code == 403 and "rate limit" in r.text.lower():
            # backoff if rate limited
            time.sleep(60)
            r = requests.get(GITHUB_API, params=params, headers=GH_HEADERS, timeout=20)
        r.raise_for_status()
        items = r.json().get("items", [])
        for it in items:
            key = it.get("full_name")
            if key and key not in seen:
                seen.add(key)
                out.append({
                    "full_name": key,
                    "html_url": it.get("html_url"),
                    "description": it.get("description") or "",
                    "stargazers_count": it.get("stargazers_count", 0),
                    "language": it.get("language") or "",
                    "topics": ", ".join(it.get("topics", [])),
                })
        # stop early if last page small
        if len(items) < per_page: break
        time.sleep(0.3)
    return out

def repos_for_scholar(name: str, limit: int = 5):
    # search name plus DH/CA/CTA signals
    name_q = re.sub(r'["\']', "", name)
    q = f'"{name_q}" (text OR "text analysis" OR "digital humanities" OR "cultural analytics") in:readme,description'
    results = gh_search(q, per_page=30, pages=1)
    # filter out obvious noise and forks
    filt = [r for r in results if "fork" not in r["full_name"].lower()]
    filt.sort(key=lambda r: -r["stargazers_count"])
    return filt[:limit]

def global_repos(limit_per_query: int = 8):
    rows = []
    for q in GLOBAL_QUERIES:
        res = gh_search(q + " stars:>10 fork:false", per_page=30, pages=1)
        res.sort(key=lambda r: -r["stargazers_count"])
        rows.extend(res[:limit_per_query])
    # dedupe by full_name across queries; keep top by stars
    by = {}
    for r in rows:
        k = r["full_name"]
        if k not in by or r["stargazers_count"] > by[k]["stargazers_count"]:
            by[k] = r
    return sorted(by.values(), key=lambda r: -r["stargazers_count"])

# -------------------------- rendering --------------------------
def sanitize_filename(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_") or "scholar"

def render_markdown(meta: Dict, partners: List[Tuple[str, int]], contexts: List[str],
                    works_md: str, repos_md: str) -> str:
    front = [
        "---",
        f'title: "{meta.get("title","")}"',
        f'strength: {meta.get("strength",0)}',
        f'degree: {meta.get("degree",0)}',
        f'betweenness: {meta.get("betweenness",0.0)}',
        f'community: {meta.get("community",-1)}',
        "---",
        "",
        f"# {meta.get('title','Scholar')}",
        "",
        f"**Metrics:** strength={meta.get('strength',0)}, degree={meta.get('degree',0)}, "
        f"betweenness={meta.get('betweenness',0.0):.3f}, community={meta.get('community',-1)}",
        "",
        "## Overview",
        "_Add your summary here._",
        "",
        "## Relevant Repositories",
        repos_md or "_(Add or run with --include-repos to auto-fill.)_",
        "",
        "## Key Works (optional, from OpenAlex)",
        works_md or "_(You can enrich with the previous --fetch-works script if desired.)_",
        "",
        "## Top Co-mentions",
    ]
    if partners:
        for p, w in partners[:12]:
            front.append(f"- **{p}** (w={w})")
    else:
        front.append("_No strong co-mentions found._")
    front += ["", "## Context Sentences (from your corpus)"]
    if contexts:
        for s in contexts[:6]:
            front.append(f"- {textwrap.fill(s, width=100)}")
    else:
        front.append("_No example sentences captured._")
    front += ["", "## Notes / Quotes", "- ", "", "## Related Links",
              "- Google Scholar: https://scholar.google.com/scholar?q=" + meta.get("title","").replace(" ", "+"), ""]
    return "\n".join(front)

# -------------------------- main build --------------------------
def build_annotations(mentions: List[dict], outdir: Path, top: int,
                      verified_only: bool, include_repos: bool,
                      repos_per: int, global_repos_per: int, source_path: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    people = [m for m in mentions if m.get("mention_type") == "person"]
    if verified_only:
        people = [m for m in people if m.get("is_person_verified")]

    G = build_comention_graph(people)
    deg, strength, betw, comm = metrics(G)
    ranking = sorted(G.nodes(), key=lambda n: (-strength.get(n,0), -deg.get(n,0), n.lower()))
    if top > 0:
        ranking = ranking[:top]

    contexts = collect_contexts(people)

    # Global repo catalog
    global_catalog = []
    if include_repos:
        global_catalog = global_repos(limit_per_query=global_repos_per)

    # Write a CSV catalog of repos
    if include_repos:
        import csv
        rcsv = outdir / "repos_catalog.csv"
        with rcsv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["scope","full_name","html_url","description","stars","language","topics"])
            for r in global_catalog:
                w.writerow(["global", r["full_name"], r["html_url"], r["description"], r["stargazers_count"], r["language"], r["topics"]])

    index_lines = [
        "# Scholar Annotations (with Repositories)",
        "",
        f"_Source: {source_path.as_posix()}_",
        "",
        "| Scholar | strength | degree | betweenness | community |",
        "|---|---:|---:|---:|---:|",
    ]

    iterator = ranking if tqdm is None else tqdm(ranking, desc="Annotating")
    for name in iterator:
        partners = top_partners(G, name, k=12)
        cx = contexts.get(name, [])[:6]
        meta = {
            "title": name,
            "strength": strength.get(name, 0),
            "degree": deg.get(name, 0),
            "betweenness": round(float(betw.get(name, 0.0)), 6),
            "community": int(comm.get(name, -1)),
        }

        # Per-scholar repos
        repos_md = ""
        if include_repos:
            per = repos_for_scholar(name, limit=repos_per)
            # append per-scholar to catalog CSV
            import csv
            rcsv = outdir / "repos_catalog.csv"
            with rcsv.open("a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                for r in per:
                    w.writerow([name, r["full_name"], r["html_url"], r["description"], r["stargazers_count"], r["language"], r["topics"]])

            if global_catalog:
                repos_md += "**Field Repositories (selected):**\n"
                for r in global_catalog[:global_repos_per]:
                    line = f"- [{r['full_name']}]({r['html_url']}) ★{r['stargazers_count']} — {r['description'][:160]}"
                    repos_md += line + "\n"
                repos_md += "\n"
            repos_md += "**Name-related Repositories:**\n" if per else ""
            for r in per:
                line = f"- [{r['full_name']}]({r['html_url']}) ★{r['stargazers_count']} — {r['description'][:160]}"
                repos_md += line + "\n"

        md = render_markdown(meta, partners, cx, works_md="", repos_md=repos_md)
        fn = outdir / (sanitize_filename(name) + ".md")
        fn.write_text(md, encoding="utf-8")

        index_lines.append(f"| [{name}]({fn.name}) | {meta['strength']} | {meta['degree']} | {meta['betweenness']:.3f} | {meta['community']} |")

    (outdir / "INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    return outdir

def main():
    ap = argparse.ArgumentParser(description="Build scholar annotations with GitHub repository lookups.")
    ap.add_argument("-i","--input", type=Path, default=None, help="Path to mentions.json (defaults to kirilloff_big/kirilloff/processed lookup)")
    ap.add_argument("-o","--outdir", type=Path, default=Path("annotations_repos"), help="Output directory")
    ap.add_argument("--verified-only", action="store_true", help="Use only mentions flagged is_person_verified=True")
    ap.add_argument("--top", type=int, default=25, help="Number of scholars to annotate (ranked by strength)")
    ap.add_argument("--include-repos", action="store_true", help="Search GitHub for relevant repositories and include them")
    ap.add_argument("--repos-per", type=int, default=5, help="Per-scholar repo count")
    ap.add_argument("--global-repos-per", type=int, default=10, help="Field repo count (per combined global query set)")
    args = ap.parse_args()

    mentions, src = load_mentions(args.input)
    outdir = build_annotations(
        mentions=mentions,
        outdir=args.outdir,
        top=args.top,
        verified_only=args.verified_only,
        include_repos=args.include_repos,
        repos_per=args.repos_per,
        global_repos_per=args.global_repos_per,
        source_path=src,
    )
    print("Wrote annotation set to:", outdir / "INDEX.md")
    if args.include_repos:
        print("Repo catalog:", outdir / "repos_catalog.csv")

if __name__ == "__main__":
    main()
