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
</context>
</TS>
