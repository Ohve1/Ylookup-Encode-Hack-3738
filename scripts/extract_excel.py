"""Excel extractor — extract cell values and preserve sheet/row location. No accounting."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def make_source_id(path: Path, sheet: str) -> str:
    digest = hashlib.sha1(f"{path.name}:sheet:{sheet}".encode()).hexdigest()[:8].upper()
    return f"SRC-XLS-{digest}"


def _serialize_cell(value: Any) -> Any:
    """Make openpyxl values JSON-serializable."""
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def extract_excel(path: Path | str) -> list[dict[str, Any]]:
    """Extract one row record per worksheet row with lineage metadata."""
    from openpyxl import load_workbook

    path = Path(path)
    workbook = load_workbook(path, data_only=True, read_only=True)
    rows: list[dict[str, Any]] = []
    for sheet in workbook.worksheets:
        source_id = make_source_id(path, sheet.title)
        for row_number, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            # Skip completely empty trailing rows
            values = [_serialize_cell(c) for c in row]
            if all(v is None or v == "" for v in values):
                continue
            rows.append(
                {
                    "source_id": source_id,
                    "filename": path.name,
                    "file_type": "xlsx",
                    "role": "working_file",
                    "location": {
                        "sheet": sheet.title,
                        "row": row_number,
                    },
                    "values": values,
                }
            )
    workbook.close()
    return rows


def extract_excels(paths: list[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in paths:
        out.extend(extract_excel(p))
    return out


if __name__ == "__main__":
    import json
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not target:
        raise SystemExit("usage: extract_excel.py <xlsx-or-dir>")
    files = (
        [target]
        if target.is_file()
        else sorted(list(target.rglob("*.xlsx")) + list(target.rglob("*.xls")))
    )
    print(json.dumps(extract_excels(files), indent=2, ensure_ascii=False, default=str))
