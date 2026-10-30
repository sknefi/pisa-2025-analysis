"""Jednorazovo prevedie celý pôvodný SAV do Parquetu bez výberu premenných."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq
import pyreadstat


PROJECT = Path(__file__).resolve().parents[1]
FORMAT_VERSION = 1


def json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8")


def cached_dataset(output: Path, metadata_path: Path, source: dict) -> dict | None:
    """Overí, že oba výstupy patria k rovnakému úplnému prevodu zdrojového súboru."""
    try:
        info = json.loads(metadata_path.read_text(encoding="utf-8"))
        parquet = pq.ParquetFile(output)
        embedded = json.loads(parquet.schema_arrow.metadata[b"pisa_metadata"])
        names = [column["name"] for column in info["columns"]]
        if (
            info == embedded
            and info["format_version"] == FORMAT_VERSION
            and info["source"] == source
            and parquet.metadata.num_rows == info["rows"]
            and parquet.schema_arrow.names == names
        ):
            return info
    except (OSError, ValueError, KeyError, TypeError, pa.ArrowException):
        pass
    return None


def build_dataset(data: Path, output: Path, chunk_size: int = 20_000, force: bool = False) -> dict:
    data, output = Path(data).resolve(), Path(output).resolve()
    if not data.is_file():
        raise FileNotFoundError(f"Chýba pôvodný dátový súbor: {data}")
    if output.suffix.lower() != ".parquet" or output == data:
        raise ValueError("Výstup musí byť samostatný súbor s príponou .parquet.")
    if chunk_size < 1:
        raise ValueError("Veľkosť dávky musí byť kladná.")

    original_stat = data.stat()
    print("Overujem verziu pôvodných dát…", flush=True)
    with data.open("rb") as source_file:
        digest = hashlib.file_digest(source_file, "sha256").hexdigest()
    source = {"name": data.name, "size_bytes": original_stat.st_size, "sha256": digest}
    metadata_path = output.with_name(f"{output.stem}_metadata.json")

    if not force and (output.exists() or metadata_path.exists()):
        cached = cached_dataset(output, metadata_path, source)
        if cached is not None:
            print(f"Hotový úplný Parquet už existuje: {output}", flush=True)
            return cached
        raise ValueError("Výstupy sú neúplné alebo patria k iným dátam. Na nový prevod použi --force.")

    _, meta = pyreadstat.read_sav(data, metadataonly=True, user_missing=True)
    if not meta.number_rows or not meta.column_names:
        raise ValueError("Zdroj musí obsahovať riadky aj premenné a uvádzať ich počet v metadátach.")

    columns = []
    fields = []
    for name in meta.column_names:
        kind = meta.readstat_variable_types[name]
        if kind not in {"string", "double"}:
            raise ValueError(f"Nepodporovaný typ {kind!r} v premennej {name}.")
        column = {
            "name": name,
            "label": meta.column_names_to_labels.get(name),
            "readstat_type": kind,
            "spss_format": meta.original_variable_types.get(name),
            "measure": meta.variable_measure.get(name),
            "value_labels": [
                {"value": value, "label": label}
                for value, label in meta.variable_value_labels.get(name, {}).items()
            ],
            "missing_ranges": meta.missing_ranges.get(name, []),
        }
        columns.append(column)
        fields.append(pa.field(
            name,
            pa.string() if kind == "string" else pa.float64(),
            metadata={b"label": (column["label"] or "").encode("utf-8")},
        ))

    info = {
        "format_version": FORMAT_VERSION,
        "build_id": uuid4().hex,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "rows": meta.number_rows,
        "columns": columns,
        "read_options": {
            "apply_value_formats": False,
            "user_missing": True,
            "disable_datetime_conversion": True,
        },
        "note": "Všetky riadky a premenné, pôvodné kódy bez čistenia. Popisy pochádzajú zo SAV; na interpretáciu používaj aj codebook.",
    }
    metadata_content = json_bytes(info)
    schema = pa.schema(fields, metadata={b"pisa_metadata": metadata_content})
    output.parent.mkdir(parents=True, exist_ok=True)
    token = info["build_id"]
    temporary = output.with_name(f".{output.name}.{token}.tmp")
    metadata_temporary = metadata_path.with_name(f".{metadata_path.name}.{token}.tmp")
    rows = 0
    try:
        with pq.ParquetWriter(temporary, schema, compression="zstd") as writer:
            chunks = pyreadstat.read_file_in_chunks(
                pyreadstat.read_sav,
                data,
                chunksize=chunk_size,
                apply_value_formats=False,
                user_missing=True,
                disable_datetime_conversion=True,
            )
            for frame, _ in chunks:
                table = pa.Table.from_pandas(frame, schema=schema, preserve_index=False, safe=True)
                writer.write_table(table)
                rows += len(frame)
                print(f"Uložené: {rows:,} / {meta.number_rows:,} riadkov", flush=True)

        if rows != meta.number_rows:
            raise ValueError(f"Neúplný prevod: {rows} namiesto {meta.number_rows} riadkov.")
        final_stat = data.stat()
        if (final_stat.st_size, final_stat.st_mtime_ns) != (original_stat.st_size, original_stat.st_mtime_ns):
            raise ValueError("Pôvodné dáta sa počas prevodu zmenili; výstup sa nepoužije.")
        check = pq.ParquetFile(temporary)
        if check.metadata.num_rows != rows or check.schema_arrow.names != meta.column_names:
            raise ValueError("Kontrola výstupnej schémy alebo počtu riadkov zlyhala.")
        metadata_temporary.write_bytes(metadata_content + b"\n")
        temporary.replace(output)
        metadata_temporary.replace(metadata_path)
    finally:
        temporary.unlink(missing_ok=True)
        metadata_temporary.unlink(missing_ok=True)

    print(f"Hotovo: {rows:,} riadkov × {len(columns)} premenných", flush=True)
    print(f"Parquet: {output}", flush=True)
    print(f"Popisy premenných a verzia zdroja: {metadata_path}", flush=True)
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=PROJECT / "data/raw/CY09_MS_STU_PUF.sav")
    parser.add_argument("--output", type=Path, default=PROJECT / "data/processed/student_full.parquet")
    parser.add_argument("--chunk-size", type=int, default=20_000, help="Počet riadkov v jednej dávke.")
    parser.add_argument("--force", action="store_true", help="Znova vytvorí už existujúce výstupy.")
    args = parser.parse_args()
    try:
        build_dataset(args.data, args.output, args.chunk_size, args.force)
    except (FileNotFoundError, ValueError) as error:
        parser.exit(1, f"Chyba: {error}\n")


if __name__ == "__main__":
    main()
