<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="it_IT">
<context>
    <name>PG2GPKG</name>

    <!-- Plugin action -->
    <message>
        <source>Export PostgreSQL to GeoPackage</source>
        <translation>Esporta PostgreSQL in GeoPackage</translation>
    </message>
    <message>
        <source>Export PostgreSQL/PostGIS database to GeoPackage</source>
        <translation>Esporta database PostgreSQL/PostGIS in GeoPackage</translation>
    </message>

    <!-- Dialog title -->
    <message>
        <source>Export PostgreSQL → GeoPackage</source>
        <translation>Esporta PostgreSQL → GeoPackage</translation>
    </message>

    <!-- Connection group -->
    <message>
        <source>PostgreSQL Connection</source>
        <translation>Connessione PostgreSQL</translation>
    </message>
    <message>
        <source>Connection:</source>
        <translation>Connessione:</translation>
    </message>
    <message>
        <source>Use manual parameters</source>
        <translation>Usa parametri manuali</translation>
    </message>
    <message>
        <source>Host:</source>
        <translation>Host:</translation>
    </message>
    <message>
        <source>Port:</source>
        <translation>Porta:</translation>
    </message>
    <message>
        <source>Database:</source>
        <translation>Database:</translation>
    </message>
    <message>
        <source>User:</source>
        <translation>Utente:</translation>
    </message>
    <message>
        <source>Password:</source>
        <translation>Password:</translation>
    </message>
    <message>
        <source>Connect and load schemas/tables</source>
        <translation>Connetti e carica schemi/tabelle</translation>
    </message>

    <!-- Table tree -->
    <message>
        <source>Schemas and tables</source>
        <translation>Schemi e tabelle</translation>
    </message>
    <message>
        <source>Name</source>
        <translation>Nome</translation>
    </message>
    <message>
        <source>Type</source>
        <translation>Tipo</translation>
    </message>
    <message>
        <source>Geometry</source>
        <translation>Geometria</translation>
    </message>
    <message>
        <source>SRID</source>
        <translation>SRID</translation>
    </message>
    <message>
        <source>Select all</source>
        <translation>Seleziona tutto</translation>
    </message>
    <message>
        <source>Deselect all</source>
        <translation>Deseleziona tutto</translation>
    </message>
    <message>
        <source>Spatial only</source>
        <translation>Solo spaziali</translation>
    </message>
    <message>
        <source>Table</source>
        <translation>Tabella</translation>
    </message>
    <message>
        <source>View</source>
        <translation>Vista</translation>
    </message>

    <!-- Export mode -->
    <message>
        <source>GeoPackage mode</source>
        <translation>Modalità GeoPackage</translation>
    </message>
    <message>
        <source>One GeoPackage per schema  (output/schema.gpkg)</source>
        <translation>Un GeoPackage per ogni schema  (output/schema.gpkg)</translation>
    </message>
    <message>
        <source>Everything in a single GeoPackage</source>
        <translation>Tutto in un unico GeoPackage</translation>
    </message>
    <message>
        <source>One GeoPackage per table  (output/schema/table.gpkg)</source>
        <translation>Un GeoPackage per ogni tabella  (output/schema/tabella.gpkg)</translation>
    </message>
    <message>
        <source>filename.gpkg</source>
        <translation>nome_file.gpkg</translation>
    </message>

    <!-- Options -->
    <message>
        <source>Options</source>
        <translation>Opzioni</translation>
    </message>
    <message>
        <source>Export QGIS projects from DB (with updated paths to GeoPackages)</source>
        <translation>Esporta progetti QGIS dal DB (con percorsi aggiornati ai GeoPackage)</translation>
    </message>

    <!-- Output -->
    <message>
        <source>Select output folder...</source>
        <translation>Seleziona cartella di output...</translation>
    </message>
    <message>
        <source>Browse...</source>
        <translation>Sfoglia...</translation>
    </message>
    <message>
        <source>Output:</source>
        <translation>Output:</translation>
    </message>
    <message>
        <source>Select output folder</source>
        <translation>Seleziona cartella di output</translation>
    </message>

    <!-- Buttons -->
    <message>
        <source>Export</source>
        <translation>Esporta</translation>
    </message>
    <message>
        <source>Close</source>
        <translation>Chiudi</translation>
    </message>

    <!-- Progress -->
    <message>
        <source>Exporting...</source>
        <translation>Esportazione in corso...</translation>
    </message>
    <message>
        <source>Cancel</source>
        <translation>Annulla</translation>
    </message>
    <message>
        <source>Searching for QGIS projects in database...</source>
        <translation>Ricerca progetti QGIS nel database...</translation>
    </message>
    <message>
        <source>Project</source>
        <translation>Progetto</translation>
    </message>

    <!-- Errors -->
    <message>
        <source>Missing dependency</source>
        <translation>Dipendenza mancante</translation>
    </message>
    <message>
        <source>The 'psycopg2' module is not installed.

Install it with: pip install psycopg2-binary</source>
        <translation>Il modulo 'psycopg2' non è installato.

Installalo con: pip install psycopg2-binary</translation>
    </message>
    <message>
        <source>Error</source>
        <translation>Errore</translation>
    </message>
    <message>
        <source>No connection selected.</source>
        <translation>Nessuna connessione selezionata.</translation>
    </message>
    <message>
        <source>Connection error</source>
        <translation>Errore connessione</translation>
    </message>
    <message>
        <source>Select a valid output folder.</source>
        <translation>Seleziona una cartella di output valida.</translation>
    </message>
    <message>
        <source>Select at least one table.</source>
        <translation>Seleziona almeno una tabella.</translation>
    </message>
    <message>
        <source>Connect to database first.</source>
        <translation>Connettiti al database prima.</translation>
    </message>

    <!-- Status -->
    <message>
        <source>{count} tables/views in {schemas} schemas — {db}</source>
        <translation>{count} tabelle/viste in {schemas} schemi — {db}</translation>
    </message>

    <!-- Summary -->
    <message>
        <source>one GeoPackage per schema</source>
        <translation>un GeoPackage per schema</translation>
    </message>
    <message>
        <source>single GeoPackage</source>
        <translation>unico GeoPackage</translation>
    </message>
    <message>
        <source>one GeoPackage per table</source>
        <translation>un GeoPackage per tabella</translation>
    </message>
    <message>
        <source>Export completed! ({mode})

Layers exported: {ok}/{total}
GeoPackages created: {gpkg}
</source>
        <translation>Esportazione completata! ({mode})

Layer esportati: {ok}/{total}
GeoPackage creati: {gpkg}
</translation>
    </message>
    <message>
        <source>
QGIS projects: {count}
</source>
        <translation>
Progetti QGIS: {count}
</translation>
    </message>
    <message>
        <source>
Errors ({count}):
</source>
        <translation>
Errori ({count}):
</translation>
    </message>
    <message>
        <source>  … and {n} more (see log)
</source>
        <translation>  … e altri {n} (vedi log)
</translation>
    </message>
    <message>
        <source>Result</source>
        <translation>Risultato</translation>
    </message>
    <message>
        <source>Completed: {ok} layers, {err} errors</source>
        <translation>Completato: {ok} layer, {err} errori</translation>
    </message>

    <!-- ============================================================ -->
    <!-- IMPORT  (GeoPackage → PostgreSQL)                              -->
    <!-- ============================================================ -->

    <!-- Plugin action -->
    <message>
        <source>Import GeoPackage to PostgreSQL</source>
        <translation>Importa GeoPackage in PostgreSQL</translation>
    </message>
    <message>
        <source>Import a GeoPackage into PostgreSQL/PostGIS</source>
        <translation>Importa un GeoPackage in PostgreSQL/PostGIS</translation>
    </message>

    <!-- Dialog title -->
    <message>
        <source>Import GeoPackage → PostgreSQL</source>
        <translation>Importa GeoPackage → PostgreSQL</translation>
    </message>

    <!-- GPKG file group -->
    <message>
        <source>GeoPackage file</source>
        <translation>File GeoPackage</translation>
    </message>
    <message>
        <source>Select a .gpkg file...</source>
        <translation>Seleziona un file .gpkg...</translation>
    </message>
    <message>
        <source>Analyze GPKG</source>
        <translation>Analizza GPKG</translation>
    </message>
    <message>
        <source>Select GeoPackage</source>
        <translation>Seleziona GeoPackage</translation>
    </message>
    <message>
        <source>GeoPackage files (*.gpkg)</source>
        <translation>File GeoPackage (*.gpkg)</translation>
    </message>

    <!-- Connection group (import-specific) -->
    <message>
        <source>Connect and load schemas</source>
        <translation>Connetti e carica schemi</translation>
    </message>

    <!-- Layers table -->
    <message>
        <source>Layers in the GeoPackage</source>
        <translation>Layer nel GeoPackage</translation>
    </message>
    <message>
        <source>Layer</source>
        <translation>Layer</translation>
    </message>
    <message>
        <source>Rows</source>
        <translation>Righe</translation>
    </message>
    <message>
        <source>Dest. schema</source>
        <translation>Schema dest.</translation>
    </message>
    <message>
        <source>Dest. table</source>
        <translation>Tabella dest.</translation>
    </message>
    <message>
        <source>Mode</source>
        <translation>Modalità</translation>
    </message>
    <message>
        <source>Mapping</source>
        <translation>Mappatura</translation>
    </message>
    <message>
        <source>create</source>
        <translation>crea</translation>
    </message>
    <message>
        <source>append</source>
        <translation>aggiungi</translation>
    </message>
    <message>
        <source>replace</source>
        <translation>sostituisci</translation>
    </message>
    <message>
        <source>Edit...</source>
        <translation>Modifica...</translation>
    </message>
    <message>
        <source>Edit... ({n})</source>
        <translation>Modifica... ({n})</translation>
    </message>

    <!-- Reprojection options -->
    <message>
        <source>Reproject all layers to a target SRID</source>
        <translation>Riproietta tutti i layer in uno SRID di destinazione</translation>
    </message>
    <message>
        <source>Target EPSG:</source>
        <translation>EPSG di destinazione:</translation>
    </message>

    <!-- Buttons / progress -->
    <message>
        <source>Import</source>
        <translation>Importa</translation>
    </message>
    <message>
        <source>Importing...</source>
        <translation>Importazione in corso...</translation>
    </message>

    <!-- Errors / messages -->
    <message>
        <source>GDAL/OGR Python bindings are not available.</source>
        <translation>I binding Python di GDAL/OGR non sono disponibili.</translation>
    </message>
    <message>
        <source>Select a valid .gpkg file.</source>
        <translation>Seleziona un file .gpkg valido.</translation>
    </message>
    <message>
        <source>No layers found in the GeoPackage.</source>
        <translation>Nessun layer trovato nel GeoPackage.</translation>
    </message>
    <message>
        <source>Analyze a GeoPackage first.</source>
        <translation>Analizza prima un GeoPackage.</translation>
    </message>
    <message>
        <source>Destination table for layer '{layer}' is empty.</source>
        <translation>La tabella di destinazione per il layer '{layer}' è vuota.</translation>
    </message>
    <message>
        <source>Select at least one layer.</source>
        <translation>Seleziona almeno un layer.</translation>
    </message>
    <message>
        <source>{n} layer(s) will overwrite existing tables. Continue?</source>
        <translation>{n} layer sovrascriveranno tabelle esistenti. Continuare?</translation>
    </message>
    <message>
        <source>Confirm overwrite</source>
        <translation>Conferma sovrascrittura</translation>
    </message>

    <!-- Status -->
    <message>
        <source>Loaded {n} layer(s) from {file}</source>
        <translation>Caricati {n} layer da {file}</translation>
    </message>
    <message>
        <source>Connected to {db} — {n} writable schemas</source>
        <translation>Connesso a {db} — {n} schemi scrivibili</translation>
    </message>

    <!-- Summary -->
    <message>
        <source>Import cancelled.

</source>
        <translation>Importazione annullata.

</translation>
    </message>
    <message>
        <source>Import completed!

Layers imported: {ok}/{total}
Features inserted: {feat}
</source>
        <translation>Importazione completata!

Layer importati: {ok}/{total}
Feature inserite: {feat}
</translation>
    </message>
    <message>
        <source>Completed: {ok} layers, {feat} features, {err} errors</source>
        <translation>Completato: {ok} layer, {feat} feature, {err} errori</translation>
    </message>

    <!-- ============================================================ -->
    <!-- FIELD MAPPING SUB-DIALOG                                       -->
    <!-- ============================================================ -->

    <message>
        <source>Field mapping — {layer}</source>
        <translation>Mappatura campi — {layer}</translation>
    </message>
    <message>
        <source>Uncheck columns to exclude them. Edit destination names to rename. Lowercase + snake_case is recommended.</source>
        <translation>Deseleziona le colonne per escluderle. Modifica i nomi di destinazione per rinominare. Si consiglia minuscolo + snake_case.</translation>
    </message>
    <message>
        <source>Include</source>
        <translation>Includi</translation>
    </message>
    <message>
        <source>GPKG column</source>
        <translation>Colonna GPKG</translation>
    </message>
    <message>
        <source>Destination column</source>
        <translation>Colonna di destinazione</translation>
    </message>
    <message>
        <source>Include all</source>
        <translation>Includi tutto</translation>
    </message>
    <message>
        <source>Exclude all</source>
        <translation>Escludi tutto</translation>
    </message>
    <message>
        <source>All to snake_case</source>
        <translation>Tutto in snake_case</translation>
    </message>
    <message>
        <source>Reset to original</source>
        <translation>Ripristina originali</translation>
    </message>
    <message>
        <source>OK</source>
        <translation>OK</translation>
    </message>
    <message>
        <source>Invalid mapping</source>
        <translation>Mappatura non valida</translation>
    </message>
    <message>
        <source>Destination column for '{col}' cannot be empty.</source>
        <translation>La colonna di destinazione per '{col}' non può essere vuota.</translation>
    </message>
    <message>
        <source>Duplicate destination column: '{col}'</source>
        <translation>Colonna di destinazione duplicata: '{col}'</translation>
    </message>
    <message>
        <source>At least one column must be included.</source>
        <translation>Almeno una colonna deve essere inclusa.</translation>
    </message>

    <!-- ============================================================ -->
    <!-- PREVIEW                                                       -->
    <!-- ============================================================ -->
    <message>
        <source>Preview — {layer}</source>
        <translation>Anteprima — {layer}</translation>
    </message>
    <message>
        <source>Showing first {n} rows of '{layer}' ({total} columns)</source>
        <translation>Prime {n} righe di '{layer}' ({total} colonne)</translation>
    </message>
    <message>
        <source>Preview</source>
        <translation>Anteprima</translation>
    </message>
    <message>
        <source>View...</source>
        <translation>Visualizza...</translation>
    </message>

    <!-- ============================================================ -->
    <!-- BATCH HELPERS                                                  -->
    <!-- ============================================================ -->
    <message>
        <source>Apply to all selected layers</source>
        <translation>Applica a tutti i layer selezionati</translation>
    </message>
    <message>
        <source>Schema:</source>
        <translation>Schema:</translation>
    </message>
    <message>
        <source>Set schema</source>
        <translation>Imposta schema</translation>
    </message>
    <message>
        <source>Mode:</source>
        <translation>Modalità:</translation>
    </message>
    <message>
        <source>Set mode</source>
        <translation>Imposta modalità</translation>
    </message>
    <message>
        <source>Source EPSG:</source>
        <translation>EPSG di origine:</translation>
    </message>
    <message>
        <source>EPSG for layers without CRS:</source>
        <translation>EPSG per layer senza CRS:</translation>
    </message>
    <message>
        <source>Set source SRID (layers without CRS only)</source>
        <translation>Imposta SRID di origine (solo layer senza CRS)</translation>
    </message>
    <message>
        <source>Assign source SRID (only layers without CRS)</source>
        <translation>Assegna SRID di origine (solo layer senza CRS)</translation>
    </message>
    <message>
        <source>Layer has no CRS. Set an EPSG code to assign one before import.</source>
        <translation>Il layer non ha un CRS. Imposta un codice EPSG per assegnarne uno prima dell'importazione.</translation>
    </message>
    <message>
        <source>EPSG code to assign to layers that DO NOT declare a CRS in the GeoPackage. This is NOT a reprojection — layers that already have a CRS are left untouched. For reprojection use the Options panel below.</source>
        <translation>Codice EPSG da assegnare ai layer che NON dichiarano un CRS nel GeoPackage. NON è una riproiezione — i layer che hanno già un CRS non vengono toccati. Per riproiettare usa il pannello Opzioni più in basso.</translation>
    </message>
    <message>
        <source>Set the destination schema for all selected layers.</source>
        <translation>Imposta lo schema di destinazione per tutti i layer selezionati.</translation>
    </message>
    <message>
        <source>Set the create/append/replace mode for all selected layers.</source>
        <translation>Imposta la modalità crea/aggiungi/sostituisci per tutti i layer selezionati.</translation>
    </message>

    <!-- New schema -->
    <message>
        <source>New schema...</source>
        <translation>Nuovo schema...</translation>
    </message>
    <message>
        <source>Create a new schema in the database. Requires CREATE privilege on the database.</source>
        <translation>Crea un nuovo schema nel database. Richiede il privilegio CREATE sul database.</translation>
    </message>
    <message>
        <source>New schema</source>
        <translation>Nuovo schema</translation>
    </message>
    <message>
        <source>New schema name (lowercase, snake_case recommended):</source>
        <translation>Nome del nuovo schema (minuscolo, snake_case consigliato):</translation>
    </message>
    <message>
        <source>Schema name cannot be empty.</source>
        <translation>Il nome dello schema non può essere vuoto.</translation>
    </message>
    <message>
        <source>Quoting required</source>
        <translation>Quoting necessario</translation>
    </message>
    <message>
        <source>'{name}' contains characters that will require quoting in every future SQL statement. Create it anyway?</source>
        <translation>'{name}' contiene caratteri che richiederanno il quoting in ogni futura istruzione SQL. Crearlo comunque?</translation>
    </message>
    <message>
        <source>Schema exists</source>
        <translation>Schema esistente</translation>
    </message>
    <message>
        <source>Schema '{name}' already exists.</source>
        <translation>Lo schema '{name}' esiste già.</translation>
    </message>
    <message>
        <source>Cannot create schema</source>
        <translation>Impossibile creare lo schema</translation>
    </message>
    <message>
        <source>Schema '{name}' created.</source>
        <translation>Schema '{name}' creato.</translation>
    </message>

    <!-- ============================================================ -->
    <!-- PRE-IMPORT VALIDATION                                          -->
    <!-- ============================================================ -->
    <message>
        <source>Pre-import checks</source>
        <translation>Controlli pre-importazione</translation>
    </message>
    <message>
        <source>Pre-import checks:</source>
        <translation>Controlli pre-importazione:</translation>
    </message>
    <message>
        <source>Proceed with import?</source>
        <translation>Procedere con l'importazione?</translation>
    </message>
    <message>
        <source>Destination {kind} for layer '{layer}' is empty.</source>
        <translation>Il {kind} di destinazione per il layer '{layer}' è vuoto.</translation>
    </message>
    <message>
        <source>These names contain characters that will require quoting in every future SQL statement:</source>
        <translation>Questi nomi contengono caratteri che richiederanno il quoting in ogni futura istruzione SQL:</translation>
    </message>
    <message>
        <source>Layers '{a}' and '{b}' both target {s}.{t}</source>
        <translation>I layer '{a}' e '{b}' puntano entrambi a {s}.{t}</translation>
    </message>
    <message>
        <source>missing in destination: {cols}</source>
        <translation>mancanti nella destinazione: {cols}</translation>
    </message>
    <message>
        <source>missing in source: {cols}</source>
        <translation>mancanti nella sorgente: {cols}</translation>
    </message>
    <message>
        <source>Append mismatch on {s}.{t} ← {layer}: {parts}</source>
        <translation>Incongruenza in modalità append su {s}.{t} ← {layer}: {parts}</translation>
    </message>
    <message>
        <source>Could not validate append schema for {layer}: {err}</source>
        <translation>Impossibile validare lo schema in append per {layer}: {err}</translation>
    </message>
    <message>
        <source>{n} layer(s) will DROP and recreate existing tables (CASCADE).</source>
        <translation>{n} layer eseguiranno DROP e ricreazione delle tabelle esistenti (CASCADE).</translation>
    </message>

    <!-- ============================================================ -->
    <!-- RETRY FAILED                                                    -->
    <!-- ============================================================ -->
    <message>
        <source>Retry failed (0)</source>
        <translation>Riprova falliti (0)</translation>
    </message>
    <message>
        <source>Retry failed ({n})</source>
        <translation>Riprova falliti ({n})</translation>
    </message>
    <message>
        <source>Re-run the import for the layers that failed in the last run (e.g. when the database was momentarily in recovery mode).</source>
        <translation>Riesegui l'importazione per i layer che sono falliti nell'ultima esecuzione (ad es. quando il database era momentaneamente in modalità recovery).</translation>
    </message>
    <message>
        <source>
Failed layers ({n}):
</source>
        <translation>
Layer falliti ({n}):
</translation>
    </message>
    <message>
        <source>
Click 'Retry failed ({n})' below to re-run just these layers.</source>
        <translation>
Clicca 'Riprova falliti ({n})' qui sotto per rieseguire solo questi layer.</translation>
    </message>

    <!-- ============================================================ -->
    <!-- ADVANCED OPTIONS / HEALTH CHECK                                -->
    <!-- ============================================================ -->
    <message>
        <source>Advanced options (for fragile PostgreSQL servers)</source>
        <translation>Opzioni avanzate (per server PostgreSQL fragili)</translation>
    </message>
    <message>
        <source>Use COPY (fast bulk-load)</source>
        <translation>Usa COPY (caricamento rapido in blocco)</translation>
    </message>
    <message>
        <source>Uncheck if the server crashes during large imports. Falls back to INSERT statements: much slower (5-10×), but lighter on the server's memory and more compatible with old PostgreSQL versions.</source>
        <translation>Deseleziona se il server va in crash durante import grandi. Ripiega su istruzioni INSERT: molto più lento (5-10×), ma più leggero per la memoria del server e più compatibile con vecchie versioni di PostgreSQL.</translation>
    </message>
    <message>
        <source>Create spatial index after load</source>
        <translation>Crea indice spaziale dopo il caricamento</translation>
    </message>
    <message>
        <source>Uncheck if the server crashes right at the end of an import. Building a GiST index on millions of features can double the memory the server needs.</source>
        <translation>Deseleziona se il server va in crash proprio alla fine di un'importazione. Costruire un indice GiST su milioni di feature può raddoppiare la memoria richiesta dal server.</translation>
    </message>
    <message>
        <source>Force 2D geometry (drop Z/M components)</source>
        <translation>Forza geometria 2D (rimuovi componenti Z/M)</translation>
    </message>
    <message>
        <source>Strips Z and M values from 3D/Measured geometries. Useful when the server has bugs with COPY on 3D/Measured types, or when you don't need the third dimension.</source>
        <translation>Rimuove i valori Z e M dalle geometrie 3D/Measured. Utile quando il server ha bug con COPY su tipi 3D/Measured, o quando non serve la terza dimensione.</translation>
    </message>
    <message>
        <source>Pause between layers:</source>
        <translation>Pausa tra layer:</translation>
    </message>
    <message>
        <source>Wait this many milliseconds between layers. Gives the server time to flush WAL, autovacuum, and free memory between burst loads.</source>
        <translation>Attendi questi millisecondi tra un layer e l'altro. Dà al server il tempo di scrivere il WAL, eseguire autovacuum e liberare memoria tra caricamenti consecutivi.</translation>
    </message>
    <message>
        <source>Health check</source>
        <translation>Verifica stato server</translation>
    </message>
    <message>
        <source>Health check:</source>
        <translation>Verifica stato server:</translation>
    </message>
    <message>
        <source>Cannot reach the database: {err}</source>
        <translation>Impossibile raggiungere il database: {err}</translation>
    </message>
    <message>
        <source>Server reports pg_is_in_recovery()=true. The database is still completing recovery from a previous crash or is a read-only replica. Writes will fail.</source>
        <translation>Il server riporta pg_is_in_recovery()=true. Il database sta ancora completando il recovery da un crash precedente oppure è una replica di sola lettura. Le scritture falliranno.</translation>
    </message>
    <message>
        <source>Some selected layers have 3D / Measured geometry types. If the server crashes during import, retry with 'Use COPY' disabled or with 'Force 2D' enabled in Advanced options.</source>
        <translation>Alcuni layer selezionati hanno tipi di geometria 3D / Measured. Se il server va in crash durante l'importazione, riprova disattivando 'Usa COPY' oppure attivando 'Forza 2D' nelle opzioni avanzate.</translation>
    </message>
    <message>
        <source>Proceed anyway?</source>
        <translation>Procedere comunque?</translation>
    </message>
</context>
</TS>
