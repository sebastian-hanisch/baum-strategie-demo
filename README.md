# Entscheiden mit Baum: Erwartungswert, Strategie, Rollback – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-baum-strategie-demo.streamlit.app/)** -->

Erste Demo der Konzepte-Gruppe „Entscheidungsanalyse“ für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Die Gruppe fragt: **Wie entscheidet man einmal unter Unsicherheit, was ist eine Information wert, und wo
hört der Erwartungsnutzen auf zu reichen?** Diese Demo steht am Anfang: sie führt den **Erwartungswert**, den **Entscheidungsbaum (Ereignisknoten)**, die **Strategie** und den **Rollback** (Rückwärtsrechnung) ein und lässt die Annahmen unberührt, die die
Nachbar-Demos einzeln aufheben: [testwert-evsi-demo](https://github.com/sebastian-hanisch/testwert-evsi-demo) (Information ist kostenlos und vollkommen), [kipp-schwelle-demo](https://github.com/sebastian-hanisch/kipp-schwelle-demo) (die Wahrscheinlichkeiten
sind bekannt), [risiko-aequivalent-demo](https://github.com/sebastian-hanisch/risiko-aequivalent-demo) (risikoneutral), [baum-waechst-demo](https://github.com/sebastian-hanisch/baum-waechst-demo) (der Baum ist aufschreibbar) und
[entscheidung-verfahrenswahl-demo](https://github.com/sebastian-hanisch/entscheidung-verfahrenswahl-demo) (welches Verfahren rechnet es). Das Beispiel ist der **Kapazitätsfall**: **ausgedacht, ein Modell und kein Fall** (Einheit Geldeinheiten GE).
Die Auszahlungen sind erfunden; es gibt keinen Echtdatenbezug.

## Warum dieses Problem

Eine einzelne Wahl unter Unsicherheit ist schnell entschieden: den Erwartungswert ausrechnen und die Wahl mit dem größeren nehmen. Mit mehreren Perioden wird aus der Wahl eine **Strategie**, eine Wahl an jedem Knoten, den man erreicht, und eine
Falle liegt nahe: einen festen **Plan** (die Wahlfolge im Voraus, ohne zu beobachten) für eine Strategie zu halten. Die Demo zeigt beides mit Zähleinheiten (Knoten, Besuche, Strategien) an einem Beispiel. Kernfragen: (1) Was heißt „nach dem Erwartungswert
entscheiden“? (2) Was ist eine Strategie, und wie findet der Rollback sie? (3) Wann nützt es, auf Beobachtungen zu reagieren? **Neu im wissenschaftlichen Sinn ist nichts davon**: Rollback, Strategie und Strategienzahl sind Lehrbuchstoff; neu ist nur die Vorführbarkeit
mit Zähleinheiten an einem durchgehenden Beispiel.

## Modell

**Kapazitätsfall, eine Periode.** G (groß bauen) zahlt +200 GE bei hoher und −100 GE bei niedriger Nachfrage, K (klein bauen oder mieten) zahlt sicher +30 GE. P(hoch) = p; in der ersten Periode und in Experiment 1 mit der Voreinstellung p = 1/2. Erwartungswerte
EW(G) = 50 und EW(K) = 30; die Schwelle, ab der G im Erwartungswert besser ist, ist p* = (30 + 100)/300 = 13/30.

**Kapazitätsfall in k Perioden** (die Zusätze sind eigene Annahmen dieser Demo, ausgedacht, damit der Baum mehr als einen Knoten hat und die Wahl von der Beobachtung abhängen kann). Je Periode wird G oder K gewählt, **vor** der Nachfrage dieser Periode und **nach** Beobachtung der
Vorperiode. Die Nachfrage der ersten Periode ist mit 1/2 hoch; danach bleibt sie mit **Persistenz** q (Voreinstellung 3/4) wie in der Vorperiode. Ein Wechsel der Wahl gegenüber der Vorperiode kostet **w** (Voreinstellung 25 GE, nicht in Periode 1). Die Perioden werden
ohne Diskontierung addiert. Ohne Persistenz (q = 1/2, erste Periode P(hoch) = 1/2) hat die Beobachtung keinen Wert: der feste Plan ist dann schon eine beste Strategie (B8). Ohne Wechselkosten hängt die Wahl nur an der letzten Nachfrage, nicht an der letzten Wahl (Eigenschaftstest).

**Begriffe und Zählweisen** (jede Zahl nennt ihre Zählweise; „Strategien“ ohne Zusatz heißt **reduziert** gezählt):

| Begriff | Bedeutung | Zahl bei zwei Wahlen und zwei Ausgängen |
|---|---|---|
| Entscheidungsknoten | hier wählt man (G oder K) | (4^k − 1)/3 |
| Ereignisknoten | hier entscheidet der Zufall (die Nachfrage) | das Doppelte der Entscheidungsknoten |
| Endknoten | Ende eines Pfades (Gesamtauszahlung) | 4^k |
| Knoten gesamt | Entscheidungs- + Ereignis- + Endknoten | 2·4^k − 1 (7, 31, 127, 511 für k = 1 bis 4) |
| Pfad | Folge Wahl/Ausgang von der Wurzel bis zu einem Endknoten | 4^k |
| Plan | feste Wahlfolge ohne Beobachtung | 2^k |
| Strategie, reduziert | eine Wahl an jedem Entscheidungsknoten, **den die Strategie selbst erreicht**: R_k = 2·R_(k−1)^2, R_0 = 1 | 2^(2^k − 1): 2, 8, 128, 32 768 |
| Strategie, nicht reduziert | eine Wahl an **allen** Entscheidungsknoten | 2^((4^k − 1)/3): 2, 32, 2 097 152, 3,9·10^25 |
| Besuch | ein Knoten, den ein Rechenschritt anfasst | Rollback: jeder Knoten einmal; Aufzählung: je Strategie 3·2^k − 2 Knoten |

**Rollback** (Rückwärtsrechnung): von den Endknoten her an Ereignisknoten mitteln, an Entscheidungsknoten maximieren. Raiffa/Schlaifer 1961 (Abschn. 1.2.1, S. 7 bis 8, Gl. 1-1 bis 1-4) nennen das „backwards induction“ und „averaging out and folding back“; **das Wort „Rollback“ steht
in den gelesenen Quellen nicht** (Lehrbuch- und Softwarejargon), die App sagt „Rollback (Rückwärtsrechnung)“. Voraussetzungen des Baums nach Howard/Matheson 2005 (Abschn. 13): ein einziger Entscheider und „no-forgetting“ (Beobachtetes wird nicht vergessen); beides gilt im Modell.
**Der Entscheidungsbaum (Ereignisknoten) ist kein CART** ([cart-demo](https://github.com/sebastian-hanisch/cart-demo)): CART teilt Daten nach Merkmalen, hier wird eine Folge aus Wahl und Zufall bewertet. Die Kanten des Baums bedeuten in dieser Demo Reihenfolge, nicht Ursache.

**Verlust und Abstand** meinen in der Demo den Mehrwert einer Wahlregel im Erwartungswert gegenüber einer anderen, gemessen am Optimum **des Modells** (ex post, in GE). Das ist **nicht** das Savage-Kriterium (Minimax-Regret). Die Formeln stehen im 📐-Expander der App, beginnend mit einer Lesehilfe.

## Methodik

Die App zeigt oben das Ergebnis (beste Strategie, bester fester Plan, Wert der Anpassung für die Regler der Seitenleiste) mit einem Balkendiagramm von fünf Wahlregeln, dann drei Kernfragen mit je einer Verdikt-Zeile, die aus der Rechnung kommt, dann fünf Experimente:

1. **Ein Knoten.** Regler: P(hoch), Auszahlung von G bei hoher und niedriger Nachfrage, sichere Auszahlung von K (gelten nur hier). Anzeige: Baum mit 7 Knoten, EW(G), EW(K), p*, die Erwartungswertgerade von G gegen K und der Streifen, in dem die Regel „nach dem Erwartungswert“ und die Regel „nach dem wahrscheinlichsten
   Ausgang“ (G nur, wenn „hoch“ wahrscheinlicher ist: p > 1/2) verschieden wählen. Raster p = j/300, j = 0 bis 300, ohne p = 1/2.
2. **Rollback von Hand.** Perioden 1 bis 3, Rechenschritt 0 bis 2k (Endknoten, dann abwechselnd Ereignis- und Entscheidungsknoten von hinten nach vorn). Bis k = 2 wird der Baum mit Graphviz gezeichnet (optimale Äste fett), bei k = 3 (127 Knoten) zeigt eine Tabelle die Zustände; dazu bei k ≤ 2 alle Strategien nach Wert sortiert.
3. **Plan oder Strategie? Die Falle.** Regler der Seitenleiste: Persistenz q, Wechselkosten w, Perioden k (1 bis 10). Fünf Wahlregeln im Balkendiagramm (beste Strategie, bester fester Plan, gierig, „G nach hoch, K nach niedrig“, Münzwurf), Verteilung der Gesamtauszahlung (die 2^k Nachfragefolgen werden aufgezählt) und zwei Raster
   (Rollback gegen gierig, Wert der Anpassung) im Expander. **Gierig** heißt: in jeder Periode die Wahl mit dem besten Erwartungswert dieser einen Periode einschließlich Wechselkosten (Gleichstand: G). **Münzwurf** heißt: an jedem Knoten fair gewürfelt.
4. **Aufzählen oder Rollback?** k = 1 bis 4: alle reduzierten Strategien werden bewertet (vektorisiert; die Bewertung im Objektbaum prüfen die Tests), Histogramm mit den Marken Rollback, bester Plan und Mittel, die Besuche beider Verfahren, zehn zufällig gezogene Strategien (Zufalls-Seed einstellbar). Ab k = 5 gibt es 2 147 483 648
   Strategien: nur noch eine Zahl.
5. **Wie groß wird der Baum?** k = 1 bis 11: Tabelle der Zählweisen, die Rechenzeit der Feldfassung (der volle Baum als numpy-Felder, jetzt gemessen) und der Konvention „Knoten je Seite“ (Voreinstellung 100, einstellbar; eine Konvention, kein Messwert).

**Umsetzungen des Rollback** (je Zahl in `bst_cap.py` und `bst_tree.py`): der **Objektbaum** aus Tupeln (Brüche in Tests, Gleitkomma in der App), die **Zustands-Rechnung** (vier Zustände je Stufe: letzte Wahl und letzte Nachfrage, in Brüchen) und der **Feldbaum** (alle 4^k Pfade als numpy-Felder). Die Aufzählung aller Strategien
benutzt die Eigenschaft, dass der Wert einer Teilstrategie nur am Zustand hängt (äußere Summe über die beiden Teilstrategien je Wahl).

**Zufall:** nur ganzzahliger SplitMix64 (`bst_rng.py`, Kopie der geprüften Vorlage; benutzt wird nur `below`). Die App zieht damit zufällige Strategien, Tests und Messskript Zufallsbäume. Kein `hash()`, kein `numpy.random`, kein `math.log`.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen gelten **für dieses ausgedachte Modell**, bei den genannten Reglern (Basisfall: Persistenz 3/4, Wechselkosten 25 GE, erste Periode P(hoch) = 1/2), in **GE im Erwartungswert**, Strategien **reduziert** gezählt. Gerechnet ist in Brüchen und damit exakt, Gleitkomma nur als Band (relativ 1e-9).
Die Messungen stehen in `data/bst_messung.txt` (`tools/bst_messungen.py`), die Zahlen prüft `tests/test_claims.py`. Zeiten und Speicher stehen nur in der Messdatei und in keinem Test.

| Nr | Frage | Befund (Voraussetzung im Satz) | Test |
|---|---|---|---|
| B1 | Eine Periode | EW(G) = 50, EW(K) = 30, p* = 13/30. Die Regel „wahrscheinlichster Ausgang“ wählt anders als der Erwartungswert für 13/30 < p < 1/2: auf dem Raster p = j/300 (ohne p = 1/2) in **19 von 300 Rasterpunkten** (j = 131 bis 149), größter Verlust auf dem Raster 19 GE (bei p = 149/300). Bei p = 0,45: EW(G) = 35 gegen 30, Verlust 5 GE. Eine Periode hat 1 Entscheidungs-, 2 Ereignis-, 4 Endknoten (7 Knoten) | `test_b1_eine_periode` (exakt) |
| B2 | Rollback von Hand, zwei Perioden | 31 Knoten (5 Entscheidungs-, 10 Ereignis-, 16 Endknoten). Stufe 2: nach (G, hoch) EW(G) 125, EW(K) 5; nach (G, niedrig) −25 und 5; nach (K, hoch) 100 und 30; nach (K, niedrig) −50 und 30. Wurzel: G = 50 + 125/2 + 5/2 = **115**, K = 30 + 100/2 + 30/2 = 95. Beste Strategie: zuerst G; nach hoch G; nach niedrig K (der Wechsel kostet 25 GE und ist trotzdem besser als EW(G) = −25). Die acht Strategien haben die Werte 20, 40, 55, 55, 60, 95, 100, 115 (Mittel 135/2); genau eine erreicht 115. Bester fester Plan „GG“ 100 GE, **Wert der Anpassung 15 GE**; nur 1 von 8 Strategien schlägt ihn. Schwelle der Persistenz bei w = 25: q* = 13/20 (genau ein Gleichstand, zwei optimale Strategien) | `test_b2_zwei_perioden_von_hand` (exakt) |
| B3 | Drei Umsetzungen | Objektbaum und Zustands-Rechnung geben für k = 1 bis 6 denselben Bruch, die Feldfassung für k = 1 bis 10 denselben Wert auf relativ 1e-9. Werte der besten Strategie für k = 1 bis 10: 50, 115, 745/4, 515/2, 1315/4, 400, 1885/4, 1085/2, 2455/4, 685 GE. Ein lineares Programm (SciPy, HiGHS) gibt im Orakel-Test dieselben Werte auf 1e-6 (k = 1, 2, 3, 5, sieben Parameterpaare) | `test_b3_*`, `test_oracle_*` |
| B4 | Aufzählung gegen Rollback | k = 1 bis 4: das Maximum über alle Strategien ist der Rollback-Wert (exakt); Strategien 2 / 8 / 128 / 32 768 (= 2^(2^k − 1)); **genau eine** Strategie erreicht das Maximum (Zählung durch Aufzählung gleich der Rollback-Zählung). Knotenbesuche (instrumentiert im Objektbaum, k = 3 im Test, k = 4 im Orakel-Test): Rollback 7 / 31 / 127 / 511 (= 2·4^k − 1, jeder Knoten einmal), Aufzählung 8 / 80 / 2 816 / 1 507 328 (je Strategie 3·2^k − 2 Knoten). **300 Zufallsbäume** (d ∈ {2, 3} Wahlen, b ∈ {2, 3} Ausgänge, k ≤ 4 bei (2, 2), k ≤ 3 sonst und k ≤ 2 bei (3, 3); ganzzahlige Auszahlungen, gerade Nummern in [−30, 60], ungerade in [0, 3] mit vielen Gleichständen; Zufalls-Seed 20261117): Rollback gleich Maximum der Aufzählung, Zahl optimaler Strategien, Strategienzahl und Knotenzahl gleich der Formel in 300 von 300, davon 12 mit Gleichstand (mehr als eine optimale Strategie). Im Repo laufen zweimal 60 solche Bäume (k ≤ 3: Orakel-Test und Claims-Test) | Messdatei (300 Bäume); `test_b4_*`, `test_oracle_*` (60 Bäume) |
| B5 | Verteilung der Strategienwerte | Mittel aller Strategien für k = 1 bis 4: 40 / 135/2 / 95 / 245/2 (gleich dem Wert der Münzwurf-Politik); schlechteste 30 / 20 / 65/4 / 25/2; Median 40 / 115/2 / 90 / 1915/16 (bei gerader Zahl das Mittel der beiden mittleren Werte). **Strategien über dem besten festen Plan:** 0 von 2, 1 von 8, 13 von 128, **1 474 von 32 768** | `test_b5_*` (exakt) |
| B6 | Plan gegen Strategie (die Falle) | Basisfall, Wert der besten Strategie gegen besten festen Plan („immer G“), Wert der Anpassung: k = 1: 50 / 50 / 0; k = 2: 115 / 100 / 15; k = 3: 186,25 / 150 / 36,25; k = 4: **257,5 / 200 / 57,5**; k = 6: 400 / 300 / 100; k = 10: 685 / 500 / 185. Im Basisfall ist die gierige Regel schon optimal (gleich dem Rollback für k = 1 bis 10), ebenso „G nach hoch, K nach niedrig“, und an jedem Zustand gibt es genau eine optimale Wahl (k = 8). Münzwurf-Politik: 40 / 67,5 / 95 / 122,5 / 177,5 / 287,5 für k = 1, 2, 3, 4, 6, 10 | `test_b6_*` (exakt) |
| B7 | Rollback gegen gierig | Raster q ∈ {1/2, 3/5, 2/3, 3/4, 4/5, 9/10, 19/20} × w ∈ {0, 10, 25, 40, 50, 75, 100, 150, 200} × k ∈ {2, 3, 4, 6} = 252 Zellen: Rollback besser in **29**, gleich in 223, schlechter in 0. Beispiel q = 3/4, w = 75: Rollback 605/4 (151,25) gegen gierig 150 bei k = 3 (Abstand 5/4), 210 gegen 200 bei k = 4 (10), 327,5 gegen 300 bei k = 6 (27,5); bei k = 3 unterscheiden sich die Wahlen an genau einem Zustand: nach (G, niedrig) wählt der Rollback K, die gierige Regel G | `test_b7_*` (exakt) |
| B8 | Wann nützt Anpassen | Wert der Anpassung (Strategie minus bester Plan), Raster q ∈ {1/2, 3/5, 2/3, 3/4, 9/10} × w ∈ {0, 25, 50} × k = 1 bis 8 = 120 Zellen: nie negativ (0 Verletzungen), Wert 0 in **57** Zellen (15 davon trivial bei k = 1), Wert > 0 in 63. q = 1/2: 0 in allen 24 Zellen. Bei q = 3/5 und w = 25 oder 50 ist der Wert für k = 1 bis 8 überall 0, bei q = 2/3 und w = 50 ebenfalls; bei q = 3/5 und w = 0 wächst er um 5 GE je Periode. Schwelle der Persistenz bei w = 25 (kleinstes q mit Wert > 0, Bisektion in Brüchen; oberhalb auf dem Raster 1/100 durchgehend > 0): k = 2: 13/20, k = 3: 0,6361, k = 4: 0,6323, k = 5: 0,6306, k = 6: 0,6298. Für k = 2: q* = (170 + w)/300 | `test_b8_*` (exakt, Schwellen auf 1e-4); Monotonie auf dem Raster 1/100 in der Messdatei |
| B9 | Erwartungswert ist ein Mittel, kein Pfad | k = 2, beste Strategie: Gesamtauszahlung 400 (3/8), 100 (1/8), −95 (1/2); P(Gesamt < 60) = **1/2**, wobei 60 GE der sichere Wert von „immer K“ ist; „immer G“: 400 (3/8), 100 (1/4), −200 (3/8), P(Gesamt < 60) = 3/8. k = 4: P(Gesamt < 120) = 0,4375 gegen 0,3984 bei „immer G“, P(Gesamt < 0) 0,3672 gegen 0,3984. **Der Vergleich wechselt mit k** (Basisfall, k = 1 bis 8, Anteil unter 30 k GE): Strategie höher als „immer G“ bei k = 2 (0,5 gegen 0,375) und k = 4, gleich bei k = 1 und k = 3 (0,5), niedriger ab k = 5 (k = 5: 0,3906 gegen 0,5; k = 6: 0,3555 gegen 0,4131; k = 6, Anteil unter 0: 0,0830 gegen 0,2505); darum nennt das Verdikt nur die Zahlen des eingestellten k (Zählung über die 2^k Nachfragefolgen) | `test_b9_*` (Bruch, Anteile auf 6e-5) |
| B10 | Zählweisen | Knoten k = 1 bis 7: 7 / 31 / 127 / 511 / 2 047 / 8 191 / 32 767; Pfade k = 1 bis 5: 4 / 16 / 64 / 256 / 1 024; Pläne 2 / 4 / 8 / 16 / 32; Entscheidungsknoten k = 1 bis 4: 1 / 5 / 21 / 85; Strategien reduziert k = 1 bis 5: 2 / 8 / 128 / 32 768 / 2 147 483 648 (k = 6: 9,2·10^18; k = 7: 1,7·10^38); nicht reduziert: 2 / 32 / 2 097 152 / 3,9·10^25 / 4,5·10^102. Mit der Konvention 100 Knoten je Seite überschreitet der Baum die Seite ab k = 3 (127 Knoten; k = 2 hat 31) | `test_b10_zaehlweisen` (exakt) |
| B11 | Rechenaufwand | Zustands-Rechnung in Brüchen bis k = 300 (der Baum hätte 2·4^300 − 1 Knoten), Wertzuwachs je Stufe dort 285/4 = 71,25 GE (exakt; Test). **Zeiten, eine CPU, ein Lauf, Größenordnung, Windows, Python 3.14.6, numpy 2.5.3:** Feldfassung des vollen Baums k = 11 (8 388 607 Knoten) etwa 0,1 bis 0,2 s; Objektbaum aus Tupeln bis k = 8 gebaut: etwa 0,3 bis 0,6 s (131 071 Knoten); Zustands-Rechnung k = 300 etwa 0,03 bis 0,04 s; 125 Byte je Knoten beim Objektbaum bei k = 7 (tracemalloc) | `test_b11_zustandsrechnung_*` (exakt); Zeiten nur in `data/bst_messung.txt` |
| B12 | Eigenschaften der Rollback-Rechnung | Je 100 Zufallsbäume (k ≤ 3), exakt, in 100 von 100: Auszahlungen mal 3 gibt Wert mal 3, je Stufe + 7 gibt Wert + 7k, Reihenfolge der Wahlen umgekehrt ändert nichts, strikt dominierte Zusatzwahl ändert nichts, eine Zusatzwahl an der Wurzel senkt den Wert nie (wo es um Gleichheit geht, bei gleicher Zahl optimaler Strategien) | Messdatei (je 100 Bäume); `tests/test_eigenschaften_*` (je 30 Bäume) |

### Rechenregeln und Hinweise zu den Zahlen

- **Exakt** heißt: in Brüchen gerechnet. Die Feldfassung und die vektorisierten Strategiewerte sind Gleitkomma; ihre Tests sind Bänder (relativ 1e-9). Anteile in B9 gelten als Bruch und sind im Test auf 6·10⁻⁵ gerundet verglichen.
- **Zähleinheit:** B1 Rasterpunkt; B2 bis B8 Strategie, Plan oder Zelle (Persistenz × Wechselkosten × Perioden); B9 Nachfragefolge; B10 Knoten, Pfad, Plan, Strategie; Besuche in B4: Knoten.
- **Absolutaussagen und ihre Bedingungen:** „genau eine Strategie erreicht den Rollback-Wert“ gilt im Basisfall für k ≤ 4 und nicht allgemein (12 der 300 Zufallsbäume haben Gleichstand; bei q = 13/20, k = 2 gibt es zwei). „Gierig ist optimal“ gilt für q = 3/4, w = 25, k = 1 bis 10, nicht allgemein (B7: 29 von 252 Zellen).
  „Der Wert der Anpassung ist nie negativ“ ist ein Satz (jeder feste Plan ist eine Strategie) und hier mit 0 Verletzungen in 120 Zellen und im Eigenschaftstest belegt. „Der Baum ist rechenbar bis k = 11“ heißt: die Feldfassung rechnet ihn in etwa 0,1 bis 0,2 s (B11); aufgezählt würden bei k = 5 schon 2 147 483 648 Strategien (Formel, nicht gelaufen).

## Befunde und Korrekturen gegenüber der ersten Rechnung

- **Median bei gerader Zahl der Strategien:** die erste Rechnung nahm den oberen der beiden mittleren Werte (k = 1: 50, k = 2: 60); die Demo nimmt das Mittel der beiden mittleren Werte (k = 1: 40, k = 2: 57,5, k = 3: 90, k = 4: 1915/16 gleich in beiden). Mittel, schlechteste Strategie und die Zahlen „über dem besten Plan“ blieben gleich.
- **Zufallsbäume:** 12 statt 13 von 300 mit Gleichstand, weil Zufalls-Seed und Ziehung der Auszahlungen im Bau neu geschrieben sind; die Aussage „Gleichstände kommen vor“ gilt unverändert.
- **Zeiten und Speicher** sind im Bau neu gemessen (B11): der Objektbaum wird nur bis k = 8 gebaut (die erste Rechnung ging bis k = 10), der Speicher je Knoten ist 125 Byte (erste Rechnung 113,6 Byte bei anderem Aufbau); die Hochrechnung auf k ≥ 12 bleibt ungemessen.
- **Schwelle der Persistenz:** die Monotonie oberhalb der Schwelle ist auf dem Raster 1/100 geprüft (die erste Rechnung nahm 1/1000); die Schwellen stimmen auf vier Stellen überein.
- **Negativbefund zu „Rollback schaut weiter voraus“:** im Basisfall (q = 3/4, w = 25) ist die gierige Regel bereits optimal; im Raster (B7, 29 von 252 Zellen) zeigt sich der Vorsprung des Rollback überwiegend bei hohen Wechselkosten (24 von 29 Zellen bei w ≥ 75), vereinzelt auch bei w = 10 und w = 40, nicht bei w = 0, 25 und 50 und nicht bei q = 1/2. Die Kernaussage der Demo stützt sich deshalb auf **Plan gegen Strategie** (B6, B8), nicht auf gierig gegen Rollback.
- **Bei p = 1/2** hat die Regel „wahrscheinlichster Ausgang“ keinen wahrscheinlicheren Ausgang; das Verdikt zu Experiment 1 sagt dann, dass sie nicht entscheiden kann, und meldet keinen Verlust.

## Quellen

- Raiffa, H., Schlaifer, R. (1961): *Applied Statistical Decision Theory*, Harvard University, Abschn. 1.2.1, S. 7 bis 8, Gl. 1-1 bis 1-4: Rückwärtsinduktion (Mitteln und Zurückfalten). Gelesen (Wortlaut); Tabelle 1.1 (Bauteil-Beispiel) nicht gelesen. Die Gleichungen stehen hier in eigener Schreibweise für dieses Modell, nichts wörtlich übernommen.
- Howard, R. A., Matheson, J. E. (2005): „Influence Diagrams“, *Decision Analysis* 2(3), 127 bis 143, Abschn. 13: ein Entscheidungsbaum setzt einen einzigen Entscheider und „no-forgetting“ voraus. Gelesen (Wortlaut).
- Der Name „Rollback“, die Wachstumsformeln (Knoten, Strategien) und das Zählen der Besuche sind keine Quelle, sondern Arithmetik und Jargon (eigene Rechnung, Tests). Alles Inhaltliche ist Lehrbuchstoff.

## Ehrliche Grenzen

- **Ein Modell.** Auszahlungen, Persistenz und Wechselkosten sind ausgedacht; andere Parameter ändern jede Zahl zur Anpassung (gemessen nur in den Rastern B7 und B8). Das Beispiel ist kein Fall.
- **Gedächtnis eine Periode.** Nachfrage mit längerem Gedächtnis, mehr als zwei Wahlen oder Ausgänge im Kapazitätsfall sind nicht gemessen; die Zufallsbäume (d, b bis (3, 3)) decken die Zählformeln und die Gleichheit von Rollback und Aufzählung, nicht die Anpassungswerte.
- **Der höhere Erwartungswert ist kein Garantiewert** (B9): bei zwei Perioden liegt die beste Strategie mit Wahrscheinlichkeit 1/2 unter dem sicheren Wert von „immer K“. Eine Nutzenfunktion kommt hier nicht vor.
- **„Aufschreibbar“ ist eine Konvention** (100 Knoten je Seite, einstellbar), kein Messwert.
- **Linux:** alle 161 Tests bestehen im Linux-Container (Docker, Python 3.12); der erste Lauf war rot, weil `pytest.approx` dort keine Bruchzahl als absolute Toleranz annimmt (Test geändert, Zahl unverändert). Wie weit die Zeiten und Gleitkomma-Bänder dort abweichen, ist nicht einzeln gemessen.
- **Zeiten:** eine CPU, ein Lauf, Windows, Streuung nicht bestimmt; k ≥ 12 nicht gelaufen. Die App misst die Rechenzeit der Feldfassung bei jedem neuen k einmal selbst (Größenordnung).
- **Nicht mit echtem Mausklick im Browser getestet:** die Bedienung ist mit AppTest geprüft (jeder Knopf, jeder Regler am Minimum und Maximum); der Graphviz-Baum wird vom Browser gezeichnet und im AppTest nur als Element gesehen.
- **Nachbarn nicht gelesen:** die READMEs von `cart-demo`, `bestell-rueckwaerts-demo`, `dp-grenze-demo`, `routenresilienz-demo`, `newsvendor-evpi-demo` und `informationsleiter-demo` wurden nur in der Einleitung gelesen; die Abgrenzung unten folgt dieser Einleitung.

## Abgrenzung zu Nachbarn

- **Bestandspolitiken** ([bestell-rueckwaerts-demo](https://github.com/sebastian-hanisch/bestell-rueckwaerts-demo), [dp-grenze-demo](https://github.com/sebastian-hanisch/dp-grenze-demo)): Rückwärtsrechnung (Bellman) über **Zustände** (Bestand), Wachstum der Zustandstabelle. Hier nicht wiederholt: Zustandsraum, Lagerkosten, Wachstum der Tabelle. Neu hier ist der **Baum selbst** (Ereignis- und Entscheidungsknoten), die **Strategie als Wahl an jedem Knoten** gegen den festen Plan und die Zählweisen. Die vier Zustände der Zustands-Rechnung
  erscheinen nur als Nebenbemerkung; Zustandskompression gehört [baum-waechst-demo](https://github.com/sebastian-hanisch/baum-waechst-demo).
- **Optimales Stoppen** ([routenresilienz-demo](https://github.com/sebastian-hanisch/routenresilienz-demo), [informationsleiter-demo](https://github.com/sebastian-hanisch/informationsleiter-demo)): Wann man aufhört; hier gibt es keine Stoppregel. Der Vergleich Rollback gegen Aufzählung als Orakel ist dort wie hier ein Muster, kein neuer Befund.
- **Wert der Information** ([newsvendor-evpi-demo](https://github.com/sebastian-hanisch/newsvendor-evpi-demo)): EVPI und VSS einer Entscheidung vor der Nachfrage; hier nicht berührt. Der Wert eines Tests gehört [testwert-evsi-demo](https://github.com/sebastian-hanisch/testwert-evsi-demo).
- **CART** ([cart-demo](https://github.com/sebastian-hanisch/cart-demo)): anderer Baum, siehe Modell.

## Verifikation

- **Kern:** Handbeispiele in Brüchen (31 Knoten, die vier Stufe-2-Werte, 115 gegen 95, alle acht Strategien, Pläne, Verteilungen, Zählformeln) und Mini-Baum von Hand (`tests/test_handbeispiel.py`), SplitMix64 gegen die Referenzfolge.
- **Orakel** (`tests/test_oracle_baum_strategie.py`, anderer Rechenweg): Rollback gegen die Aufzählung aller reduzierten Strategien auf 60 Zufallsbäumen und im Kapazitätsfall bis k = 4 (Werte, Zahl der optimalen Strategien, Besuche, Knotenzahl); Objektbaum gegen Zustands-Rechnung (Brüche) und
  Feldbaum (1e-9); Rollback gegen ein lineares Programm (SciPy, HiGHS); bester Plan gegen Aufzählung aller 2^k Pläne und gegen eine Markov-Kette mit Matrixpotenzen; vektorisierte Strategiewerte gegen die Bewertung im Objektbaum; Mittel aller Strategien gegen die Münzwurf-Rechnung; Verteilungen gegen die Politikwerte.
- **Eigenschaften** (`tests/test_eigenschaften_baum_strategie.py`, je 30 Zufallsbäume, fester Zufalls-Seed): Auszahlungen skalieren und verschieben, Wahlen umordnen, dominierte und zusätzliche Wahl, Summe der Pfadwahrscheinlichkeiten; im Kapazitätsfall Wert der Anpassung nie negativ, q = 1/2 gibt 0, hohe Wechselkosten geben 0, Skalierung, Spiegelung.
- **Randfälle** (`tests/test_edge_cases.py`): k = 0 und k = 1, Gleichstand bei der Schwelle, p = 0 und p = 1, sehr hohe Wechselkosten, doppelte Wahlen, Bäume nur mit Ereignis- oder nur mit Entscheidungsknoten, Extremwerte der Regler.
- **Verdikte** als reine Funktionen an von Hand gesetzten Werten (`tests/test_verdicts.py`), je Schnellstart-Szenario die erwartete Verdikt-Zeile (`tests/test_presets.py`: „Unabhängige Perioden“ und „Anpassung lohnt nicht“ melden den Wert 0, nicht „Anpassung hilft“).
- **Claims:** jede Zahl der Befunde B1 bis B11 (`tests/test_claims.py`); B4 (300 Bäume) und B12 stehen in der Messdatei.
- **Oberfläche:** AppTest-Rauchtest (jeder Knopf, jeder Regler am Minimum und Maximum), Footer-Test, Layout (Schnellstart in der Seitenleiste, fester Kopf, aktives Szenario hervorgehoben, jede Änderung eines Reglers hebt die Markierung auf), Laufzeit-Importe.
- **Testzahl:** 161 Tests (`pytest --collect-only -q tests`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Ergebnis, Kernfragen, fünf Experimente, Grenzen, Formeln |
| `bst_cap.py` | Kapazitätsfall: Objektbaum, Zustands-Rechnung, Pläne, Politiken, alle Strategienwerte, Feldbaum |
| `bst_tree.py` | allgemeiner Entscheidungsbaum aus Tupeln: Rollback, Aufzählung, Besuche, Zufallsbäume, Umbauten |
| `bst_count.py` | Zählweisen (Formeln) und Schreibweise großer Zahlen |
| `bst_constants.py` | Regler-Grenzen, Voreinstellungen, Raster, Farben, Schnellstart-Szenarien |
| `bst_evaluation.py` | Auswertung je Experiment, Raster, Verdikte |
| `bst_layout.py` | fester Kopf (Stylesheet) |
| `bst_presets.py` | Permalink (Begrenzen), Schnellstart in der Seitenleiste, aktives Szenario hervorgehoben, Zufalls-Seed-Knopf |
| `bst_rng.py` | SplitMix64 (Kopie der geprüften Vorlage) |
| `bst_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) und der Baum als Graphviz-Text |
| `data/bst_messung.txt` | Messung zu den Befunden B1 bis B12 (Ausgabe von `tools/bst_messungen.py`) |
| `tools/bst_messungen.py` | Messskript (rund anderthalb Minuten) |
| `requirements.txt` | Laufzeit-Bibliotheken (streamlit, numpy, pandas, plotly; ungepinnt) |
| `requirements-dev.txt` | Laufzeit plus pytest und SciPy (nur für das Orakel mit dem linearen Programm) |
| `tests/` | Handbeispiele, Orakel, Eigenschaften, Randfälle, Claims, Verdikte, Schnellstart, AppTest-Rauchtest, Layout, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Zustandskompression und Einflussdiagramm:** wie man weiterrechnet, wenn der Baum nicht mehr aufschreibbar ist ([baum-waechst-demo](https://github.com/sebastian-hanisch/baum-waechst-demo)).
- **Wert eines Tests, Bayes-Update:** [testwert-evsi-demo](https://github.com/sebastian-hanisch/testwert-evsi-demo). **Schwellen und Kippen der Wahl:** [kipp-schwelle-demo](https://github.com/sebastian-hanisch/kipp-schwelle-demo). **Nutzenfunktion und Risikoeinstellung:** [risiko-aequivalent-demo](https://github.com/sebastian-hanisch/risiko-aequivalent-demo).
- **Diskontierung, mehr als zwei Wahlen oder Ausgänge im Kapazitätsfall, Nachfrage mit längerem Gedächtnis:** nicht gebaut (siehe Ehrliche Grenzen).
- **PDF-Export** der Ergebnisse.
- Das Savage-Kriterium (Minimax-Regret) kommt nicht vor.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, pandas und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Entscheidungsanalyse: Information, Risiko, Grenzen](https://sebastianhanisch.net/konzepte-entscheidungsanalyse.html).
