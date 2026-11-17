"""Zählweisen eines Entscheidungsbaums (Ereignisknoten): Knoten, Pfade, Pläne, Strategien (reduziert und nicht reduziert), Besuche.

Ein Baum hat k Stufen; an jedem Entscheidungsknoten stehen d Wahlen, an jedem Ereignisknoten b Ausgänge. Alle Zahlen hier sind **Formeln**; sie werden in den Tests
gegen einen Durchlauf des Objektbaums (`bst_tree`) und gegen die Aufzählung verglichen. Jede Zahl braucht ihre Zählweise:

- Knoten gesamt = Entscheidungs- + Ereignis- + Endknoten.
- Pfad = Folge Wahl/Ausgang von der Wurzel bis zu einem Endknoten ((d·b)^k).
- Plan = feste Wahlfolge ohne Beobachtung (d^k).
- Strategie *reduziert* = eine Wahl an jedem Entscheidungsknoten, den die Strategie selbst erreicht: R_k = d · R_(k−1)^b mit R_0 = 1.
- Strategie *nicht reduziert* = eine Wahl an **allen** Entscheidungsknoten: d^(Zahl der Entscheidungsknoten).
- Besuch = ein Knoten, den ein Rechenschritt anfasst (Rollback: jeder Knoten einmal; Aufzählung: je Strategie jeder Knoten ihres erreichbaren Teilbaums).
"""

import math

THIN = " "  # geschütztes Leerzeichen als Tausendertrenner


def n_decision(d: int, b: int, k: int) -> int:
    return sum((d * b) ** t for t in range(k))


def n_events(d: int, b: int, k: int) -> int:
    return d * n_decision(d, b, k)


def n_end(d: int, b: int, k: int) -> int:
    return (d * b) ** k


def n_nodes(d: int, b: int, k: int) -> int:
    """Knoten gesamt: Σ_t (d·b)^t · (1 + d) + (d·b)^k (Entscheidungs-, Ereignis- und Endknoten)."""
    return sum((d * b) ** t * (1 + d) for t in range(k)) + (d * b) ** k


def n_paths(d: int, b: int, k: int) -> int:
    return (d * b) ** k


def n_plans(d: int, k: int) -> int:
    return d**k


def n_strategies_reduced(d: int, b: int, k: int) -> int:
    r = 1
    for _ in range(k):
        r = d * r**b
    return r


def n_strategies_full_exponent(d: int, b: int, k: int) -> int:
    """Exponent der nicht reduzierten Strategienzahl: Zahl der Entscheidungsknoten (die Zahl selbst ist d hoch diesem Exponenten)."""
    return n_decision(d, b, k)


def nodes_per_strategy(d: int, b: int, k: int) -> int:
    """Knoten, die eine reduzierte Strategie erreicht: Entscheidungsknoten Σ b^t, ebenso viele gewählte Ereignisknoten, dazu b^k Endknoten (b = 2: 3·2^k − 2)."""
    reached = sum(b**t for t in range(k))
    return 2 * reached + b**k


def visits_rollback(d: int, b: int, k: int) -> int:
    """Der Rollback fasst jeden Knoten genau einmal an."""
    return n_nodes(d, b, k)


def visits_enumeration(d: int, b: int, k: int) -> int:
    """Aufzählung aller reduzierten Strategien: je Strategie jeder Knoten ihres erreichbaren Teilbaums."""
    return n_strategies_reduced(d, b, k) * nodes_per_strategy(d, b, k)


def first_k_over_page(nodes_per_page: int, d: int = 2, b: int = 2, kmax: int = 40) -> int:
    """Kleinstes k, dessen Baum mehr Knoten hat als `nodes_per_page` (Konvention: so viele Knoten passen auf eine Seite)."""
    for k in range(1, kmax + 1):
        if n_nodes(d, b, k) > nodes_per_page:
            return k
    return kmax + 1


# --- Schreibweise ----------------------------------------------------------------------------------------------------------------------------

def ints(n: int) -> str:
    """Ganzzahl mit geschütztem Leerzeichen als Tausendertrenner ab fünf Stellen (1507328 -> 1 507 328; 2816 bleibt 2816)."""
    s = f"{abs(n)}"
    if len(s) >= 5:
        groups = []
        while s:
            groups.append(s[-3:])
            s = s[:-3]
        s = THIN.join(reversed(groups))
    return ("−" if n < 0 else "") + s


def power_text(base: int, exponent: int, nd: int = 1) -> str:
    """base^exponent als Text: bis 10^15 ausgeschrieben, darüber als Mantisse·10^Exponent (ohne die riesige Zahl auszurechnen)."""
    lg = exponent * math.log10(base)
    if lg < 15:
        return ints(base**exponent)
    e10 = math.floor(lg)
    mant = 10 ** (lg - e10)
    sup = str(e10).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
    return f"{mant:.{nd}f}".replace(".", ",") + f"·10{sup}"


def strategies_reduced_text(d: int, b: int, k: int) -> str:
    """Reduzierte Strategienzahl für d = b = 2 als d^(Exponent) ausgedrückt (R_k = 2^(2^k − 1)); sonst als Ganzzahl."""
    if (d, b) == (2, 2):
        return power_text(2, 2**k - 1)
    return ints(n_strategies_reduced(d, b, k)) if k <= 6 else "sehr groß"


def table_rows(ks, d: int = 2, b: int = 2) -> list[dict]:
    """Zeilen der Tabelle „Zählweisen“ (eine je k) für d Wahlen und b Ausgänge; Zahlen als Ganzzahlen, Texte für die Anzeige."""
    rows = []
    for k in ks:
        rows.append(
            {
                "k": k,
                "decision": n_decision(d, b, k),
                "events": n_events(d, b, k),
                "end": n_end(d, b, k),
                "nodes": n_nodes(d, b, k),
                "paths": n_paths(d, b, k),
                "plans": n_plans(d, k),
                "strategies_reduced_text": strategies_reduced_text(d, b, k),
                "strategies_full_text": power_text(d, n_strategies_full_exponent(d, b, k)),
            }
        )
    return rows
