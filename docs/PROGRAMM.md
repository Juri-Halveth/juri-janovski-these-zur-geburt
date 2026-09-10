# Das Programm hinter der PDF

`build_pdf.py` ist ein kleines, eigenständiges Python-Programm. Es setzt die These als zweisprachiges, vierseitiges A4-Dokument und schreibt die fertige Datei nach `output/pdf/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf`.

## Ablauf

1. ReportLab lädt die mit dem Paket ausgelieferten Bitstream-Vera-Schriften.
2. Das Programm definiert Farben, Typografie und wiederverwendbare Zeichenfunktionen.
3. `page_de()` erzeugt die deutsche Seite.
4. `page_en()` erzeugt die englische Seite.
5. `page_rights()` erzeugt die zweisprachige Rechte- und Provenienzseite.
6. `page_third_party()` bettet die erforderlichen Drittanbieterhinweise ein.
7. `build()` bindet Titel, Autor und Betreff und schreibt die PDF.

## Reproduzierbarkeit

Der PDF-Canvas läuft mit `invariant=1`. Dadurch verwendet ReportLab stabile
Metadaten und Objektkennungen. Der Generator greift auf keine Netzwerkquelle
und keine private lokale Datei zu. Inhalt, Layout und Schriften sind durch das
Repository gebunden. Der bytegenaue Release-Build bindet zusätzlich Python
3.12, `reportlab==4.4.9`, `PYTHONHASHSEED=0` und `TZ=UTC`.

Der GitHub-Actions-Workflow baut die PDF zweimal und vergleicht:

- den SHA-256-Wert beider Builds;
- die vollständigen PDF-Bytes;
- das Vorhandensein einer nichtleeren Ausgabedatei.
- die Unit-Tests des Provenienzwerkzeugs.

Anschließend stellt GitHub PDF und Prüfsumme als Workflow-Artefakt bereit. Das GitHub-Release enthält dieselben beiden Dateien als dauerhaften Download.

## Ausführen

Für einen bytegleichen Referenz-Build muss `python --version` Python 3.12
ausgeben.

```console
python -m pip install -r requirements.txt
python build_pdf.py
```

Die einzige Python-Abhängigkeit ist `reportlab==4.4.9`.

## CODE ZEITWÄRTSZURÜCK

`scripts/code_zeitwaertszurueck.py` erzeugt zu einem Git-Tag einen kanonischen JSON-Umschlag. Er bindet Tagobjekt und Payload, Commit, Tree, Pfad, Git-Blob, Bytezahl, SHA-256, sichtbare First-Parent-Historie und Lizenzregel. Die Prüfung akzeptiert keine still verschobenen Tags, geänderten Bytes, Pfade oder Digests.

```console
python scripts/code_zeitwaertszurueck.py create --ref v1.2.0 --output juri-janovski-these-v1.2.0-provenance.json
python scripts/code_zeitwaertszurueck.py verify --manifest juri-janovski-these-v1.2.0-provenance.json
```

Der Umschlag belegt den gebundenen Repository-Stand. Seine Beweisgrenze steht in [PROVENANCE_AND_RIGHTS.md](../PROVENANCE_AND_RIGHTS.md).

## Eingaben und Ausgaben

| Typ | Pfad | Bedeutung |
|---|---|---|
| Programm | `build_pdf.py` | Layout, Text und PDF-Erzeugung |
| Lesetext | `JURI_THESE_GEBURTSRAUM.md` | ausführliche Textfassung |
| Ausgabe | `output/pdf/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf` | veröffentlichte PDF |
| Integrität | `output/pdf/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf.sha256` | SHA-256-Prüfsumme |
| Provenienzprogramm | `scripts/code_zeitwaertszurueck.py` | erstellt und prüft den Release-Umschlag |
| Provenienztest | `tests/test_code_zeitwaertszurueck.py` | prüft Tag-, Byte-, Digest-, Pfad- und Lizenzbindung |
