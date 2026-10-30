# PISA 2025 student questionnaire analysis

The raw SPSS file is about 2 GB, so the project starts by reading its metadata
and a tiny row-limited preview rather than loading the entire file into pandas.

## Setup

```bash
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m ipykernel install --user --name pisa-2025 --display-name "Python (pisa-2025)"
```

## Inspect safely from the terminal

```bash
.venv/bin/python src/inspect_pisa.py
```

This writes `data/interim/student_questionnaire_schema.csv` and prints only ten
rows for the first twelve variables. To inspect chosen variables:

```bash
.venv/bin/python src/inspect_pisa.py --rows 20 --columns CNT CNTSCHID CNTSTUID
```

## Build the smaller core dataset

```bash
.venv/bin/python src/build_core_dataset.py
```

The script reads the `.sav` file in 50,000-row chunks and creates
`data/processed/student_core.parquet`. It keeps all students but only core IDs,
demographics, socioeconomic indicators, the final and 80 replicate weights,
and ten plausible values for each of science, mathematics, and reading. This is
the right base for weighted analysis and is much faster to reopen than SPSS.

For a quick pipeline test without processing every student:

```bash
.venv/bin/python src/build_core_dataset.py \
  --limit 1000 --output /tmp/student_core_test.parquet
```

## Explore in Jupyter

```bash
source .venv/bin/activate
jupyter lab
```

Open `notebooks/01_data_overview.ipynb`. The notebook reads the full variable
dictionary but only 20 student records.

## Browse every column and coded value

The official OECD workbook is stored at `data/reference/PISA2025_Codebook.xlsx`.
Generate a searchable dictionary and CSV mappings with:

```bash
.venv/bin/python src/export_data_dictionary.py
```

Open `outputs/pisa_2025_data_dictionary.html` to search all 885 variables by
name, full meaning, questionnaire family, or analysis role. The companion CSVs
in `data/interim/` separate the variable-level dictionary from the normalized
code-to-label mapping.

## Recommended workflow

1. Use the schema and official questionnaire/codebook to choose variables.
2. Include identifiers, country, sampling weights, replicate weights, and the
   selected questionnaire/outcome variables.
3. Add those columns to the core extraction and rebuild the Parquet file.
4. Analyze the smaller Parquet file; do not repeatedly scan the SPSS source.
5. Use PISA's survey weights and replicate-weight method for population
   estimates and uncertainty. Plain unweighted means are usually not defensible.
