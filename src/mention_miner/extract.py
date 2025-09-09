# src/mention_miner/extract.py

import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import spacy

# --- Strip References / Works Cited / Bibliography (your update) ---
REF_HEADER_RX = re.compile(r"\n\s*(References|Works Cited|Bibliography)\s*\n", re.IGNORECASE)

def strip_references(text: str) -> str:
    m = REF_HEADER_RX.search(text)
    return text[:m.start()] if m and m.start() > 2000 else text


# --- Patterns ---
# Narrative citations like: "Surname (2013)"
NARRATIVE_CITE_RX = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})\s\(\d{4}[a-z]?\)")
# Also allow "Surname 2013" (no parentheses)
NARRATIVE_CITE_RX2 = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})\s(?:19|20)\d{2}[a-z]?\b")
# Eponyms like "Zipf's law" or "Flesch–Kincaid"
EPONYM_RX = re.compile(r"\b([A-Z][a-z]+)’s\s+([A-Za-z-]+)\b|([A-Z][a-z]+(?:–|-)[A-Z][a-z]+)\b")


@dataclass
class Mention:
    doc_id: str
    span_text: str
    span_start: int
    span_end: int
    sentence_text: str
    mention_type: str  # person | concept_eponym
    source_type: str   # prose | narrative_cite
    confidence: float = 0.7
    norm_name: str = ""
    entity_id: str = ""


class Extractor:
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        self.nlp = spacy.load(spacy_model)

    def extract(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        # Apply your references stripping first
        text = strip_references(text)

        doc = self.nlp(text)
        mentions: List[Mention] = []

        # 1) spaCy PERSON entities from prose
        for ent in doc.ents:
            if ent.label_ == "PERSON" and 2 <= len(ent.text.split()) <= 5:
                mentions.append(Mention(
                    doc_id=doc_id,
                    span_text=ent.text,
                    span_start=ent.start_char,
                    span_end=ent.end_char,
                    sentence_text=ent.sent.text,
                    mention_type="person",
                    source_type="prose",
                    confidence=0.8,
                ))

        # 2) Narrative citations: "Surname (2013)"
        for m in NARRATIVE_CITE_RX.finditer(text):
            span = m.group(1)
            mentions.append(Mention(
                doc_id=doc_id,
                span_text=span,
                span_start=m.start(1),
                span_end=m.end(1),
                sentence_text="",
                mention_type="person",
                source_type="narrative_cite",
                confidence=0.9,
            ))

        # 3) Narrative citations: "Surname 2013"
        for m in NARRATIVE_CITE_RX2.finditer(text):
            span = m.group(1)
            mentions.append(Mention(
                doc_id=doc_id,
                span_text=span,
                span_start=m.start(1),
                span_end=m.end(1),
                sentence_text="",
                mention_type="person",
                source_type="narrative_cite",
                confidence=0.85,
            ))

        # 4) Eponymous concepts
        for m in EPONYM_RX.finditer(text):
            label = m.group(0)
            mentions.append(Mention(
                doc_id=doc_id,
                span_text=label,
                span_start=m.start(),
                span_end=m.end(),
                sentence_text="",
                mention_type="concept_eponym",
                source_type="prose",
                confidence=0.7,
            ))

        return [asdict(m) for m in mentions]
