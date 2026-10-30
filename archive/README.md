# Archív predchádzajúcej prípravy dát

Sem bola 30. 10. 2026 presunutá doterajšia príprava projektu.
Na začiatok používaj **[nový úvodný notebook](../notebooks/01_uvod_do_dat.ipynb)**.

| Umiestnenie | Obsah |
| --- | --- |
| `src/inspect_pisa.py` | Kontrola metadát, export schémy a malá ukážka dát. |
| `src/build_core_dataset.py` | Výber 132 premenných a vytvorenie menšieho Parquet súboru. |
| `src/export_data_dictionary.py` | Slovník premenných, kontrola codebooku a HTML prehliadač. |
| `notebooks/01_data_overview.ipynb` | Pôvodný prehľadový notebook. |
| `docs/variable_naming_guide.md` | Orientácia v názvoch premenných a kódovaní. |
| `data/interim/` | Lokálne vygenerované slovníky, schéma a kontrolný report. |
| `data/processed/` | Lokálny `student_core.parquet`, jeho schéma a manifest. |
| `outputs/` | Lokálny vyhľadávateľný HTML slovník premenných. |
| `README_original.md` | Pôvodný návod zachovaný ako historický podklad. |
| `requirements.txt` | Pôvodný širší zoznam knižníc. |

Kód, pôvodný notebook a dokumentácia sú uložené v Gite. Generované dáta
a HTML slovník zostávajú na tomto počítači a Git ich ignoruje.
Pôvodný SPSS súbor aj codebook zostali v hlavnom `data/`.
Pôvodný obsah je navyše zachytený prvým commitom; v archivovanom notebooku
bola upravená iba cesta k pôvodnému SPSS súboru.

## Otvorenie slovníka premenných

Ak bol už vytvorený, otvor
**[outputs/pisa_2025_data_dictionary.html](outputs/pisa_2025_data_dictionary.html)**.
Je to pomocný podklad; nový úvodný notebook od neho nezávisí.

## Opätovné použitie pôvodných skriptov

Nasledujúce príkazy spúšťaj z hlavného priečinka projektu. Pôvodný návod
v `README_original.md` opisuje staré rozloženie; aktuálne cesty sú tu:

```bash
.venv/bin/python -m pip install -r archive/requirements.txt
cd archive
../.venv/bin/python src/inspect_pisa.py --data ../data/raw/CY09_MS_STU_PUF.sav
../.venv/bin/python src/build_core_dataset.py --data ../data/raw/CY09_MS_STU_PUF.sav
../.venv/bin/python src/export_data_dictionary.py --data ../data/raw/CY09_MS_STU_PUF.sav --codebook ../data/reference/PISA2025_Codebook.xlsx
```

Tieto skripty zapisujú výstupy do archívu; spúšťaj ich len vtedy, keď ich chceš
obnoviť. Pôvodný notebook spúšťaj s pracovným priečinkom `archive/notebooks/`.
Jeho Parquet časť používa lokálny archivovaný dataset, ktorý sa do Gitu neukladá.
Relatívne cesty v starších schémach a manifeste sú zachované z pôvodného exportu.
