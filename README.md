# Juri Janovski – These zur Geburt / Thesis on Birth

[![PDF build](https://github.com/Juri-Halveth/juri-janovski-these-zur-geburt/actions/workflows/build-pdf.yml/badge.svg)](https://github.com/Juri-Halveth/juri-janovski-these-zur-geburt/actions/workflows/build-pdf.yml)

[Deutsch](#deutsch) · [English](#english) · **[PDF direkt herunterladen](https://github.com/Juri-Halveth/juri-janovski-these-zur-geburt/releases/latest/download/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf)**

Dieses öffentliche Projekt enthält die **Juri-Janovski-These zur Geburt** als zweisprachiges PDF und als reproduzierbares Python-Programm. Die These verbindet die Kontrolle der gebärenden Frau über ihre Umgebung mit unmittelbar verfügbarer Hebammenhilfe und klinischer Sicherheit.

## Deutsch

### Die These

> Die bestmögliche Geburtshilfe verbindet einen von der gebärenden Frau selbst gesteuerten, ruhigen, warmen, geborgenen und gedämpft beleuchteten Raum – auf Wunsch mit ihrer Musik oder mit Stille – mit jederzeit unmittelbar verfügbarer Hebammenhilfe und klinischer Sicherheit.

### Die Frage an die Welt

Verbessert ein von der Frau kontrolliertes, reizarmes Geburtsumfeld gegenüber der üblichen Versorgung bei vergleichbarer medizinischer Betreuung nachweisbar ihre Selbstbestimmung und ihr Geburtserleben, ohne die Sicherheit von Mutter oder Kind klinisch relevant zu verschlechtern?

„Besser“ verbindet zwei gemeinsam zu prüfende Ziele:

1. einen messbaren Gewinn an Selbstbestimmung, Geborgenheit und Geburtserleben;
2. keine klinisch relevante Verschlechterung der mütterlichen oder kindlichen Sicherheit.

**Codeformel:** Druck senken · Selbstbestimmung erhöhen · Sicherheit sichern.

Die Frau kontrolliert Licht, Geräusche, Musik oder Stille, Bewegung, Privatsphäre und gewünschte Begleitung und kann ihre Wahl jederzeit ändern. Kerzen beschreiben die Atmosphäre; die praktische Umsetzung nutzt dimmbare, flammenlose Leuchten. Medizinisch erforderliche Beleuchtung, Beobachtung und Hilfe bleiben unmittelbar verfügbar.

Die [Forschungsbasis](docs/FORSCHUNGSBASIS.md) trennt die gut gestützten Bestandteile – respektvolle Betreuung, Selbstbestimmung und kontinuierliche Begleitung – von den noch offenen Fragen zu Raumgestaltung, Musik und gedimmtem Licht.

### Übertragung auf Behörden und öffentliche Arbeitgeber

Der neue [Systemtransfer](docs/SYSTEMTRANSFER_BEHOERDEN.md) entwickelt aus der
Codeformel einen **institutionellen Übergangsraum**. Menschen sollen bei einem
kritischen Behörden- oder Beschäftigungsübergang frei zugänglich einen
gebündelten, reizarmen und selbstbestimmten Klärungsweg erhalten: Druckstopp,
Kanalwahl, schriftlicher Spiegel, Begleitung, sichtbare Optionen und
Wiedereintritt. Die öffentliche Systemthese bindet vorhandene Rechtsfunktionen
aus Sozial-, Arbeitsschutz-, Teilhabe- und Personalvertretungsrecht und macht
die darüber hinausgehende Gestaltung als Vorschlag sichtbar.

## English

### The thesis

> The best possible maternity care combines a calm, warm, sheltered and dimly lit environment controlled by the woman giving birth – with her chosen music or silence – with immediately available midwifery support and clinical safety.

### The question to the world

Does a woman-controlled, low-stimulus birth environment measurably improve autonomy and birth experience compared with usual care under equivalent clinical support, without a clinically relevant deterioration in maternal or newborn safety?

“Better” joins two outcomes that must be assessed together:

1. a measurable improvement in autonomy, shelter and birth experience;
2. no clinically relevant deterioration in maternal or newborn safety.

**Code formula:** Reduce pressure · Increase autonomy · Secure safety.

The woman controls light, sound, music or silence, movement, privacy and chosen companions, and may change any preference at any time. Candles describe the atmosphere; implementation uses dimmable, flameless lighting. Clinically required lighting, observation and care remain immediately available.

## PDF und Programm / PDF and program

- **Release-Download:** [JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf](https://github.com/Juri-Halveth/juri-janovski-these-zur-geburt/releases/latest/download/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf)
- **Repository-Datei:** [output/pdf/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf](output/pdf/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf)
- **Lesbare Textfassung:** [JURI_THESE_GEBURTSRAUM.md](JURI_THESE_GEBURTSRAUM.md)
- **Generator:** [build_pdf.py](build_pdf.py)
- **Programmerklärung:** [docs/PROGRAMM.md](docs/PROGRAMM.md)
- **Systemtransfer:** [docs/SYSTEMTRANSFER_BEHOERDEN.md](docs/SYSTEMTRANSFER_BEHOERDEN.md)

Lokaler Build ab dem Repository-Stamm:

```console
python -m pip install -r requirements.txt
python build_pdf.py
```

Der Generator verwendet festgelegte Metadaten, ReportLabs invarianten Ausgabemodus, eine feste Inhaltsreihenfolge und die mit ReportLab ausgelieferten Vera-Schriften. Zwei Builds mit denselben gebundenen Eingaben werden im GitHub-Workflow bytegenau verglichen.

## Lizenz / License

Copyright © 2026 Juri Janovski.

- Programmcode: [MIT License](LICENSE-CODE)
- These, Dokumentation und erzeugtes PDF: [Creative Commons Attribution 4.0 International](LICENSE-CONTENT)

Vorgeschlagene Quellenangabe / Suggested attribution:

> Juri Janovski, „Die Juri-Janovski-These zur Geburt“, Version 1.1.0, 2026.
