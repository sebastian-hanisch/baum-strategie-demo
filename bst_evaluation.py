"""Auswertungen je Experiment, Raster und Verdikte (reine Funktionen: (Art, Text)).

Alle Verdikte bekommen Zeilen (Wörterbücher oder Datenklassen), nicht Zufalls-Seeds; `tests/test_verdicts.py` prüft jede Schwelle und jede genannte Zahl an von Hand
gesetzten Werten. Gerechnet wird in Brüchen (`fractions`) und erst für die Anzeige in Dezimalzahlen mit Komma umgewandelt.

Zähleinheiten: Wert und Abstand in GE im **Erwartungswert**; Strategien **reduziert** gezählt (eine Wahl an jedem Knoten, den die Strategie selbst erreicht);
Besuch = ein Knoten, den ein Rechenschritt anfasst."""

import math
import time
from dataclasses import dataclass
from fractions import Fraction

import bst_cap as CAP
import bst_constants as C
import bst_count as N
import bst_rng as R


@dataclass(frozen=True)
class Settings:
    p: int = C.DEFAULT_P
    gh: int = C.DEFAULT_GH
    gl: int = C.DEFAULT_GL
    kk: int = C.DEFAULT_KK
    q: int = C.DEFAULT_Q
    w: int = C.DEFAULT_W
    k: int = C.DEFAULT_K
    k2: int = C.DEFAULT_K2
    step: int = C.DEFAULT_STEP
    k4: int = C.DEFAULT_K4
    seed: int = C.DEFAULT_SEED
    k5: int = C.DEFAULT_K5
    seite: int = C.DEFAULT_SEITE


# --- Zahlen als deutscher Text --------------------------------------------------------------------------------------------------------------------

def de(x, nd=2) -> str:
    """Dezimalzahl mit Komma und echtem Minuszeichen; Nachkommastellen ohne abschließende Nullen (257,50 -> 257,5; 115,00 -> 115)."""
    x = float(x)
    if not math.isfinite(x):
        return "–"
    s = f"{x:.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s.replace(".", ",").replace("-", "−")


def prozent(x, nd=1) -> str:
    """Anteil (0 bis 1) als Prozentzahl mit Komma, immer mit `nd` Stellen."""
    return f"{100 * float(x):.{nd}f}".replace(".", ",") + " %"


def bruch(x: Fraction) -> str:
    """Bruch als „a/b“ (ganze Zahlen ohne Nenner)."""
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def cap1(text: str) -> str:
    """Erster Buchstabe groß, der Rest bleibt (str.capitalize würde „G“ zu „g“ machen)."""
    return text[:1].upper() + text[1:]


def plan_text(plan) -> str:
    return "".join(plan)


def to_cap(s: Settings, one_period: bool = False) -> CAP.Cap:
    """Der Kapazitätsfall zu den Reglern: Experiment 1 mit eigenen Auszahlungen und P(hoch), die übrigen mit den festen Auszahlungen und q, w der Seitenleiste."""
    if one_period:
        return CAP.make_cap(gh=s.gh, gl=s.gl, kk=s.kk, p1=Fraction(s.p, 100))
    return CAP.make_cap(q=Fraction(s.q, 100), w=s.w)


# --- Experiment 1: ein Knoten ---------------------------------------------------------------------------------------------------------------------

def analyse_one(s: Settings) -> dict:
    cap = to_cap(s, one_period=True)
    p = cap.p1
    ew_g, ew_k = CAP.ew_period(cap, CAP.G, p), CAP.ew_period(cap, CAP.K, p)
    raster = CAP.rule_comparison_raster(cap)
    return {
        "cap": cap, "p": p, "ew_g": ew_g, "ew_k": ew_k, "p_star": CAP.threshold(cap),
        "by_expectation": CAP.choice_by_expectation(cap, p), "by_modal": CAP.choice_by_modal_outcome(cap, p),
        "loss": CAP.one_period_loss(cap, p), "raster": raster,
    }


def verdict_one(a: dict) -> tuple[str, str]:
    """Verdikt zu Experiment 1: Erwartungswert gegen wahrscheinlichsten Ausgang bei einer Periode."""
    p, ps = a["p"], a["p_star"]
    head = f"Bei p = {de(p, 3)}: EW(G) = {de(a['ew_g'])}, EW(K) = {de(a['ew_k'])} GE."
    r = a["raster"]
    lo, hi = min(ps, Fraction(1, 2)), max(ps, Fraction(1, 2))
    n_diff = len(r["different"])
    if n_diff:
        span = f"Beide Regeln wählen verschieden für {de(float(lo), 3)} < p < {de(float(hi), 3)} ({n_diff} von {r['points']} Rasterpunkten), der größte Verlust der Modalregel auf dem Raster ist {de(r['worst_loss'])} GE."
    else:
        span = f"Beide Regeln wählen auf dem Raster p = j/{r['steps']} nie verschieden (0 von {r['points']} Rasterpunkten)."
    if a["by_expectation"] is None:
        return "info", f"{head} Gleichstand im Erwartungswert: beide Wahlen sind gleich gut. {span}"
    if a["by_modal"] is None:
        return "info", (f"{head} Die Regel „wahrscheinlichster Ausgang“ kann nicht entscheiden (beide Ausgänge gleich wahrscheinlich oder gleiche Auszahlung); "
                        f"der Erwartungswert wählt {a['by_expectation']}. {span}")
    if a["by_expectation"] == a["by_modal"]:
        return "info", f"{head} Beide Regeln wählen {a['by_expectation']}: hier gibt es nichts zu verlieren. {span}"
    return "warning", (f"{head} Die Regel „wahrscheinlichster Ausgang“ wählt {a['by_modal']} und verschenkt {de(a['loss'])} GE im Erwartungswert "
                       f"(der Erwartungswert wählt {a['by_expectation']}). {span}")


# --- Experiment 2: Rollback von Hand --------------------------------------------------------------------------------------------------------------

def analyse_hand(s: Settings) -> dict:
    cap = to_cap(s)
    k = s.k2
    sol = CAP.solve(cap, k)
    rows = []
    for t in range(1, k):
        for state in CAP.STATES:
            vals = sol.q_values[t][state]
            best = sol.best[t][state]
            rows.append({"stage": t + 1, "state": state, "ew_g": vals[CAP.G], "ew_k": vals[CAP.K], "choice": best, "value": sol.V[t][state]})
    root = sol.q_values[0][CAP.START]
    strategies = None
    if k <= 2:
        strategies = sorted(float(v) for v in CAP.strategy_values(cap, k, exact=True))
    return {
        "cap": cap, "k": k, "sol": sol, "rows": rows, "root_g": root[CAP.G], "root_k": root[CAP.K], "root_best": sol.best[0][CAP.START],
        "nodes": N.n_nodes(2, 2, k), "strategies": strategies, "n_strategies": N.n_strategies_reduced(2, 2, k),
    }


def step_text(k: int, step: int) -> str:
    """Was der Rechenschritt `step` (0 bis 2k) im Rollback von Hand rechnet."""
    if step == 0:
        return "Endknoten: die Gesamtauszahlung jedes Pfades (Summe der Auszahlungen entlang des Pfades)."
    stage = k - (step + 1) // 2 + 1
    if step % 2 == 1:
        return f"Ereignisknoten der Stufe {stage}: Mittel über die beiden Ausgänge (Wahrscheinlichkeit mal Auszahlung, plus Wert des Teilbaums)."
    if stage == 1:
        return "Wurzel: Maximum der beiden Wahlen; das ist der Wert der besten Strategie."
    return f"Entscheidungsknoten der Stufe {stage}: Maximum der beiden Wahlen, der bessere Ast ist fett."


def state_name(state) -> str:
    a, d = state
    return f"{a}, {d}"


def verdict_hand(a: dict) -> tuple[str, str]:
    """Verdikt zu Experiment 2: der Wert, die Wahl der ersten Periode und (bei k = 2) die Wahl nach hoher und niedriger Nachfrage."""
    k, value = a["k"], a["sol"].value
    first = a["root_best"]
    head = f"k = {k}: {a['nodes']} Knoten, Wert {de(value)} GE."
    first_text = "zuerst " + (first[0] if len(first) == 1 else " oder ".join(first) + " (Gleichstand)")
    if k == 1:
        return "info", f"{head} Eine Periode, nichts zu beobachten: {first_text} (EW(G) = {de(a['root_g'])}, EW(K) = {de(a['root_k'])})."
    if k == 2:
        a1 = first[0]
        by_state = {r["state"]: r for r in a["rows"]}
        parts = []
        for demand in (CAP.HOCH, CAP.NIEDRIG):
            r = by_state[(a1, demand)]
            choice = r["choice"][0] if len(r["choice"]) == 1 else "/".join(r["choice"])
            parts.append(f"nach {demand} {choice} (EW(G) = {de(r['ew_g'])}, EW(K) = {de(r['ew_k'])})")
        return "success", f"{head} {cap1(first_text)}; {parts[0]}; {parts[1]}. Die Strategie ist eine Tabelle von Zuständen, kein Pfad."
    return "info", (f"{head} {cap1(first_text)}; danach hängt die Wahl vom Zustand (letzte Wahl, letzte Nachfrage) ab, die Tabelle zeigt sie je Stufe. "
                    f"Der Baum hat zu viele Knoten zum Zeichnen.")


# --- Experiment 3: Plan oder Strategie ------------------------------------------------------------------------------------------------------------

def analyse_plan(s: Settings) -> dict:
    cap = to_cap(s)
    k = s.k
    sol = CAP.solve(cap, k)
    plan_v, plan = CAP.best_plan(cap, k)
    greedy = CAP.policy_value(cap, k, CAP.greedy_policy(cap))
    reactive = CAP.policy_value(cap, k, CAP.reactive_policy)
    coin = CAP.coin_value(cap, k)
    safe = CAP.plan_value(cap, tuple(CAP.K for _ in range(k)))          # „immer K“: sicher 30 k
    dist_s = CAP.total_distribution(cap, k, CAP.optimal_policy(cap, k, sol))
    dist_p = CAP.total_distribution(cap, k, CAP.plan_policy(plan))
    return {
        "cap": cap, "k": k, "strategy": sol.value, "plan": plan_v, "plan_choices": plan, "adaptation": sol.value - plan_v, "greedy": greedy,
        "reactive": reactive, "coin": coin, "safe": safe, "dist_strategy": dist_s, "dist_plan": dist_p,
        "below_strategy": CAP.probability_below(dist_s, safe), "below_plan": CAP.probability_below(dist_p, safe),
        "n_optimal": sol.n_optimal,
    }


def verdict_plan(a: dict) -> tuple[str, str]:
    """Verdikt zu Experiment 3: Wert der Anpassung (Strategie minus bester fester Plan), gierige Regel, Anteil unter dem sicheren Wert."""
    k, adapt = a["k"], a["adaptation"]
    cap = a["cap"]
    q, w = de(cap.q, 3), de(cap.w)
    head = f"k = {k}: Strategie {de(a['strategy'])} GE, bester fester Plan {de(a['plan'])} GE ({plan_text(a['plan_choices'])}), Wert der Anpassung {de(adapt)} GE."
    tail = ""
    gap = a["strategy"] - a["greedy"]
    if gap > 0:
        tail = f" Der Rollback schlägt hier sogar die gierige Regel: {de(a['strategy'])} gegen {de(a['greedy'])} GE."
    if k == 1:
        return "info", f"{head} Bei einer Periode gibt es nichts zu beobachten: der Plan ist die Strategie."
    if adapt == 0:
        return "info", f"{head} Bei Persistenz q = {q} und Wechselkosten w = {w} GE ist der beste feste Plan schon eine beste Strategie: Beobachten bringt hier nichts.{tail}"
    return "success", f"{head} Bei Persistenz q = {q} und Wechselkosten w = {w} GE lohnt es, auf die Beobachtung zu reagieren.{tail}"


def verdict_distribution(a: dict) -> tuple[str, str]:
    """Verdikt zur Verteilung: der Erwartungswert ist ein Mittel, kein Pfad (Anteil der Gesamtauszahlungen unter dem sicheren Wert von „immer K“)."""
    k = a["k"]
    safe = de(a["safe"])
    sentence = (f"k = {k}: Mit Wahrscheinlichkeit {prozent(a['below_strategy'])} liegt die Gesamtauszahlung der besten Strategie unter dem sicheren Wert {safe} GE von „immer K“ "
                f"(beim besten festen Plan {prozent(a['below_plan'])}). Der höhere Erwartungswert ist kein Garantiewert.")
    if a["below_strategy"] == 0:
        return "info", f"k = {k}: Die Gesamtauszahlung der besten Strategie liegt in keiner Nachfragefolge unter dem sicheren Wert {safe} GE von „immer K“."
    return "warning", sentence


# --- Raster: gierig gegen Rollback, Wert der Anpassung --------------------------------------------------------------------------------------------

def greedy_gap(q: Fraction, w, k: int) -> Fraction:
    cap = CAP.make_cap(q=q, w=w)
    return CAP.solve(cap, k).value - CAP.policy_value(cap, k, CAP.greedy_policy(cap))


def greedy_raster() -> dict:
    """Raster q × w × k: In wie vielen Zellen ist der Rollback besser (gleich, schlechter) als die gierige Regel?"""
    better = equal = worse = 0
    cells = {}
    for qn, qd in C.RASTER_Q:
        for w in C.RASTER_W:
            for k in C.RASTER_K:
                g = greedy_gap(Fraction(qn, qd), w, k)
                cells[(Fraction(qn, qd), w, k)] = g
                better += g > 0
                equal += g == 0
                worse += g < 0
    return {"cells": cells, "better": better, "equal": equal, "worse": worse, "n": better + equal + worse}


def adaptation_raster() -> dict:
    """Raster q × w × k = 1 bis 8: Wert der Anpassung (Strategie minus bester fester Plan)."""
    cells = {}
    zero = pos = neg = 0
    for qn, qd in C.ADAPT_Q:
        for w in C.ADAPT_W:
            for k in C.ADAPT_K:
                v = CAP.adaptation_value(CAP.make_cap(q=Fraction(qn, qd), w=w), k)
                cells[(Fraction(qn, qd), w, k)] = v
                zero += v == 0
                pos += v > 0
                neg += v < 0
    return {"cells": cells, "zero": zero, "positive": pos, "negative": neg, "n": zero + pos + neg}


def persistence_threshold(w, k: int, lo=Fraction(1, 2), hi=Fraction(99, 100), rounds: int = 40) -> Fraction:
    """Kleinstes q, ab dem die Anpassung etwas bringt (Wert der Anpassung > 0), bei Wechselkosten w und k Perioden; Bisektion in Brüchen.
    Gilt nur, wenn der Wert in q ab dort monoton wirkt (auf dem Raster 1/100 geprüft, siehe README); Rückgabe: obere Intervallgrenze."""
    def positive(q):
        return CAP.adaptation_value(CAP.make_cap(q=q, w=w), k) > 0

    if not positive(hi):
        return hi
    for _ in range(rounds):
        mid = (lo + hi) / 2
        if positive(mid):
            hi = mid
        else:
            lo = mid
    return hi


# --- Experiment 4: Aufzählung gegen Rollback ------------------------------------------------------------------------------------------------------

def analyse_enum(s: Settings) -> dict:
    cap = to_cap(s)
    k = s.k4
    values = CAP.strategy_values(cap, k)
    sol = CAP.solve(cap, k)
    plan_v, _plan = CAP.best_plan(cap, k)
    tol = 1e-9
    top = float(sol.value)
    rng = R.SplitMix64(s.seed)
    drawn = []
    for _ in range(C.N_RANDOM_STRATEGIES):
        strat = CAP.random_strategy(cap, k, rng)
        drawn.append({"value": float(CAP.strategy_value(cap, k, strat)), "first": strat[0]})
    sorted_values = sorted(float(v) for v in values)
    mid = len(sorted_values) // 2
    median = sorted_values[mid] if len(sorted_values) % 2 else 0.5 * (sorted_values[mid - 1] + sorted_values[mid])
    return {
        "cap": cap, "k": k, "values": values, "rollback": top, "plan": float(plan_v), "mean": float(values.mean()), "median": median,
        "worst": float(values.min()), "n_strategies": len(values), "n_best": int((abs(values - top) <= tol).sum()),
        "n_over_plan": int((values > float(plan_v) + tol).sum()), "n_rollback_optimal": sol.n_optimal,
        "visits_rollback": N.visits_rollback(2, 2, k), "visits_enum": N.visits_enumeration(2, 2, k), "drawn": drawn,
    }


def verdict_enum(a: dict) -> tuple[str, str]:
    """Verdikt zu Experiment 4: Rollback gegen Aufzählung (Besuche, Zahl der besten Strategien, Strategien über dem besten Plan, Mittel)."""
    k = a["k"]
    n_best = a["n_best"]
    if n_best == 1:
        best_text = f"Genau eine Strategie erreicht {de(a['rollback'])} GE und ist die des Rollback."
    else:
        best_text = f"{N.ints(n_best)} Strategien erreichen {de(a['rollback'])} GE (Gleichstand); der Rollback findet eine davon."
    return "success", (f"k = {k}: {N.ints(a['n_strategies'])} Strategien, {N.ints(a['visits_enum'])} Knotenbesuche bei der Aufzählung; der Rollback braucht {N.ints(a['visits_rollback'])}. "
                       f"{best_text} {N.ints(a['n_over_plan'])} schlagen den besten festen Plan ({de(a['plan'])} GE), das Mittel aller ist {de(a['mean'])} GE.")


# --- Experiment 5: wie groß wird der Baum ---------------------------------------------------------------------------------------------------------

def analyse_size(s: Settings, measure_time: bool = True) -> dict:
    cap = to_cap(s)
    k = s.k5
    rows = N.table_rows(range(1, C.K5_MAX + 1))
    field_seconds = object_seconds = None
    if measure_time:
        t0 = time.perf_counter()
        field_value = CAP.field_rollback(cap, k)
        field_seconds = time.perf_counter() - t0
        if k <= 7:
            t0 = time.perf_counter()
            object_value = CAP.tree_rollback_value(cap, k, float)
            object_seconds = time.perf_counter() - t0
            assert abs(object_value - field_value) < 1e-6
    else:
        field_value = CAP.field_rollback(cap, k)
    return {
        "k": k, "rows": rows, "nodes": N.n_nodes(2, 2, k), "seite": s.seite, "first_k_over_page": N.first_k_over_page(s.seite),
        "field_seconds": field_seconds, "object_seconds": object_seconds, "field_value": field_value,
        "strategies_reduced_text": N.strategies_reduced_text(2, 2, k),
    }


def verdict_size(a: dict) -> tuple[str, str]:
    """Verdikt zu Experiment 5: Knoten gegen Seitenkonvention, Rechenzeit der Feldfassung (Größenordnung), Strategienzahl."""
    k, nodes, seite = a["k"], a["nodes"], a["seite"]
    fits = nodes <= seite
    page = (f"k = {k}: {N.ints(nodes)} Knoten, "
            + (f"das passt noch auf eine Seite ({N.ints(seite)} Knoten je Seite, eine Konvention)." if fits
               else f"mehr als eine Seite ({N.ints(seite)} Knoten je Seite, eine Konvention; ab k = {a['first_k_over_page']})."))
    secs = a["field_seconds"]
    time_text = ""
    if secs is not None:
        time_text = f" Die Feldfassung rechnet den vollen Baum in {'unter einer Sekunde' if secs < 1 else de(secs, 1) + ' s'} (jetzt gemessen, Größenordnung, eine CPU)."
    return "info", (f"{page}{time_text} Aufgezählt wären es {a['strategies_reduced_text']} Strategien (reduziert gezählt, nach der Formel 2^(2^k − 1)): "
                    "der Baum ist zu groß zum Aufschreiben und zum Aufzählen, nicht zum Rechnen.")
