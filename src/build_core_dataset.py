"""Stream a compact, analysis-ready PISA core dataset to Parquet."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pyreadstat


DEFAULT_DATA = Path("data/raw/CY09_MS_STU_PUF.sav")
DEFAULT_OUTPUT = Path("data/processed/student_core.parquet")

BASE_COLUMNS = [
    "CNT",
    "CNTRYID",
    "CNTSCHID",
    "CNTSTUID",
    "SUBNATIO",
    "REGION",
    "OECD",
    "ADMINMODE",
    "LANGTEST_COG",
    "LANGTEST_QQQ",
    "ST001D01T",
    "ST004D01T",
    "MALE",
    "AGE",
    "GRADE",
    "ESCS",
    "IMMIG",
    "HISEI",
    "PAREDINT",
    "HOMEPOS",
    "W_FSTUWT",
    "SENWT",
]


def numbered(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{number}" for number in range(1, count + 1)]


def selected_columns(available: list[str]) -> list[str]:
    """Return the core fields in a stable and documented order."""
    requested = BASE_COLUMNS + numbered("W_FSTURWT", 80)
    for domain in ("SCIE", "MATH", "READ"):
        requested.extend(f"PV{number}{domain}" for number in range(1, 11))

    missing = [name for name in BASE_COLUMNS if name not in available]
    if missing:
        raise ValueError(f"Required core variables are missing: {', '.join(missing)}")
    return [name for name in requested if name in available]


def schema_frame(meta: object, columns: list[str]) -> pd.DataFrame:
    labels = getattr(meta, "column_names_to_labels", {}) or {}
    original_types = getattr(meta, "original_variable_types", {}) or {}
    readstat_types = getattr(meta, "readstat_variable_types", {}) or {}
    measures = getattr(meta, "variable_measure", {}) or {}
    return pd.DataFrame(
        {
            "variable": columns,
            "label": [labels.get(name) for name in columns],
            "original_type": [original_types.get(name) for name in columns],
            "readstat_type": [readstat_types.get(name) for name in columns],
            "measure": [measures.get(name) for name in columns],
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--chunk-size", type=int, default=50_000)
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Read only this many rows (0 means all rows; useful for testing).",
    )
    args = parser.parse_args()

    if not args.data.is_file():
        raise SystemExit(f"Data file not found: {args.data}")
    if args.chunk_size < 1 or args.limit < 0:
        raise SystemExit("--chunk-size must be positive and --limit cannot be negative")

    _, meta = pyreadstat.read_sav(args.data, metadataonly=True)
    columns = selected_columns(meta.column_names)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    writer: pq.ParquetWriter | None = None
    arrow_schema: pa.Schema | None = None
    rows_written = 0

    try:
        chunks = pyreadstat.read_file_in_chunks(
            pyreadstat.read_sav,
            args.data,
            chunksize=args.chunk_size,
            limit=args.limit,
            usecols=columns,
            apply_value_formats=False,
        )
        for chunk_number, (frame, _) in enumerate(chunks, start=1):
            if args.limit:
                remaining = args.limit - rows_written
                if remaining <= 0:
                    break
                frame = frame.iloc[:remaining]
            table = pa.Table.from_pandas(
                frame,
                schema=arrow_schema,
                preserve_index=False,
                safe=False,
            )
            if writer is None:
                arrow_schema = table.schema
                writer = pq.ParquetWriter(temporary, arrow_schema, compression="zstd")
            writer.write_table(table)
            rows_written += len(frame)
            print(f"Chunk {chunk_number}: {rows_written:,} rows written", flush=True)
            if args.limit and rows_written >= args.limit:
                break
    except Exception:
        if writer is not None:
            writer.close()
        temporary.unlink(missing_ok=True)
        raise
    else:
        if writer is not None:
            writer.close()

    if rows_written == 0:
        raise RuntimeError("No rows were read; no output was created")
    temporary.replace(args.output)

    schema_path = args.output.with_name(f"{args.output.stem}_schema.csv")
    schema_frame(meta, columns).to_csv(schema_path, index=False)
    manifest_path = args.output.with_name(f"{args.output.stem}_manifest.json")
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(args.data),
        "output": str(args.output),
        "rows": rows_written,
        "columns": len(columns),
        "column_names": columns,
        "note": "Raw coded values; use the schema and OECD codebook for interpretation.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Completed: {args.output} ({rows_written:,} rows × {len(columns)} columns)")
    print(f"Schema: {schema_path}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
