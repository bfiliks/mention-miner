
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import spacy

# Patterns
NARRATIVE_CITE_RX = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})\s\(\d{4}[a-z]?\)")
EPONYM_RX = re.compile(r"\b([A-Z][a-z]+)’s\s+([A-Za-z-]+)\b|([A-Z][a-z]+(?:–|-)[A-Z][a-z]+)\b")

@dataclass
class Mention:
    doc_id: str
    span_text: str
    span_start: int
    span_end: int
    sentence_text: str
    mention_type: str  # person | concept_eponym | group (future)
    source_type: str   # prose | narrative_cite | footnote | biblio
    confidence: float = 0.7
    norm_name: str = ""
    entity_id: str = ""

class Extractor:
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        self.nlp = spacy.load(spacy_model)

    def extract(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        doc = self.nlp(text)
        mentions: List[Mention] = []

        # 1) spaCy PERSON
        for ent in doc.ents:
            if ent.label_ == "PERSON" and 2 <= len(ent.text.split()) <= 4:
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

        # 2) Narrative citations
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

        # 3) Eponyms
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
