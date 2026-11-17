"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): k = 0 und k = 1, Gleichstände, P(hoch) = 0 und 1, sehr große Wechselkosten,
doppelte Wahlen, Bäume nur mit Ereignisknoten (d = 1) und nur mit Entscheidungsknoten (b = 1)."""

from fractions import Fraction as F

import numpy as np
import pytest

import bst_cap as CAP
import bst_count as N
import bst_evaluation as ev
import bst_tree as T


def test_k_0_hat_keinen_knoten_ausser_dem_endknoten_und_den_wert_null(basis):
    assert CAP.build_tree(basis, 0) is None
    assert CAP.solve(basis, 0).value == 0 and CAP.best_plan(basis, 0) == (0, ()) and CAP.field_rollback(basis, 0) == 0.0
    assert list(CAP.strategy_values(basis, 0)) == [0.0] and CAP.coin_value(basis, 0) == 0
    assert T.count_nodes(None) == (0, 0, 1) and N.n_nodes(2, 2, 0) == 1


def test_k_1_hat_nur_den_start_und_keine_stufe_zwei(basis):
    sol = CAP.solve(basis, 1)
    assert sol.value == 50 and list(sol.q_values[0]) == [CAP.START] and sol.n_optimal == 1
    a = ev.analyse_hand(ev.Settings(k2=1, step=2))
    assert a["rows"] == [] and a["root_best"] == [CAP.G]
    assert CAP.best_plan(basis, 1) == (50, ("G",)) and CAP.adaptation_value(basis, 1) == 0


def test_gleichstand_bei_der_schwelle_ist_ein_gleichstand_und_keine_wahl():
    cap = CAP.make_cap()
    p_star = CAP.threshold(cap)
    assert CAP.choice_by_expectation(cap, p_star) is None
    assert CAP.choice_by_expectation(cap, p_star + F(1, 1000)) == CAP.G and CAP.choice_by_expectation(cap, p_star - F(1, 1000)) == CAP.K
    a = ev.analyse_one(ev.Settings(p=50, kk=50))                              # p* = 1/2: EW(G) = EW(K) = 50 und die Modalregel hat keinen wahrscheinlicheren Ausgang
    assert a["ew_g"] == a["ew_k"] == 50 and a["p_star"] == F(1, 2)
    assert ev.verdict_one(a)[0] == "info" and "Gleichstand" in ev.verdict_one(a)[1]


def test_p_gleich_null_und_eins_lassen_den_knoten_stehen_und_der_wert_ist_definiert():
    for p, expected in ((0, 30), (1, 200)):                                   # G zahlt bei p = 0 nur −100, bei p = 1 nur +200
        cap = CAP.make_cap(p1=F(p))
        tree = CAP.build_tree(cap, 1)
        assert T.count_nodes(tree) == (1, 2, 4)                               # der Ast mit Wahrscheinlichkeit 0 bleibt im Baum
        assert T.rollback(tree)[0] == expected
        assert CAP.solve(cap, 1).value == expected


def test_sehr_grosse_wechselkosten_wechseln_nie():
    cap = CAP.make_cap(w=10**9)
    sol = CAP.solve(cap, 5)
    assert all(sol.best[t][s] == [s[0]] for t in range(1, 5) for s in CAP.STATES)   # nach G bleibt G, nach K bleibt K
    assert sol.value == CAP.best_plan(cap, 5)[0]


def test_wechselkosten_null_ohne_persistenz_haengen_die_wahl_nicht_an_der_beobachtung(basis):
    cap = CAP.make_cap(q=F(1, 2), w=0)
    sol = CAP.solve(cap, 4)
    assert all(sol.best[t][s] == [CAP.G] for t in range(1, 4) for s in CAP.STATES)     # EW(G) = 50 > 30 in jedem Zustand


def test_doppelte_wahlen_mit_gleichen_auszahlungen_verdoppeln_die_optimalen_strategien():
    tree = (("A", ((F(1, 2), 1, None), (F(1, 2), 3, None))), ("A2", ((F(1, 2), 1, None), (F(1, 2), 3, None))))
    value, n_opt, names = T.rollback(tree)
    assert (value, n_opt, names) == (2, 2, ["A", "A2"])
    assert sorted(T.enumerate_values(tree)) == [2, 2]


def test_baum_nur_mit_ereignisknoten_d_gleich_1_ist_der_mittelwert_ueber_alle_pfade():
    tree = (("nur", ((F(1, 2), 4, (("a", ((F(1, 4), 8, None), (F(3, 4), 0, None))),)), (F(1, 2), -2, (("a", ((F(1, 1), 10, None),)),)))),)
    # Pfade: 1/2 (4 + 1/4 · 8 + 3/4 · 0) + 1/2 (−2 + 10) = 1/2 · 6 + 1/2 · 8 = 7
    assert T.rollback(tree) == (7, 1, ["nur"]) and T.enumerate_values(tree) == [7]
    assert N.n_strategies_reduced(1, 2, 3) == 1 and N.n_nodes(1, 2, 2) == 2 * (1 + 2) + 4 == 10


def test_baum_nur_mit_entscheidungsknoten_b_gleich_1_ist_eine_folge_von_wahlen():
    tree = (("x", ((F(1), 5, (("y", ((F(1), 1, None),)), ("z", ((F(1), 9, None),)))),)), ("w", ((F(1), 20, (("y", ((F(1), -1, None),)),)),)))
    # x dann y: 5 + 1 = 6; x dann z: 5 + 9 = 14; w dann y: 20 − 1 = 19
    assert T.rollback(tree) == (19, 1, ["w"]) and sorted(T.enumerate_values(tree)) == [6, 14, 19]
    assert N.n_strategies_reduced(2, 1, 1) == 2 and N.n_nodes(2, 1, 1) == 3 + 2 == 5


def test_feldfassung_und_objektbaum_bei_extremen_reglern():
    for gh, gl, kk in ((100, -200, 100), (300, 0, 0), (300, -200, 100)):
        cap = CAP.make_cap(gh=gh, gl=gl, kk=kk)
        for k in (1, 2, 3):
            assert CAP.field_rollback(cap, k) == pytest.approx(float(CAP.solve(cap, k).value), abs=1e-9)
    assert np.isfinite(CAP.field_rollback(CAP.make_cap(q=F(19, 20), w=200), 6))
