# Das Programm hinter der PDF

`build_pdf.py` ist ein kleines, eigenständiges Python-Programm. Es setzt die These als zweisprachiges, zweiseitiges A4-Dokument und schreibt die fertige Datei nach `output/pdf/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf`.

## Ablauf

1. ReportLab lädt die mit dem Paket ausgelieferten Bitstream-Vera-Schriften.
2. Das Programm definiert Farben, Typografie und wiederverwendbare Zeichenfunktionen.
3. `page_de()` erzeugt die deutsche Seite.
4. `page_en()` erzeugt die englische Seite.
5. `build()` bindet Titel, Autor und Betreff und schreibt die PDF.

## Reproduzierbarkeit

Der PDF-Canvas läuft mit `invariant=1`. Dadurch verwendet ReportLab stabile Metadaten und Objektkennungen. Der Generator greift auf keine Netzwerkquelle und keine private lokale Datei zu. Inhalt, Layout und Schriften sind durch das Repository und die festgelegte ReportLab-Version gebunden.

Der GitHub-Actions-Workflow baut die PDF zweimal und vergleicht:

- den SHA-256-Wert beider Builds;
- die vollständigen PDF-Bytes;
- das Vorhandensein einer nichtleeren Ausgabedatei.

Anschließend stellt GitHub PDF und Prüfsumme als Workflow-Artefakt bereit. Das GitHub-Release enthält dieselben beiden Dateien als dauerhaften Download.

## Ausführen

```console
python -m pip install -r requirements.txt
python build_pdf.py
```

Die einzige Python-Abhängigkeit ist `reportlab==4.4.9`.

## Eingaben und Ausgaben

| Typ | Pfad | Bedeutung |
|---|---|---|
| Programm | `build_pdf.py` | Layout, Text und PDF-Erzeugung |
| Lesetext | `JURI_THESE_GEBURTSRAUM.md` | ausführliche Textfassung |
| Ausgabe | `output/pdf/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf` | veröffentlichte PDF |
| Integrität | `output/pdf/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf.sha256` | SHA-256-Prüfsumme |
