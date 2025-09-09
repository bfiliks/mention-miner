import re
from typing import List, Dict, Any, Iterable
from rapidfuzz import fuzz, process

def canonicalize(name: str) -> str:
    # normalize quotes/possessives, strip trailing punctuation
    name = name.replace("’", "'").strip()
    name = re.sub(r"[’']s\b", "", name)         # drop possessive 's
    name = re.sub(r"[.,:;]+$", "", name)        # trailing punctuation

    # "Last, First M." -> "First M. Last"
    if "," in name:
        parts = [p.strip() for p in name.split(",")]
        name = " ".join(parts[::-1])

    tokens = name.split()
    clean = []
    for i, t in enumerate(tokens):
        # keep initials like "J." if followed by a capitalized token
        if re.fullmatch(r"[A-Z]\.", t) and i + 1 < len(tokens) and tokens[i+1][:1].isupper():
            clean.append(t)
        # drop lone single-letter tokens without period
        elif len(t) == 1 and t.isalpha():
            continue
        else:
            clean.append(t)
    return " ".join(clean)

def disambiguate(mentions: List[Dict[str, Any]], seed_author_list: Iterable[str]=None, threshold: int=90):
    canon_set = set(canonicalize(a) for a in (seed_author_list or []))
    for m in mentions:
        if m["mention_type"] != "person":
            m["norm_name"], m["entity_id"] = m["span_text"], ""
            continue
        cand = canonicalize(m["span_text"])
        choices = list(canon_set) if canon_set else []
        if choices:
            match = process.extractOne(cand, choices, scorer=fuzz.token_sort_ratio)
            if match and match[1] >= threshold:
                m["norm_name"] = match[0]
            else:
                m["norm_name"] = cand
                canon_set.add(cand)
        else:
            m["norm_name"] = cand
            canon_set.add(cand)
        m["entity_id"] = ""
    return mentions
