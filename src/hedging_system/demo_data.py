"""Loading and validating the bundled synthetic cross-hedge dataset."""

from __future__ import annotations

import csv
import os
from math import isfinite
from pathlib import Path


def _dataset_path() -> Path:
    configured_path = os.environ.get("HEDGING_DEMO_DATA")
    if configured_path:
        return Path(configured_path)
    source_tree_path = Path(__file__).resolve().parents[2] / "dane_cross_hedge.csv"
    if source_tree_path.is_file():
        return source_tree_path
    working_directory_path = Path.cwd() / "dane_cross_hedge.csv"
    if working_directory_path.is_file():
        return working_directory_path
    raise FileNotFoundError(
        "Synthetic demo data is missing. Set HEDGING_DEMO_DATA to dane_cross_hedge.csv."
    )


def load_cross_hedge_data() -> list[dict[str, str | int | float]]:
    """Load the example data and reject malformed or non-finite rows."""
    path = _dataset_path()
    required_fields = {
        "observation_id",
        "sample",
        "benchmark_change_usd_per_bbl",
        "physical_change_usd_per_bbl",
    }
    rows: list[dict[str, str | int | float]] = []
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None or not required_fields.issubset(reader.fieldnames):
            raise ValueError("Demo CSV is missing one or more required columns.")
        for row_number, row in enumerate(reader, start=2):
            try:
                observation_id = int(row["observation_id"])
                sample = row["sample"]
                benchmark = float(row["benchmark_change_usd_per_bbl"])
                physical = float(row["physical_change_usd_per_bbl"])
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid demo data at CSV row {row_number}.") from error
            if sample not in {"train", "test"}:
                raise ValueError(f"Invalid sample label at CSV row {row_number}.")
            if not isfinite(benchmark) or not isfinite(physical):
                raise ValueError(f"Non-finite demo data at CSV row {row_number}.")
            rows.append(
                {
                    "observation_id": observation_id,
                    "sample": sample,
                    "benchmark_change_usd_per_bbl": benchmark,
                    "physical_change_usd_per_bbl": physical,
                }
            )
    if not rows:
        raise ValueError("Demo CSV contains no observations.")
    return rows
