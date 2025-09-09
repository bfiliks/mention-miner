# extract_only.py
import json
from pathlib import Path
from mention_miner.extract import Extractor
from mention_miner.normalize import disambiguate

text_dir = Path("data/raw")
out_dir = Path("data/processed")
out_dir.mkdir(parents=True, exist_ok=True)

# Use the small model to avoid heavy deps
ex = Extractor(spacy_model="en_core_web_sm")

all_mentions = []
for p in sorted(text_dir.glob("*.txt")):
    t = p.read_text(encoding="utf-8", errors="ignore")
    ms = ex.extract(t, doc_id=p.stem)
    ms = disambiguate(ms)
    all_mentions.extend(ms)

(out_dir / "mentions.json").write_text(
    json.dumps(all_mentions, indent=2, ensure_ascii=False),
    encoding="utf-8"
)
print(f"Wrote {out_dir/'mentions.json'} with {len(all_mentions)} mentions")
