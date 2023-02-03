# Baukosten im Vergleich zur Lohnentwicklung
Analyse von 8833 Schätzwerten von Ein- und Mehrfamilienhäusern in Liechtenstein aus den Jahren 1995-2020

![Einfamilienhaus](https://github.com/ValeskaBlank/Valeskas-Repo/blob/main/Abschlussarbeit%20CAS/Einfamilienhaus-Mauren.jpg)
Bild: Archiv «Liechtensteiner Vaterland»

## Checkliste

* These formulieren: **Bauen war früher einfacher leistbar als heute. Die Schere zwischen Lohn und Baukosten hat sich geöffnet.**
* These checken: Relevanz? Neu? Aufwand/Ertrag? **Sehr relevantes Thema für Liechtensteiner:innen. Die Klagen, sich kein Haus mehr leisten zu können, häufen sich. Eine solche Auswertung gab es fürs Land noch nie. Geschätzter Aufwand: hoch aufgrund der dünnen Datenlage; Ertrag: hoch, da Geschichte neu**
* Knackpunkt bestimmen: **Geeignete Daten lassen sich nicht beschaffen**
* Briefing Person konsultieren: **Rücksprache fand regelmässig statt**
* Daten beschaffen/reinigen/analysieren/visualisieren -> These justieren: **War nicht nötig, These hat sich bestätigt**
* Ergänzen durch klassische Recherche (Experten, Politiker etc.)
* Dokumentieren Code und statistische Annahmen
* Link auf Publikation
* Aufwandslogbuch

## Datenquelle

### 1.

Grundlage der Auswertung sind Excel-Tabellen, die das Liechtensteiner Immobilienbewertungsunternehmen Bewera auf Anfrage zur Verfügung stellte. Die notwendige Genehmigung des Schweizerischen Versicherungsverbands (SVV) wurde eingeholt. Die Tabellen umfassen Daten von allen Liechtensteiner Gemeinden (die kleinste Gemeinde, Planken, wurde aufgrund der zu geringen Anzahl Daten nicht berücksichtigt) und reichen bis in die 1990er-Jahre zurück. Enthalten sind 
* Datum der Schätzung
* Art des Gebäudes
* Neuwert des Gebäudes bei Erstellung
* Baukostenindex (BKI) zum Zeitpunkt der Erstellung
* Kubatur des Gebäudes in Kubikmeter (m3)

Erstellt wurden die Tabellen von Bewera-Geschäftsführer Karl Laternser, auf Grundlage der firmeninternen Datenbank. 

## Analyse mit Pandas


