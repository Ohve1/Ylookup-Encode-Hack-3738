"""PDF extractor — extract text and preserve page location. No accounting decisions."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def make_source_id(path: Path, page: int) -> str:
    digest = hashlib.sha1(f"{path.name}:page:{page}".encode()).hexdigest()[:8].upper()
    return f"SRC-PDF-{digest}-P{page}"


def extract_pdf(path: Path | str) -> list[dict[str, Any]]:
    """Extract one document per PDF page with lineage metadata."""
    from pypdf import PdfReader

    path = Path(path)
    reader = PdfReader(str(path))
    documents: list[dict[str, Any]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        documents.append(
            {
                "source_id": make_source_id(path, page_number),
                "filename": path.name,
                "file_type": "pdf",
                "role": "bank_statement",
                "location": {"page": page_number},
                "text": text,
            }
        )
    return documents


def extract_pdfs(paths: list[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in paths:
        out.extend(extract_pdf(p))
    return out


if __name__ == "__main__":
    import json
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not target:
        raise SystemExit("usage: extract_pdf.py <pdf-or-dir>")
    pdfs = [target] if target.is_file() else sorted(target.rglob("*.pdf"))
    print(json.dumps(extract_pdfs(pdfs), indent=2, ensure_ascii=False))
