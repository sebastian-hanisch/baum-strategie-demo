"""Der Kapazitätsfall als Entscheidungsbaum: ein ausgedachtes Zahlenbeispiel, **ein Modell, kein Fall** (Einheit: Geldeinheiten GE).

Je Periode wird G (groß bauen) oder K (klein bauen oder mieten) gewählt, **vor** der Nachfrage dieser Periode und **nach** Beobachtung der Vorperiode.
G zahlt `gh` = +200 bei hoher und `gl` = −100 bei niedriger Nachfrage; K zahlt sicher `kk` = +30. Periode 1: P(hoch) = `p1` = 1/2; danach bleibt die Nachfrage
mit der Wahrscheinlichkeit `q` (Persistenz, Voreinstellung 3/4) wie in der Vorperiode. Ein Wechsel der Wahl gegenüber der Vorperiode kostet `w` (Voreinstellung 25 GE,
nicht in Periode 1). Die Perioden werden ohne Diskontierung addiert. Alle Zusätze (Persistenz, Wechselkosten) sind eigene Annahmen dieser Demo, nicht Fall oder Literatur.

Ein **Zustand** vor einer Wahl ist (letzte Wahl, letzte Nachfrage); die Wahl der ersten Periode hat keinen. Der Baum hat dennoch 2·4^k − 1 Knoten, weil jeder Pfad
einen eigenen Knoten hat; die Zustands-Rechnung fasst alle Knoten mit demselben Zustand zusammen (vier statt 4^t je Stufe).

Alle Rechnungen laufen mit Brüchen (`fractions`) oder, wo es um Größe und Zeit geht, mit Gleitkommazahlen (`field_rollback`, `strategy_values(exact=False)`).
Herkunft: neu geschrieben für diese Demo; der Aufbau der Messlogik folgt einer früheren Messung, Code wurde nicht übernommen.
"""

import itertools
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

import bst_tree as T

G, K = "G", "K"
HOCH, NIEDRIG = "hoch", "niedrig"
ACTIONS = (G, K)
DEMANDS = (HOCH, NIEDRIG)
START = (None, None)
STATES = tuple((a, d) for a in ACTIONS for d in DEMANDS)


@dataclass(frozen=True)
class Cap:
    gh: Fraction
    gl: Fraction
    kk: Fraction
    q: Fraction
    w: Fraction
    p1: Fraction


def make_cap(gh=200, gl=-100, kk=30, q=Fraction(3, 4), w=25, p1=Fraction(1, 2)) -> Cap:
    return Cap(*(Fraction(x) for x in (gh, gl, kk, q, w, p1)))


BASIS = make_cap()


def payoff(cap: Cap, a: str, d: str) -> Fraction:
    if a == K:
        return cap.kk
    return cap.gh if d == HOCH else cap.gl


def p_hoch(cap: Cap, t: int, d_prev) -> Fraction:
    """P(hoch) in der Periode t (0-basiert) nach der Vorperiode mit der Nachfrage `d_prev`."""
    if t == 0:
        return cap.p1
    return cap.q if d_prev == HOCH else 1 - cap.q


def switch_cost(cap: Cap, a_prev, a: str) -> Fraction:
    return cap.w if (a_prev is not None and a != a_prev) else Fraction(0)


def ew_period(cap: Cap, a: str, p: Fraction) -> Fraction:
    """Erwartungswert der Auszahlung einer Periode (ohne Wechselkosten) bei P(hoch) = p."""
    return p * payoff(cap, a, HOCH) + (1 - p) * payoff(cap, a, NIEDRIG)


# --- eine Periode: Erwartungswert gegen wahrscheinlichsten Ausgang ------------------------------------------------------------------------------

def threshold(cap: Cap) -> Fraction:
    """p*, bei dem EW(G) = EW(K) gilt: (K − G niedrig)/(G hoch − G niedrig); G ist besser für p > p*."""
    return (cap.kk - cap.gl) / (cap.gh - cap.gl)


def choice_by_expectation(cap: Cap, p: Fraction):
    """Wahl nach dem Erwartungswert; `None` bei Gleichstand."""
    eg, ek = ew_period(cap, G, p), ew_period(cap, K, p)
    return G if eg > ek else (K if ek > eg else None)


def choice_by_modal_outcome(cap: Cap, p: Fraction):
    """Wahl nach dem wahrscheinlichsten Ausgang: die Wahl mit der besten Auszahlung bei der wahrscheinlicheren Nachfrage; `None` bei gleich wahrscheinlichen
    Ausgängen oder gleicher Auszahlung."""
    if p == Fraction(1, 2):
        return None
    d = HOCH if p > Fraction(1, 2) else NIEDRIG
    pg, pk = payoff(cap, G, d), payoff(cap, K, d)
    return G if pg > pk else (K if pk > pg else None)


def rule_comparison_raster(cap: Cap, steps: int = 300) -> dict:
    """Raster p = j/steps (j = 0 bis steps, ohne p = 1/2): Wo wählen beide Regeln verschieden, und was verliert die Modalregel im Erwartungswert?"""
    different, worst, worst_j = [], Fraction(0), None
    for j in range(steps + 1):
        p = Fraction(j, steps)
        if p == Fraction(1, 2):
            continue
        ce, cm = choice_by_expectation(cap, p), choice_by_modal_outcome(cap, p)
        if ce is not None and cm is not None and ce != cm:
            loss = ew_period(cap, ce, p) - ew_period(cap, cm, p)
            different.append(j)
            if loss > worst:
                worst, worst_j = loss, j
    return {"steps": steps, "points": steps, "different": different, "worst_loss": worst, "worst_j": worst_j}


def one_period_loss(cap: Cap, p: Fraction) -> Fraction:
    """Erwartungswertverlust der Modalregel gegen die Erwartungswert-Regel bei P(hoch) = p (0, wenn beide gleich wählen oder ein Gleichstand vorliegt)."""
    ce, cm = choice_by_expectation(cap, p), choice_by_modal_outcome(cap, p)
    if ce is None or cm is None or ce == cm:
        return Fraction(0)
    return ew_period(cap, ce, p) - ew_period(cap, cm, p)


# --- Objektbaum ---------------------------------------------------------------------------------------------------------------------------------

def build_tree(cap: Cap, k: int, num=Fraction):
    """Vollständiger Entscheidungsbaum (Ereignisknoten) für k Perioden als Tupelbaum (`bst_tree`). `num` ist `Fraction` (exakt) oder `float`."""
    conv = (lambda x: x) if num is Fraction else (lambda x: float(x))

    def dec(t, a_prev, d_prev):
        if t == k:
            return None
        p = p_hoch(cap, t, d_prev)
        choices = []
        for a in ACTIONS:
            sw = switch_cost(cap, a_prev, a)
            branches = []
            for d, prob in ((HOCH, p), (NIEDRIG, 1 - p)):
                branches.append((conv(prob), conv(payoff(cap, a, d) - sw), dec(t + 1, a, d)))
            choices.append((a, tuple(branches)))
        return tuple(choices)

    return dec(0, None, None)


# --- Rollback über Zustände (vier Zustände je Stufe) ----------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Solution:
    k: int
    value: Fraction
    V: list                    # V[t][Zustand]: Wert ab Periode t (0-basiert); V[k] = 0
    q_values: list             # q_values[t][Zustand] = {G: Wert, K: Wert} der beiden Wahlen in Periode t
    best: list                 # best[t][Zustand] = Liste der optimalen Wahlen (mehrere bei Gleichstand)
    n_optimal: int             # Zahl der optimalen reduzierten Strategien


def solve(cap: Cap, k: int) -> Solution:
    """Rückwärtsrechnung über die Zustände (letzte Wahl, letzte Nachfrage); exakt in Brüchen."""
    V = [dict() for _ in range(k + 1)]
    C = [dict() for _ in range(k + 1)]
    q_values = [dict() for _ in range(k)]
    best = [dict() for _ in range(k)]
    for s in STATES:
        V[k][s] = Fraction(0)
        C[k][s] = 1
    V[k][START], C[k][START] = Fraction(0), 1
    for t in range(k - 1, -1, -1):
        for s in ((START,) if t == 0 else STATES):
            a_prev, d_prev = s
            p = p_hoch(cap, t, d_prev)
            vals, counts = {}, {}
            for a in ACTIONS:
                sw = switch_cost(cap, a_prev, a)
                vals[a] = ew_period(cap, a, p) - sw + p * V[t + 1][(a, HOCH)] + (1 - p) * V[t + 1][(a, NIEDRIG)]
                counts[a] = C[t + 1][(a, HOCH)] * C[t + 1][(a, NIEDRIG)] if t + 1 < k else 1
            top = max(vals.values())
            opt = [a for a in ACTIONS if vals[a] == top]
            V[t][s] = top
            C[t][s] = sum(counts[a] for a in opt)
            q_values[t][s] = vals
            best[t][s] = opt
    return Solution(k, V[0][START], V, q_values, best, C[0][START] if k > 0 else 1)


# --- Politiken: Wert einer Wahlregel ------------------------------------------------------------------------------------------------------------

def policy_value(cap: Cap, k: int, policy) -> Fraction:
    """Exakter Erwartungswert einer Wahlregel `policy(t, a_prev, d_prev) -> G oder K` über k Perioden (Zustands-Rechnung)."""
    V = [dict() for _ in range(k + 1)]
    for s in STATES:
        V[k][s] = Fraction(0)
    for t in range(k - 1, -1, -1):
        for s in ((START,) if t == 0 else STATES):
            a_prev, d_prev = s
            p = p_hoch(cap, t, d_prev)
            a = policy(t, a_prev, d_prev)
            V[t][s] = ew_period(cap, a, p) - switch_cost(cap, a_prev, a) + p * V[t + 1][(a, HOCH)] + (1 - p) * V[t + 1][(a, NIEDRIG)]
    return V[0][START] if k > 0 else Fraction(0)


def greedy_policy(cap: Cap):
    """Gierig: in jeder Periode die Wahl mit dem besten Erwartungswert **dieser einen Periode** einschließlich Wechselkosten (Gleichstand: G)."""
    def policy(t, a_prev, d_prev):
        p = p_hoch(cap, t, d_prev)
        vg = ew_period(cap, G, p) - switch_cost(cap, a_prev, G)
        vk = ew_period(cap, K, p) - switch_cost(cap, a_prev, K)
        return G if vg >= vk else K
    return policy


def reactive_policy(t, a_prev, d_prev):
    """„G nach hoher, K nach niedriger Nachfrage“, unabhängig von der letzten Wahl; in Periode 1 G."""
    if t == 0:
        return G
    return G if d_prev == HOCH else K


def coin_value(cap: Cap, k: int) -> Fraction:
    """Wert der Münzwurf-Politik (an jedem Entscheidungsknoten fair gewürfelt) = Mittel über alle reduzierten Strategien."""
    V = [dict() for _ in range(k + 1)]
    for s in STATES:
        V[k][s] = Fraction(0)
    for t in range(k - 1, -1, -1):
        for s in ((START,) if t == 0 else STATES):
            a_prev, d_prev = s
            p = p_hoch(cap, t, d_prev)
            total = Fraction(0)
            for a in ACTIONS:
                total += ew_period(cap, a, p) - switch_cost(cap, a_prev, a) + p * V[t + 1][(a, HOCH)] + (1 - p) * V[t + 1][(a, NIEDRIG)]
            V[t][s] = total / 2
    return V[0][START] if k > 0 else Fraction(0)


# --- feste Pläne (Wahlfolge ohne Beobachtung) ---------------------------------------------------------------------------------------------------

def marginals(cap: Cap, k: int) -> list:
    """P(hoch) je Periode ohne Beobachtung (Randverteilung der Nachfrage)."""
    m, out = cap.p1, []
    for _ in range(k):
        out.append(m)
        m = m * cap.q + (1 - m) * (1 - cap.q)
    return out


def plan_value(cap: Cap, plan) -> Fraction:
    m = marginals(cap, len(plan))
    total = Fraction(0)
    for t, a in enumerate(plan):
        total += ew_period(cap, a, m[t]) - switch_cost(cap, plan[t - 1] if t > 0 else None, a)
    return total


def best_plan(cap: Cap, k: int):
    """Bester fester Plan über Rückwärtsrechnung über die letzte Wahl (Gleichstand: G zuerst). Gibt `(Wert, Plan)` zurück."""
    if k == 0:
        return Fraction(0), ()
    m = marginals(cap, k)
    V = [{a: Fraction(0) for a in ACTIONS} for _ in range(k + 1)]   # V[t][letzte Wahl in Periode t − 1]: bester Rest ab Periode t
    for t in range(k - 1, -1, -1):
        for a_prev in ACTIONS if t > 0 else (None,):
            V[t][a_prev] = max(ew_period(cap, a, m[t]) - switch_cost(cap, a_prev, a) + V[t + 1][a] for a in ACTIONS)
    plan, a_prev = [], None
    for t in range(k):
        vals = {a: ew_period(cap, a, m[t]) - switch_cost(cap, a_prev, a) + V[t + 1][a] for a in ACTIONS}
        a_prev = G if vals[G] >= vals[K] else K
        plan.append(a_prev)
    return V[0][None], tuple(plan)


def best_plan_enumeration(cap: Cap, k: int):
    """Bester fester Plan durch Aufzählung aller 2^k Pläne (Gleichstand: der erste in der Reihenfolge G vor K)."""
    best, best_plan_ = None, None
    for plan in itertools.product(ACTIONS, repeat=k):
        v = plan_value(cap, plan)
        if best is None or v > best:
            best, best_plan_ = v, plan
    return (Fraction(0), ()) if best is None else (best, best_plan_)


def adaptation_value(cap: Cap, k: int) -> Fraction:
    """Wert der Anpassung = Wert der besten Strategie minus Wert des besten festen Plans (jeder Plan ist eine Strategie: nie negativ)."""
    return solve(cap, k).value - best_plan(cap, k)[0]


# --- Verteilung der Gesamtauszahlung --------------------------------------------------------------------------------------------------------------

def total_distribution(cap: Cap, k: int, policy) -> dict:
    """Verteilung der Gesamtauszahlung unter einer Wahlregel: Wert -> Wahrscheinlichkeit; Aufzählung der 2^k Nachfragefolgen."""
    dist: dict = {}

    def rec(t, a_prev, d_prev, prob, total):
        if t == k:
            dist[total] = dist.get(total, Fraction(0)) + prob
            return
        p = p_hoch(cap, t, d_prev)
        a = policy(t, a_prev, d_prev)
        sw = switch_cost(cap, a_prev, a)
        for d, pd in ((HOCH, p), (NIEDRIG, 1 - p)):
            rec(t + 1, a, d, prob * pd, total + payoff(cap, a, d) - sw)

    rec(0, None, None, Fraction(1), Fraction(0))
    return dist


def optimal_policy(cap: Cap, k: int, sol: Solution | None = None):
    """Die beste Strategie als Wahlregel (bei Gleichstand die erste optimale Wahl in der Reihenfolge G vor K)."""
    sol = sol or solve(cap, k)
    return lambda t, a_prev, d_prev: sol.best[t][START if t == 0 else (a_prev, d_prev)][0]


def plan_policy(plan):
    return lambda t, a_prev, d_prev: plan[t]


def probability_below(dist: dict, limit) -> Fraction:
    return sum((p for v, p in dist.items() if v < limit), Fraction(0))


# --- alle reduzierten Strategien: Werte (vektorisiert) -----------------------------------------------------------------------------------------

def strategy_values(cap: Cap, k: int, exact: bool = False) -> np.ndarray:
    """Werte aller 2^(2^k − 1) reduzierten Strategien (ein Wert je Strategie), ohne die Strategien einzeln durchzugehen.

    Der Wert einer Strategie in einem Teilbaum hängt nur vom Zustand (letzte Wahl, letzte Nachfrage) ab. Mit W[m][Zustand] = Werte aller Strategien der
    letzten m Perioden ab diesem Zustand gilt: Wert = −Wechselkosten + EW(Wahl) + p · Wert(Teilstrategie nach hoch) + (1 − p) · Wert(Teilstrategie nach niedrig),
    und jede Wahl lässt jede Kombination der beiden Teilstrategien zu (äußere Summe). `exact=True` rechnet in Brüchen (Feld vom Typ object)."""
    if k < 1:
        return np.array([0.0])
    num = (lambda x: x) if exact else (lambda x: float(x))
    dtype = object if exact else float

    def level(m, state):
        a_prev, d_prev = state
        t = k - m
        p = p_hoch(cap, t, d_prev)
        parts = []
        for a in ACTIONS:
            base = ew_period(cap, a, p) - switch_cost(cap, a_prev, a)
            if m == 1:
                parts.append(np.array([num(base)], dtype=dtype))
            else:
                high, low = W[m - 1][(a, HOCH)], W[m - 1][(a, NIEDRIG)]
                block = num(base) + num(p) * high[:, None] + num(1 - p) * low[None, :]
                parts.append(np.asarray(block, dtype=dtype).reshape(-1))
        return np.concatenate(parts)

    W = {0: {}}
    for m in range(1, k):
        W[m] = {s: level(m, s) for s in STATES}
    return level(k, START)


def random_strategy(cap: Cap, k: int, rng):
    """Eine zufällig gezogene reduzierte Strategie: an jedem erreichbaren Entscheidungsknoten eine faire Münze (`rng.below(2)`, ganzzahliger SplitMix64).

    Das ist die Gleichverteilung über alle reduzierten Strategien (R_k = 2 · R_(k−1)^2: erst die Wahl, dann unabhängig je Ausgang eine Teilstrategie).
    Darstellung: `(Wahl, (Teilstrategie nach hoch, Teilstrategie nach niedrig))`; in der letzten Periode `(Wahl, None)`."""
    def draw(t):
        a = ACTIONS[rng.below(2)]
        if t == k - 1:
            return (a, None)
        return (a, (draw(t + 1), draw(t + 1)))

    return draw(0) if k > 0 else None


def strategy_value(cap: Cap, k: int, strategy) -> Fraction:
    """Exakter Erwartungswert einer explizit gegebenen reduzierten Strategie."""
    def rec(t, a_prev, d_prev, strat):
        a, subs = strat
        p = p_hoch(cap, t, d_prev)
        sw = switch_cost(cap, a_prev, a)
        total = Fraction(0)
        for index, (d, pd) in enumerate(((HOCH, p), (NIEDRIG, 1 - p))):
            total += pd * (payoff(cap, a, d) - sw + (rec(t + 1, a, d, subs[index]) if subs is not None else 0))
        return total

    return rec(0, None, None, strategy) if k > 0 else Fraction(0)


def strategy_choices(strategy) -> dict:
    """Die Wahlen einer reduzierten Strategie als Tabelle Pfad -> Wahl (Pfad = Tuple der bisherigen Nachfragen), zum Anzeigen."""
    out = {}

    def rec(strat, path):
        a, subs = strat
        out[path] = a
        if subs is not None:
            rec(subs[0], path + (HOCH,))
            rec(subs[1], path + (NIEDRIG,))

    rec(strategy, ())
    return out


# --- Feldbaum: der volle Baum als numpy-Felder ------------------------------------------------------------------------------------------------

def field_rollback(cap: Cap, k: int) -> float:
    """Rollback über den **vollen** Baum als Felder (Gleitkomma): Stufe t hat 4^t Entscheidungsknoten, das Kind (Wahl a, Ausgang d) von Knoten i hat den Index
    4·i + 2·a + d (a: 0 = G, 1 = K; d: 0 = hoch, 1 = niedrig). Es werden alle 4^k Pfade einzeln bewertet; die Zustände werden nicht zusammengefasst."""
    if k == 0:
        return 0.0
    gh, gl, kk = float(cap.gh), float(cap.gl), float(cap.kk)
    q, w, p1 = float(cap.q), float(cap.w), float(cap.p1)
    V = np.zeros(4**k)
    for t in range(k - 1, -1, -1):
        n = 4**t
        child = V.reshape(n, 2, 2)                 # [Knoten, Wahl, Ausgang]
        if t == 0:
            p = np.full(1, p1)
            a_prev = np.full(1, -1)
        else:
            state = np.arange(n) % 4
            a_prev = state // 2                    # 0 = G, 1 = K
            p = np.where(state % 2 == 0, q, 1.0 - q)
        out = np.empty((n, 2))
        for a in (0, 1):
            sw = np.where((a_prev >= 0) & (a_prev != a), w, 0.0)
            pay_high, pay_low = (gh, gl) if a == 0 else (kk, kk)
            out[:, a] = p * (pay_high - sw + child[:, a, 0]) + (1 - p) * (pay_low - sw + child[:, a, 1])
        V = out.max(axis=1)
    return float(V[0])


def tree_rollback_value(cap: Cap, k: int, num=Fraction):
    """Wert der besten Strategie über den Objektbaum (nur für kleine k; der Baum hat 2·4^k − 1 Knoten)."""
    tree = build_tree(cap, k, num)
    tol = 0 if num is Fraction else 1e-9
    return T.rollback(tree, tol)[0]
