"""Claims-Tests: jede Zahl der Befunde B1 bis B11 der README mit ihren Voraussetzungen (DEMO-PLAYBOOK §4, §11a; die Tabelle „Zahl → Test“ der README nennt je Befund die Funktion).

Zähleinheiten: Wert und Abstand in GE im Erwartungswert; Strategien reduziert gezählt; Besuch = ein Knoten wird angefasst; Verteilungsanteile über die 2^k Nachfragefolgen.
Plattform (Lehre 2026-11-15): alle Werte hier sind in Brüchen gerechnet und deshalb exakt; Gleitkommawerte (Feldfassung, vektorisierte Strategiewerte) nur als Band
(relativ 1e-9). Zeiten und Speicher stehen in `data/bst_messung.txt` (`tools/bst_messungen.py`), nie in einem Test. Zufall nur aus SplitMix64 (`bst_rng`)."""

from fractions import Fraction as F
from pathlib import Path

import numpy as np
import pytest

import bst_cap as CAP
import bst_constants as C
import bst_count as N
import bst_evaluation as ev
import bst_rng as R
import bst_tree as T

MESSUNG = Path(__file__).resolve().parent.parent / "data" / "bst_messung.txt"


def _g(q, w):
    return CAP.make_cap(q=q, w=w)


# --- B1: eine Periode ----------------------------------------------------------------------------------------------------------------------------

def test_b1_eine_periode():
    cap = CAP.BASIS
    assert (CAP.ew_period(cap, CAP.G, F(1, 2)), CAP.ew_period(cap, CAP.K, F(1, 2)), CAP.threshold(cap)) == (50, 30, F(13, 30))
    r = CAP.rule_comparison_raster(cap)
    assert (len(r["different"]), r["points"], r["different"][0], r["different"][-1], r["worst_loss"], r["worst_j"]) == (19, 300, 131, 149, 19, 149)
    assert CAP.ew_period(cap, CAP.G, F(9, 20)) == 35 and CAP.one_period_loss(cap, F(9, 20)) == 5
    assert T.count_nodes(CAP.build_tree(cap, 1)) == (1, 2, 4)


# --- B2: Rollback von Hand, zwei Perioden --------------------------------------------------------------------------------------------------------

def test_b2_zwei_perioden_von_hand():
    cap = CAP.BASIS
    sol = CAP.solve(cap, 2)
    assert [sol.V[1][s] for s in ((CAP.G, CAP.HOCH), (CAP.G, CAP.NIEDRIG), (CAP.K, CAP.HOCH), (CAP.K, CAP.NIEDRIG))] == [125, 5, 100, 30]
    assert (sol.q_values[0][CAP.START][CAP.G], sol.q_values[0][CAP.START][CAP.K]) == (115, 95) and sol.value == 115
    assert T.count_nodes(CAP.build_tree(cap, 2)) == (5, 10, 16)
    assert sorted(CAP.strategy_values(cap, 2, exact=True)) == [20, 40, 55, 55, 60, 95, 100, 115]
    assert (CAP.best_plan(cap, 2), CAP.adaptation_value(cap, 2)) == ((100, ("G", "G")), 15)
    assert float(ev.persistence_threshold(25, 2)) == pytest.approx(0.65, abs=1e-9)
    assert CAP.solve(_g(F(13, 20), 25), 2).n_optimal == 2


# --- B3: drei Umsetzungen ------------------------------------------------------------------------------------------------------------------------

def test_b3_werte_k_1_bis_10_und_drei_umsetzungen():
    expected = [50, 115, F(745, 4), F(515, 2), F(1315, 4), 400, F(1885, 4), F(1085, 2), F(2455, 4), 685]
    for k, e in enumerate(expected, start=1):
        assert CAP.solve(CAP.BASIS, k).value == e
        assert CAP.field_rollback(CAP.BASIS, k) == pytest.approx(float(e), rel=1e-9)
        if k <= 6:
            assert CAP.tree_rollback_value(CAP.BASIS, k) == e                  # Objektbaum, exakt


# --- B4: Aufzählung gegen Rollback, Besuche -------------------------------------------------------------------------------------------------------

def test_b4_aufzaehlung_gleich_rollback_besuche_und_strategienzahl():
    for k, (n_strat, v_roll, v_enum) in enumerate([(2, 7, 8), (8, 31, 80), (128, 127, 2816), (32768, 511, 1507328)], start=1):
        assert N.n_strategies_reduced(2, 2, k) == len(CAP.strategy_values(CAP.BASIS, k)) == n_strat
        assert (N.visits_rollback(2, 2, k), N.visits_enumeration(2, 2, k)) == (v_roll, v_enum)
        sol = CAP.solve(CAP.BASIS, k)
        values = CAP.strategy_values(CAP.BASIS, k, exact=True)
        assert max(values) == sol.value and sum(1 for v in values if v == sol.value) == 1 == sol.n_optimal
    tree = CAP.build_tree(CAP.BASIS, 3)
    counter = T.Counter()
    T.enumerate_values(tree, counter)
    assert counter.visits == 2816
    counter = T.Counter()
    T.rollback(tree, counter=counter)
    assert counter.visits == 127


def test_b4_zufallsbaeume_im_repo_60_von_60_und_gleichstaende_kommen_vor():
    rng = R.SplitMix64(424242)
    ties = 0
    for i in range(60):
        d, b, k = [(2, 2, 1), (2, 2, 2), (2, 2, 3), (2, 3, 2), (3, 2, 2), (3, 3, 1)][rng.below(6)]
        tree = T.random_tree(rng, d, b, k, "weit" if i % 2 == 0 else "eng")
        value, n_opt, _ = T.rollback(tree)
        values = T.enumerate_values(tree)
        assert max(values) == value and T.count_optimal(values, value) == n_opt and T.check_counts(tree, d, b, k)
        ties += n_opt > 1
    assert ties >= 1


# --- B5: Verteilung der Strategienwerte -----------------------------------------------------------------------------------------------------------

def test_b5_verteilung_der_strategienwerte():
    expected = {1: (F(30), F(40), F(40), 0, 2), 2: (F(20), F(135, 2), F(115, 2), 1, 8), 3: (F(65, 4), F(95), F(90), 13, 128), 4: (F(25, 2), F(245, 2), F(1915, 16), 1474, 32768)}
    for k, (worst, mean, median, over, n) in expected.items():
        values = sorted(CAP.strategy_values(CAP.BASIS, k, exact=True))
        plan = CAP.best_plan(CAP.BASIS, k)[0]
        mid = len(values) // 2
        med = values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2
        assert (values[0], sum(values) / n, med, sum(1 for v in values if v > plan), len(values)) == (worst, mean, median, over, n)
        assert CAP.coin_value(CAP.BASIS, k) == mean                          # das Mittel aller Strategien ist der Wert der Münzwurf-Politik


# --- B6: Plan gegen Strategie, Basisfall ------------------------------------------------------------------------------------------------------------

def test_b6_plan_gegen_strategie_im_basisfall():
    table = {1: (50, 50, 0), 2: (115, 100, 15), 3: (F(745, 4), 150, F(145, 4)), 4: (F(515, 2), 200, F(115, 2)), 6: (400, 300, 100), 10: (685, 500, 185)}
    for k, (strat, plan, adapt) in table.items():
        sol = CAP.solve(CAP.BASIS, k)
        pv, choices = CAP.best_plan(CAP.BASIS, k)
        assert (sol.value, pv, sol.value - pv) == (strat, plan, adapt) and choices == ("G",) * k
    for k in range(1, 11):                                                    # Basisfall: gierig und „G nach hoch, K nach niedrig“ sind schon optimal
        value = CAP.solve(CAP.BASIS, k).value
        assert CAP.policy_value(CAP.BASIS, k, CAP.greedy_policy(CAP.BASIS)) == value
        assert CAP.policy_value(CAP.BASIS, k, CAP.reactive_policy) == value
    sol = CAP.solve(CAP.BASIS, 8)
    assert all(len(sol.best[t][s]) == 1 for t in range(8) for s in ((CAP.START,) if t == 0 else CAP.STATES))
    assert [CAP.coin_value(CAP.BASIS, k) for k in (1, 2, 3, 4, 6, 10)] == [40, F(135, 2), 95, F(245, 2), F(355, 2), F(575, 2)]
    assert [sol_k for sol_k in (CAP.solve(CAP.BASIS, 4).best[1][s][0] for s in CAP.STATES)] == [CAP.G, CAP.K, CAP.G, CAP.K]   # (G,hoch) (G,niedrig) (K,hoch) (K,niedrig): G nach hoch, K nach niedrig


# --- B7: Rollback gegen gierig -----------------------------------------------------------------------------------------------------------------------

def test_b7_rollback_gegen_gierig_im_raster():
    r = ev.greedy_raster()
    assert (r["n"], r["better"], r["equal"], r["worse"]) == (252, 29, 223, 0)
    assert all(g == 0 for (q, w, k), g in r["cells"].items() if q == F(3, 4) and w == 25)            # Basisfall: gierig = Rollback für k = 2, 3, 4, 6
    assert [ev.greedy_gap(F(3, 4), 75, k) for k in (3, 4, 6)] == [F(5, 4), 10, F(55, 2)]
    cap = _g(F(3, 4), 75)
    assert [CAP.solve(cap, k).value for k in (3, 4, 6)] == [F(605, 4), 210, F(655, 2)]
    assert [CAP.policy_value(cap, k, CAP.greedy_policy(cap)) for k in (3, 4, 6)] == [150, 200, 300]
    sol = CAP.solve(cap, 3)
    assert sol.best[1][(CAP.G, CAP.NIEDRIG)] == [CAP.K] and CAP.greedy_policy(cap)(1, CAP.G, CAP.NIEDRIG) == CAP.G     # die Wahl unterscheidet sich nach (G, niedrig)
    differ = [(s, t) for t in range(3) for s in ((CAP.START,) if t == 0 else CAP.STATES) if CAP.greedy_policy(cap)(t, *s) != sol.best[t][s][0]]
    assert differ == [((CAP.G, CAP.NIEDRIG), 1)]                                                       # an genau einem Zustand und einer Stufe


# --- B8: Wann nützt Anpassen --------------------------------------------------------------------------------------------------------------------------

def test_b8_wert_der_anpassung_im_raster_und_schwellen():
    r = ev.adaptation_raster()
    assert (r["n"], r["zero"], r["positive"], r["negative"]) == (120, 57, 63, 0)
    assert sum(1 for (q, w, k), v in r["cells"].items() if k == 1 and v == 0) == 15                    # 15 der 57 Nullen sind trivial (k = 1)
    assert all(v == 0 for (q, w, k), v in r["cells"].items() if q == F(1, 2))                           # q = 1/2: 24 Zellen
    assert sum(1 for (q, w, k) in r["cells"] if q == F(1, 2)) == 24
    assert all(r["cells"][(F(3, 5), w, k)] == 0 for w in (25, 50) for k in range(1, 9))
    assert all(r["cells"][(F(2, 3), 50, k)] == 0 for k in range(1, 9))
    assert [r["cells"][(F(3, 5), 0, k)] for k in range(1, 9)] == [0, 5, 10, 15, 20, 25, 30, 35]
    assert [float(ev.persistence_threshold(25, k)) for k in range(2, 7)] == pytest.approx([0.65, 0.6361, 0.6323, 0.6306, 0.6298], abs=1e-4)
    for w, q_star in ((0, F(17, 30)), (25, F(13, 20)), (50, F(11, 15))):
        assert F(170 + w, 300) == q_star                                                              # k = 2: q* = (170 + w)/300


# --- B9: Erwartungswert ist ein Mittel, kein Pfad ------------------------------------------------------------------------------------------------------

def test_b9_verteilung_der_gesamtauszahlung():
    cap = CAP.BASIS
    best2 = CAP.total_distribution(cap, 2, CAP.optimal_policy(cap, 2))
    assert best2 == {400: F(3, 8), 100: F(1, 8), -95: F(1, 2)}
    assert CAP.probability_below(best2, 60) == F(1, 2)
    assert CAP.probability_below(CAP.total_distribution(cap, 2, CAP.plan_policy(("G", "G"))), 60) == F(3, 8)
    for k, (below_s, below_g, zero_s, zero_g) in {4: (0.4375, 0.3984, 0.3672, 0.3984), 6: (0.3555, 0.4131, 0.0830, 0.2505)}.items():
        ds = CAP.total_distribution(cap, k, CAP.optimal_policy(cap, k))
        dg = CAP.total_distribution(cap, k, CAP.plan_policy(("G",) * k))
        safe = 30 * k
        assert (float(CAP.probability_below(ds, safe)), float(CAP.probability_below(dg, safe)), float(CAP.probability_below(ds, 0)), float(CAP.probability_below(dg, 0))) == pytest.approx(
            (below_s, below_g, zero_s, zero_g), abs=6e-5)
    # der Vergleich Strategie gegen „immer G“ (Anteil unter 30 k) wechselt mit k: 0 = gleich, + = Strategie höher, − = niedriger
    signs = []
    for k in range(1, 9):
        a = CAP.probability_below(CAP.total_distribution(cap, k, CAP.optimal_policy(cap, k)), 30 * k)
        b = CAP.probability_below(CAP.total_distribution(cap, k, CAP.plan_policy(("G",) * k)), 30 * k)
        signs.append((a > b) - (a < b))
    assert signs == [0, 1, 0, 1, -1, -1, -1, -1]
    d5s = CAP.total_distribution(cap, 5, CAP.optimal_policy(cap, 5))
    assert float(CAP.probability_below(d5s, 150)) == pytest.approx(0.3906, abs=6e-5)


# --- B10: Zählweisen -----------------------------------------------------------------------------------------------------------------------------

def test_b10_zaehlweisen():
    rows = {r["k"]: r for r in N.table_rows(range(1, 8))}
    assert [rows[k]["nodes"] for k in range(1, 8)] == [7, 31, 127, 511, 2047, 8191, 32767]
    assert [rows[k]["paths"] for k in (1, 2, 3, 4, 5)] == [4, 16, 64, 256, 1024] and [rows[k]["plans"] for k in (1, 2, 3, 4, 5)] == [2, 4, 8, 16, 32]
    assert [rows[k]["decision"] for k in (1, 2, 3, 4)] == [1, 5, 21, 85] and rows[3]["strategies_full_text"] == "2 097 152"
    assert [rows[k]["strategies_reduced_text"] for k in (1, 2, 3, 4)] == ["2", "8", "128", "32 768"] and rows[5]["strategies_reduced_text"] == "2 147 483 648"
    assert rows[4]["strategies_full_text"] == "3,9·10²⁵" and rows[5]["strategies_full_text"] == "4,5·10¹⁰²" and rows[7]["strategies_reduced_text"] == "1,7·10³⁸"
    assert N.n_strategies_reduced(2, 2, 7) == 2**127 and N.n_strategies_reduced(2, 2, 6) == 2**63
    assert N.first_k_over_page(100) == 3                                      # Konvention: 100 Knoten je Seite


# --- B11: Rechenaufwand: nur exakte Teile; Zeiten stehen in der Messdatei -----------------------------------------------------------------------------

def test_b11_zustandsrechnung_bis_k_300_und_wertzuwachs_je_stufe():
    v300, v299 = CAP.solve(CAP.BASIS, 300).value, CAP.solve(CAP.BASIS, 299).value
    assert v300 - v299 == F(285, 4) == F(71, 1) + F(1, 4)                     # 71,25 GE je Stufe
    assert N.n_nodes(2, 2, 300) == 2 * 4**300 - 1                              # so viele Knoten hätte der Baum
    assert np.isfinite(CAP.field_rollback(CAP.BASIS, 11)) and CAP.field_rollback(CAP.BASIS, 11) == pytest.approx(756.25, rel=1e-9)


def test_b11_zeiten_stehen_nur_in_der_messdatei():
    text = MESSUNG.read_text(encoding="utf-8")
    assert "GESAMT: 35 Prüfungen, 0 Fehler" in text and "Feldfassung" in text and "Byte je Knoten" in text
    assert "300 von 300" in text and "Bäume mit mehr als einer optimalen Strategie (Gleichstand): 12 von 300" in text


def test_messdatei_enthaelt_jede_zaehlung_der_readme_die_nicht_im_test_steht():
    text = MESSUNG.read_text(encoding="utf-8")
    assert text.count("in 100 von 100 Bäumen (k ≤ 3): OK") == 5
    assert "Rollback = Maximum der Aufzählung in 300 von 300 Bäumen (exakt, Brüche): OK" in text


def test_grenzen_der_regler_fuer_die_aufzaehlung():
    assert C.K4_MAX == 4 and N.n_strategies_reduced(2, 2, C.K4_MAX) == 32768 and N.n_strategies_reduced(2, 2, C.K4_MAX + 1) == 2147483648
    assert C.K5_MAX == 11 and N.n_nodes(2, 2, C.K5_MAX) == 8388607 and C.K_MAX == 10
