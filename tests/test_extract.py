
from mention_miner.extract import Extractor

def test_extract_basic():
    text = "Matthew Jockers (2013) argues that Franco Moretti's distant reading is influential."
    ex = Extractor(spacy_model="en_core_web_sm")  # small model for CI speed
    ms = ex.extract(text, "doc1")
    assert any(m["mention_type"]=="person" for m in ms)
