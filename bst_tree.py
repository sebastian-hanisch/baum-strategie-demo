"""Entscheidungsbaum (Ereignisknoten) als Objekt: Rollback (Rückwärtsrechnung), Aufzählung aller Strategien, Zählung der Besuche, Zufallsbäume.

Darstellung (Tupel, keine Klassen):

- Entscheidungsknoten = Tupel von Wahlen; eine Wahl ist `(Name, Ereignisknoten)`.
- Ereignisknoten = Tupel von Ästen `(Wahrscheinlichkeit, Auszahlung, Kind)`; das Kind ist ein Entscheidungsknoten oder `None` (Endknoten).
- Die Auszahlung eines Astes gilt, sobald der Ausgang eintritt; die Gesamtauszahlung eines Pfades ist die Summe der Auszahlungen seiner Äste.

Zahlen können Brüche (`fractions.Fraction`, exakt) oder Gleitkommazahlen sein; bei Gleitkommazahlen gilt zwischen zwei Wahlen die Toleranz `tol` als Gleichstand.

Rollback nach Raiffa/Schlaifer 1961 (Abschn. 1.2.1, Gl. 1-1 bis 1-4: „backwards induction“, „averaging out and folding back“): von den Endknoten her an
Ereignisknoten mitteln, an Entscheidungsknoten maximieren. Das Wort „Rollback“ ist Lehrbuch- und Softwarejargon, in den gelesenen Quellen steht es nicht.

Dieser Baum ist **kein CART**: CART teilt Daten nach Merkmalen, hier wird eine Folge aus Wahl und Zufall bewertet.
"""

import itertools
from fractions import Fraction

import bst_count as N


def count_nodes(node) -> tuple[int, int, int]:
    """(Entscheidungsknoten, Ereignisknoten, Endknoten) des Teilbaums."""
    if node is None:
        return (0, 0, 1)
    dec, ev, end = 1, 0, 0
    for _name, branches in node:
        ev += 1
        for _p, _pay, child in branches:
            a, b, c = count_nodes(child)
            dec += a
            ev += b
            end += c
    return dec, ev, end


class Counter:
    """Zählt Knotenbesuche (ein Besuch = ein Knoten wird angefasst)."""

    def __init__(self):
        self.visits = 0


def rollback(node, tol=0, counter: Counter | None = None):
    """Rückwärtsrechnung. Gibt `(Wert, Zahl optimaler Strategien (reduziert gezählt), Namen der optimalen Wahlen an der Wurzel)` zurück.

    `counter` zählt die Besuche: jeder Entscheidungs-, Ereignis- und Endknoten genau einmal."""
    if counter is not None:
        counter.visits += 1
    if node is None:
        return (Fraction(0) if tol == 0 else 0.0), 1, []
    best, n_opt, names = None, 0, []
    for name, branches in node:
        if counter is not None:
            counter.visits += 1
        value, count = 0, 1
        for p, pay, child in branches:
            child_value, child_count, _ = rollback(child, tol, counter)
            value += p * (pay + child_value)
            count *= child_count
        if best is None or value > best + tol:
            best, n_opt, names = value, count, [name]
        elif abs(value - best) <= tol:
            n_opt += count
            names.append(name)
    return best, n_opt, names


def strategies(node) -> list:
    """Alle reduzierten Strategien als verschachtelte Tupel `(Index der Wahl, (Teilstrategie je Ausgang))`; ein Endknoten hat die Teilstrategie `None`."""
    out = []
    for index, (_name, branches) in enumerate(node):
        options = [strategies(child) if child is not None else [None] for _p, _pay, child in branches]
        for combo in itertools.product(*options):
            out.append((index, combo))
    return out


def evaluate(node, strategy, counter: Counter | None = None):
    """Erwartete Gesamtauszahlung einer reduzierten Strategie; zählt je Strategie ihren erreichbaren Teilbaum
    (Entscheidungsknoten, gewählter Ereignisknoten, Endknoten)."""
    if counter is not None:
        counter.visits += 2
    index, combo = strategy
    _name, branches = node[index]
    value = 0
    for (p, pay, child), sub in zip(branches, combo):
        if child is None:
            if counter is not None:
                counter.visits += 1
            value += p * pay
        else:
            value += p * (pay + evaluate(child, sub, counter))
    return value


def enumerate_values(node, counter: Counter | None = None) -> list:
    """Werte aller reduzierten Strategien (Aufzählung); `counter` zählt die Besuche der Bewertung."""
    return [evaluate(node, s, counter) for s in strategies(node)]


def count_optimal(values, best, tol=0) -> int:
    return sum(1 for v in values if abs(v - best) <= tol)


# --- Zufallsbäume (Orakel und Messung) -------------------------------------------------------------------------------------------------------

def random_tree(rng, d: int, b: int, k: int, payoff: str = "weit"):
    """Zufallsbaum mit d Wahlen, b Ausgängen und k Stufen aus dem ganzzahligen SplitMix64 `rng` (nur `below`; kein log, kein cos).

    Wahrscheinlichkeiten: Gewichte 1 bis 4, zu Brüchen normiert. Auszahlungen ganzzahlig: `payoff == "weit"` in [−30, 60], `"eng"` in [0, 3] (viele Gleichstände)."""
    def pay():
        return -30 + rng.below(91) if payoff == "weit" else rng.below(4)

    def dec(level):
        if level == k:
            return None
        choices = []
        for a in range(d):
            weights = [rng.below(4) + 1 for _ in range(b)]
            total = sum(weights)
            choices.append((f"a{a}", tuple((Fraction(w, total), pay(), dec(level + 1)) for w in weights)))
        return tuple(choices)

    return dec(0)


def check_counts(node, d: int, b: int, k: int) -> bool:
    """Stimmen Knotenzahl und Besuche des Rollbacks mit den Formeln überein? (Test- und Messhilfe)"""
    dec, ev, end = count_nodes(node)
    counter = Counter()
    rollback(node, counter=counter)
    return dec + ev + end == N.n_nodes(d, b, k) and counter.visits == N.visits_rollback(d, b, k)


# --- Umbauten eines Baums (Eigenschaftstests und Messskript) ----------------------------------------------------------------------------------

def map_payoffs(node, f):
    """Derselbe Baum mit der Abbildung `f` auf jede Auszahlung (z. B. mal 3 oder plus 7)."""
    if node is None:
        return None
    return tuple((name, tuple((p, f(pay), map_payoffs(child, f)) for p, pay, child in branches)) for name, branches in node)


def reverse_choices(node):
    """Dieselben Wahlen in umgekehrter Reihenfolge an jedem Entscheidungsknoten."""
    if node is None:
        return None
    return tuple((name, tuple((p, pay, reverse_choices(child)) for p, pay, child in branches)) for name, branches in reversed(node))


def add_dominated_choice(node, bad=-10000):
    """An jedem Entscheidungsknoten eine zusätzliche, strikt schlechtere Wahl (gleiche Wahrscheinlichkeiten, Auszahlung `bad` je Ast)."""
    if node is None:
        return None
    rebuilt = tuple((name, tuple((p, pay, add_dominated_choice(child, bad)) for p, pay, child in branches)) for name, branches in node)
    name0, branches0 = rebuilt[0]
    return rebuilt + ((name0 + "x", tuple((p, bad, child) for p, _pay, child in branches0)),)


def add_root_choice(node, bonus=5):
    """Eine zusätzliche Wahl nur an der Wurzel (Kopie der ersten Wahl mit `bonus` mehr je Ast): der Wert kann nicht sinken."""
    name0, branches0 = node[0]
    return node + ((name0 + "+", tuple((p, pay + bonus, child) for p, pay, child in branches0)),)
