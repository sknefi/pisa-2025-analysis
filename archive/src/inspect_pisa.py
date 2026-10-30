"""Inspect a large SPSS PISA file without loading it fully into memory."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyreadstat


DEFAULT_DATA = Path("data/raw/CY09_MS_STU_PUF.sav")
DEFAULT_SCHEMA = Path("data/interim/student_questionnaire_schema.csv")


def read_metadata(path: Path) -> tuple[pd.DataFrame, object]:
    """Return a compact variable dictionary and the pyreadstat metadata object."""
    _, meta = pyreadstat.read_sav(path, metadataonly=True)
    labels = getattr(meta, "column_names_to_labels", {}) or {}
    original_types = getattr(meta, "original_variable_types", {}) or {}
    readstat_types = getattr(meta, "readstat_variable_types", {}) or {}
    measures = getattr(meta, "variable_measure", {}) or {}

    schema = pd.DataFrame(
        {
            "variable": meta.column_names,
            "label": [labels.get(name) for name in meta.column_names],
            "original_type": [original_types.get(name) for name in meta.column_names],
            "readstat_type": [readstat_types.get(name) for name in meta.column_names],
            "measure": [measures.get(name) for name in meta.column_names],
        }
    )
    return schema, meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--rows", type=int, default=10)
    parser.add_argument("--schema-out", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument(
        "--columns",
        nargs="*",
        help="Optional variables to preview. Defaults to the first 12 variables.",
    )
    args = parser.parse_args()

    if not args.data.is_file():
        raise SystemExit(f"Data file not found: {args.data}")
    if args.rows < 1:
        raise SystemExit("--rows must be at least 1")

    schema, meta = read_metadata(args.data)
    args.schema_out.parent.mkdir(parents=True, exist_ok=True)
    schema.to_csv(args.schema_out, index=False)

    row_count = getattr(meta, "number_rows", None)
    column_count = getattr(meta, "number_columns", len(schema))
    print(f"File: {args.data}")
    print(f"Rows reported in metadata: {row_count:,}" if row_count is not None else "Rows: unknown")
    print(f"Columns: {column_count:,}")
    print(f"Schema written to: {args.schema_out}")

    columns = args.columns or schema["variable"].head(12).tolist()
    preview, _ = pyreadstat.read_sav(
        args.data,
        usecols=columns,
        row_limit=args.rows,
        apply_value_formats=False,
    )
    print("\nSmall preview (raw coded values):")
    with pd.option_context("display.max_columns", None, "display.width", 160):
        print(preview)


if __name__ == "__main__":
    main()
