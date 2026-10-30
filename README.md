# PISA 2025 – úvod do dát

Projekt na postupné skúmanie dodaných žiackych dát PISA 2025.
Aktuálne slúži na zoznámenie sa s dátami a významom premenných.
Výskumnú otázku, výber premenných a analytické metódy doplníme neskôr.

## Kde začať

Otvor **[notebooks/01_uvod_do_dat.ipynb](notebooks/01_uvod_do_dat.ipynb)**
a spúšťaj bunky postupne zhora nadol. Vysvetlenia sú po slovensky.
Notebook ukáže:

1. počet riadkov a premenných z metadát,
2. názvy a významy premenných vrátane jednoduchého vyhľadávania,
3. prvých 20 záznamov pre niekoľko ukážkových premenných,
4. kódy odpovedí a chýbajúce hodnoty v tejto malej ukážke,
5. počty záznamov podľa krajiny alebo ekonomiky z jedného stĺpca celého súboru.

Veľký SPSS súbor sa nenačítava celý do pamäte. Posledná časť číta len
stĺpec `CNT`, ale musí prejsť celý súbor a môže chvíľu trvať.
Notebook zdrojové dáta nemení a nevytvára ďalšie dátové súbory.

## Usporiadanie

```text
pisa-2025-analysis/
├── README.md
├── requirements.txt
├── notebooks/
│   └── 01_uvod_do_dat.ipynb
├── data/
│   ├── raw/CY09_MS_STU_PUF.sav          # pôvodné dáta, približne 2 GB
│   └── reference/PISA2025_Codebook.xlsx # dodaný codebook
└── archive/                            # predchádzajúca príprava dát
```

Pôvodné dáta a codebook ponechávame bez úprav. Veľké dáta ani generované
výstupy sa neukladajú do Gitu; codebook je súčasťou repozitára.
Po skopírovaní projektu na iný počítač treba dátový súbor vložiť do `data/raw/`.

## Spustenie

Príkazy spusti z hlavného priečinka projektu. Ak už existuje funkčné prostredie
`.venv`, môžeš preskočiť jeho vytvorenie.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/jupyter lab
```

V Jupyteri otvor úvodný notebook a vyber jadro z tohto prostredia.
Súčasné prostredie `.venv` zostalo zachované; na čistý úvodný notebook stačia
knižnice v hlavnom `requirements.txt`.

## Archív

V **[archive/README.md](archive/README.md)** je mapa pôvodného kódu,
notebooku, dokumentácie a vygenerovaných výstupov. Patrí tam aj existujúci
menší dataset s 132 premennými. Úvodný notebook ho nepotrebuje.
Archív je lokálne zachovaný; jeho veľké a generované súbory Git ignoruje.

## Ako pokračovať

Po oboznámení sa s dátami vyberieme výskumnú otázku, krajiny a potrebné
premenné. Ďalšie kroky budeme pridávať samostatne a s vysvetlením.
Počty riadkov opisujú dostupný súbor. Pre budúce populačné odhady bude treba
zohľadniť výberové váhy, replikačné váhy a pri výsledkoch testov aj plausible values;
pomocné podklady k tomu sú v archíve.
