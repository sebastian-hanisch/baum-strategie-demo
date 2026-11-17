"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Aussagen, die für den Rollback gelten müssen, ohne dass man das richtige Ergebnis kennt.

Zufallsbäume mit festem Zufalls-Seed (ganzzahliger SplitMix64), exakt in Brüchen; im Kapazitätsfall feste Raster. Jede Eigenschaft ist eine belegte Aussage:
Skalieren und Verschieben der Auszahlungen, Umordnen der Wahlen, strikt dominierte oder zusätzliche Wahlen, Gesamtwahrscheinlichkeit der Pfade, und im
Kapazitätsfall: ein fester Plan ist selbst eine Strategie (der Wert der Anpassung ist nie negativ)."""

from fractions import Fraction as F

import bst_cap as CAP
import bst_rng as R
import bst_tree as T


def _random_trees(count, seed, kinds=((2, 2, 2), (2, 2, 3), (2, 3, 2), (3, 2, 2))):
    rng = R.SplitMix64(seed)
    for _ in range(count):
        d, b, k = kinds[rng.below(len(kinds))]
        yield d, b, k, T.random_tree(rng, d, b, k, "weit")


def test_auszahlungen_mal_drei_geben_wert_mal_drei_bei_gleicher_zahl_optimaler_strategien():
    for _d, _b, _k, tree in _random_trees(30, 1):
        v, n, _ = T.rollback(tree)
        v3, n3, _ = T.rollback(T.map_payoffs(tree, lambda x: x * 3))
        assert v3 == 3 * v and n3 == n


def test_auszahlung_je_stufe_plus_sieben_gibt_wert_plus_sieben_k():
    for _d, _b, k, tree in _random_trees(30, 2):
        v, n, _ = T.rollback(tree)
        v7, n7, _ = T.rollback(T.map_payoffs(tree, lambda x: x + 7))
        assert v7 == v + 7 * k and n7 == n


def test_umkehren_der_reihenfolge_der_wahlen_aendert_nichts():
    for _d, _b, _k, tree in _random_trees(30, 3):
        assert T.rollback(T.reverse_choices(tree))[:2] == T.rollback(tree)[:2]


def test_strikt_dominierte_zusatzwahl_aendert_nichts():
    for _d, _b, _k, tree in _random_trees(30, 4):
        assert T.rollback(T.add_dominated_choice(tree))[:2] == T.rollback(tree)[:2]


def test_zusatzwahl_an_der_wurzel_senkt_den_wert_nie():
    for _d, _b, _k, tree in _random_trees(30, 5):
        assert T.rollback(T.add_root_choice(tree))[0] >= T.rollback(tree)[0]


def _path_probability_sum(node):
    """Summe der Wahrscheinlichkeiten aller Pfade einer festen Strategie (erste Wahl überall): muss 1 sein."""
    if node is None:
        return F(1)
    _name, branches = node[0]
    return sum((p * _path_probability_sum(child) for p, _pay, child in branches), F(0))


def test_gesamtwahrscheinlichkeit_der_pfade_ist_eins():
    for _d, _b, _k, tree in _random_trees(30, 6):
        assert _path_probability_sum(tree) == 1
    for q, w in ((F(3, 4), 25), (F(1, 2), 0), (F(9, 10), 100)):
        assert _path_probability_sum(CAP.build_tree(CAP.make_cap(q=q, w=w), 4)) == 1


# --- Kapazitätsfall ------------------------------------------------------------------------------------------------------------------------------

GRID = [(F(qn, qd), w) for qn, qd in ((1, 2), (3, 5), (2, 3), (3, 4), (9, 10)) for w in (0, 25, 75, 200)]


def test_wert_der_anpassung_ist_nie_negativ_und_regeln_sind_nie_besser_als_der_rollback():
    for q, w in GRID:
        cap = CAP.make_cap(q=q, w=w)
        for k in range(1, 7):
            sol = CAP.solve(cap, k)
            assert CAP.adaptation_value(cap, k) >= 0
            assert sol.value >= CAP.policy_value(cap, k, CAP.greedy_policy(cap))
            assert sol.value >= CAP.policy_value(cap, k, CAP.reactive_policy)
            assert sol.value >= CAP.coin_value(cap, k)


def test_unabhaengige_perioden_q_gleich_einhalb_geben_wert_der_anpassung_null_fuer_jedes_w():
    for w in (0, 10, 25, 50, 100, 200):
        for k in range(1, 9):
            assert CAP.adaptation_value(CAP.make_cap(q=F(1, 2), w=w), k) == 0     # P1 = 1/2: jede Periode ist unabhängig und gleich verteilt


def test_sehr_hohe_wechselkosten_machen_den_plan_zur_strategie():
    for q in (F(1, 2), F(3, 4), F(9, 10)):
        for k in range(1, 6):
            assert CAP.adaptation_value(CAP.make_cap(q=q, w=10**6), k) == 0


def test_alle_auszahlungen_und_wechselkosten_mal_c_geben_wert_mal_c():
    for c in (F(2), F(1, 3), F(7)):
        for q, w in GRID[:8]:
            big = CAP.make_cap(gh=200 * c, gl=-100 * c, kk=30 * c, q=q, w=w * c)
            small = CAP.make_cap(q=q, w=w)
            for k in range(1, 5):
                assert CAP.solve(big, k).value == c * CAP.solve(small, k).value


def test_wert_waechst_mit_k_im_basisfall_und_feldfassung_stimmt():
    values = [CAP.solve(CAP.BASIS, k).value for k in range(1, 9)]
    assert all(b > a for a, b in zip(values, values[1:]))
    for k, v in enumerate(values, start=1):
        assert abs(CAP.field_rollback(CAP.BASIS, k) - float(v)) < 1e-9


def test_ohne_wechselkosten_haengt_die_wahl_nur_an_der_letzten_nachfrage():
    for q, _w in GRID:
        cap = CAP.make_cap(q=q, w=0)
        sol = CAP.solve(cap, 5)
        for t in range(1, 5):
            for d in CAP.DEMANDS:
                assert sol.best[t][(CAP.G, d)] == sol.best[t][(CAP.K, d)]
                assert sol.V[t][(CAP.G, d)] == sol.V[t][(CAP.K, d)]


def test_spiegelung_der_nachfrage_aendert_den_wert_nicht():
    """Vertauscht man hoch und niedrig (G zahlt −100 bei hoch, +200 bei niedrig; P(hoch) in Periode 1 = 1/2), bleibt der Wert gleich."""
    for q, w in GRID[:10]:
        a = CAP.make_cap(q=q, w=w)
        mirrored = CAP.Cap(gh=a.gl, gl=a.gh, kk=a.kk, q=a.q, w=a.w, p1=1 - a.p1)
        for k in range(1, 5):
            assert CAP.solve(mirrored, k).value == CAP.solve(a, k).value
