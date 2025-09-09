from pathlib import Path
from pdfminer.high_level import extract_text
import re

pdf_dir = Path("data/raw_pdfs")
txt_dir = Path("data/raw")
txt_dir.mkdir(parents=True, exist_ok=True)

def clean(txt: str) -> str:
    txt = txt.replace("\r", "")
    # join hyphenated breaks, normalize spacing
    txt = re.sub(r"-\n", "", txt)
    txt = re.sub(r"[ \t]+\n", "\n", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    # common ligatures
    txt = txt.replace("ﬁ","fi").replace("ﬂ","fl")
    return txt.strip() + "\n"

for pdf in pdf_dir.glob("*.pdf"):
    text = extract_text(str(pdf)) or ""
    out = txt_dir / (pdf.stem + ".txt")
    out.write_text(clean(text), encoding="utf-8")
    print(f"Wrote {out} ({len(text)} chars)")
