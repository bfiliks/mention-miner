
import json
from pathlib import Path
import click
from .extract import Extractor
from .normalize import disambiguate
from .graph import build_comention_graph, export_json
from .visualize import to_pyvis

@click.group()
def main():
    """mention-miner CLI"""

@main.command("run-batch")
@click.option("--text_dir", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("--out_dir", type=click.Path(file_okay=False), default="data/processed")
def run_batch(text_dir, out_dir):
    text_dir = Path(text_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extractor = Extractor()
    all_mentions = []
    for p in sorted(text_dir.glob("*.txt")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        ms = extractor.extract(text, doc_id=p.stem)
        ms = disambiguate(ms)
        all_mentions.extend(ms)

    export_json(all_mentions, out_dir / "mentions.json")
    G = build_comention_graph(all_mentions)
    html = to_pyvis(G, str(out_dir / "mentions_network.html"))
    click.echo(f"Saved mentions to {out_dir/'mentions.json'} and network to {html}")
