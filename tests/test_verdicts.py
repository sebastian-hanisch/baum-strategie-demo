"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Schwelle der Art und jede Zahl im Text steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Zufalls-Seeds. Die Zeiten sind von Hand gesetzt: Zeiten werden nie als Zahl getestet."""

from fractions import Fraction as F

import bst_cap as CAP
import bst_evaluation as ev


def _one(**kw):
    a = {"p": F(9, 20), "ew_g": F(35), "ew_k": F(30), "p_star": F(13, 30), "by_expectation": "G", "by_modal": "K", "loss": F(5),
         "raster": {"steps": 300, "points": 300, "different": list(range(131, 150)), "worst_loss": F(19), "worst_j": 149}}
    a.update(kw)
    return a


# --- Formatierung ----------------------------------------------------------------------------------------------------------------------------

def test_zahlen_als_deutscher_text():
    assert ev.de(257.5) == "257,5" and ev.de(115.0) == "115" and ev.de(F(745, 4)) == "186,25" and ev.de(-25) == "−25" and ev.de(-0.001) == "0"
    assert ev.de(F(13, 30), 4) == "0,4333" and ev.de(float("nan")) == "–"
    assert ev.prozent(F(7, 16)) == "43,8 %" and ev.prozent(0) == "0,0 %"
    assert ev.bruch(F(26, 2)) == "13" and ev.bruch(F(13, 30)) == "13/30" and ev.bruch(F(-1, 2)) == "-1/2"
    assert ev.plan_text(("G", "K", "G")) == "GKG" and ev.cap1("zuerst G") == "Zuerst G"


# --- Experiment 1 ----------------------------------------------------------------------------------------------------------------------------

def test_verdict_eins_warnung_wenn_die_regeln_verschieden_waehlen_nennt_jede_zahl():
    kind, text = ev.verdict_one(_one())
    assert kind == "warning"
    assert text.startswith("Bei p = 0,45: EW(G) = 35, EW(K) = 30 GE.")
    assert "wählt K und verschenkt 5 GE im Erwartungswert (der Erwartungswert wählt G)" in text
    assert "0,433 < p < 0,5 (19 von 300 Rasterpunkten)" in text and "größte Verlust der Modalregel auf dem Raster ist 19 GE" in text


def test_verdict_eins_info_wenn_beide_regeln_gleich_waehlen():
    kind, text = ev.verdict_one(_one(p=F(3, 4), ew_g=F(125), by_modal="G", loss=F(0)))
    assert kind == "info" and "Beide Regeln wählen G: hier gibt es nichts zu verlieren." in text and "Bei p = 0,75: EW(G) = 125" in text


def test_verdict_eins_gleichstand_im_erwartungswert_ist_info():
    kind, text = ev.verdict_one(_one(p=F(1, 2), ew_g=F(30), by_expectation=None, by_modal=None, loss=F(0)))
    assert kind == "info" and "Gleichstand im Erwartungswert: beide Wahlen sind gleich gut." in text


def test_verdict_eins_modalregel_kann_nicht_entscheiden_ist_info():
    kind, text = ev.verdict_one(_one(p=F(1, 2), ew_g=F(50), by_modal=None, loss=F(0)))
    assert kind == "info" and "kann nicht entscheiden" in text and "der Erwartungswert wählt G" in text and "Bei p = 0,5: EW(G) = 50" in text


def test_verdict_eins_ohne_verschiedene_rasterpunkte_nennt_null_von_300():
    raster = {"steps": 300, "points": 300, "different": [], "worst_loss": F(0), "worst_j": None}
    kind, text = ev.verdict_one(_one(by_modal="G", loss=F(0), raster=raster))
    assert kind == "info" and "nie verschieden (0 von 300 Rasterpunkten)" in text


# --- Experiment 2 ----------------------------------------------------------------------------------------------------------------------------

class _Sol:
    def __init__(self, value):
        self.value = value


def _hand(k=2, value=F(115), root_best=("G",), **kw):
    rows = [
        {"stage": 2, "state": ("G", "hoch"), "ew_g": F(125), "ew_k": F(5), "choice": ["G"], "value": F(125)},
        {"stage": 2, "state": ("G", "niedrig"), "ew_g": F(-25), "ew_k": F(5), "choice": ["K"], "value": F(5)},
        {"stage": 2, "state": ("K", "hoch"), "ew_g": F(100), "ew_k": F(30), "choice": ["G"], "value": F(100)},
        {"stage": 2, "state": ("K", "niedrig"), "ew_g": F(-50), "ew_k": F(30), "choice": ["K"], "value": F(30)},
    ]
    a = {"k": k, "sol": _Sol(value), "root_best": list(root_best), "root_g": F(115), "root_k": F(95), "nodes": 31, "rows": rows}
    a.update(kw)
    return a


def test_verdict_hand_k_2_nennt_wert_und_beide_folgewahlen():
    kind, text = ev.verdict_hand(_hand())
    assert kind == "success"
    assert text.startswith("k = 2: 31 Knoten, Wert 115 GE. Zuerst G; nach hoch G (EW(G) = 125, EW(K) = 5); nach niedrig K (EW(G) = −25, EW(K) = 5).")
    assert "Tabelle von Zuständen, kein Pfad" in text


def test_verdict_hand_k_2_nach_wechsel_der_ersten_wahl_liest_die_zustaende_von_k():
    kind, text = ev.verdict_hand(_hand(root_best=("K",)))
    assert "Zuerst K; nach hoch G (EW(G) = 100, EW(K) = 30); nach niedrig K (EW(G) = −50, EW(K) = 30)" in text


def test_verdict_hand_k_1_und_k_3_und_gleichstand():
    kind, text = ev.verdict_hand(_hand(k=1, value=F(50), nodes=7, rows=[]))
    assert kind == "info" and "k = 1: 7 Knoten, Wert 50 GE" in text and "EW(G) = 115" in text and "nichts zu beobachten" in text
    kind, text = ev.verdict_hand(_hand(k=3, value=F(745, 4), nodes=127))
    assert kind == "info" and "k = 3: 127 Knoten, Wert 186,25 GE" in text and "zu viele Knoten zum Zeichnen" in text
    kind, text = ev.verdict_hand(_hand(root_best=("G", "K")))
    assert "Zuerst G oder K (Gleichstand); nach hoch G" in text


def test_schritte_des_rollbacks_von_hand():
    assert ev.step_text(2, 0).startswith("Endknoten")
    assert ev.step_text(2, 1).startswith("Ereignisknoten der Stufe 2") and ev.step_text(2, 2).startswith("Entscheidungsknoten der Stufe 2")
    assert ev.step_text(2, 3).startswith("Ereignisknoten der Stufe 1") and ev.step_text(2, 4).startswith("Wurzel")
    assert ev.step_text(1, 1).startswith("Ereignisknoten der Stufe 1") and ev.step_text(1, 2).startswith("Wurzel")
    assert ev.step_text(3, 5).startswith("Ereignisknoten der Stufe 1") and ev.step_text(3, 2).startswith("Entscheidungsknoten der Stufe 3")


# --- Experiment 3 ----------------------------------------------------------------------------------------------------------------------------

def _plan(**kw):
    a = {"cap": CAP.make_cap(), "k": 4, "strategy": F(515, 2), "plan": F(200), "plan_choices": ("G",) * 4, "adaptation": F(115, 2), "greedy": F(515, 2),
         "below_strategy": F(7, 16), "below_plan": F(51, 128), "safe": F(120)}
    a.update(kw)
    return a


def test_verdict_plan_erfolg_nennt_strategie_plan_und_anpassung():
    kind, text = ev.verdict_plan(_plan())
    assert kind == "success"
    assert text.startswith("k = 4: Strategie 257,5 GE, bester fester Plan 200 GE (GGGG), Wert der Anpassung 57,5 GE.")
    assert "Persistenz q = 0,75 und Wechselkosten w = 25 GE lohnt es, auf die Beobachtung zu reagieren." in text and "gierige" not in text


def test_verdict_plan_nennt_den_vorsprung_vor_der_gierigen_regel_nur_wenn_er_positiv_ist():
    kind, text = ev.verdict_plan(_plan(strategy=F(210), plan=F(200), adaptation=F(10), greedy=F(200)))
    assert kind == "success" and "Der Rollback schlägt hier sogar die gierige Regel: 210 gegen 200 GE." in text


def test_verdict_plan_ohne_wert_der_anpassung_meldet_keinen_effekt():
    kind, text = ev.verdict_plan(_plan(strategy=F(200), adaptation=F(0), greedy=F(200), cap=CAP.make_cap(q=F(3, 5))))
    assert kind == "info" and "Wert der Anpassung 0 GE" in text and "q = 0,6" in text and "schon eine beste Strategie" in text and "lohnt es" not in text


def test_verdict_plan_k_1_hat_nichts_zu_beobachten():
    kind, text = ev.verdict_plan(_plan(k=1, strategy=F(50), plan=F(50), adaptation=F(0), plan_choices=("G",)))
    assert kind == "info" and "nichts zu beobachten" in text and "k = 1" in text


def test_verdict_verteilung_nennt_anteile_und_den_sicheren_wert():
    kind, text = ev.verdict_distribution(_plan())
    assert kind == "warning" and "k = 4:" in text and "43,8 %" in text and "sicheren Wert 120 GE" in text and "39,8 %" in text and "kein Garantiewert" in text


def test_verdict_verteilung_ohne_anteil_unter_dem_sicheren_wert_ist_info():
    kind, text = ev.verdict_distribution(_plan(k=1, below_strategy=F(0), below_plan=F(0), safe=F(30)))
    assert kind == "info" and "in keiner Nachfragefolge unter dem sicheren Wert 30 GE" in text


# --- Experiment 4 ----------------------------------------------------------------------------------------------------------------------------

def _enum(**kw):
    a = {"k": 4, "n_strategies": 32768, "visits_enum": 1507328, "visits_rollback": 511, "n_best": 1, "n_rollback_optimal": 1, "rollback": 257.5,
         "n_over_plan": 1474, "plan": 200.0, "mean": 122.5}
    a.update(kw)
    return a


def test_verdict_aufzaehlung_nennt_besuche_beste_strategien_und_mittel():
    kind, text = ev.verdict_enum(_enum())
    assert kind == "success"
    assert "k = 4: 32 768 Strategien, 1 507 328 Knotenbesuche bei der Aufzählung; der Rollback braucht 511." in text
    assert "Genau eine Strategie erreicht 257,5 GE und ist die des Rollback." in text
    assert "1474 schlagen den besten festen Plan (200 GE), das Mittel aller ist 122,5 GE." in text


def test_verdict_aufzaehlung_bei_gleichstand_zaehlt_mehrere_beste_strategien():
    kind, text = ev.verdict_enum(_enum(n_best=2, n_rollback_optimal=2, k=2, n_strategies=8, visits_enum=80, visits_rollback=31, rollback=115.0, n_over_plan=1, plan=100.0, mean=67.5))
    assert "2 Strategien erreichen 115 GE (Gleichstand); der Rollback findet eine davon." in text
    assert "k = 2: 8 Strategien, 80 Knotenbesuche" in text and "1 schlagen den besten festen Plan (100 GE)" in text


# --- Experiment 5 ----------------------------------------------------------------------------------------------------------------------------

def _size(**kw):
    a = {"k": 3, "nodes": 127, "seite": 100, "first_k_over_page": 3, "field_seconds": 0.0002, "strategies_reduced_text": "128"}
    a.update(kw)
    return a


def test_verdict_groesse_k_3_ist_mehr_als_eine_seite():
    kind, text = ev.verdict_size(_size())
    assert kind == "info" and "k = 3: 127 Knoten, mehr als eine Seite (100 Knoten je Seite, eine Konvention; ab k = 3)." in text
    assert "unter einer Sekunde" in text and "Aufgezählt wären es 128 Strategien" in text


def test_verdict_groesse_k_2_passt_noch_auf_eine_seite_und_zeit_ueber_einer_sekunde():
    kind, text = ev.verdict_size(_size(k=2, nodes=31, field_seconds=1.26, strategies_reduced_text="8"))
    assert "k = 2: 31 Knoten, das passt noch auf eine Seite (100 Knoten je Seite, eine Konvention)." in text and "in 1,3 s" in text


def test_verdict_groesse_ohne_zeitmessung_nennt_keine_zeit():
    kind, text = ev.verdict_size(_size(field_seconds=None))
    assert "Sekunde" not in text and " s " not in text
