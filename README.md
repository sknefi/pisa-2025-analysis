# PISA 2025 – úvod do dát

Spoločný projekt na skúmanie žiackych dát PISA 2025. Aktuálne sa zoznamujeme
so súborom a významom premenných. Výskumnú otázku a analýzy doplníme postupne.

**Prvé spustenie:** naklonuj projekt → vytvor prostredie → nainštaluj knižnice
→ doplň dátový súbor → jednorazovo priprav plný Parquet → otvor Jupyter.

## 1. Čo potrebuješ

- **Git** na stiahnutie projektu a zdieľanie zmien.
- **Python 3.11** – na tejto verzii je projekt overený.
- Internet na stiahnutie knižníc a dát; potom môžeš notebook používať lokálne.
- Miesto na približne 2,17 GB pôvodný dátový súbor, približne 1,01 GB plný Parquet a prostredie s knižnicami.

Projekt nevyžaduje nainštalovaný SPSS. Súbor `.sav` číta knižnica `pyreadstat`.
Každý člen tímu si vytvorí svoje prostredie `.venv`; tento priečinok sa nezdieľa.

## 2. Naklonovanie projektu

Skopíruj adresu spoločného repozitára. V nasledujúcom príkaze nahraď
`URL_REPOZITARA` touto adresou; úvodzovky môžeš ponechať.

```bash
git clone "URL_REPOZITARA" pisa-2025-analysis
cd pisa-2025-analysis
```

Ďalšie príkazy spúšťaj z hlavného priečinka projektu, kde je tento `README.md`
a `requirements.txt`. Ak už projekt máš stiahnutý, tento krok preskoč.

## 3. Jednorazový setup

Vyber postup pre svoj systém. Prostredie oddelí knižnice projektu od ostatných
Python projektov. Každý príkaz nižšie používa priamo Python z `.venv`, takže
nemusíš prostredie ručne aktivovať.

### Windows – PowerShell

Najprv over, že máš dostupný Python 3.11:

```powershell
py -3.11 --version
```

Potom vytvor prostredie, nainštaluj knižnice a zaregistruj jadro pre Jupyter:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ipykernel install --sys-prefix --name pisa-2025 --display-name "Python (pisa-2025)"
```

Ak príkaz `py` nemáš, ale `python --version` vypíše Python 3.11, v prvom
príkaze na vytvorenie prostredia môžeš použiť `python -m venv .venv`.

### macOS / Linux – terminál

Najprv over verziu:

```bash
python3.11 --version
```

Potom priprav prostredie:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m ipykernel install --sys-prefix --name pisa-2025 --display-name "Python (pisa-2025)"
```

Ak sa Python 3.11 u teba spúšťa príkazom `python3`, môžeš ním nahradiť
`python3.11` pri vytváraní prostredia. Najprv si over `python3 --version`.

## 4. Získanie a umiestnenie dát

**Samotný `git clone` veľký dátový súbor nestiahne.** V repozitári je kód
a codebook; pôvodné dáta a generované výstupy Git ignoruje.

Získaj **`CY09_MS_STU_PUF.sav`** od člena tímu, ktorý už má dohodnutú verziu
dát, alebo cez oficiálnu [databázu OECD PISA 2025](https://www.oecd.org/en/data/datasets/pisa-2025-database.html)
v časti **Download the datasets**. Potrebujeme súbor **Student questionnaire
vo formáte SPSS**. Ak je stiahnutý v ZIP archíve, najprv ho rozbaľ.

Súbor vlož sem, pričom zachovaj presný názov:

```text
pisa-2025-analysis/
└── data/
    └── raw/
        └── CY09_MS_STU_PUF.sav
```

Codebook `data/reference/PISA2025_Codebook.xlsx` už dostaneš s repozitárom.
Pôvodné súbory ponechávame bez úprav. Pre spoločné výsledky používajme rovnakú
verziu dát; prípadné novšie vydanie si najprv dohodnime v tíme.

## 5. Jednorazová príprava plného Parquetu

Po vložení SAV súboru vytvor jednu spoločnú dátovú základňu so **všetkými
riadkami a všetkými 885 premennými**. Spusti z hlavného priečinka projektu:

**Windows:**

```powershell
.\.venv\Scripts\python.exe src/prepare_data.py
```

**macOS / Linux:**

```bash
.venv/bin/python src/prepare_data.py
```

Prevod beží po menších dávkach, vypisuje priebeh a môže trvať niekoľko minút.
Vzniknú dva súbory, ktoré patria k sebe:

- `data/processed/student_full.parquet` – všetky pôvodné riadky, stĺpce a kódy.
- `data/processed/student_full_metadata.json` – popisy premenných, významy kódov,
  deklarované chýbajúce hodnoty a kontrolný súčet verzie pôvodných dát.

Popisy sú zároveň vložené do Parquetu. Samotný prevod nevyberá premenné,
nedopĺňa chýbajúce údaje ani nemení kódy odpovedí. Číselné hodnoty zostávajú
v pôvodnej presnosti a textové identifikátory si ponechajú aj úvodné nuly.

**Pre novú analýzu sa Parquet nevytvára znova.** Pri načítaní si vyberieš
iné stĺpce alebo krajiny podľa ukážky v nasledujúcom kroku. Opakované
spustenie prípravy pri rovnakých dátach overí hotové súbory a použije ich.
Pri novom vydaní zdroja sa dohodnite v tíme a prevod obnovte pridaním
`--force` k rovnakému príkazu. Knižnice pre prevod sú v hlavnom `requirements.txt`.

Každý si môže súbory vytvoriť raz lokálne. Alternatívne môže tím zdieľať už
hotový Parquet **spolu s príslušným JSON**. Oba vlož do `data/processed/`
a príkaz na prevod preskoč. Notebook na prácu s Parquetom potom pôvodný SAV
nepotrebuje; úvodný notebook o SAV a prípadná obnova prevodu ho potrebujú.
Veľké súbory sa naďalej neposielajú cez Git.

## 6. Spustenie notebooku

Z hlavného priečinka projektu spusti JupyterLab.

**Windows:**

```powershell
.\.venv\Scripts\python.exe -m jupyterlab
```

**macOS / Linux:**

```bash
.venv/bin/python -m jupyterlab
```

1. V prehliadači sa otvorí JupyterLab. Ak sa neotvorí automaticky, použi
   lokálny odkaz, ktorý vypíše terminál.
2. Na zoznámenie s pôvodným SAV otvor **[01_uvod_do_dat.ipynb](notebooks/01_uvod_do_dat.ipynb)**.
   Na rýchlu prácu so spoločným Parquetom otvor **[02_praca_s_parquetom.ipynb](notebooks/02_praca_s_parquetom.ipynb)**.
3. Vyber jadro **Python (pisa-2025)**. Jadro určuje, ktorý Python a knižnice
   notebook používa; zmeniť ho môžeš cez **Kernel → Change Kernel**.
4. Spúšťaj bunky zhora nadol, napríklad pomocou **Shift+Enter**.

Úvodný notebook o SAV postupne zobrazí metadáta, prehľad a vyhľadávanie premenných, prvých
20 záznamov pre šesť ukážkových premenných, kódy odpovedí, chýbajúce hodnoty
v ukážke a počty záznamov podľa krajiny alebo ekonomiky.

**Kontrola úspešného spustenia:** pri dohodnutom súbore uvidíš **755 721
záznamov a 885 premenných**. Posledná časť spočíta **90 kódov krajín / ekonomík**.
Číta jeden stĺpec celého veľkého súboru a môže chvíľu trvať. Počty žiakov sú
nevážené počty záznamov v súbore. Chýbajúce hodnoty v predchádzajúcej časti
sa týkajú iba 20-riadkovej ukážky.

Notebook o Parquete ukáže vyhľadanie všetkých premenných, načítanie vybraných
stĺpcov len pre Česko a Slovensko a výpis významov kódov. Pri novej téme
stačí zmeniť výber v `COLUMNS` a `COUNTRIES`; Parquet zostáva rovnaký.

Oba notebooky zdrojové súbory nemenia. Terminál s Jupyterom nechaj počas práce
otvorený. Po skončení ulož notebook a server zastav v termináli cez **Ctrl+C**;
ak si vypýta potvrdenie, potvrď ukončenie.

## 7. Každodenný postup a spolupráca

### Keď projekt otvoríš nabudúce

1. Z hlavného priečinka skontroluj `git status`. Ak máš rozpracované zmeny,
   najprv ich ulož do commitu alebo dokonči pred aktualizáciou projektu.
2. Keď je pracovný priečinok čistý, stiahni novšie zmeny cez `git pull --ff-only`.
3. Ak sa zmenil `requirements.txt`, zopakuj inštaláciu knižníc pre svoj systém
   z kroku 3. Prostredie `.venv` nemusíš vytvárať znova.
4. Spusti Jupyter príkazom z kroku 6, vyber správne jadro a pokračuj v práci.
   Po novom spustení jadra treba predchádzajúce bunky vykonať znova.

### Keď pridávaš vlastnú analýzu

- Najprv sa v tíme dohodnime na výskumnej otázke, krajinách a premenných.
- Úvodný notebook nechávame ako spoločný začiatok. Novú analýzu pridaj
  do ďalšieho notebooku s výstižným názvom, napríklad
  `notebooks/03_vlastna_analyza.ipynb`.
- Pracuj vo vlastnej vetve. Nasledujúci príklad predpokladá, že máš
  aktualizovanú spoločnú vetvu a pridávaš uvedený nový notebook:

```bash
git switch -c analyza-vlastna
```

Po úpravách reštartuj jadro a spusti všetky bunky od začiatku, aby notebook
fungoval bez premenných z predchádzajúcich pokusov. Pred commitom vymaž jeho
výstupy a ulož ho; spoluhráči tak dostanú prehľadný notebook na vlastné spustenie.
Potom zdieľaj zmeny, pričom cestu a názov vetvy prispôsob svojej práci:

```bash
git status
git add notebooks/03_vlastna_analyza.ipynb
git diff --cached --stat
git commit -m "Add initial analysis notebook"
git push -u origin analyza-vlastna
```

Vetvu potom navrhni na zlúčenie do spoločnej vetvy cez pull/merge request.
Do Gitu patria notebooky, kód, návody a zmeny v zozname knižníc. `.venv`,
veľké dáta a vygenerované dátové súbory zostávajú lokálne.

## 8. Ako sú rozdelené súbory a kde je Parquet

| Umiestnenie | Na čo slúži | Dostaneš cez Git? |
| --- | --- | --- |
| `notebooks/01_uvod_do_dat.ipynb` | Aktuálny východiskový notebook. | Áno |
| `notebooks/02_praca_s_parquetom.ipynb` | Rýchle načítanie vybraných premenných zo spoločného Parquetu. | Áno |
| `src/prepare_data.py` | Jednorazový prevod celého SAV bez výberu stĺpcov. | Áno |
| `requirements.txt` | Knižnice pre notebooky, prevod a Jupyter. | Áno |
| `data/processed/student_full.parquet` | Všetci žiaci a všetkých 885 premenných. | Nie, vytvoríš v kroku 5 alebo dostaneš od tímu. |
| `data/processed/student_full_metadata.json` | Význam premenných a kódov, verzia pôvodných dát. | Nie, vznikne spolu s Parquetom. |
| `data/raw/CY09_MS_STU_PUF.sav` | Pôvodný súbor so všetkými 885 premennými. | Nie, doplň ho samostatne. |
| `data/reference/PISA2025_Codebook.xlsx` | Význam premenných a kódov odpovedí. | Áno |
| `.venv/` | Tvoj lokálny Python a nainštalované knižnice. | Nie, vytvoríš ho pri setupe. |
| `archive/` | Starší kód, notebook a dokumentácia. | Áno, okrem generovaných súborov. |
| `archive/data/processed/student_core.parquet` | Starší výber 132 premenných pre všetkých žiakov. | Nie, je to lokálny výstup. |
| `archive/data/interim/`, `archive/outputs/` | Staršie slovníky, schémy, kontrolný report a HTML prehliadač. | Len prázdne priečinky. |

**Pre ďalšie analýzy používame plný `student_full.parquet`.** Starší
`student_core.parquet` v archíve obsahuje len 132 vopred vybraných premenných
a nie je potrebný pre aktuálny postup. Úvodný notebook číta pôvodný SAV;
druhý notebook pracuje s plným Parquetom a sprievodnými metadátami.

Na prvé spustenie použi kroky 1 až 6. Podrobnosti o staršom kóde sú
v **[archive/README.md](archive/README.md)**. Jeho širší zoznam knižníc
v `archive/requirements.txt` nepotrebuješ na nový prevod ani nové notebooky.

Pri budúcich populačných odhadoch budeme pracovať s výberovými a replikačnými
váhami a pri výsledkoch testov aj s plausible values. Spôsob práce s chýbajúcimi
kódmi určíme podľa konkrétnych premenných a codebooku.

## 9. Keď niečo nefunguje

| Problém | Čo skontrolovať |
| --- | --- |
| Príkaz `py -3.11` alebo `python3.11` neexistuje. | Doinštaluj Python 3.11 alebo použi jeho správnu cestu; verziu over pred vytvorením `.venv`. |
| Na Linuxe zlyhá vytvorenie `.venv` na chýbajúcom `ensurepip`. | Doinštaluj systémový balík podpory `venv` pre svoju verziu Pythonu a zopakuj vytvorenie prostredia. |
| `requirements.txt` sa nenašiel. | Terminál musí byť v hlavnom priečinku projektu. |
| `ModuleNotFoundError` v notebooku. | Dokonči inštaláciu knižníc, vyber jadro **Python (pisa-2025)** a reštartuj ho. |
| Jadro **Python (pisa-2025)** nie je v ponuke. | Zopakuj registráciu `ipykernel` z kroku 3, reštartuj Jupyter a otvor notebook znova. |
| `FileNotFoundError` pre `.sav`. | Súbor musí byť rozbalený v `data/raw/`, s presným názvom `CY09_MS_STU_PUF.sav`. |
| Chýba plný Parquet alebo metadata JSON. | Dokonči krok 5; pri zdieľaní hotového prevodu skopíruj oba súbory do `data/processed/`. |
| Výstupy patria k iným dátam alebo sú neúplné. | Použi zhodnú verziu SAV a po dohode v tíme obnov prevod s `--force`. |
| Prevod spotrebuje priveľa pamäte. | Zmenši dávku pridaním `--chunk-size 5000` k príkazu na prípravu. |
| `NameError` po spustení bunky. | Spusti najprv predchádzajúce bunky zhora nadol; novému jadru nestačia uložené výstupy. |
| Počty podľa krajín ešte nie sú zobrazené. | Počkaj na dokončenie čítania stĺpca celého súboru. |
| `git pull --ff-only` sa nepodarí. | Skontroluj správnu vetvu, lokálne zmeny a prístup do repozitára; pri rozdielnej histórii sa dohodni s tímom na zlúčení. |

## Oficiálne návody

- [Python: virtuálne prostredia](https://docs.python.org/3.11/library/venv.html)
- [JupyterLab: spustenie](https://jupyterlab.readthedocs.io/en/stable/getting_started/starting.html)
- [IPython: registrácia jadra](https://ipython.readthedocs.io/en/stable/install/kernel_install.html)
- [Apache Arrow: čítanie a zápis Parquetu](https://arrow.apache.org/docs/python/parquet/index.html)
- [OECD: databáza PISA 2025](https://www.oecd.org/en/data/datasets/pisa-2025-database.html)
