# PISA 2025 student-file variable naming guide

The full, authoritative meaning of each variable is in
`data/interim/pisa_2025_student_data_dictionary.csv`. The patterns below are a
navigation aid, not a substitute for the full label or technical report.

## Main families

| Pattern | Meaning | Count |
| --- | --- | ---: |
| `ST…Q…` | Raw student questionnaire item | 280 |
| `ST…D…` | Student-derived or recoded variable | 8 |
| `IC…Q…` | ICT familiarity questionnaire item | 93 |
| `PA…Q…` | Parent questionnaire item | 196 |
| `PV1…PV10…` | Ten plausible values for an achievement domain or subscale | 110 |
| `W_FSTUWT` and `SENWT` | Student weights | 2 |
| `W_FSTURWT1…80` | BRR-Fay replicate weights | 80 |
| Short uppercase names such as `ESCS` or `BELONG` | Usually a derived scale, index, classification, or design field | 94 |
| IDs, routing, and administration fields | Country, school/student IDs, language, mode, form, and design fields | 22 |

Questionnaire names commonly encode the instrument, question block, item, and
international adaptation type. For example, `ST004D01T` belongs to the student
instrument (`ST`), block 004, derived item 01; its full label is “Students'
gender from sampling data (Female/Male)”. Always use the dictionary label rather
than trying to interpret every suffix from the name alone.

## Plausible-value suffixes

| Suffix | Domain |
| --- | --- |
| `SCIE` | Science |
| `MATH` | Mathematics |
| `READ` | Reading |
| `CMPS` | LDW computational problem solving |
| `CPPK` | LDW computational practices prior knowledge |
| `SEPS` | Science: explain phenomena scientifically |
| `SEDE` | Science: evaluate designs for scientific enquiry |
| `SEID` | Science: evaluate scientific information for decision making |
| `SENV` | Environmental science |
| `CMOD` | LDW modelling subscale |
| `CPRO` | LDW programming subscale |

Use all ten plausible values for a domain. Do not treat `PV1…` as a student's
single observed test score. Use the final student weight for point estimates and
the 80 replicate weights with the OECD method for sampling variance.

## Missing and routing codes

Codes such as `5/6/7/8/9`, `95/96/97/98/99`, or wider equivalents can mean valid
skip, system missing, not administered, invalid, or no response. The exact code
depends on the variable's format. Use
`data/interim/pisa_2025_student_value_labels.csv`; do not apply one global list
of missing codes to every column.

## Validation note

All 885 variable names, positions, and full variable labels match between the
official OECD workbook and the SPSS file. Twelve variables have response-code
differences. Most are extra Cyprus codes present in the official workbook but
absent from this SPSS file. `OCOD3`, `OCOP1`, and `OCOP2` contain conflicting
occupation labels for a small set of codes. The generated dictionary uses the
official OECD workbook as its primary code-label source and records every
conflict in `data/interim/pisa_2025_dictionary_validation.json`.

## Source

OECD, PISA 2025 Database:
https://www.oecd.org/en/data/datasets/pisa-2025-database.html
