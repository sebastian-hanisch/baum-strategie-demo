"""Handbeispiele in Brüchen (DEMO-PLAYBOOK §1b): jede Einheit gegen eine von Hand gerechnete Mini-Instanz. Alle Erwartungswerte stehen als Rechnung im Test.

Kapazitätsfall (ausgedacht, ein Modell): G +200/−100, K +30, P(hoch) = 1/2 in Periode 1, danach bleibt die Nachfrage mit q = 3/4 wie in der Vorperiode,
Wechselkosten w = 25 (nicht in Periode 1). Exakt verglichen wird nur, was in Brüchen gerechnet ist."""

import itertools
from fractions import Fraction as F

import bst_cap as CAP
import bst_count as N
import bst_tree as T

# --- eine Periode ---------------------------------------------------------------------------------------------------------------------------

def test_eine_periode_erwartungswerte_und_schwelle(basis):
    assert CAP.ew_period(basis, CAP.G, F(1, 2)) == F(1, 2) * 200 + F(1, 2) * (-100) == 50
    assert CAP.ew_period(basis, CAP.K, F(1, 2)) == 30
    assert CAP.threshold(basis) == F(30 + 100, 200 + 100) == F(13, 30)
    assert CAP.ew_period(basis, CAP.G, F(13, 30)) == 30                       # bei p* sind beide Wahlen gleich gut
    assert CAP.choice_by_expectation(basis, F(13, 30)) is None                # Gleichstand ist ein Gleichstand, keine Wahl


def test_modalregel_verliert_bei_p_045_fuenf_ge(basis):
    p = F(9, 20)
    assert CAP.ew_period(basis, CAP.G, p) == F(9, 20) * 200 + F(11, 20) * (-100) == 35
    assert CAP.choice_by_expectation(basis, p) == CAP.G and CAP.choice_by_modal_outcome(basis, p) == CAP.K
    assert CAP.one_period_loss(basis, p) == 35 - 30 == 5
    p2 = F(499, 1000)                                                         # EW(G) = 300 · 0,499 − 100 = 49,7; Verlust 49,7 − 30
    assert CAP.one_period_loss(basis, p2) == F(497, 10) - 30 == F(197, 10)


def test_modalregel_verlust_bei_p_knapp_unter_einhalb(basis):
    p = F(149, 300)
    assert CAP.ew_period(basis, CAP.G, p) == 300 * F(149, 300) - 100 == 49
    assert CAP.one_period_loss(basis, p) == 49 - 30 == 19


def test_raster_19_von_300_punkten(basis):
    r = CAP.rule_comparison_raster(basis)
    assert r["different"] == list(range(131, 150)) and r["points"] == 300 and r["worst_loss"] == 19 and r["worst_j"] == 149


# --- zwei Perioden, 31 Knoten ----------------------------------------------------------------------------------------------------------------

def test_zwei_perioden_von_hand_stufe_zwei(basis):
    sol = CAP.solve(basis, 2)
    q = sol.q_values[1]
    assert (q[(CAP.G, CAP.HOCH)][CAP.G], q[(CAP.G, CAP.HOCH)][CAP.K]) == (F(3, 4) * 200 - F(1, 4) * 100 - 0, 30 - 25) == (125, 5)
    assert (q[(CAP.G, CAP.NIEDRIG)][CAP.G], q[(CAP.G, CAP.NIEDRIG)][CAP.K]) == (F(1, 4) * 200 - F(3, 4) * 100, 5) == (-25, 5)
    assert (q[(CAP.K, CAP.HOCH)][CAP.G], q[(CAP.K, CAP.HOCH)][CAP.K]) == (125 - 25, 30) == (100, 30)
    assert (q[(CAP.K, CAP.NIEDRIG)][CAP.G], q[(CAP.K, CAP.NIEDRIG)][CAP.K]) == (-25 - 25, 30) == (-50, 30)
    assert [sol.V[1][s] for s in ((CAP.G, CAP.HOCH), (CAP.G, CAP.NIEDRIG), (CAP.K, CAP.HOCH), (CAP.K, CAP.NIEDRIG))] == [125, 5, 100, 30]


def test_zwei_perioden_wurzel_115_gegen_95(basis):
    sol = CAP.solve(basis, 2)
    assert sol.q_values[0][CAP.START] == {CAP.G: 50 + F(1, 2) * 125 + F(1, 2) * 5, CAP.K: 30 + F(1, 2) * 100 + F(1, 2) * 30}
    assert sol.value == 115 and sol.q_values[0][CAP.START][CAP.K] == 95
    assert sol.best[0][CAP.START] == [CAP.G] and sol.n_optimal == 1
    assert sol.best[1][(CAP.G, CAP.HOCH)] == [CAP.G] and sol.best[1][(CAP.G, CAP.NIEDRIG)] == [CAP.K]    # nach niedrig wechselt die Strategie zu K


def test_alle_acht_strategien_bei_k_2(basis):
    values = CAP.strategy_values(basis, 2, exact=True)
    assert sorted(values) == [20, 40, 55, 55, 60, 95, 100, 115]
    assert sum(values) / 8 == F(135, 2)                                      # Mittel 540/8
    assert N.n_strategies_reduced(2, 2, 2) == len(values) == 8
    assert CAP.coin_value(basis, 2) == F(135, 2)


def test_feste_plaene_und_wert_der_anpassung_bei_k_2(basis):
    assert F(1, 2) * F(3, 4) + F(1, 2) * F(1, 4) == F(1, 2)                  # die Randwahrscheinlichkeit der Nachfrage bleibt 1/2
    plaene = {p: CAP.plan_value(basis, p) for p in itertools.product("GK", repeat=2)}
    assert plaene == {("G", "G"): 100, ("G", "K"): 55, ("K", "G"): 55, ("K", "K"): 60}
    assert CAP.best_plan(basis, 2) == (100, ("G", "G")) and CAP.adaptation_value(basis, 2) == 15
    assert sum(1 for v in CAP.strategy_values(basis, 2, exact=True) if v > 100) == 1


def test_schwelle_der_persistenz_bei_k_2():
    # nach (G, niedrig) wählt man K genau dann, wenn 30 − w > 200 − 300 q, also q > (170 + w)/300
    assert F(170 + 25, 300) == F(13, 20)
    cap = CAP.make_cap(q=F(13, 20))
    assert cap.q * 300 == 195 and 200 - 300 * cap.q == 5 == 30 - 25            # genau ein Gleichstand
    sol = CAP.solve(cap, 2)
    assert sol.best[1][(CAP.G, CAP.NIEDRIG)] == [CAP.G, CAP.K] and sol.n_optimal == 2
    assert CAP.adaptation_value(cap, 2) == 0
    assert CAP.adaptation_value(CAP.make_cap(q=F(13, 20) + F(1, 1000)), 2) > 0
    assert CAP.adaptation_value(CAP.make_cap(q=F(13, 20) - F(1, 1000)), 2) == 0
    assert CAP.ew_period(CAP.BASIS, CAP.G, 1 - F(3, 5)) == 200 - 300 * F(3, 5) == 20   # bei q = 3/5 ist EW(G) nach (G, niedrig) 20 > 5: die Anpassung lohnt nicht


def test_verteilung_der_besten_strategie_bei_k_2(basis):
    dist = CAP.total_distribution(basis, 2, CAP.optimal_policy(basis, 2))
    assert dist == {400: F(3, 8), 100: F(1, 8), -95: F(1, 2)}                # −95 = −100 + 30 − 25
    assert sum(v * p for v, p in dist.items()) == 115
    immer_g = CAP.total_distribution(basis, 2, CAP.plan_policy(("G", "G")))
    assert immer_g == {400: F(3, 8), 100: F(1, 4), -200: F(3, 8)}
    assert CAP.probability_below(dist, 60) == F(1, 2) and CAP.probability_below(immer_g, 60) == F(3, 8)


# --- Zählen ----------------------------------------------------------------------------------------------------------------------------------

def test_zaehlweisen_von_hand():
    assert [N.n_nodes(2, 2, k) for k in (1, 2, 3, 4)] == [7, 31, 127, 511]
    assert [N.n_strategies_reduced(2, 2, k) for k in (1, 2, 3, 4, 5)] == [2, 8, 128, 32768, 2**31]
    assert [N.n_decision(2, 2, k) for k in (1, 2, 3, 4)] == [1, 5, 21, 85]
    assert [N.n_paths(2, 2, k) for k in (1, 2, 3)] == [4, 16, 64] and [N.n_plans(2, k) for k in (1, 2, 3, 4)] == [2, 4, 8, 16]
    assert (N.n_decision(2, 2, 2), N.n_events(2, 2, 2), N.n_end(2, 2, 2)) == (5, 10, 16)
    assert N.n_strategies_full_exponent(2, 2, 3) == 21 and 2**21 == 2097152 and N.n_strategies_full_exponent(2, 2, 4) == 85
    assert N.n_strategies_reduced(2, 3, 3) == 8192 and N.n_nodes(2, 3, 3) == 3 * (1 + 6 + 36) + 216 == 345
    assert N.nodes_per_strategy(2, 2, 2) == 10 and N.visits_enumeration(2, 2, 2) == 8 * 10 == 80
    assert N.visits_enumeration(2, 2, 4) == 32768 * 46 == 1507328


def test_schreibweise_der_zahlen():
    assert N.ints(2816) == "2816" and N.ints(32768) == "32 768" and N.ints(1507328) == "1 507 328" and N.ints(-12345) == "−12 345"
    assert N.power_text(2, 31) == "2 147 483 648" and N.power_text(2, 85) == "3,9·10²⁵" and N.power_text(2, 127) == "1,7·10³⁸"
    assert N.first_k_over_page(100) == 3 and N.first_k_over_page(31) == 3 and N.first_k_over_page(30) == 2   # 31 Knoten passen noch auf eine Seite von 31


# --- Objektbaum an der Mini-Instanz -----------------------------------------------------------------------------------------------------------

def test_mini_baum_rollback_aufzaehlung_und_zaehlung(mini_tree):
    # Stufe 2: max(0, 4) = 4; A: 1/2 (10 + 4) + 1/2 (−2 + 4) = 8; B: 3 + 4 = 7
    assert T.rollback(mini_tree) == (8, 1, ["A"])
    assert T.count_nodes(mini_tree) == (4, 8, 6)
    assert sorted(T.enumerate_values(mini_tree)) == [3, 4, 6, 6, 7, 8]
    counter = T.Counter()
    T.rollback(mini_tree, counter=counter)
    assert counter.visits == 18
    counter = T.Counter()
    T.enumerate_values(mini_tree, counter)
    assert counter.visits == 4 * 8 + 2 * 5 == 42                              # A-Strategien 8 Knoten, B-Strategien 5 Knoten


def test_objektbaum_k_2_hat_31_knoten_und_wert_115(basis):
    tree = CAP.build_tree(basis, 2)
    assert T.count_nodes(tree) == (5, 10, 16)
    assert T.rollback(tree) == (115, 1, ["G"])


def test_rng_splitmix64_referenzwerte():
    import bst_rng as R
    g = R.SplitMix64(0)
    assert [g.next_u64() for _ in range(3)] == [16294208416658607535, 7960286522194355700, 487617019471545679]   # Referenzfolge von SplitMix64 mit Seed 0
    assert R.SplitMix64(7).below(10) == R.SplitMix64(7).below(10)
