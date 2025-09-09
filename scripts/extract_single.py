from pathlib import Path
import json, sys
from mention_miner.extract import Extractor
from mention_miner.normalize import disambiguate, dedupe_person_names
from mention_miner.graph import build_comention_graph
from mention_miner.visualize import to_pyvis

inp_dir = Path("data/only_kirilloff")
txts = sorted(inp_dir.glob("*.txt"))
if not txts:
    print("No .txt in data/only_kirilloff"); sys.exit(1)
# if there are multiple, pick the newest by modified time
txt = max(txts, key=lambda p: p.stat().st_mtime)
print("Using:", txt.name)

out_dir = Path("data/kirilloff"); out_dir.mkdir(parents=True, exist_ok=True)

text = txt.read_text(encoding="utf-8", errors="ignore")
ex = Extractor(spacy_model="en_core_web_sm")

ms = ex.extract(text, doc_id=txt.stem)
ms = disambiguate(ms)
ms = dedupe_person_names(ms)

(out_dir / "mentions.json").write_text(json.dumps(ms, indent=2, ensure_ascii=False), encoding="utf-8")
G = build_comention_graph(ms)
to_pyvis(G, str(out_dir / "mentions_network.html"))

print("Wrote:", out_dir / "mentions.json")
print("Wrote:", out_dir / "mentions_network.html")
