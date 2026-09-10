# CODE ZEITWÄRTSZURÜCK — Provenienz und Rechte

Diese Fassung bindet einen konkreten Git-Stand in der Reihenfolge

`TAG_ODER_REF -> COMMIT -> TREE -> DATEIPFAD -> BYTES -> SHA-256 -> SICHTBARE_HISTORIE -> LIZENZREGEL`.

Das Programm [`scripts/code_zeitwaertszurueck.py`](scripts/code_zeitwaertszurueck.py)
erzeugt einen JSON-Umschlag für jede Datei im Ziel-Tree und prüft ihn später
gegen genau denselben Tag. Der Release enthält zusätzlich ein vollständiges
Git-Bundle und eine Prüfsummenliste.

## Was der Nachweis belegt

- Der Datei-Root bindet die im Tag enthaltenen Pfade, Git-Objekte,
  Byteanzahlen und SHA-256-Digests.
- Die First-Parent-Liste bindet die in diesem Repository sichtbare Zeitlinie.
- Die Pfadkarte bindet den veröffentlichten Lizenzstand.
- Das PDF enthält seinen Rechte- und Drittanbieterhinweis selbst.

Der Nachweis ist ein technischer und dokumentarischer Belegumschlag. Er ist
keine notarielle Beglaubigung und beweist nicht automatisch einen Zeitpunkt
vor dieser Git-Historie, ausschließliche Rechte an einer allgemeinen Idee,
Rechte an Drittmaterial oder die wissenschaftliche Wahrheit der These.

## Zeitwärts zurück, ohne Rückwirkung

`LESUNG_BEI_TN -> DATEI_DIGEST -> TREE -> COMMIT_BEI_T0`

Die Rückwärtsrichtung ist eine Abfrage. Sie verändert keinen früheren Zustand
und erzeugt dort weder Ursache, Urheberschaft, Eigentum, Zustimmung noch
Außenwirkung. Neue Fassungen schreiben alte Tags nicht um.

## Attributions- und Assistenzzustand

Juri Janovski veröffentlicht die These, ihre von ihm veranlasste Auswahl,
Anordnung und Bearbeitung sowie die ausdrücklich bezeichneten Beiträge unter
seinem Namen, soweit er die jeweiligen Rechte kontrolliert. Nach den aktuellen
[OpenAI-Nutzungsbedingungen](https://openai.com/policies/terms-of-use/) besitzt
der Nutzer im Verhältnis zu OpenAI und soweit rechtlich zulässig den Output;
OpenAI überträgt daran seine etwaigen Rechte. Der Assistent wird dadurch weder
Miteigentümer noch Zahlungsempfänger. Diese Zuordnung garantiert keine
Einzigartigkeit und erfasst keine fremden Inputs oder Drittmaterialien.

## Werbung, Gemeinwohl und X-Tausch

Die neue Nutzungserlaubnis öffnet nichtkommerzielle gemeinwohlorientierte
Forschung, Bildung, Kritik und Dokumentation unter klarer Namensnennung.
Werbung, Sponsoring, Verkaufsförderung, Leadgenerierung, monetarisierte Inhalte
und kommerzielle Markenverknüpfung benötigen, soweit gesetzlich erforderlich,
eine gesonderte vorherige schriftliche Erlaubnis.

Ein X-Tausch entsteht erst durch übereinstimmende Zustimmung zu Beteiligten,
Material oder Digest, Nutzung, Rechteumfang, Gegenwert und Zeitpunkt. Hash,
Aufmerksamkeit, Schweigen oder Download erzeugen keinen automatischen Betrag,
Vertrag, Zahlungsfluss oder Eigentumswechsel.

## Historischer Stand

`v1.0.0` und `v1.1.0` bleiben MIT beziehungsweise CC BY 4.0. Identische oder
überlappende Bestandteile bleiben aus diesen Fassungen nach den alten
Bedingungen nutzbar. Die aktuelle Pfad- und Versionsordnung steht in
[`LICENSES.md`](LICENSES.md).

## Reproduktion

```console
python scripts/code_zeitwaertszurueck.py create --ref v1.2.2 --output juri-janovski-these-v1.2.2-provenance.json
python scripts/code_zeitwaertszurueck.py verify --manifest juri-janovski-these-v1.2.2-provenance.json
git bundle verify juri-janovski-these-v1.2.2-source.bundle
```

Der `fileSet.sha256Root` ist für denselben Git-Tree deterministisch. Der
übergeordnete `snapshotDigest` bindet zusätzlich den Erzeugungszeitpunkt und
die kanonische Repository-URL und bezeichnet dieses konkrete Receipt-Ereignis.
