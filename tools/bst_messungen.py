"""Messskript: erzeugt `data/bst_messung.txt`, die Messungen, auf die sich die README beruft (Befunde B1 bis B12).

Aufruf (Wurzelordner des Repos): python tools/bst_messungen.py [--out data/bst_messung.txt]

Gerechnet wird in Brüchen (`fractions`), Zufall nur aus dem ganzzahligen SplitMix64 (`bst_rng`). Zeiten und Speicher sind eine CPU, ein Lauf, Größenordnung;
sie stehen in der Messdatei und in keinem Test. Die übrigen Zahlen prüft `tests/test_claims.py` (Zählungen exakt, Neu-Rechnungen als Band).
Laufzeit rund eine Minute (die 300 Zufallsbäume machen den Hauptteil aus)."""

import argparse
import sys
import time
import tracemalloc
from fractions import Fraction as F
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import bst_cap as CAP  # noqa: E402
import bst_constants as C  # noqa: E402
import bst_count as N  # noqa: E402
import bst_evaluation as ev  # noqa: E402
import bst_rng as R  # noqa: E402
import bst_tree as T  # noqa: E402

LINES: list[str] = []
CHECKS = [0, 0]   # Prüfungen, Fehler


def out(text=""):
    LINES.append(text)


def check(name, ok):
    CHECKS[0] += 1
    if not ok:
        CHECKS[1] += 1
    out(f"  [Prüfung] {name}: {'OK' if ok else 'FEHLER'}")


def head(text):
    out()
    out("=" * 100)
    out(text)
    out("=" * 100)


def fs(x):
    x = F(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def abschnitt_a():
    head("A: eine Periode (Kapazitätsfall: G +200/−100, K +30)")
    cap = CAP.BASIS
    check("EW(G) bei p = 1/2 ist 50, EW(K) ist 30", (CAP.ew_period(cap, CAP.G, F(1, 2)), CAP.ew_period(cap, CAP.K, F(1, 2))) == (50, 30))
    out(f"  Schwelle p* = {fs(CAP.threshold(cap))} = {float(CAP.threshold(cap)):.5f}")
    r = CAP.rule_comparison_raster(cap)
    out(f"  Raster p = j/300 (ohne p = 1/2): verschieden gewählt in {len(r['different'])} von {r['points']} Punkten (j = {r['different'][0]} bis {r['different'][-1]}); größter Verlust der Modalregel {fs(r['worst_loss'])} GE (j = {r['worst_j']})")
    out(f"  Verlust bei p = 0,45: {fs(CAP.one_period_loss(cap, F(9, 20)))} GE (EW(G) = {fs(CAP.ew_period(cap, CAP.G, F(9, 20)))})")


def abschnitt_b():
    head("B: Basisfall (q = 3/4, w = 25): Strategie, Plan, gierig, reaktiv, Münzwurf (Zähleinheit GE im Erwartungswert)")
    cap = CAP.BASIS
    out("  k   Strategie    bester Plan        Anpassung   gierig   reaktiv   Münzwurf")
    for k in list(range(1, 11)):
        sol = CAP.solve(cap, k)
        pv, plan = CAP.best_plan(cap, k)
        g = CAP.policy_value(cap, k, CAP.greedy_policy(cap))
        rv = CAP.policy_value(cap, k, CAP.reactive_policy)
        out(f"  {k:<3} {fs(sol.value):>9}   {fs(pv):>8} ({''.join(plan)})   {fs(sol.value - pv):>9}   {fs(g):>8} {fs(rv):>8}   {fs(CAP.coin_value(cap, k)):>8}   optimale Strategien: {sol.n_optimal}")
        check(f"k = {k}: Strategie ≥ Plan, ≥ gierig, ≥ reaktiv, ≥ Münzwurf", sol.value >= pv and sol.value >= g and sol.value >= rv and sol.value >= CAP.coin_value(cap, k))
    out()
    out("  Aufzählung aller reduzierten Strategien (vektorisiert, exakt), k = 1 bis 4:")
    for k in range(1, 5):
        values = CAP.strategy_values(cap, k, exact=True)
        sv = sorted(values)
        top = sol_top = CAP.solve(cap, k).value
        plan_v = CAP.best_plan(cap, k)[0]
        mid = len(sv) // 2
        median = sv[mid] if len(sv) % 2 else (sv[mid - 1] + sv[mid]) / 2
        out(f"  k = {k}: {len(sv)} Strategien; Rollback {fs(top)}; schlechteste {fs(sv[0])}; Mittel {fs(sum(sv) / len(sv))}; Median {fs(median)}; über dem besten Plan ({fs(plan_v)}): "
            f"{sum(1 for v in sv if v > plan_v)}; optimal: {sum(1 for v in sv if v == sol_top)}; Besuche Rollback {N.visits_rollback(2, 2, k)}, Aufzählung {N.visits_enumeration(2, 2, k)}")
        check(f"k = {k}: Maximum der Aufzählung = Rollback", max(sv) == sol_top)
    out()
    out("  Zählweisen (Formeln):")
    for row in N.table_rows(range(1, 8)):
        out(f"  k = {row['k']}: Knoten {row['nodes']}, Pfade {row['paths']}, Pläne {row['plans']}, Strategien reduziert {row['strategies_reduced_text']}, nicht reduziert {row['strategies_full_text']}")


def abschnitt_c():
    head("C: Rollback gegen gierig (252 Zellen), Wert der Anpassung (120 Zellen), Schwellen der Persistenz")
    gr = ev.greedy_raster()
    out(f"  Raster q × w × k = {len(C.RASTER_Q)} × {len(C.RASTER_W)} × {len(C.RASTER_K)} = {gr['n']} Zellen: Rollback besser in {gr['better']}, gleich in {gr['equal']}, schlechter in {gr['worse']}")
    check("gierig nie besser als Rollback", gr["worse"] == 0)
    for k in (3, 4, 6):
        cap = CAP.make_cap(q=F(3, 4), w=75)
        out(f"  q = 3/4, w = 75, k = {k}: Rollback {fs(CAP.solve(cap, k).value)}, gierig {fs(CAP.policy_value(cap, k, CAP.greedy_policy(cap)))}, Abstand {fs(ev.greedy_gap(F(3, 4), 75, k))}")
    ar = ev.adaptation_raster()
    out(f"  Wert der Anpassung, Raster q × w × k = 5 × 3 × 8 = {ar['n']} Zellen: Wert 0 in {ar['zero']}, größer 0 in {ar['positive']}, negativ in {ar['negative']}")
    check("Wert der Anpassung nie negativ", ar["negative"] == 0)
    out("  Schwelle der Persistenz bei w = 25 (kleinstes q mit Wert der Anpassung > 0; Bisektion in Brüchen; Raster 1/100 ab dort monoton geprüft):")
    for k in range(2, 7):
        q_star = ev.persistence_threshold(25, k)
        grid_ok = all(CAP.adaptation_value(CAP.make_cap(q=F(j, 100), w=25), k) > 0 for j in range(int(q_star * 100) + 1, 100))
        out(f"    k = {k}: q* ≈ {float(q_star):.6f}; Raster 1/100 oberhalb von q* durchgehend > 0: {grid_ok}")
        check(f"k = {k}: Anpassung oberhalb der Schwelle auf dem Raster 1/100 immer positiv", grid_ok)


def abschnitt_d():
    head("D: Verteilung der Gesamtauszahlung (Erwartungswert ist ein Mittel, kein Pfad), Basisfall")
    cap = CAP.BASIS
    out("  k   Politik     Erwartungswert   kleinster   größter   P(Gesamt < 30 k, „immer K“)   P(Gesamt < 0)")
    for k in range(1, 9):
        sol = CAP.solve(cap, k)
        safe = 30 * k
        for name, policy in (("Strategie", CAP.optimal_policy(cap, k, sol)), ("immer G", CAP.plan_policy(("G",) * k))):
            dist = CAP.total_distribution(cap, k, policy)
            out(f"  {k:<3} {name:<10} {fs(sum(v * p for v, p in dist.items())):>12} {fs(min(dist)):>10} {fs(max(dist)):>9}   {float(CAP.probability_below(dist, safe)):>10.4f}   {float(CAP.probability_below(dist, 0)):>14.4f}")


def abschnitt_e():
    head("E: Zufallsbäume (Orakel): Rollback gegen Aufzählung; Eigenschaften (Zufall: ganzzahliger SplitMix64, Zufalls-Seed 20261117)")
    rng = R.SplitMix64(20261117)
    kinds = [(2, 2, 1), (2, 2, 2), (2, 2, 3), (2, 2, 4), (2, 3, 1), (2, 3, 2), (2, 3, 3), (3, 2, 1), (3, 2, 2), (3, 2, 3), (3, 3, 1), (3, 3, 2)]
    n44 = 0
    bad_value = bad_count = bad_nstrat = bad_nodes = ties = 0
    t0 = time.perf_counter()
    for i in range(300):
        while True:
            d, b, k = kinds[rng.below(len(kinds))]
            if (d, b, k) == (2, 2, 4):
                if n44 >= 12:
                    continue
                n44 += 1
            break
        tree = T.random_tree(rng, d, b, k, "weit" if i % 2 == 0 else "eng")
        value, n_opt, _ = T.rollback(tree)
        values = T.enumerate_values(tree)
        bad_value += max(values) != value
        bad_count += T.count_optimal(values, value) != n_opt
        bad_nstrat += len(values) != N.n_strategies_reduced(d, b, k)
        bad_nodes += not T.check_counts(tree, d, b, k)
        ties += n_opt > 1
    out(f"  300 Zufallsbäume (d Wahlen, b Ausgänge, k Stufen; ganzzahlige Auszahlungen; gerade Nummern in [−30, 60], ungerade in [0, 3]), Zeit {time.perf_counter() - t0:.1f} s")
    check("Rollback = Maximum der Aufzählung in 300 von 300 Bäumen (exakt, Brüche)", bad_value == 0)
    check("Zahl optimaler Strategien: Rollback-Zählung = Aufzählung in 300 von 300", bad_count == 0)
    check("Strategienzahl = Formel in 300 von 300", bad_nstrat == 0)
    check("Knotenzahl und Besuche des Rollbacks = Formel in 300 von 300", bad_nodes == 0)
    out(f"  Bäume mit mehr als einer optimalen Strategie (Gleichstand): {ties} von 300")
    rng2 = R.SplitMix64(777)
    ok = {"mal 3": 0, "plus 7": 0, "umgekehrt": 0, "dominiert": 0, "Wurzelwahl": 0}
    for _ in range(100):
        d, b, k = [(2, 2, 2), (2, 2, 3), (2, 3, 2), (3, 2, 2)][rng2.below(4)]
        tree = T.random_tree(rng2, d, b, k, "weit")
        v0, n0, _ = T.rollback(tree)
        v1, n1, _ = T.rollback(T.map_payoffs(tree, lambda x: x * 3))
        ok["mal 3"] += v1 == 3 * v0 and n1 == n0
        v2, n2, _ = T.rollback(T.map_payoffs(tree, lambda x: x + 7))
        ok["plus 7"] += v2 == v0 + 7 * k and n2 == n0
        v3, n3, _ = T.rollback(T.reverse_choices(tree))
        ok["umgekehrt"] += v3 == v0 and n3 == n0
        v4, n4, _ = T.rollback(T.add_dominated_choice(tree))
        ok["dominiert"] += v4 == v0 and n4 == n0
        ok["Wurzelwahl"] += T.rollback(T.add_root_choice(tree))[0] >= v0
    for name, count in ok.items():
        check(f"Eigenschaft „{name}“ in 100 von 100 Bäumen (k ≤ 3)", count == 100)


def abschnitt_f():
    head("F: Rechenzeit und Speicher (eine CPU, ein Lauf: nur Größenordnung, kein Testwert)")
    out(f"Python {sys.version.split()[0]}, numpy {np.__version__}")
    cap = CAP.BASIS
    out("  k    Knoten    Objektbaum (Bau + Rollback) s    Feldfassung s    Wert")
    for k in (3, 6, 8, 9, 10, 11):
        obj = "nicht gebaut"
        if k <= 8:
            t0 = time.perf_counter()
            v_obj = CAP.tree_rollback_value(cap, k, float)
            obj = f"{time.perf_counter() - t0:.3f}"
        t0 = time.perf_counter()
        v_f = CAP.field_rollback(cap, k)
        out(f"  {k:<3} {N.n_nodes(2, 2, k):>10} {obj:>30} {time.perf_counter() - t0:>16.4f}   {v_f:.6f}")
        if k <= 8:
            check(f"k = {k}: Objektbaum = Feldfassung", abs(v_obj - v_f) < 1e-6)
    tracemalloc.start()
    tree = CAP.build_tree(cap, 7, float)
    cur, _peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    out(f"  Speicher des Objektbaums (Tupel, Gleitkomma) bei k = 7: {cur / N.n_nodes(2, 2, 7):.1f} Byte je Knoten ({N.n_nodes(2, 2, 7)} Knoten, tracemalloc)")
    del tree
    t0 = time.perf_counter()
    v300 = CAP.solve(cap, 300).value
    out(f"  Zustands-Rechnung exakt in Brüchen, k = 300 (der Baum hätte 2·4^300 − 1 Knoten): {time.perf_counter() - t0:.2f} s; Wert {float(v300):.4f}")
    incr = v300 - CAP.solve(cap, 299).value
    out(f"  Wertzuwachs je Stufe bei k = 300: {float(incr):.6f}")
    check("Wertzuwachs je Stufe bei k = 300 gleich 285/4 = 71,25", incr == F(285, 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data" / "bst_messung.txt"))
    args = ap.parse_args()
    t0 = time.perf_counter()
    out("Messung zu baum-strategie-demo: Baum, Strategie, Rollback im Kapazitätsfall (ausgedacht, ein Modell, kein Fall; GE im Erwartungswert)")
    out(f"Python {sys.version.split()[0]}, numpy {np.__version__}")
    for part in (abschnitt_a, abschnitt_b, abschnitt_c, abschnitt_d, abschnitt_e, abschnitt_f):
        part()
    out()
    out(f"GESAMT: {CHECKS[0]} Prüfungen, {CHECKS[1]} Fehler, Laufzeit {time.perf_counter() - t0:.1f} s")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(LINES) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(LINES[-3:]))


if __name__ == "__main__":
    main()
