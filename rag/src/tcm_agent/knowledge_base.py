from __future__ import annotations

import csv
from pathlib import Path

from .models import Record


def load_records(path: Path) -> list[Record]:
    if not path.exists():
        raise FileNotFoundError(f"Knowledge base file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    records = [Record(**row) for row in rows]
    if not records:
        raise ValueError("Knowledge base is empty.")
    return records
