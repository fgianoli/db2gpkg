# PG2GPKG — PostgreSQL/PostGIS ⇄ GeoPackage

**Author:** Federico Gianoli  
**License:** GNU GPLv3  
**Version:** 2.0  
**QGIS version:** ≥ 3.20 — compatible with QGIS 3.x and 4.x (Qt5 & Qt6)

## Description

PG2GPKG is a QGIS plugin that moves data **both ways** between PostgreSQL/PostGIS and GeoPackage:

- **Export** — dump entire PostgreSQL/PostGIS databases (or selected tables) to GeoPackage files, with three layout modes and automatic rewriting of QGIS projects stored in the database.
- **Import** — load one or more layers from a `.gpkg` file into PostgreSQL/PostGIS, with per-layer destination control, field mapping, and reprojection.

## Export features

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

## Import features

- **Multi-layer batch import:** Choose a `.gpkg` file and pick which of its layers to import; each row in the layer table has its own destination schema, table name, and mode.

- **Three modes:**
  - *create* — fail if the destination table already exists
  - *append* — add features to an existing table
  - *replace* — drop and recreate the destination table, then load

- **Interactive field mapping:** Per-layer sub-dialog to include/exclude columns and rename them (with quick `snake_case` conversion). Mappings are **persisted as presets** per GeoPackage + layer and restored automatically the next time you analyze the same file.

- **Layer preview:** "View..." opens a read-only preview of the first 50 rows of any layer before importing.

- **Batch helpers:** Apply a destination schema, mode, or source SRID to all selected layers at once. **"New schema..."** creates a schema directly from the dialog (requires `CREATE` privilege).

- **Reprojection:** Optionally reproject all layers to a target EPSG before loading.

- **Source SRID assignment:** Layers that declare no CRS get an editable EPSG field so you can assign one before import (this is *not* a reprojection — layers that already have a CRS are untouched).

- **Fast loading:** Uses GDAL's PostgreSQL driver with `PG_USE_COPY=YES`, so inserts go through PostgreSQL `COPY` instead of single `INSERT` statements — typically 5–10× faster than row-by-row imports.

- **Pre-import safety checks:** Validates destination identifiers, warns on append-mode column mismatches and duplicate destinations, and confirms `replace` (DROP CASCADE). A **health check** detects `pg_is_in_recovery()` and flags the known 3D/Measured + COPY combination.

- **Resilience:** Auto-retries on transient PostgreSQL errors (recovery mode, "server closed unexpectedly", "too many connections", …) with 2/5/10 s backoff. A **"Retry failed (N)"** button re-runs only the layers that failed in the last run.

- **Advanced options (for fragile PostgreSQL servers):** disable COPY (fall back to `INSERT`), skip the post-load spatial index, force 2D (drop Z/M), and pause N ms between layers.

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

## Usage — Export

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

## Usage — Import

1. Open the plugin from **Database → PG2GPKG → Import GeoPackage to PostgreSQL** or from the toolbar icon.

2. **Browse and analyze** a `.gpkg` file. The layer table is populated with one row per layer (rows, geometry, SRID).

3. **Connect to PostgreSQL** (same connection picker as the export dialog). After connecting, the destination *schema* combo on each row is populated with schemas where the current user has `CREATE` privilege.

4. **Configure each layer** in the table:
   - Tick / untick to include it in the batch
   - Set the destination schema and table name
   - Pick a mode (`create` / `append` / `replace`)
   - Click *Edit...* in the Mapping column to rename or exclude individual columns (the mapping is remembered as a preset)
   - Click *View...* in the Preview column to inspect the first rows
   - For layers without a CRS, set an EPSG code in the SRID column

   Use **Apply to all selected layers** to set schema / mode / source SRID in bulk, or **New schema...** to create a schema on the fly.

5. **Options:**
   - *Reproject all layers to a target SRID* — runs a coordinate transform before insert

6. **Advanced options (for fragile PostgreSQL servers)** — optional:
   - *Use COPY* — uncheck to fall back to slower but lighter `INSERT` statements
   - *Create spatial index after load* — uncheck if the server crashes at the end of large imports
   - *Force 2D* — strips Z/M from 3D/Measured geometries
   - *Pause between layers* — wait N ms between layers to let the server recover

7. Click **Import**. A pre-import check and a server health check may ask for confirmation. If some layers fail (e.g. the database was momentarily in recovery), use **Retry failed (N)** to re-run just those layers.

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

# PG2GPKG — PostgreSQL/PostGIS ⇄ GeoPackage

**Autore:** Federico Gianoli  
**Licenza:** GNU GPLv3  
**Versione:** 2.0  
**Versione QGIS:** ≥ 3.20 — compatibile con QGIS 3.x e 4.x (Qt5 e Qt6)

## Descrizione

PG2GPKG è un plugin QGIS che sposta i dati **nei due sensi** tra PostgreSQL/PostGIS e GeoPackage:

- **Esportazione** — riversa interi database PostgreSQL/PostGIS (o tabelle selezionate) in file GeoPackage, con tre modalità di layout e riscrittura automatica dei progetti QGIS memorizzati nel database.
- **Importazione** — carica uno o più layer da un file `.gpkg` in PostgreSQL/PostGIS, con controllo per-layer della destinazione, mappatura campi e riproiezione.

## Funzionalità di esportazione

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

## Funzionalità di importazione

- **Import batch multi-layer:** scegli un file `.gpkg`, seleziona quali layer importare; ogni riga della tabella ha schema, nome tabella e modalità di destinazione indipendenti.

- **Tre modalità:**
  - *create* — fallisce se la tabella di destinazione esiste già
  - *append* — aggiunge i record a una tabella esistente
  - *replace* — elimina e ricrea la tabella di destinazione prima del caricamento

- **Mappatura campi interattiva:** sub-dialog per ogni layer per includere/escludere colonne e rinominarle (con conversione rapida in `snake_case`). Le mappature sono **salvate come preset** per GeoPackage + layer e ripristinate automaticamente alla successiva analisi dello stesso file.

- **Anteprima layer:** "Visualizza..." apre un'anteprima in sola lettura delle prime 50 righe di un layer prima dell'import.

- **Helper batch:** applica schema, modalità o SRID sorgente a tutti i layer selezionati in un colpo solo. **"Nuovo schema..."** crea uno schema direttamente dal dialog (richiede privilegio `CREATE`).

- **Riproiezione:** opzionalmente riproietta tutti i layer in un EPSG di destinazione prima dell'inserimento.

- **Assegnazione SRID sorgente:** ai layer privi di CRS viene offerto un campo EPSG modificabile per assegnarne uno prima dell'import (non è una riproiezione — i layer che hanno già un CRS non vengono toccati).

- **Caricamento veloce:** usa il driver PostgreSQL di GDAL con `PG_USE_COPY=YES`, sfruttando `COPY` invece dei singoli `INSERT` — tipicamente 5–10× più veloce dell'import riga-per-riga.

- **Controlli di sicurezza pre-import:** valida gli identificatori di destinazione, avvisa su mismatch di colonne in modalità append e su destinazioni duplicate, e chiede conferma per `replace` (DROP CASCADE). Un **health check** rileva `pg_is_in_recovery()` e segnala la combinazione critica 3D/Measured + COPY.

- **Resilienza:** ritenta automaticamente sugli errori PostgreSQL transitori (recovery mode, "server closed unexpectedly", "too many connections", …) con backoff 2/5/10 s. Il pulsante **"Riprova falliti (N)"** riesegue solo i layer falliti nell'ultima esecuzione.

- **Opzioni avanzate (per server PostgreSQL fragili):** disabilita COPY (fallback a `INSERT`), salta l'indice spaziale post-caricamento, forza 2D (rimuove Z/M), e pausa di N ms tra un layer e l'altro.

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

## Utilizzo — Esportazione

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

## Utilizzo — Importazione

1. Apri il plugin da **Database → PG2GPKG → Importa GeoPackage in PostgreSQL** o dall'icona nella toolbar.

2. **Sfoglia e analizza** un file `.gpkg`. La tabella dei layer viene popolata con una riga per layer (righe, geometria, SRID).

3. **Connettiti a PostgreSQL** (stesso selettore di connessione del dialog di esportazione). Dopo la connessione, il combo *schema di destinazione* su ogni riga viene popolato con gli schemi su cui l'utente corrente ha il privilegio `CREATE`.

4. **Configura ogni layer** nella tabella:
   - Spunta/desconta per includerlo nel batch
   - Imposta schema e nome tabella di destinazione
   - Scegli una modalità (`create` / `append` / `replace`)
   - Clicca *Modifica...* nella colonna Mappatura per rinominare o escludere singole colonne (la mappatura viene memorizzata come preset)
   - Clicca *Visualizza...* nella colonna Anteprima per ispezionare le prime righe
   - Per i layer privi di CRS, imposta un codice EPSG nella colonna SRID

   Usa **Applica a tutti i layer selezionati** per impostare schema / modalità / SRID sorgente in blocco, oppure **Nuovo schema...** per creare uno schema al volo.

5. **Opzioni:**
   - *Riproietta tutti i layer in un SRID di destinazione* — esegue una trasformazione di coordinate prima dell'inserimento

6. **Opzioni avanzate (per server PostgreSQL fragili)** — facoltative:
   - *Usa COPY* — deseleziona per usare gli `INSERT`, più lenti ma più leggeri
   - *Crea indice spaziale dopo il caricamento* — deseleziona se il server va in crash a fine import
   - *Forza 2D* — rimuove Z/M dalle geometrie 3D/Measured
   - *Pausa tra i layer* — attende N ms tra un layer e l'altro per dare respiro al server

7. Clicca **Importa**. Un controllo pre-import e un health check del server potrebbero chiedere conferma. Se alcuni layer falliscono (es. il database era momentaneamente in recovery), usa **Riprova falliti (N)** per rieseguire solo quei layer.
