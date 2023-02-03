# Baukosten im Vergleich zur Lohnentwicklung
Analyse von 8833 Schätzwerten von Ein- und Mehrfamilienhäusern in Liechtenstein aus den Jahren 1995-2020

![Einfamilienhaus](https://github.com/ValeskaBlank/Valeskas-Repo/blob/main/Abschlussarbeit%20CAS/Einfamilienhaus-Mauren.jpg)
Ein Einfamilienhaus in der liechtensteinischen Gemeinde Mauren.   Bild: Archiv «Liechtensteiner Vaterland»

## Checkliste

* These formulieren: **Bauen war früher einfacher leistbar als heute. Die Schere zwischen Lohn und Baukosten hat sich geöffnet.**
* These checken: Relevanz? Neu? Aufwand/Ertrag? **Sehr relevantes Thema für Liechtensteiner:innen. Die Klagen, sich kein Haus mehr leisten zu können, häufen sich. Eine solche Auswertung gab es fürs Land noch nie. Geschätzter Aufwand: hoch aufgrund der dünnen Datenlage; Ertrag: hoch, da Geschichte neu und grosses «talking piece»**
* Knackpunkt bestimmen: **Geeignete Daten lassen sich nicht beschaffen**
* Briefing Person konsultieren: **Rücksprache fand regelmässig statt**
* Daten beschaffen/reinigen/analysieren/visualisieren -> These justieren: **War nicht nötig, These hat sich bestätigt**
* Ergänzen durch klassische Recherche (Experten, Politiker etc.)
* Dokumentieren Code und statistische Annahmen
* Link auf Publikation
* Aufwandslogbuch

## Datenquelle

## 1. Schätzwerte der Gebäude

Grundlage der Auswertung sind Excel-Tabellen, die das Liechtensteiner Immobilienbewertungsunternehmen Bewera auf Anfrage zur Verfügung stellte. Die notwendige Genehmigung des Schweizerischen Versicherungsverbands (SVV) wurde eingeholt. Die Tabellen umfassen Daten von allen Liechtensteiner Gemeinden (die kleinste Gemeinde, Planken, wurde aufgrund der zu geringen Anzahl Daten nicht berücksichtigt) und reichen bis in die 1990er-Jahre zurück. Enthalten sind 
* Datum der Schätzung
* Art des Gebäudes
* Neuwert des Gebäudes bei Erstellung
* Baukostenindex (BKI) zum Zeitpunkt der Erstellung
* Kubatur des Gebäudes in Kubikmeter (m3)

Erstellt wurden die Tabellen von Bewera-Geschäftsführer Karl Laternser, auf Grundlage der firmeninternen Datenbank. Zusätzlich lieferte er eine Zeitreihe des Baukostenindex, der für die Indexierung (Hochrechnung) der Neuwerte auf das Jahr der Schätzung benötigt wurde. 

## 2. Medianlöhne

Die Medianlöhne weren in Liechtenstein erst seit dem Jahr 2006 veröffentlicht. Das Amt für Statistik empfahl, für die früheren Jahre eine Annahme aufgrund der Entwicklung in der benachbarten Schweiz zu treffen. Das Amt hält diese Schätzung für vertretbar. Die entsprechende Excel-Tabelle für die benötigten Jahre habe ich selbst erstellt. 

## Zeitliche Entwicklung: Analyse mit Pandas

Für das Einlesen, Reinigen und Auswerten der Daten wurde die Python-Bibliothek Pandas verwendet. Berücksichtigt wurden die Jahre ab 1995 bis 2020, weil damit ein «runder» Zeitraum von 25 Jahren abgedeckt werden kann. Ausserdem war die Anzahl Daten aus den verschiedenen Gemeinden in früheren Jahren gering. Die Jahre 2021 und 2022 wurden nicht berücksichtigt; für diesen Zeitraum gibt es noch keinen aktuellen Medianlohn.

Pandas ermöglichte das effiziente Einlesen der Excel-Tabellen mit den Gemeindedaten in einem «Rutsch», eine zeitliche Sortierung der Daten, die Berechnung der indexierten Neuwerte und letztlich die Kombination der Auswertung mit den Medianlöhnen. 

Zur Kontrolle wurden die Berechnungen nochmals in Excel wiederholt. 

## Artikel

afe

## Aufwandslogbuch

* **Geeignete Daten finden:** Anfragen bei Amt für Statistik und Grundbuchamt (beide mit keinem befriedigendem Ergebnis), Anfrage bei Immobilienbewertungsbüro Bewera plus anschliessendem Pitch des Vorhabens beim Firmenchef: Netto ein halber Arbeitstag (4 Std.)
* **Datenreinigung, Berechnungen und Auswertungen in Pandas:** Drei Arbeitstage (ziemlich lange, da immer wieder mit Code verzettelt)
* **Visualisierung:** 4 Std. (das ging dank Googeln erstaunlich schnell)
* **Medienanfrage bei Banken/Interview mit Datenlieferant:** 2 Std.
* **Artikel schreiben:** 4 Std. 
* **Total Aufwand:** Knapp 5 Arbeitstage
