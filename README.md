# PG2GPKG — Export PostgreSQL/PostGIS to GeoPackage

**Author:** Federico Gianoli  
**License:** GNU GPLv3  
**QGIS version:** ≥ 3.16

## Description

PG2GPKG is a QGIS plugin that exports entire PostgreSQL/PostGIS databases (or selected tables) to GeoPackage files. It supports three export modes, selective table export, and automatic rewriting of QGIS projects stored in the database.

## Features

- **Three export modes:**
  - One GeoPackage per schema (`output/schema.gpkg`)
  - Everything in a single GeoPackage (`output/database.gpkg`)
  - One GeoPackage per table (`output/schema/table.gpkg`)

- **Selective export:** Tree widget with checkboxes allows selecting individual schemas and tables. Quick-select buttons for "all", "none", or "spatial only".

- **QGIS project export:** Detects QGIS projects stored in the database (`qgis_projects` table), exports them as `.qgs` files, and rewrites all PostgreSQL datasource paths to point to the corresponding GeoPackage files.

- **Handles edge cases:**
  - `fid` fields of type `double/real` (GeoPackage requires integer FID)
  - SSL mode normalization (Qt enum → psycopg2 strings)
  - Compressed project formats (zlib, ZIP/.qgz)
  - System tables are automatically filtered out

- **Bilingual:** Full Italian and English interface (auto-detected from QGIS locale).

## Installation

### From ZIP file

1. Download or create the `pg2gpkg.zip` file
2. In QGIS: *Plugins → Manage and Install Plugins → Install from ZIP*
3. Select the ZIP file and click *Install Plugin*

### Manual installation

1. Copy the `pg2gpkg` folder to your QGIS plugins directory:
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
2. Restart QGIS
3. Enable the plugin in *Plugins → Manage and Install Plugins*

### Dependency

The plugin requires `psycopg2`. Install it if not already present:

```bash
pip install psycopg2-binary
```

On Windows with OSGeo4W:
```bash
python -m pip install psycopg2-binary
```

## Usage

1. Open the plugin from **Database → PG2GPKG → Export PostgreSQL to GeoPackage** or from the toolbar icon.

2. **Select a connection:** Choose a registered PostgreSQL connection from the dropdown, or enter parameters manually.

3. **Click "Connect and load schemas/tables"** to populate the tree widget.

4. **Select tables:** Use checkboxes to select/deselect individual tables or entire schemas. Use the quick buttons:
   - *Select all* — check everything
   - *Deselect all* — uncheck everything
   - *Spatial only* — check only tables with geometry columns

5. **Choose export mode:**
   - **One GeoPackage per schema** — creates `schema.gpkg` in the output folder, each containing all selected tables from that schema
   - **Single GeoPackage** — creates one file with all tables; if multiple schemas are selected, layer names are prefixed with `schema__`
   - **One GeoPackage per table** — creates a subfolder per schema with individual `.gpkg` files

6. **Options:**
   - *Export QGIS projects* — finds projects in the `qgis_projects` table and exports them with rewritten datasource paths

7. **Select output folder** and click **Export**.

8. Check the **QGIS Log Messages** panel (tab "PG2GPKG") for detailed progress and diagnostic information.

## Compiling translations

If you modify the `.ts` translation files, compile them to `.qm`:

```bash
cd pg2gpkg/i18n
lrelease pg2gpkg_it.ts
```

Or use the provided script:
```bash
python pg2gpkg/i18n/compile_translations.py
```

---

# PG2GPKG — Esporta PostgreSQL/PostGIS in GeoPackage

**Autore:** Federico Gianoli  
**Licenza:** GNU GPLv3  
**Versione QGIS:** ≥ 3.16

## Descrizione

PG2GPKG è un plugin QGIS che esporta interi database PostgreSQL/PostGIS (o tabelle selezionate) in file GeoPackage. Supporta tre modalità di esportazione, selezione selettiva delle tabelle e riscrittura automatica dei progetti QGIS salvati nel database.

## Funzionalità

- **Tre modalità di esportazione:**
  - Un GeoPackage per schema (`output/schema.gpkg`)
  - Tutto in un unico GeoPackage (`output/database.gpkg`)
  - Un GeoPackage per tabella (`output/schema/tabella.gpkg`)

- **Esportazione selettiva:** Widget ad albero con checkbox per selezionare singoli schemi e tabelle. Pulsanti rapidi per "tutto", "niente" o "solo spaziali".

- **Esportazione progetti QGIS:** Rileva i progetti salvati nel database (tabella `qgis_projects`), li esporta come file `.qgs` e riscrive tutti i percorsi delle sorgenti dati PostgreSQL per puntare ai file GeoPackage corrispondenti.

- **Gestione casi particolari:**
  - Campi `fid` di tipo `double/real` (GeoPackage richiede FID intero)
  - Normalizzazione modalità SSL (enum Qt → stringhe psycopg2)
  - Formati progetto compressi (zlib, ZIP/.qgz)
  - Tabelle di sistema filtrate automaticamente

- **Bilingue:** Interfaccia completa in italiano e inglese (rilevamento automatico dalla lingua di QGIS).

## Installazione

### Da file ZIP

1. Scarica o crea il file `pg2gpkg.zip`
2. In QGIS: *Plugin → Gestisci e installa plugin → Installa da ZIP*
3. Seleziona il file ZIP e clicca *Installa plugin*

### Installazione manuale

1. Copia la cartella `pg2gpkg` nella directory dei plugin QGIS:
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
2. Riavvia QGIS
3. Abilita il plugin in *Plugin → Gestisci e installa plugin*

### Dipendenza

Il plugin richiede `psycopg2`. Installalo se non già presente:

```bash
pip install psycopg2-binary
```

## Utilizzo

1. Apri il plugin da **Database → PG2GPKG → Esporta PostgreSQL in GeoPackage** o dall'icona nella toolbar.

2. **Seleziona una connessione:** scegli una connessione PostgreSQL registrata o inserisci i parametri manualmente.

3. **Clicca "Connetti e carica schemi/tabelle"** per popolare l'albero.

4. **Seleziona le tabelle** con le checkbox. Usa i pulsanti rapidi:
   - *Seleziona tutto*
   - *Deseleziona tutto*
   - *Solo spaziali* — seleziona solo le tabelle con colonne geometria

5. **Scegli la modalità di esportazione.**

6. **Seleziona la cartella di output** e clicca **Esporta**.

7. Controlla il pannello **Messaggi di log** di QGIS (tab "PG2GPKG") per informazioni dettagliate.
