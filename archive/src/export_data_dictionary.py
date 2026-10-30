"""Create searchable PISA 2025 column and coded-value dictionaries."""

from __future__ import annotations

import argparse
import html
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
import pyreadstat


DEFAULT_DATA = Path("data/raw/CY09_MS_STU_PUF.sav")
DEFAULT_CODEBOOK = Path("data/reference/PISA2025_Codebook.xlsx")
DEFAULT_OUTPUT_DIR = Path("data/interim")
DEFAULT_HTML = Path("outputs/pisa_2025_data_dictionary.html")

TECHNICAL_VARIABLES = {
    "CNT",
    "CNTRYID",
    "CNTSCHID",
    "CNTSTUID",
    "CYC",
    "NatCen",
    "STRATUM",
    "SUBNATIO",
    "REGION",
    "OECD",
    "ADMINMODE",
    "LANGTEST_COG",
    "LANGTEST_QQQ",
    "BOOKID",
    "UNIT",
    "WVARSTRR",
    "VER_DAT",
}

MISSING_LABEL_TERMS = (
    "valid skip",
    "system missing",
    "not administered",
    "not applicable",
    "invalid",
    "no response",
)


def parse_codebook(path: Path) -> dict[str, dict]:
    """Convert the OECD STU codebook's continuation-row layout to records."""
    frame = pd.read_excel(path, sheet_name="STU", dtype=str, keep_default_na=False)
    frame.columns = [str(column).strip() for column in frame.columns]
    required = {"NAME", "VARLABEL", "TYPE", "FORMAT", "VARNUM", "VAL", "LABEL"}
    if not required.issubset(frame.columns):
        missing = sorted(required - set(frame.columns))
        raise ValueError(f"Unexpected OECD codebook layout; missing: {', '.join(missing)}")

    records: dict[str, dict] = {}
    current: str | None = None
    for row in frame.to_dict("records"):
        name = str(row["NAME"]).strip()
        if name:
            current = name
            records[current] = {
                "label": str(row["VARLABEL"]).strip(),
                "type": str(row["TYPE"]).strip(),
                "format": str(row["FORMAT"]).strip(),
                "position": int(float(row["VARNUM"])),
                "values": [],
            }
        if current and (str(row["VAL"]).strip() or str(row["LABEL"]).strip()):
            records[current]["values"].append(
                {
                    "code": str(row["VAL"]).strip(),
                    "label": str(row["LABEL"]).strip(),
                }
            )
    return records


def family_for(name: str, label: str) -> tuple[str, str]:
    if re.match(r"^ST\d{3}Q", name):
        return "Student questionnaire item", "Questionnaire response"
    if re.match(r"^ST\d{3}D", name):
        return "Student derived variable", "Derived/categorical"
    if re.match(r"^IC\d{3}Q", name):
        return "ICT familiarity questionnaire item", "Questionnaire response"
    if re.match(r"^PA\d{3}Q", name):
        return "Parent questionnaire item", "Questionnaire response"
    if re.match(r"^PV\d+", name):
        return "Plausible value", "Achievement/outcome"
    if re.match(r"^W_FSTURWT\d+$", name):
        return "Replicate weight", "Variance estimation weight"
    if name in {"W_FSTUWT", "SENWT"}:
        return "Student survey weight", "Point-estimation weight"
    if name in TECHNICAL_VARIABLES or name.startswith("Option_"):
        return "Identifier / administration", "Identifier/design metadata"
    if "(WLE)" in label or "index" in label.casefold():
        return "Derived scale / index", "Continuous derived measure"
    return "Other derived variable", "Derived/other"


def item_parts(label: str) -> tuple[str, str]:
    stem, separator, item = label.partition(" - ")
    return (stem, item) if separator else (label, "")


def normalize_code(value: object) -> str:
    """Make Excel string codes and ReadStat numeric codes comparable."""
    text = str(value).strip()
    try:
        number = Decimal(text)
        if number == number.to_integral():
            return str(number.quantize(Decimal(1)))
        return format(number.normalize(), "f")
    except InvalidOperation:
        return text


def html_document(dictionary: pd.DataFrame, values: pd.DataFrame) -> str:
    family_counts = dictionary["family"].value_counts().to_dict()
    value_groups = {
        variable: group[["code", "value_label", "is_missing_code"]].to_dict("records")
        for variable, group in values.groupby("variable", sort=False)
    }

    rows = []
    for record in dictionary.to_dict("records"):
        variable = record["variable"]
        codes = value_groups.get(variable, [])
        code_html = ""
        if codes:
            code_lines = []
            for code in codes:
                css = "missing-code" if code["is_missing_code"] else ""
                code_lines.append(
                    f'<div class="{css}"><code>{html.escape(str(code["code"]))}</code> '
                    f'{html.escape(str(code["value_label"]))}</div>'
                )
            code_html = (
                f"<details><summary>{len(codes)} codes</summary>"
                + "".join(code_lines)
                + "</details>"
            )
        else:
            code_html = '<span class="muted">Continuous or uncoded</span>'

        core_text = "Yes" if record["in_core_dataset"] else "No"
        validation_text = (
            "Matched" if record["value_labels_match_sav"] else "Official/SAV differ"
        )
        search_text = " ".join(
            str(record[key])
            for key in ("variable", "label", "family", "analysis_role", "question_stem")
        ).casefold()
        rows.append(
            "<tr "
            f'data-search="{html.escape(search_text, quote=True)}" '
            f'data-family="{html.escape(record["family"], quote=True)}" '
            f'data-core="{core_text}">'
            f'<td class="num">{record["position"]}</td>'
            f'<td><code class="variable">{html.escape(variable)}</code></td>'
            f'<td>{html.escape(record["family"])}</td>'
            f'<td>{html.escape(record["analysis_role"])}</td>'
            f'<td class="meaning">{html.escape(record["label"])}</td>'
            f'<td>{html.escape(record["oecd_type"])} / {html.escape(record["oecd_format"])}</td>'
            f"<td>{core_text}</td>"
            f'<td class="validation">{html.escape(validation_text)}</td>'
            f'<td class="codes">{code_html}</td>'
            "</tr>"
        )

    family_options = "".join(
        f'<option value="{html.escape(name, quote=True)}">{html.escape(name)} ({count})</option>'
        for name, count in sorted(family_counts.items())
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PISA 2025 student data dictionary</title>
<style>
:root {{ color-scheme: light; --ink:#172033; --muted:#667085; --line:#d9dee8; --navy:#17365d; --blue:#eaf1fb; --amber:#fff5d6; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font:14px/1.45 Arial, sans-serif; color:var(--ink); background:#f7f8fb; }}
main {{ max-width:1600px; margin:0 auto; padding:28px; }}
h1 {{ margin:0 0 8px; font-size:28px; }}
p {{ max-width:1050px; color:#475467; }}
.summary {{ display:flex; gap:12px; flex-wrap:wrap; margin:20px 0; }}
.card {{ background:white; border:1px solid var(--line); border-radius:8px; padding:12px 16px; min-width:150px; }}
.card b {{ display:block; font-size:22px; color:var(--navy); }}
.legend {{ background:var(--blue); border-left:4px solid var(--navy); padding:12px 16px; margin:18px 0; }}
.controls {{ position:sticky; top:0; z-index:2; display:flex; gap:10px; flex-wrap:wrap; padding:12px 0; background:#f7f8fb; }}
input, select {{ border:1px solid #98a2b3; border-radius:6px; background:white; padding:9px 11px; font:inherit; }}
input[type=search] {{ flex:1; min-width:300px; }}
.table-wrap {{ background:white; border:1px solid var(--line); border-radius:8px; overflow:auto; max-height:72vh; }}
table {{ border-collapse:separate; border-spacing:0; width:100%; min-width:1250px; }}
th {{ position:sticky; top:0; z-index:1; background:var(--navy); color:white; text-align:center; padding:9px; border-right:1px solid #fff5; }}
td {{ padding:8px 9px; border-bottom:1px solid var(--line); vertical-align:top; }}
tr:nth-child(even) td {{ background:#fafbfc; }}
.meaning {{ min-width:360px; }} .codes {{ min-width:300px; }} .num {{ text-align:right; color:var(--muted); }}
code {{ font-family:ui-monospace, SFMono-Regular, Menlo, monospace; }}
.variable {{ font-weight:700; color:#0b4f8a; white-space:nowrap; }}
details summary {{ cursor:pointer; color:#0b4f8a; }}
.missing-code {{ color:#8a5a00; background:var(--amber); }}
.validation {{ white-space:nowrap; }}
.muted {{ color:var(--muted); }}
#shown {{ align-self:center; color:var(--muted); min-width:110px; }}
</style>
</head>
<body><main>
<h1>PISA 2025 student data dictionary</h1>
<p>Column meanings come from the official OECD PISA 2025 STU codebook and were cross-checked against the labels embedded in <code>CY09_MS_STU_PUF.sav</code>. “Missing code” highlights include valid skips, non-response, invalid responses, and items that were not administered.</p>
<div class="summary">
  <div class="card"><b>{len(dictionary):,}</b>variables</div>
  <div class="card"><b>{dictionary['has_value_labels'].sum():,}</b>coded variables</div>
  <div class="card"><b>{len(values):,}</b>code meanings</div>
  <div class="card"><b>{dictionary['in_core_dataset'].sum():,}</b>in core Parquet</div>
  <div class="card"><b>{(~dictionary['value_labels_match_sav']).sum():,}</b>code-label conflicts</div>
</div>
<div class="legend"><b>Naming guide.</b> <code>ST…Q</code>: student questionnaire item. <code>IC…Q</code>: ICT questionnaire item. <code>PA…Q</code>: parent questionnaire item. <code>PV1…PV10</code>: plausible values. <code>W_FSTUWT</code>: final student weight. <code>W_FSTURWT1…80</code>: replicate weights. Other uppercase names are generally derived indices, classifications, or design variables; use their full label below.</div>
<div class="controls">
  <input id="search" type="search" placeholder="Search variable name or meaning…">
  <select id="family"><option value="">All families</option>{family_options}</select>
  <select id="core"><option value="">All variables</option><option value="Yes">Core Parquet only</option><option value="No">Not in core Parquet</option></select>
  <span id="shown"></span>
</div>
<div class="table-wrap"><table>
<thead><tr><th>#</th><th>Variable</th><th>Family</th><th>Analysis role</th><th>Meaning</th><th>Type / format</th><th>Core</th><th>Validation</th><th>Codes</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table></div>
<p>Official source: <a href="https://www.oecd.org/en/data/datasets/pisa-2025-database.html">OECD PISA 2025 Database</a>. Interpretation of derived scales, plausible values, and survey variance estimation should follow the OECD codebook and technical report.</p>
</main>
<script>
const q=document.querySelector('#search'), f=document.querySelector('#family'), c=document.querySelector('#core'), out=document.querySelector('#shown');
const rows=[...document.querySelectorAll('tbody tr')];
function filter() {{
  const term=q.value.trim().toLowerCase(); let shown=0;
  for (const row of rows) {{
    const visible=(!term||row.dataset.search.includes(term))&&(!f.value||row.dataset.family===f.value)&&(!c.value||row.dataset.core===c.value);
    row.hidden=!visible; if(visible) shown++;
  }}
  out.textContent=`${{shown.toLocaleString()}} shown`;
}}
q.addEventListener('input',filter); f.addEventListener('change',filter); c.addEventListener('change',filter); filter();
</script></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--codebook", type=Path, default=DEFAULT_CODEBOOK)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    args = parser.parse_args()

    if not args.data.is_file():
        raise SystemExit(f"SPSS data file not found: {args.data}")
    if not args.codebook.is_file():
        raise SystemExit(f"OECD codebook not found: {args.codebook}")

    official = parse_codebook(args.codebook)
    _, meta = pyreadstat.read_sav(args.data, metadataonly=True)
    embedded_labels = meta.column_names_to_labels or {}
    embedded_values = meta.variable_value_labels or {}
    core_schema_path = Path("data/processed/student_core_schema.csv")
    core_variables = (
        set(pd.read_csv(core_schema_path)["variable"])
        if core_schema_path.is_file()
        else set()
    )

    if set(meta.column_names) != set(official):
        only_sav = sorted(set(meta.column_names) - set(official))
        only_oecd = sorted(set(official) - set(meta.column_names))
        raise ValueError(f"Variable mismatch. SAV only: {only_sav}; OECD only: {only_oecd}")

    dictionary_rows = []
    value_rows = []
    label_mismatches = []
    value_label_mismatches = []
    for position, variable in enumerate(meta.column_names, start=1):
        record = official[variable]
        label = record["label"] or embedded_labels.get(variable, "")
        embedded_label = embedded_labels.get(variable, "") or ""
        if label.strip() != embedded_label.strip():
            label_mismatches.append(variable)
        family, role = family_for(variable, label)
        stem, item_text = item_parts(label)
        missing_codes = []
        official_value_map = {
            normalize_code(value["code"]): value["label"] for value in record["values"]
        }
        embedded_value_map = {
            normalize_code(code): value_label
            for code, value_label in embedded_values.get(variable, {}).items()
        }
        value_labels_match = official_value_map == embedded_value_map
        if not value_labels_match:
            official_differences = {
                code: value_label
                for code, value_label in official_value_map.items()
                if embedded_value_map.get(code) != value_label
            }
            embedded_differences = {
                code: value_label
                for code, value_label in embedded_value_map.items()
                if official_value_map.get(code) != value_label
            }
            value_label_mismatches.append(
                {
                    "variable": variable,
                    "official_differences": official_differences,
                    "embedded_sav_differences": embedded_differences,
                }
            )
        for value in record["values"]:
            is_missing = any(term in value["label"].casefold() for term in MISSING_LABEL_TERMS)
            if is_missing:
                missing_codes.append(value["code"])
            value_rows.append(
                {
                    "variable": variable,
                    "position": position,
                    "code": value["code"],
                    "value_label": value["label"],
                    "is_missing_code": is_missing,
                }
            )
        dictionary_rows.append(
            {
                "position": position,
                "variable": variable,
                "label": label,
                "family": family,
                "analysis_role": role,
                "question_stem": stem,
                "item_text": item_text,
                "oecd_type": record["type"],
                "oecd_format": record["format"],
                "readstat_type": (meta.readstat_variable_types or {}).get(variable),
                "measurement_level": (meta.variable_measure or {}).get(variable),
                "value_label_set": (meta.variable_to_label or {}).get(variable),
                "has_value_labels": bool(record["values"]),
                "value_label_count": len(record["values"]),
                "semantic_missing_codes": ", ".join(missing_codes),
                "in_core_dataset": variable in core_variables,
                "value_labels_match_sav": value_labels_match,
            }
        )

    dictionary = pd.DataFrame(dictionary_rows)
    values = pd.DataFrame(value_rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    dictionary_path = args.output_dir / "pisa_2025_student_data_dictionary.csv"
    values_path = args.output_dir / "pisa_2025_student_value_labels.csv"
    report_path = args.output_dir / "pisa_2025_dictionary_validation.json"
    dictionary.to_csv(dictionary_path, index=False)
    values.to_csv(values_path, index=False)
    report = {
        "sav_variables": len(meta.column_names),
        "oecd_variables": len(official),
        "same_variable_set": set(meta.column_names) == set(official),
        "same_variable_order": meta.column_names == list(official),
        "label_mismatch_count": len(label_mismatches),
        "label_mismatch_variables": label_mismatches,
        "value_label_mismatch_count": len(value_label_mismatches),
        "value_label_mismatches": value_label_mismatches,
        "variables_with_official_value_labels": int(dictionary["has_value_labels"].sum()),
        "official_value_label_rows": len(values),
        "embedded_value_label_variables": len(embedded_values),
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.html.write_text(html_document(dictionary, values), encoding="utf-8")

    print(f"Variables mapped: {len(dictionary):,}")
    print(f"Value-code meanings mapped: {len(values):,}")
    print(f"Label mismatches (OECD vs SAV): {len(label_mismatches):,}")
    print(f"Code-label mismatches (OECD vs SAV): {len(value_label_mismatches):,}")
    print(f"Dictionary: {dictionary_path}")
    print(f"Value labels: {values_path}")
    print(f"Validation: {report_path}")
    print(f"Searchable HTML: {args.html}")


if __name__ == "__main__":
    main()
