"""Abbildungen: Plotly (alle Achsen gesperrt, `fixedrange`) und der Baum als Graphviz-DOT-Text (nie von Hand koordiniert).

Der Baum wird mit `st.graphviz_chart` gezeichnet: Entscheidungsknoten als Kasten, Ereignisknoten als Kreis, Endknoten als Text mit der Gesamtauszahlung des Pfades.
Dieser Baum ist kein CART: er teilt keine Daten, sondern bewertet eine Folge aus Wahl und Zufall."""

from fractions import Fraction

import numpy as np
import plotly.graph_objects as go

import bst_cap as CAP
import bst_constants as C
from bst_evaluation import bruch, de


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


# --- Experiment 1 -----------------------------------------------------------------------------------------------------------------------------

def build_rules(a: dict):
    """Erwartungswert von G und K über P(hoch); der Streifen zwischen p* und 1/2 ist der Bereich, in dem die beiden Regeln verschieden wählen."""
    cap = a["cap"]
    ps = [j / 100 for j in range(101)]
    fig = go.Figure()
    lo, hi = sorted((float(a["p_star"]), 0.5))
    lo, hi = max(lo, 0.0), min(hi, 1.0)
    if hi > lo:
        fig.add_vrect(x0=lo, x1=hi, fillcolor=C.COLOR_RULE, line_width=0, annotation_text="Regeln wählen verschieden", annotation_position="top left")
    fig.add_trace(go.Scatter(x=ps, y=[float(CAP.ew_period(cap, CAP.G, Fraction(j, 100))) for j in range(101)], mode="lines", name="EW(G)",
                             line=dict(color=C.COLOR_STRATEGY, width=3), hovertemplate="p = %{x:.2f}: EW(G) = %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[0, 1], y=[float(cap.kk)] * 2, mode="lines", name="EW(K)", line=dict(color=C.COLOR_PLAN, width=3),
                             hovertemplate="EW(K) = %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[float(a["p"])], y=[float(a["ew_g"])], mode="markers", name="Ihr p", marker=dict(size=11, color="black"),
                             hovertemplate="p = %{x:.2f}: EW(G) = %{y:.1f}<extra></extra>"))
    fig.add_vline(x=float(a["p_star"]) if 0 <= float(a["p_star"]) <= 1 else 0.5, line_dash="dot", line_color="gray")
    fig.update_xaxes(title_text="P(hoch)", range=[0, 1])
    fig.update_yaxes(title_text="Erwartungswert (GE)")
    return _base(fig)


def tree_dot(cap: CAP.Cap, k: int, step: int) -> str:
    """DOT-Text des Baums für k Perioden (k ≤ 2) beim Rechenschritt `step`: 0 nur Endknoten, danach abwechselnd Ereignisknoten (Mittelwert) und Entscheidungsknoten
    (Maximum), von der letzten Stufe zur Wurzel; optimale Äste sind fett."""
    tree = CAP.build_tree(cap, k)
    lines = ["digraph baum {", "  rankdir=LR;", '  node [fontname="Helvetica", fontsize=11];', '  edge [fontname="Helvetica", fontsize=10];']
    counter = [0]

    def new_id(prefix):
        counter[0] += 1
        return f"{prefix}{counter[0]}"

    def walk(node, level, before):
        """Gibt (Knoten-Id, Wert ab hier) zurück."""
        if node is None:
            nid = new_id("e")
            lines.append(f'  {nid} [shape=plaintext, label="Σ {de(before)}"];')
            return nid, Fraction(0)
        nid = new_id("d")
        shown_dec = step >= 2 * (k - level)
        shown_chance = step >= 2 * (k - level) - 1
        chance_info = []
        for name, branches in node:
            cid = new_id("c")
            value = Fraction(0)
            children = []
            for p, pay, child in branches:
                child_id, child_value = walk(child, level + 1, before + pay)
                value += p * (pay + child_value)
                children.append((child_id, p, pay))
            chance_info.append((name, cid, value, children))
        top = max(v for _n, _c, v, _ch in chance_info)
        label = "Wahl" if level else "Wurzel: Wahl"
        lines.append(f'  {nid} [shape=box, style="rounded,filled", fillcolor="{"#dcefe9" if shown_dec else "white"}", label="{label}{chr(10) + de(top) if shown_dec else ""}"];')
        for name, cid, value, children in chance_info:
            best = shown_dec and value == top
            lines.append(f'  {cid} [shape=circle, style=filled, fillcolor="{"#f7ead9" if shown_chance else "white"}", label="{name}{chr(10) + de(value) if shown_chance else ""}"];')
            lines.append(f'  {nid} -> {cid} [label="{name}", penwidth={3 if best else 1}, color="{"#2F6B65" if best else "gray40"}"];')
            for child_id, p, pay in children:
                lines.append(f'  {cid} -> {child_id} [label="{bruch(p)} | {de(pay)}"];')
        return nid, top

    walk(tree, 0, Fraction(0))
    lines.append("}")
    return "\n".join(lines)


# --- Experiment 3 -----------------------------------------------------------------------------------------------------------------------------

def build_policies(a: dict):
    """Erwartete Gesamtauszahlung der fünf Wahlregeln: beste Strategie, bester fester Plan, gierig, „G nach hoch, K nach niedrig“, Münzwurf."""
    names = ["Beste Strategie (Rollback)", f"Bester fester Plan ({''.join(a['plan_choices'])})", "Gierig (eine Periode voraus)", "G nach hoch, K nach niedrig", "Münzwurf an jedem Knoten"]
    values = [a["strategy"], a["plan"], a["greedy"], a["reactive"], a["coin"]]
    colors = [C.COLOR_STRATEGY, C.COLOR_PLAN, C.COLOR_GREEDY, C.COLOR_REACTIVE, C.COLOR_COIN]
    fig = go.Figure(go.Bar(x=names, y=[float(v) for v in values], marker_color=colors, text=[de(v) for v in values], textposition="outside",
                           hovertemplate="%{x}: %{y:.2f} GE<extra></extra>"))
    fig.update_yaxes(title_text="Erwartete Gesamtauszahlung (GE)")
    fig.update_xaxes(tickangle=0)
    return _base(fig, 380)


def build_distribution(a: dict):
    """Verteilung der Gesamtauszahlung (Wahrscheinlichkeit je möglichem Wert) für die beste Strategie und den besten festen Plan; Marke: sicherer Wert von „immer K“."""
    fig = go.Figure()
    for name, dist, color in (("Beste Strategie", a["dist_strategy"], C.COLOR_STRATEGY), ("Bester fester Plan", a["dist_plan"], C.COLOR_PLAN)):
        items = sorted(dist.items())
        fig.add_trace(go.Bar(x=[float(v) for v, _ in items], y=[float(p) for _, p in items], name=name, marker_color=color, opacity=0.8,
                             hovertemplate="Gesamt %{x:.1f} GE: Wahrscheinlichkeit %{y:.4f}<extra></extra>"))
    fig.add_vline(x=float(a["safe"]), line_dash="dash", line_color="black", annotation_text="immer K (sicher)", annotation_position="top")
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Gesamtauszahlung (GE)")
    fig.update_yaxes(title_text="Wahrscheinlichkeit")
    return _base(fig)


# --- Experiment 4 -----------------------------------------------------------------------------------------------------------------------------

def build_enum(a: dict):
    """Verteilung der Werte aller reduzierten Strategien (Histogramm) mit den Marken Rollback, bester fester Plan, Mittel und den zufällig gezogenen Strategien."""
    values = np.asarray(a["values"], dtype=float)
    fig = go.Figure(go.Histogram(x=values, nbinsx=40 if len(values) > 40 else max(len(values), 2), marker_color="rgba(76,120,168,0.55)", name="Strategien",
                                 hovertemplate="Wert %{x}: %{y} Strategien<extra></extra>"))
    fig.add_vline(x=a["rollback"], line_color=C.COLOR_STRATEGY, line_width=3, annotation_text="Rollback", annotation_position="top")
    fig.add_vline(x=a["plan"], line_color=C.COLOR_PLAN, line_width=2, line_dash="dash", annotation_text="bester Plan", annotation_position="top left")
    fig.add_vline(x=a["mean"], line_color="gray", line_width=2, line_dash="dot", annotation_text="Mittel", annotation_position="bottom right")
    fig.add_trace(go.Scatter(x=[d["value"] for d in a["drawn"]], y=[0] * len(a["drawn"]), mode="markers", name="zufällig gezogen",
                             marker=dict(size=10, color="black", symbol="diamond"), hovertemplate="gezogen: %{x:.2f}<extra></extra>"))
    fig.update_xaxes(title_text="Erwartete Gesamtauszahlung der Strategie (GE)")
    fig.update_yaxes(title_text="Zahl der Strategien")
    return _base(fig)
