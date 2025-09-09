from pathlib import Path
import json
from mention_miner.extract import Extractor
from mention_miner.normalize import disambiguate, dedupe_person_names
from mention_miner.graph import build_comention_graph
from mention_miner.visualize import to_pyvis

MODEL = "en_core_web_lg"  # change to "en_core_web_trf" only if you installed transformers
IN_DIR = Path("data/only_kirilloff")
OUT_DIR = Path("data/kirilloff_big"); OUT_DIR.mkdir(parents=True, exist_ok=True)

# pick the newest .txt in only_kirilloff
txts = sorted(IN_DIR.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
if not txts:
    raise SystemExit("No .txt files found in data/only_kirilloff")
inp = txts[0]

text = inp.read_text(encoding="utf-8", errors="ignore")
ex = Extractor(spacy_model=MODEL)
ms = ex.extract(text, doc_id=inp.stem)
ms = disambiguate(ms)
ms = dedupe_person_names(ms)

(OUT_DIR/"mentions.json").write_text(json.dumps(ms, indent=2, ensure_ascii=False), encoding="utf-8")
to_pyvis(build_comention_graph(ms), str(OUT_DIR/"mentions_network.html"))
print("Wrote:", OUT_DIR/"mentions.json")
print("Wrote:", OUT_DIR/"mentions_network.html")
