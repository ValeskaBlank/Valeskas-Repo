# Baukosten im Vergleich zur Lohnentwicklung
Analyse von 8826 geschätzten Neuwerten von Ein- und Mehrfamilienhäusern in Liechtenstein aus den Jahren 1995-2020

![Einfamilienhaus](https://github.com/ValeskaBlank/Valeskas-Repo/blob/main/Abschlussarbeit%20CAS/Einfamilienhaus-Mauren.jpg)
Ein Einfamilienhaus in der liechtensteinischen Gemeinde Mauren.   Bild: Archiv «Liechtensteiner Vaterland»

## Checkliste

* These formulieren: **Die Schere zwischen Lohn und Baukosten hat sich geöffnet oder: Früher war es einfacher, sich den Bau eines Hauses leisten zu können.**
* These checken: Relevanz? Neu? Aufwand/Ertrag? **Sehr relevantes Thema für Liechtensteiner:innen. Die Klagen, sich kein Haus mehr leisten zu können, häufen sich. Eine solche Auswertung gab es fürs Land noch nie. Geschätzter Aufwand: hoch aufgrund der dünnen Datenlage; Ertrag: hoch, da Geschichte neu und grosses «talking piece»**
* Knackpunkt bestimmen: **Geeignete Daten lassen sich nicht beschaffen**
* Briefinperson konsultieren: **Rücksprache fand regelmässig statt**
* Daten beschaffen/reinigen/analysieren/visualisieren -> These justieren: **War nicht nötig, These hat sich bestätigt**
* Ergänzen durch klassische Recherche (Experten, Politiker etc.): **Fallbeispiel eines Rentners, der in den 1980er-Jahren gebaut hat**
* Dokumentieren Code und statistische Annahmen
* Link auf Publikation
* Aufwandslogbuch

## Datenquelle

## a) Schätzwerte der Gebäude

Für die Analyse wurden 8826 Ein- und Mehrfamilienhäuser in Liechtenstein berücksichtigt. Grundlage der Auswertung sind anonymisierte Excel-Tabellen, die das Liechtensteiner Immobilienbewertungsunternehmen Bewera auf Anfrage zur Verfügung stellte. Die notwendige Genehmigung des Schweizerischen Versicherungsverbands (SVV) wurde eingeholt. Die Tabellen umfassen Daten von allen Liechtensteiner Gemeinden (die kleinste Gemeinde, Planken, wurde aufgrund der zu geringen Anzahl Daten nicht berücksichtigt) und reichen teils bis in die 1980er-Jahre zurück. Enthalten sind 
* Datum der Schätzung
* Art des Gebäudes
* Neuwert des Gebäudes bei Erstellung
* Zürcher Index der Wohnbaukosten (BKI) zum Zeitpunkt der Erstellung
* Kubatur des Gebäudes in Kubikmeter (m3)

Erstellt wurden die Tabellen von Bewera-Geschäftsführer Karl Laternser, auf Grundlage der firmeninternen Datenbank. Zusätzlich lieferte er eine Zeitreihe des Zürcher Baukostenindex, der für die Indexierung (Hochrechnung) der Neuwerte auf das Jahr der Schätzung benötigt wurde. 

## b) Medianlöhne

Die Medianlöhne werden in Liechtenstein erst seit dem Jahr 2006 veröffentlicht. Das Amt für Statistik empfahl, für die früheren Jahre eine Annahme aufgrund der Entwicklung in der benachbarten Schweiz zu treffen. Das Amt hält diese Schätzung für vertretbar. Die entsprechende Excel-Tabelle für die benötigten Jahre habe ich selbst erstellt. 

## Gespräch mit Briefingperson

Hauptansprechpartner für die Auswertung war Karl Laternser. Nachdem die offiziellen Stellen (Grundbuch, Amt für Statistik) keine offiziellen Daten herausgeben wollten bzw. konnten, bin ich auf ihn gestossen. Als ich ihm mein Vorhaben erklärte, zögerte er erst, war dann aber bereit, gewisse firmeninterne Daten herauszugeben, die der  Gebäudeversicherung geliefert werden müssen. Letztlich ärgerte sich Laternser selbst, dass auf dem hiesigen Immobilienmarkt so grosse Intransparenz herrscht.

## Zeitliche Entwicklung: Analyse mit Pandas

Für das Einlesen, Reinigen und Auswerten der Daten wurde die Python-Bibliothek Pandas verwendet. Berücksichtigt wurden die Jahre ab 1995 bis 2020, weil damit ein «runder» Zeitraum von 25 Jahren abgedeckt werden kann. Ausserdem war die Anzahl Daten aus den verschiedenen Gemeinden in früheren Jahren gering. Die Jahre 2021 und 2022 wurden nicht berücksichtigt; für diesen Zeitraum gibt es noch keinen aktuellen Medianlohn.

Pandas ermöglichte das effiziente Einlesen der Excel-Tabellen mit den Gemeindedaten in einem «Rutsch», eine zeitliche Sortierung der Daten, die Berechnung der indexierten Neuwerte und letztlich die Kombination der Auswertung mit den Medianlöhnen. 

Zur Kontrolle wurden die Berechnungen nochmals in Excel wiederholt. 

## Artikel 

[Publikation auf vaterland.li](https://www.vaterland.li/liechtenstein/wirtschaft/baukosten-im-land-steigen-staerker-als-die-loehne-art-522103)
Login: vblank@medienhaus.li, Passwort: suga9495

Print-Version:
[Aufmacher](https://github.com/ValeskaBlank/Valeskas-Repo/blob/main/Abschlussarbeit%20CAS/PDFs/Aufmacher.pdf) und 
[Bericht](https://github.com/ValeskaBlank/Valeskas-Repo/blob/main/Abschlussarbeit%20CAS/PDFs/Bericht.pdf)

## Aufwandslogbuch

* **Geeignete Daten finden:** Anfragen bei Amt für Statistik und Grundbuchamt (beide mit keinem befriedigendem Ergebnis), Anfrage bei Immobilienbewertungsbüro Bewera plus anschliessendem Pitch des Vorhabens beim Firmenchef: Netto ein halber Arbeitstag (4 Std.)
* **Datenreinigung, Berechnungen und Auswertungen in Pandas:** Drei Arbeitstage 
* **Visualisierung:** 4 Std.
* **Gespräch mit Datenlieferant und Rentner für Fallbeispiel:** 2 Std.
* **Artikel schreiben:** 6 Std. 
* **Total Aufwand:** 5 Arbeitstage

## Arbeitsprotokoll – Reihenfolge

**a) Files mit Schätzungswerten

* 1/ Einlesen eines ersten Files als Test und Schätzungsdaten gleich in Datetime umwandeln, um zeitlich sortieren zu können
* 2/ Schätzungsdaten als Index setzen, für besseren Überblick überflüssige Spalten löschen, Index zeitlich sortieren
* 3/ Index auf Jahre setzen, da die exakten Schätzungsdaten irrelevant sind
* 4/ auf benötigte Jahre (1995-2020) zugreifen
* 5/ Gewünschtes Ergebnis mit Test-Gemeinde erreicht, über alle Files/Gemeinden iterieren
* 6/ alle Gemeinden zu einem grossen Dataframe zusammenfügen

*Zeitaufwand: ca. 1,5 Arbeitstage. Gehadert habe ich mit dem PeriodIndex - das hats irgendwie ständig verhauen - und dem Loop, weil ich für das gewünschte Ergebnis ein Tuple einsetzen musste, was wir nicht gross angeschaut haben im Kurs

**b) File Baukostenindex

* 1/ Excel-Datei dem grossen Gemeinde-df angleichen, dass ich nacher mergen kann: Nach benötigten Jahren filtern, Daten in Datetime umwandeln und auf PeriodIndex setzen etc.
* 2/ Mergen mit Gemeinde-df
* 3/ Neuwerte gemäss Baukostenindex hochrechnen, um danach die indexierten Erstellungskosten/m3 zu berechnen

*Zeitaufwand: 

**c) Auswertung

* 1/ Median der Erstellungskosten/m3 pro Jahr und über alle Gemeinden zusammenrechnen (Methode .agg kannte ich noch nicht, da hat Simon geholfen)

**d) Vergleich Kosten-/Lohnentwicklung

* 1/ File Medianlöhne dem Gemeinde-df angleichen, weil nachher wieder ein merge kommt
* 2/ df's Medianlohn und mittlere Erstellungskosten kombinieren
* 3/ Prozentuale Veränderung 1996 vs. 2020 berechnen

**) Plotten

* 1/ Testen verschiedener Plots: Nur Erstellungskosten, nur Medianlohn, beides zusammen, Trendlinie

*Zeitaufwand: 4 Std. (erstaunlich wenig angesichts des komplizierten Codes für die Trendlinie, hab aber ein gutes Beispiel im Netz gefunden)

