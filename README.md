# mention-miner
Identify scholar mentions and eponymous concepts in articles, then build co-mention networks for literature scans in **Digital Humanities**, **Cultural Analytics**, **Computational Text Analytics**, and **Digital History**.

## Why?
When you’re new to a field, a fast way to learn is to see *who gets mentioned together* and what eponymous concepts appear. This tool extracts scholar mentions in prose (and narrative citations), normalizes names, and builds a co-mention network across a folder of papers.

## Features
- spaCy-based PERSON extraction + narrative-citation regex
- Eponym detection for person-named concepts (e.g., “Flesch–Kincaid”)
- Lightweight disambiguation with fuzzy matching
- Co-mention graph (sentence-window) + PyVis HTML visualization
- Streamlit curation UI for human-in-the-loop entity fixes

## Quickstart
```bash
# 1) Create environment
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -U pip

# 2) Install
pip install -e .

# 3) Download spaCy model
python -m spacy download en_core_web_trf

# 4) Put your TXT files here
#   data/raw/*.txt  (convert PDFs via GROBID or your preferred pipeline)

# 5) Run the batch extractor
mention-miner run-batch --text_dir data/raw --out_dir data/processed

# 6) Open the graph
python -m http.server 8000  # then visit http://localhost:8000/data/processed/mentions_network.html
# or just open the HTML file directly in your browser

# 7) Launch the curation UI
streamlit run apps/curation_ui/App.py
```

## Repository structure
```
mention-miner/
├─ apps/
│  └─ curation_ui/         # Streamlit app for review & corrections
├─ data/
│  ├─ raw/                 # Input TXT files
│  └─ processed/           # JSON/CSV and HTML outputs
├─ docs/
├─ notebooks/
├─ scripts/
├─ src/
│  └─ mention_miner/
│     ├─ __init__.py
│     ├─ extract.py        # NER + regex rules
│     ├─ normalize.py      # canonicalization + fuzzy disambiguation
│     ├─ graph.py          # co-mention graph + exporters
│     ├─ visualize.py      # PyVis helpers
│     └─ cli.py            # click-based CLI entrypoints
├─ tests/
├─ pyproject.toml
├─ requirements.txt
├─ LICENSE
├─ CODE_OF_CONDUCT.md
├─ CONTRIBUTING.md
└─ README.md
```

## Roadmap
- OpenAlex/Wikidata entity linking
- Section-aware weighting (methods/background > acknowledgements)
- Coreference resolution pass
- Gazetteer expansion for eponyms (“named after” relations)
- PDF→TEI ingest with GROBID

## Citation
If you use this in academic work, please cite this repository.
