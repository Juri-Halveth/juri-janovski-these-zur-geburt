from pathlib import Path

import reportlab
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output" / "pdf" / "JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf"
VERSION = "1.2.2"
CONTACT_EMAIL = "juri@halveth.de"

PAGE_W, PAGE_H = A4
MARGIN = 16 * mm

CREAM = HexColor("#FBF6EA")
NAVY = HexColor("#17243A")
INK = HexColor("#243246")
RUST = HexColor("#B55335")
TEAL = HexColor("#277A70")
GOLD = HexColor("#D4A52D")
PALE_GOLD = HexColor("#F3E7C4")
PALE_TEAL = HexColor("#E5F1ED")
WHITE = HexColor("#FFFFFF")
MUTED = HexColor("#657184")


def register_fonts():
    reportlab_fonts = Path(reportlab.__file__).resolve().parent / "fonts"
    choices = [
        ("Vera", reportlab_fonts / "Vera.ttf"),
        ("Vera-Bold", reportlab_fonts / "VeraBd.ttf"),
    ]
    for name, path in choices:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont(name, str(path)))


register_fonts()
SANS = "Vera" if "Vera" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
SANS_BOLD = "Vera-Bold" if "Vera-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
SERIF = "Times-Roman"
SERIF_BOLD = "Times-Bold"


def style(name, font=SANS, size=9.2, leading=12, color=INK, align=TA_LEFT, space_after=0):
    return ParagraphStyle(
        name=name,
        fontName=font,
        fontSize=size,
        leading=leading,
        textColor=color,
        alignment=align,
        spaceAfter=space_after,
        allowWidows=0,
        allowOrphans=0,
    )


BODY = style("body")
SMALL = style("small", size=7.4, leading=9.4, color=MUTED)
SECTION = style("section", font=SANS_BOLD, size=10.3, leading=12.5, color=NAVY)
THESIS = style("thesis", font=SERIF_BOLD, size=12.2, leading=16.5, color=NAVY, align=TA_CENTER)
CALL = style("call", font=SERIF, size=9.4, leading=13, color=NAVY)
LEGAL_BODY = style("legal_body", size=8.0, leading=10.6, color=INK)
LEGAL_SMALL = style("legal_small", size=5.65, leading=7.2, color=INK)
LEGAL_HEAD = style("legal_head", font=SANS_BOLD, size=9.3, leading=11.2, color=NAVY)


def draw_para(c, text, x, y_top, width, pstyle=BODY):
    p = Paragraph(text, pstyle)
    _, h = p.wrap(width, PAGE_H)
    p.drawOn(c, x, y_top - h)
    return y_top - h


def rounded_panel(c, x, y, w, h, fill, stroke=None, radius=10):
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1 if stroke else 0)


def header(c, lang):
    c.setFillColor(CREAM)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 51 * mm, PAGE_W, 51 * mm, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1, alpha=0.07))
    c.circle(PAGE_W - 8 * mm, PAGE_H - 15 * mm, 39 * mm, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1, alpha=0.08))
    c.circle(PAGE_W - 30 * mm, PAGE_H - 48 * mm, 20 * mm, fill=1, stroke=0)

    c.setFillColor(GOLD)
    c.setFont(SANS_BOLD, 8.4)
    label = "ÖFFENTLICHE FORSCHUNGSFRAGE" if lang == "de" else "A PUBLIC RESEARCH QUESTION"
    c.drawString(MARGIN, PAGE_H - 15 * mm, label)

    title = "DIE JURI-JANOVSKI-THESE\nZUR GEBURT" if lang == "de" else "THE JURI JANOVSKI THESIS\nON BIRTH"
    title_size = 25 if lang == "de" else 22.5
    title_leading = 28 if lang == "de" else 26
    title_style = style("title", font=SERIF_BOLD, size=title_size, leading=title_leading, color=WHITE)
    draw_para(c, title.replace("\n", "<br/>"), MARGIN, PAGE_H - 20 * mm, 170 * mm, title_style)

    c.setFillColor(WHITE)
    c.setFont(SANS, 8.4)
    sub = "Juri Janovski · 10. September 2026" if lang == "de" else "Juri Janovski · 10 September 2026"
    c.drawString(MARGIN, PAGE_H - 46 * mm, sub)


def footer(c, page_no, lang):
    c.setStrokeColor(HexColor("#D8D0C0"))
    c.line(MARGIN, 13 * mm, PAGE_W - MARGIN, 13 * mm)
    c.setFillColor(MUTED)
    c.setFont(SANS, 6.9)
    note = (
        "These zur Prüfung - keine starre Geburtsvorgabe. Die Frau entscheidet; medizinische Hilfe bleibt jederzeit verfügbar."
        if lang == "de"
        else "A thesis for testing, not a rigid birth rule. The woman decides; clinical help remains immediately available."
    )
    c.drawString(MARGIN, 9 * mm, note)
    c.drawCentredString(PAGE_W / 2, 5.7 * mm, f"Kontakt / Contact: {CONTACT_EMAIL}")
    c.drawRightString(PAGE_W - MARGIN, 9 * mm, str(page_no))


def legal_header(c, kicker, title, subtitle, page_no):
    c.setFillColor(CREAM)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 38 * mm, PAGE_W, 38 * mm, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1, alpha=0.07))
    c.circle(PAGE_W - 10 * mm, PAGE_H - 13 * mm, 28 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.setFont(SANS_BOLD, 8.1)
    c.drawString(MARGIN, PAGE_H - 12 * mm, kicker)
    draw_para(
        c,
        title,
        MARGIN,
        PAGE_H - 16 * mm,
        PAGE_W - 2 * MARGIN,
        style(f"legal_title_{page_no}", font=SERIF_BOLD, size=20, leading=23, color=WHITE),
    )
    c.setFillColor(WHITE)
    c.setFont(SANS, 7.5)
    c.drawString(MARGIN, PAGE_H - 34 * mm, subtitle)
    c.setStrokeColor(HexColor("#D8D0C0"))
    c.line(MARGIN, 13 * mm, PAGE_W - MARGIN, 13 * mm)
    c.setFillColor(MUTED)
    c.setFont(SANS, 6.6)
    c.drawString(MARGIN, 8.5 * mm, f"Juri Janovski · Version {VERSION} · {CONTACT_EMAIL} · 10 September 2026")
    c.drawRightString(PAGE_W - MARGIN, 8.5 * mm, str(page_no))


def page_de(c):
    header(c, "de")
    thesis = (
        "Die bestmögliche Geburtshilfe verbindet einen von der Frau selbst gesteuerten, ruhigen, warmen und gedämpft beleuchteten Raum - auf Wunsch mit Musik oder Stille - mit jederzeit verfügbarer Hebammenhilfe und klinischer Sicherheit."
    )
    rounded_panel(c, MARGIN, PAGE_H - 89 * mm, PAGE_W - 2 * MARGIN, 31 * mm, PALE_GOLD, HexColor("#E0C87B"), 12)
    draw_para(c, thesis, MARGIN + 9 * mm, PAGE_H - 64 * mm, PAGE_W - 2 * MARGIN - 18 * mm, THESIS)
    c.setFillColor(RUST)
    c.setFont(SANS_BOLD, 7.8)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 95 * mm, "CODE: DRUCK SENKEN | SELBSTBESTIMMUNG ERHÖHEN | SICHERHEIT SICHERN")

    y = PAGE_H - 99 * mm
    draw_para(c, "DIE FRAGE AN DIE WELT", MARGIN, y, PAGE_W - 2 * MARGIN, SECTION)
    y -= 5 * mm
    question = (
        "Verbessert ein von der Frau kontrolliertes, reizarmes Geburtsumfeld gegenüber der üblichen Versorgung bei vergleichbarer medizinischer Betreuung nachweisbar ihre <b>Selbstbestimmung und ihr Geburtserleben</b>, ohne die Sicherheit von Mutter oder Kind klinisch relevant zu verschlechtern?"
    )
    y = draw_para(c, question, MARGIN, y, PAGE_W - 2 * MARGIN, style("question", font=SERIF, size=11.4, leading=15, color=RUST))

    y -= 7 * mm
    gap = 7 * mm
    col_w = (PAGE_W - 2 * MARGIN - gap) / 2

    left_top = y
    draw_para(c, "WAS „BESSER“ BEDEUTET", MARGIN, left_top, col_w, SECTION)
    left_y = left_top - 5 * mm
    left = (
        "<b>1 · Erfahrung:</b> mehr Kontrolle, Geborgenheit und ein besseres Geburtserleben.<br/><br/>"
        "<b>2 · Sicherheit:</b> keine klinisch relevante Verschlechterung für Frau oder Kind.<br/><br/>"
        "Gemessen werden unter anderem Angst, Stress, Schmerz, Medikamentenbedarf, Wehenförderung, Geburtsdauer, Eingriffe, Blutverlust und der Zustand des Kindes. Nach 6 Wochen und 3 Monaten folgen validierte Messungen geburtsbezogener Belastung und depressiver Symptome. Medizinisch notwendige Hilfe ist kein Misserfolg."
    )
    left_y = draw_para(c, left, MARGIN, left_y, col_w, BODY)

    rx = MARGIN + col_w + gap
    draw_para(c, "DIE FRAU STEUERT DEN RAUM", rx, left_top, col_w, SECTION)
    right_y = left_top - 5 * mm
    right = (
        "Licht, Geräusche, Musik oder Stille, Bewegung, Privatsphäre und gewünschte Begleitung bleiben veränderbare Entscheidungen der Frau.<br/><br/>"
        "„Kerzen“ stehen für Atmosphäre: Kliniken nutzen dimmbare, <b>flammenlose</b> Leuchten. Untersuchungs- und Notfalllicht ist sofort verfügbar. Wärme, Monitoring und medizinische Hilfe bleiben gesichert."
    )
    right_y = draw_para(c, right, rx, right_y, col_w, BODY)

    y = min(left_y, right_y) - 8 * mm
    rounded_panel(c, MARGIN, y - 42 * mm, PAGE_W - 2 * MARGIN, 42 * mm, PALE_TEAL, HexColor("#A4CEC5"), 10)
    draw_para(c, "AUFRUF IM NAMEN VON JURI", MARGIN + 7 * mm, y - 6 * mm, PAGE_W - 2 * MARGIN - 14 * mm, style("callhead", font=SANS_BOLD, size=9.5, leading=11, color=TEAL))
    call = (
        "Ich, Juri Janovski, fordere Geburtskliniken, Geburtshäuser, Hebammen, Ärztinnen und Ärzte, Forschungseinrichtungen und internationale Gesundheitsorganisationen auf, diese Frage <b>gemeinsam mit gebärenden Frauen</b> in transparenten, vorab registrierten und ausreichend großen Studien zu beantworten.<br/><br/>"
        "Geburtsräume dürfen nicht allein nach technischer Zweckmäßigkeit gestaltet werden. Selbstbestimmung, Geborgenheit und klinische Sicherheit gehören gemeinsam untersucht und verwirklicht."
    )
    draw_para(c, call, MARGIN + 7 * mm, y - 13 * mm, PAGE_W - 2 * MARGIN - 14 * mm, CALL)

    source_y = y - 48 * mm
    draw_para(c, "WAS DIE FORSCHUNG HEUTE TRÄGT", MARGIN, source_y, PAGE_W - 2 * MARGIN, SECTION)
    evidence = (
        "WHO: frauenzentrierte, respektvolle und psychologisch wie klinisch sichere Betreuung.  ·  "
        "NICE: Musik nach Wahl der Frau unterstützen.  ·  "
        "Musik-Reviews: vielversprechend bei Schmerz und Angst, Langzeitwirkung offen.  ·  "
        "Raumdesign: positive Signale, klinische Ergebnisse bisher uneinheitlich.  ·  "
        "Gedimmtes Licht: eine registrierte Studie prüfte 50-80 Lux; Ergebnisse sind noch nicht veröffentlicht."
    )
    draw_para(c, evidence, MARGIN, source_y - 5 * mm, PAGE_W - 2 * MARGIN, style("evidence", size=7.8, leading=10, color=INK))

    refs = (
        "Quellen: WHO Intrapartum Care (2018); NICE NG235 §1.6.9; Hunter et al. (2023), 28 RCTs / n=2.835; "
        "Nilsson et al. (2020), Birthing Room Design; Lorentzen et al. (2021), RCT; ClinicalTrials.gov NCT07310602; WHO Newborn Thermal Protection."
    )
    draw_para(c, refs, MARGIN, source_y - 20 * mm, PAGE_W - 2 * MARGIN, SMALL)
    footer(c, 1, "de")
    c.showPage()


def page_en(c):
    header(c, "en")
    thesis = (
        "The best possible maternity care combines a calm, warm, sheltered and dimly lit environment controlled by the woman giving birth - with her chosen music or silence - with immediately available midwifery support and clinical safety."
    )
    rounded_panel(c, MARGIN, PAGE_H - 88 * mm, PAGE_W - 2 * MARGIN, 30 * mm, PALE_GOLD, HexColor("#E0C87B"), 12)
    draw_para(c, thesis, MARGIN + 9 * mm, PAGE_H - 64 * mm, PAGE_W - 2 * MARGIN - 18 * mm, THESIS)
    c.setFillColor(RUST)
    c.setFont(SANS_BOLD, 7.8)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 95 * mm, "CODE: LOWER PRESSURE | INCREASE AUTONOMY | PRESERVE SAFETY")

    y = PAGE_H - 99 * mm
    draw_para(c, "THE QUESTION TO THE WORLD", MARGIN, y, PAGE_W - 2 * MARGIN, SECTION)
    y -= 5 * mm
    question = (
        "Does a woman-controlled, low-stimulus birth environment measurably improve <b>autonomy and birth experience</b> compared with usual care under equivalent clinical support, without a clinically relevant deterioration in maternal or newborn safety?"
    )
    y = draw_para(c, question, MARGIN, y, PAGE_W - 2 * MARGIN, style("question_en", font=SERIF, size=11.4, leading=15, color=RUST))

    y -= 7 * mm
    gap = 7 * mm
    col_w = (PAGE_W - 2 * MARGIN - gap) / 2
    left_top = y
    draw_para(c, "WHAT “BETTER” MUST MEAN", MARGIN, left_top, col_w, SECTION)
    left_y = left_top - 5 * mm
    left = (
        "<b>1 · Experience:</b> greater perceived control, shelter and a better birth experience.<br/><br/>"
        "<b>2 · Safety:</b> no clinically relevant deterioration for mother or newborn.<br/><br/>"
        "Measure anxiety, stress, pain, medication, augmentation, labour duration, interventions, blood loss, injuries, infection, newborn condition, monitoring interruptions and time to necessary intervention. At 6 weeks and 3 months, use validated measures of birth-related distress and depressive symptoms. Necessary clinical care is not a study failure."
    )
    left_y = draw_para(c, left, MARGIN, left_y, col_w, BODY)

    rx = MARGIN + col_w + gap
    draw_para(c, "THE WOMAN CONTROLS THE ROOM", rx, left_top, col_w, SECTION)
    right_y = left_top - 5 * mm
    right = (
        "Light, sound, music or silence, movement, privacy and chosen companions remain changeable decisions of the woman.<br/><br/>"
        "Candles describe the atmosphere: clinical implementation uses dimmable <b>flameless</b> lighting. Examination and emergency lighting remain instantly available. Warmth, monitoring and immediate clinical help are preserved."
    )
    right_y = draw_para(c, right, rx, right_y, col_w, BODY)

    y = min(left_y, right_y) - 8 * mm
    rounded_panel(c, MARGIN, y - 42 * mm, PAGE_W - 2 * MARGIN, 42 * mm, PALE_TEAL, HexColor("#A4CEC5"), 10)
    draw_para(c, "A PUBLIC CALL IN JURI'S NAME", MARGIN + 7 * mm, y - 6 * mm, PAGE_W - 2 * MARGIN - 14 * mm, style("callhead_en", font=SANS_BOLD, size=9.5, leading=11, color=TEAL))
    call = (
        "I, Juri Janovski, call on maternity units, birth centres, midwives, physicians, researchers and international health organisations to answer this question <b>together with women giving birth</b> through transparent, preregistered and adequately powered studies.<br/><br/>"
        "Birth rooms should not be designed only around technical convenience. Autonomy, shelter and clinical safety must be studied and realised together."
    )
    draw_para(c, call, MARGIN + 7 * mm, y - 13 * mm, PAGE_W - 2 * MARGIN - 14 * mm, CALL)

    source_y = y - 48 * mm
    draw_para(c, "WHAT CURRENT EVIDENCE SUPPORTS", MARGIN, source_y, PAGE_W - 2 * MARGIN, SECTION)
    evidence = (
        "WHO: woman-centred, respectful, psychologically and clinically safe care.  ·  "
        "NICE: support music chosen by the woman.  ·  "
        "Music reviews: promising for pain and anxiety; long-term effects remain unclear.  ·  "
        "Room design: positive signals with inconsistent clinical outcomes.  ·  "
        "Dim light: a registered trial tested 50-80 lux; results have not yet been published."
    )
    draw_para(c, evidence, MARGIN, source_y - 5 * mm, PAGE_W - 2 * MARGIN, style("evidence_en", size=7.8, leading=10, color=INK))

    refs = (
        "Sources: WHO Intrapartum Care (2018); NICE NG235 §1.6.9; Hunter et al. (2023), 28 RCTs / n=2,835; "
        "Nilsson et al. (2020), Birthing Room Design; Lorentzen et al. (2021), RCT; ClinicalTrials.gov NCT07310602; WHO Newborn Thermal Protection."
    )
    draw_para(c, refs, MARGIN, source_y - 20 * mm, PAGE_W - 2 * MARGIN, SMALL)
    footer(c, 2, "en")
    c.showPage()


def page_rights(c):
    legal_header(
        c,
        "RECHTE · PROVENIENZ · RIGHTS",
        "CODE ZEITWÄRTSZURÜCK",
        "Ein bytegenauer Release-Nachweis mit sichtbarer Anspruchsgrenze / A byte-exact release record with a visible claim boundary",
        3,
    )

    y = PAGE_H - 48 * mm
    gap = 8 * mm
    col_w = (PAGE_W - 2 * MARGIN - gap) / 2
    rx = MARGIN + col_w + gap

    draw_para(c, "DEUTSCH", MARGIN, y, col_w, LEGAL_HEAD)
    left_y = y - 6 * mm
    left = (
        "<b>Juri Janovskis Rechteposition.</b> Diese Fassung bezeichnet Juri Janovski als Herausgeber und Urheber der von ihm kontrollierten originären Beiträge, Auswahl und Anordnung. Tatsachen, allgemeine Ideen, Methoden, Gesetzestexte, Namen, Marken, Zitate, Links und fremde Werke werden dadurch nicht angeeignet.<br/><br/>"
        "<b>Lizenzgrenze.</b> Programmcode bleibt gemäß Pfadkarte überwiegend MIT-lizenziert. Die Tags v1.0.0 und v1.1.0 bleiben für These, Dokumentation und PDF unter CC BY 4.0 nutzbar. Unterscheidbare neue Beiträge ab v1.2.0 stehen unter der Juri Public-Interest Research Permission 1.0. Identische oder überlappende ältere Teile behalten die weitergehende alte Freigabe.<br/><br/>"
        "<b>Gemeinwohl und Werbung.</b> Nichtkommerzielle Forschung, Bildung, Kritik und Dokumentation sind nach der neuen Erlaubnis mit Namensnennung, Versionsangabe, Änderungskennzeichnung und ohne Scheinendorsement erlaubt. Werbung, Sponsoring, Leadgenerierung, bezahlte Reichweite, monetarisierte Inhalte und kommerzielle Markenverknüpfung benötigen, soweit rechtlich erforderlich, eine gesonderte vorherige schriftliche Erlaubnis.<br/><br/>"
        "<b>X-Tausch.</b> Ein Tausch, eine Beteiligung oder Vergütung entsteht erst durch übereinstimmende Zustimmung zu Beteiligten, Material oder Digest, Nutzung, Rechteumfang, Gegenwert und Zeitpunkt. Hash, Aufmerksamkeit, Schweigen oder Download erzeugen keinen automatischen Vertrag oder Betrag."
    )
    left_y = draw_para(c, left, MARGIN, left_y, col_w, LEGAL_BODY)

    draw_para(c, "ENGLISH", rx, y, col_w, LEGAL_HEAD)
    right_y = y - 6 * mm
    right = (
        "<b>Juri Janovski's rights position.</b> This version identifies Juri Janovski as publisher and author of the original contributions, selection and arrangement that he controls. Facts, general ideas, methods, laws, names, marks, quotations, links and third-party works are not appropriated by that statement.<br/><br/>"
        "<b>Licence boundary.</b> Program code remains predominantly MIT-licensed according to the path map. Tags v1.0.0 and v1.1.0 remain available under CC BY 4.0 for the thesis, documentation and PDF. Distinguishable new contributions from v1.2.0 are offered under Juri Public-Interest Research Permission 1.0. Identical or overlapping earlier material retains the broader earlier grant.<br/><br/>"
        "<b>Public interest and advertising.</b> The new permission allows non-commercial research, education, criticism and documentation with attribution, version and change notices, and no implied endorsement. Advertising, sponsorship, lead generation, paid reach, monetised content and commercial brand association require separate prior written permission where the law requires it.<br/><br/>"
        "<b>X exchange.</b> An exchange, participation or payment arises only from matching assent on parties, material or digest, use, rights, consideration and time. A hash, attention, silence or download creates no automatic contract or amount."
    )
    right_y = draw_para(c, right, rx, right_y, col_w, LEGAL_BODY)

    panel_top = min(left_y, right_y) - 8 * mm
    panel_h = 43 * mm
    rounded_panel(c, MARGIN, panel_top - panel_h, PAGE_W - 2 * MARGIN, panel_h, PALE_TEAL, HexColor("#A4CEC5"), 10)
    draw_para(c, "WAS DER SNAPSHOT BELEGT / WHAT THE SNAPSHOT PROVES", MARGIN + 7 * mm, panel_top - 6 * mm, PAGE_W - 2 * MARGIN - 14 * mm, style("snapshot_head", font=SANS_BOLD, size=9.2, leading=11, color=TEAL))
    snapshot = (
        "<b>TAG_OR_REF -&gt; COMMIT -&gt; TREE -&gt; PATH -&gt; BYTES -&gt; SHA-256 -&gt; VISIBLE HISTORY -&gt; LICENCE RULE.</b><br/>"
        "Der Release-Umschlag bindet die aufgelisteten Git-Objekte, Dateien, Byteanzahlen, Digests und die im Repository sichtbare First-Parent-Historie. Er ermöglicht eine spätere bytegenaue Gleichheits- oder Abweichungsprüfung. / The release envelope binds the listed Git objects, files, byte counts, digests and first-parent history visible in this repository, enabling later byte-exact equality or divergence checks.<br/><br/>"
        "<b>Anspruchsgrenze / claim ceiling:</b> Der Nachweis ist keine notarielle Beglaubigung. Er beweist keinen Zeitpunkt vor der gebundenen Historie, keine ausschließlichen Rechte an einer allgemeinen Idee, keine wissenschaftliche Wahrheit, keine Kenntnis durch Dritte und keine äußere Kausalität."
    )
    draw_para(c, snapshot, MARGIN + 7 * mm, panel_top - 13 * mm, PAGE_W - 2 * MARGIN - 14 * mm, style("snapshot_body", size=7.35, leading=9.4, color=INK))

    note_y = panel_top - panel_h - 7 * mm
    draw_para(c, "ASSISTENZ / ASSISTANCE", MARGIN, note_y, PAGE_W - 2 * MARGIN, LEGAL_HEAD)
    assistance = (
        "OpenAI-Werkzeuge unterstützten Redaktion, Code und Prüfung. Nach den zum Releasezeitpunkt verlinkten OpenAI-Nutzungsbedingungen werden etwaige OpenAI-Rechte am Output im Verhältnis Nutzer–OpenAI und soweit rechtlich zulässig dem Nutzer zugeordnet; Outputs können nicht einzigartig sein. Daraus entstehen weder Miteigentum des Assistenten noch automatische Vergütung, Rechte an fremden Inputs oder ein Nachweis menschlicher Alleinurheberschaft. Details: PROVENANCE_AND_RIGHTS.md · LICENSES.md · https://openai.com/policies/terms-of-use/"
    )
    draw_para(c, assistance, MARGIN, note_y - 5 * mm, PAGE_W - 2 * MARGIN, style("assistance", size=7.15, leading=9.2, color=MUTED))
    c.showPage()


def page_third_party(c):
    legal_header(
        c,
        "DRITTANBIETER · THIRD-PARTY NOTICES",
        "SCHRIFTEN UND PDF-WERKZEUG",
        "Beigefügte Lizenzhinweise für eingebettete Bitstream-Vera-Schriften und ReportLab 4.4.9",
        4,
    )
    y = PAGE_H - 47 * mm
    gap = 7 * mm
    col_w = (PAGE_W - 2 * MARGIN - gap) / 2
    rx = MARGIN + col_w + gap

    draw_para(c, "BITSTREAM VERA FONTS", MARGIN, y, col_w, LEGAL_HEAD)
    vera = (
        "Copyright (c) 2003 by Bitstream, Inc. All Rights Reserved. Bitstream Vera is a trademark of Bitstream, Inc.<br/><br/>"
        "Permission is hereby granted, free of charge, to any person obtaining a copy of the fonts accompanying this license (\"Fonts\") and associated documentation files (the \"Font Software\"), to reproduce and distribute the Font Software, including without limitation the rights to use, copy, merge, publish, distribute, and/or sell copies of the Font Software, and to permit persons to whom the Font Software is furnished to do so, subject to the following conditions:<br/><br/>"
        "The above copyright and trademark notices and this permission notice shall be included in all copies of one or more of the Font Software typefaces.<br/><br/>"
        "The Font Software may be modified, altered, or added to, and in particular the designs of glyphs or characters in the Fonts may be modified and additional glyphs or characters may be added to the Fonts, only if the fonts are renamed to names not containing either the words \"Bitstream\" or the word \"Vera\".<br/><br/>"
        "This License becomes null and void to the extent applicable to Fonts or Font Software that has been modified and is distributed under the \"Bitstream Vera\" names.<br/><br/>"
        "The Font Software may be sold as part of a larger software package but no copy of one or more of the Font Software typefaces may be sold by itself.<br/><br/>"
        "THE FONT SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL BITSTREAM OR THE GNOME FOUNDATION BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM OTHER DEALINGS IN THE FONT SOFTWARE.<br/><br/>"
        "Except as contained in this notice, the names of Gnome, the Gnome Foundation, and Bitstream Inc., shall not be used in advertising or otherwise to promote the sale, use or other dealings in this Font Software without prior written authorization from the Gnome Foundation or Bitstream Inc., respectively. For further information, contact: fonts at gnome dot org."
    )
    draw_para(c, vera, MARGIN, y - 6 * mm, col_w, LEGAL_SMALL)

    draw_para(c, "REPORTLAB", rx, y, col_w, LEGAL_HEAD)
    reportlab_notice = (
        "Copyright (c) 2000-2024, ReportLab Inc. All rights reserved.<br/><br/>"
        "Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:<br/><br/>"
        "1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.<br/><br/>"
        "2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.<br/><br/>"
        "3. Neither the name of the company nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.<br/><br/>"
        "THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE OFFICERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
    )
    right_y = draw_para(c, reportlab_notice, rx, y - 6 * mm, col_w, LEGAL_SMALL)
    right_y -= 7 * mm
    draw_para(c, "ABGRENZUNG / BOUNDARY", rx, right_y, col_w, LEGAL_HEAD)
    boundary = (
        "Die eingebetteten Schriften, ReportLab, zitierte Studien, Institutionstexte, Tatsachen, Namen, Marken, Links und fremde Werke werden nicht als Eigentum von Juri Janovski beansprucht. / Embedded fonts, ReportLab, cited studies, institutional texts, facts, names, marks, links and third-party works are not claimed as Juri Janovski's property.<br/><br/>"
        "Vollständige Quellen- und Pfadzuordnung: THIRD_PARTY_NOTICES.md und LICENSES.md im Release-Repository."
    )
    draw_para(c, boundary, rx, right_y - 5 * mm, col_w, style("boundary", size=6.4, leading=8.2, color=MUTED))
    c.showPage()


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=A4, pageCompression=1, invariant=1)
    c.setTitle("Die Juri-Janovski-These zur Geburt / The Juri Janovski Thesis on Birth")
    c.setAuthor("Juri Janovski")
    c.setSubject(
        f"Public research question on birth environments; version {VERSION}; "
        f"contact {CONTACT_EMAIL}; versioned rights and byte-exact provenance record"
    )
    c.setKeywords(f"Juri Janovski, birth environment, public research, {CONTACT_EMAIL}")
    page_de(c)
    page_en(c)
    page_rights(c)
    page_third_party(c)
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    build()
