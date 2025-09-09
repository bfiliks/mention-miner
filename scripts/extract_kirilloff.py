from pathlib import Path
import json
from mention_miner.extract import Extractor
from mention_miner.normalize import disambiguate
from mention_miner.graph import build_comention_graph
from mention_miner.visualize import to_pyvis

in_path  = Path("data/only_kirilloff/Kirilloff.txt")
out_dir  = Path("data/kirilloff"); out_dir.mkdir(parents=True, exist_ok=True)

text = in_path.read_text(encoding="utf-8", errors="ignore")
ex   = Extractor(spacy_model="en_core_web_sm")  # use small model
mentions = disambiguate(ex.extract(text, doc_id="Kirilloff"))

(out_dir/"mentions.json").write_text(json.dumps(mentions, indent=2, ensure_ascii=False), encoding="utf-8")
G = build_comention_graph(mentions)
to_pyvis(G, str(out_dir/"mentions_network.html"))
print("Wrote:", out_dir/"mentions.json", "and", out_dir/"mentions_network.html")
