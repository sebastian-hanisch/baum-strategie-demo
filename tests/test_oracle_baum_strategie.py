"""Orakel-Tests (ORACLE-PLAYBOOK §5, §6): jede Kernroutine gegen einen anderen Rechenweg.

- Rollback (Objektbaum) gegen die **Aufzählung aller reduzierten Strategien** auf Zufallsbäumen (SplitMix64, ganzzahlig, Brüche) und im Kapazitätsfall bis k = 4.
- Rollback gegen die **Zustands-Rechnung** (Brüche, k = 1 bis 6), gegen den **Feldbaum** (numpy, 1e-9) und gegen ein **lineares Programm** (SciPy, HiGHS, Bänder 1e-6).
- Bester fester Plan: Rückwärtsrechnung gegen Aufzählung aller 2^k Pläne.
- Werte aller Strategien (vektorisiert) gegen die Bewertung jeder Strategie im Objektbaum; Mittel aller Strategien gegen die Münzwurf-Rechnung.
- Zahl der optimalen Strategien (Rollback-Zählung gegen Aufzählung), Knotenzahl und Besuche gegen den Durchlauf.

Plattform: Brüche exakt; Gleitkomma nur als Band. Zufall nur aus `bst_rng` (ganzzahliger SplitMix64)."""

import itertools
from fractions import Fraction as F

import numpy as np
import pytest

import bst_cap as CAP
import bst_count as N
import bst_rng as R
import bst_tree as T

PARAMS = [(F(3, 4), 25), (F(1, 2), 0), (F(3, 5), 25), (F(13, 20), 25), (F(4, 5), 75), (F(9, 10), 100), (F(2, 3), 10)]


# --- Zufallsbäume: Rollback gegen Aufzählung --------------------------------------------------------------------------------------------------

def _trees(count, seed):
    rng = R.SplitMix64(seed)
    kinds = [(2, 2, 1), (2, 2, 2), (2, 2, 3), (2, 3, 1), (2, 3, 2), (3, 2, 1), (3, 2, 2), (3, 3, 1), (2, 2, 3), (2, 3, 2)]
    for i in range(count):
        d, b, k = kinds[rng.below(len(kinds))]
        yield d, b, k, T.random_tree(rng, d, b, k, "weit" if i % 2 == 0 else "eng")


def test_rollback_gleich_maximum_der_aufzaehlung_auf_60_zufallsbaeumen():
    ties = 0
    for d, b, k, tree in _trees(60, 20261117):
        value, n_opt, _names = T.rollback(tree)
        values = T.enumerate_values(tree)
        assert max(values) == value
        assert T.count_optimal(values, value) == n_opt                       # Zahl optimaler Strategien: Rollback-Zählung gleich Aufzählung
        assert len(values) == N.n_strategies_reduced(d, b, k)
        assert T.check_counts(tree, d, b, k)
        ties += n_opt > 1
    assert ties > 0                                                           # Gleichstände kommen vor: der Zählzweig wird wirklich benutzt


def test_besuche_der_aufzaehlung_sind_strategien_mal_knoten_je_strategie():
    for d, b, k, tree in _trees(20, 99):
        counter = T.Counter()
        values = T.enumerate_values(tree, counter)
        assert counter.visits == len(values) * N.nodes_per_strategy(d, b, k) == N.visits_enumeration(d, b, k)


# --- Kapazitätsfall: drei Umsetzungen und ein lineares Programm --------------------------------------------------------------------------------

@pytest.mark.parametrize("q,w", PARAMS)
def test_objektbaum_gleich_zustands_rechnung_gleich_feldbaum(q, w):
    cap = CAP.make_cap(q=q, w=w)
    for k in range(1, 6):
        value = CAP.solve(cap, k).value
        assert CAP.tree_rollback_value(cap, k) == value                       # exakt, Brüche
        assert CAP.field_rollback(cap, k) == pytest.approx(float(value), rel=1e-9, abs=1e-9)


def test_basisfall_werte_k_1_bis_10_gegen_zustands_rechnung():
    expected = [50, 115, F(745, 4), F(515, 2), F(1315, 4), 400, F(1885, 4), F(1085, 2), F(2455, 4), 685]
    for k, e in enumerate(expected, start=1):
        assert CAP.solve(CAP.BASIS, k).value == e
    assert CAP.field_rollback(CAP.BASIS, 10) == pytest.approx(685.0, rel=1e-12)


def _linear_program_value(cap, k):
    """Rückwärtsrechnung als lineares Programm: minimiere Σ V_t(s) unter V_t(s) ≥ Erwartungswert(a) + Fortsetzung(a) für jede Wahl (SciPy, HiGHS)."""
    linprog = pytest.importorskip("scipy.optimize").linprog
    index = {}
    for t in range(k):
        for s in ((CAP.START,) if t == 0 else CAP.STATES):
            index[(t, s)] = len(index)
    n = len(index)
    rows, rhs = [], []
    for (t, s), i in index.items():
        a_prev, d_prev = s
        p = float(CAP.p_hoch(cap, t, d_prev))
        for a in CAP.ACTIONS:
            row = np.zeros(n)
            row[i] -= 1.0
            if t + 1 < k:
                row[index[(t + 1, (a, CAP.HOCH))]] += p
                row[index[(t + 1, (a, CAP.NIEDRIG))]] += 1 - p
            rows.append(row)
            rhs.append(-float(CAP.ew_period(cap, a, CAP.p_hoch(cap, t, d_prev)) - CAP.switch_cost(cap, a_prev, a)))
    res = linprog(np.ones(n), A_ub=np.array(rows), b_ub=np.array(rhs), bounds=[(None, None)] * n, method="highs")
    assert res.status == 0
    return res.x[index[(0, CAP.START)]]


@pytest.mark.parametrize("q,w", PARAMS)
def test_wert_gegen_lineares_programm(q, w):
    cap = CAP.make_cap(q=q, w=w)
    for k in (1, 2, 3, 5):
        assert _linear_program_value(cap, k) == pytest.approx(float(CAP.solve(cap, k).value), rel=1e-6, abs=1e-6)


# --- feste Pläne -------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("q,w", PARAMS)
def test_bester_plan_rueckwaerts_gleich_aufzaehlung(q, w):
    cap = CAP.make_cap(q=q, w=w)
    for k in range(1, 8):
        assert CAP.best_plan(cap, k) == CAP.best_plan_enumeration(cap, k)    # Wert und (G zuerst bei Gleichstand) auch der Plan


def test_plan_werte_gegen_unabhaengige_markov_kette():
    """Planwert über die Übergangsmatrix der Nachfrage (Matrixpotenzen), nicht über die Randverteilungs-Rekursion."""
    q = 0.7
    cap = CAP.make_cap(q=F(7, 10), w=25)
    P = np.array([[q, 1 - q], [1 - q, q]])
    start = np.array([0.5, 0.5])
    for plan in itertools.product(CAP.ACTIONS, repeat=4):
        total = 0.0
        for t, a in enumerate(plan):
            dist = start @ np.linalg.matrix_power(P, t)
            pay = dist[0] * float(CAP.payoff(cap, a, CAP.HOCH)) + dist[1] * float(CAP.payoff(cap, a, CAP.NIEDRIG))
            total += pay - (25.0 if t > 0 and a != plan[t - 1] else 0.0)
        assert CAP.plan_value(cap, plan) == pytest.approx(total, rel=1e-12)


# --- alle Strategien -----------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("q,w", PARAMS[:4])
def test_vektorisierte_strategiewerte_gleich_bewertung_im_objektbaum(q, w):
    cap = CAP.make_cap(q=q, w=w)
    for k in (1, 2, 3):
        tree = CAP.build_tree(cap, k)
        enumerated = sorted(T.enumerate_values(tree))
        vectorized = sorted(CAP.strategy_values(cap, k, exact=True))
        assert vectorized == enumerated
        assert np.allclose(sorted(CAP.strategy_values(cap, k)), [float(x) for x in enumerated], rtol=1e-12, atol=1e-9)


def test_k_4_alle_32768_strategien_im_basisfall():
    cap = CAP.BASIS
    tree = CAP.build_tree(cap, 4)
    counter = T.Counter()
    enumerated = T.enumerate_values(tree, counter)
    assert counter.visits == 1507328 == N.visits_enumeration(2, 2, 4)
    assert sorted(enumerated) == sorted(CAP.strategy_values(cap, 4, exact=True))
    assert len(enumerated) == 32768 and max(enumerated) == F(515, 2) == T.rollback(tree)[0]
    assert T.count_optimal(enumerated, F(515, 2)) == 1 == T.rollback(tree)[1]


@pytest.mark.parametrize("q,w", PARAMS)
def test_mittel_aller_strategien_gleich_muenzwurf_politik(q, w):
    cap = CAP.make_cap(q=q, w=w)
    for k in range(1, 5):
        values = CAP.strategy_values(cap, k, exact=True)
        assert sum(values) / len(values) == CAP.coin_value(cap, k)


@pytest.mark.parametrize("q,w", PARAMS[:3])
def test_politikwerte_gleich_erwartungswert_der_verteilung(q, w):
    cap = CAP.make_cap(q=q, w=w)
    for k in range(1, 6):
        sol = CAP.solve(cap, k)
        for policy in (CAP.optimal_policy(cap, k, sol), CAP.greedy_policy(cap), CAP.reactive_policy):
            dist = CAP.total_distribution(cap, k, policy)
            assert sum(dist.values()) == 1
            assert sum(v * p for v, p in dist.items()) == CAP.policy_value(cap, k, policy)
        best = CAP.total_distribution(cap, k, CAP.optimal_policy(cap, k, sol))
        assert sum(v * p for v, p in best.items()) == sol.value


def test_zufaellige_strategien_sind_strategien_und_ihr_mittel_stimmt():
    cap = CAP.BASIS
    values = CAP.strategy_values(cap, 3, exact=True)
    allowed = set(values)
    rng = R.SplitMix64(1234)
    draws = []
    for _ in range(600):
        strategy = CAP.random_strategy(cap, 3, rng)
        v = CAP.strategy_value(cap, 3, strategy)
        assert v in allowed
        draws.append(float(v))
    std = float(np.std([float(x) for x in values]))
    assert abs(np.mean(draws) - float(CAP.coin_value(cap, 3))) < 4 * std / np.sqrt(len(draws))   # Gleichverteilung über alle 128 Strategien: Mittel im Band


def test_gewaehlte_strategie_ist_bei_gleichstand_eine_von_zwei():
    cap = CAP.make_cap(q=F(13, 20))
    sol = CAP.solve(cap, 2)
    values = CAP.strategy_values(cap, 2, exact=True)
    assert sum(1 for v in values if v == sol.value) == sol.n_optimal == 2
