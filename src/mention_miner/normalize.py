# src/mention_miner/normalize.py

import re
from typing import List, Dict, Any, Iterable
from rapidfuzz import fuzz, process


def canonicalize(name: str) -> str:
    name = name.replace("’", "'").strip()
    name = re.sub(r"[’']s\b", "", name)          # drop possessive 's
    name = re.sub(r"[.,:;]+$", "", name)         # trim trailing punct
    name = re.sub(r"\s{2,}", " ", name)

    # "Last, First M." -> "First M. Last"
    if "," in name:
        parts = [p.strip() for p in name.split(",")]
        name = " ".join(parts[::-1])

    tokens = name.split()
    clean = []
    for i, t in enumerate(tokens):
        if re.fullmatch(r"[A-Z]\.", t) and i + 1 < len(tokens) and tokens[i+1][:1].isupper():
            clean.append(t)                      # keep initials like "J."
        elif len(t) == 1 and t.isalpha():
            continue                             # drop lone letters
        else:
            clean.append(t)
    return " ".join(clean)


def disambiguate(
    mentions: List[Dict[str, Any]],
    seed_author_list: Iterable[str] = None,
    threshold: int = 90,
) -> List[Dict[str, Any]]:
    """
    Canonicalize person mentions; optionally snap to a seed list using fuzzy match.
    Non-person mentions pass through with norm_name = span_text.
    """
    canon_set = set(canonicalize(a) for a in (seed_author_list or []))

    for m in mentions:
        if m.get("mention_type") != "person":
            m["norm_name"], m["entity_id"] = m.get("span_text", ""), ""
            continue

        cand = canonicalize(m.get("span_text", ""))
        if canon_set:
            match = process.extractOne(cand, list(canon_set), scorer=fuzz.token_sort_ratio)
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


def dedupe_person_names(
    mentions: List[Dict[str, Any]],
    threshold: int = 92,
) -> List[Dict[str, Any]]:
    """
    Collapse near-duplicate person names by fuzzy similarity of norm_name.
    E.g., 'J. Stephen Downie' vs 'Stephen Downie' (depending on your pipeline).
    """
    names = sorted({m["norm_name"] for m in mentions if m.get("mention_type") == "person"})
    if not names:
        return mentions

    # Build a mapping of each name to its best match
    mapping = {p: p for p in names}
    for p in names:
        best = process.extractOne(p, names, scorer=fuzz.WRatio)  # robust composite scorer
        if best and best[1] >= threshold:
            mapping[p] = best[0]

    # Apply mapping
    for m in mentions:
        if m.get("mention_type") == "person":
            m["norm_name"] = mapping.get(m["norm_name"], m["norm_name"])

    return mentions
