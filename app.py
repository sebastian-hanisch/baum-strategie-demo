"""Entscheiden mit Baum: Erwartungswert, Strategie, Rollback - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Ein ausgedachtes Zahlenbeispiel (Kapazitätsfall, Geldeinheiten GE): ein Modell, kein Fall. Aufbau nach DEMO-PLAYBOOK.md §2: fester Kopf, Schnellstart in der
Seitenleiste, Kernfragen mit Verdikt, fünf Experimente, Grenzen, Formeln.

Lauffähig mit: streamlit run app.py
"""

import time
from fractions import Fraction

import pandas as pd
import streamlit as st

import bst_cap as CAP
import bst_constants as C
import bst_count as N
import bst_evaluation as ev
import bst_visualization as V
from bst_layout import dunkles_design, kopf_css
from bst_presets import (
    SETTING_SPECS,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Entscheiden mit Baum – Sebastian Hanisch", layout="wide")


# --- gerechnete Größen, je nach Reglern zwischengespeichert -------------------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _one(p, gh, gl, kk):
    return ev.analyse_one(ev.Settings(p=p, gh=gh, gl=gl, kk=kk))


@st.cache_data(show_spinner=False)
def _hand(q, w, k2):
    return ev.analyse_hand(ev.Settings(q=q, w=w, k2=k2))


@st.cache_data(show_spinner=False)
def _plan(q, w, k):
    return ev.analyse_plan(ev.Settings(q=q, w=w, k=k))


@st.cache_data(show_spinner=False)
def _enum(q, w, k4, seed):
    t0 = time.perf_counter()
    a = ev.analyse_enum(ev.Settings(q=q, w=w, k4=k4, seed=seed))
    return a, time.perf_counter() - t0


@st.cache_data(show_spinner=False)
def _size(k5, q, w):
    return ev.analyse_size(ev.Settings(q=q, w=w, k5=k5, seite=C.DEFAULT_SEITE))


@st.cache_data(show_spinner=False)
def _greedy_raster():
    return ev.greedy_raster()


@st.cache_data(show_spinner=False)
def _adaptation_raster():
    return ev.adaptation_raster()


@st.cache_data(show_spinner=False)
def _greedy_table(k):
    rows = {}
    for qn, qd in C.RASTER_Q:
        rows[f"q = {qn}/{qd}" if qd != 1 else f"q = {qn}"] = {f"w = {w}": float(ev.greedy_gap(Fraction(qn, qd), w, k)) for w in C.RASTER_W}
    return pd.DataFrame(rows).T


@st.cache_data(show_spinner=False)
def _adaptation_table(k):
    rows = {}
    for qn, qd in C.ADAPT_Q:
        rows[f"q = {qn}/{qd}"] = {f"w = {w}": float(CAP.adaptation_value(CAP.make_cap(q=Fraction(qn, qd), w=w), k)) for w in C.ADAPT_W}
    return pd.DataFrame(rows).T


def _zwei_stellen(df):
    """Zahlenspalten mit zwei Nachkommastellen (der Browser setzt das Dezimalzeichen nach seiner Locale)."""
    return {c: st.column_config.NumberColumn(format="%.2f") for c in df.columns}


def show(verdict):
    kind, text = verdict
    getattr(st, kind)(text)


def settings_from_state() -> ev.Settings:
    ss = st.session_state
    return ev.Settings(**{spec.url_param: int(ss[key]) for key, spec in SETTING_SPECS.items()})


# --- Kopf, Einleitung ---------------------------------------------------------------------------------------------------------------------------

st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🌳 Entscheiden mit Baum: Erwartungswert, Strategie, Rollback")
st.markdown(
    """
**Ein ausgedachtes Zahlenbeispiel, ein Modell und kein Fall:** der **Kapazitätsfall** in Geldeinheiten (GE). Soll man **groß (G)** oder **klein (K)** bauen? G zahlt +200 bei hoher und −100 bei niedriger Nachfrage, K zahlt sicher +30.
Die Demo führt vom **Erwartungswert** einer einzigen Wahl über den **Entscheidungsbaum (Ereignisknoten)** zur **Strategie**: einer Wahl an jedem Knoten, den man erreicht. Der **Rollback** (Rückwärtsrechnung) findet sie,
und die Falle ist, einen festen Plan für eine Strategie zu halten. Alles ist Lehrbuchstoff; neu ist nur die Vorführbarkeit mit Zähleinheiten (Knoten, Besuche, Strategien).
Dieser Baum ist **kein CART** ([cart-demo](https://github.com/sebastian-hanisch/cart-demo)): CART teilt Daten nach Merkmalen, hier wird eine Folge aus Wahl und Zufall bewertet.

Weiter unten: **❓ Kernfragen**, fünf Experimente (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert der Baum", expanded=True):
    st.markdown(
        """
1. **Zwei Arten von Knoten.** Am **Entscheidungsknoten** (Kasten) wählt man, am **Ereignisknoten** (Kreis) entscheidet der Zufall, hier die Nachfrage. Am Ende jedes Pfades steht eine Gesamtauszahlung.
2. **Rollback (Rückwärtsrechnung).** Von den Endknoten her an Ereignisknoten **mitteln** (mit den Wahrscheinlichkeiten gewichtet), an Entscheidungsknoten **maximieren**. Raiffa/Schlaifer 1961 (Abschn. 1.2.1) nennen das „backwards induction“;
   das Wort „Rollback“ ist Lehrbuch- und Softwarejargon.
3. **Strategie gegen Plan.** Eine **Strategie** wählt an jedem Entscheidungsknoten, den sie erreicht, nach dem, was bis dahin eingetreten ist. Ein **fester Plan** legt die Wahlen im Voraus fest und beobachtet nichts. Jeder Plan ist eine Strategie, aber nicht umgekehrt.
4. **Mehrere Perioden.** In jeder Periode wird G oder K **vor** der Nachfrage gewählt und **nach** Beobachtung der Vorperiode. Die Nachfrage bleibt mit Wahrscheinlichkeit q (Persistenz) wie in der Vorperiode; ein Wechsel der Wahl kostet w.
   Beides sind **eigene Annahmen dieser Demo**, damit die Beobachtung überhaupt etwas wert sein kann.
5. **Voraussetzungen des Baums** (Howard/Matheson 2005, Abschn. 13): ein einziger Entscheider und „no-forgetting“ (Beobachtetes wird nicht vergessen). Beides gilt im Modell.

| Zählweise | Bedeutung (Entscheidungsbaum mit 2 Wahlen und 2 Ausgängen, k Perioden) |
|---|---|
| Knoten gesamt | Entscheidungs- + Ereignis- + Endknoten = 2·4^k − 1 |
| Pfad | Folge Wahl/Ausgang von der Wurzel bis zu einem Endknoten (4^k) |
| Plan | feste Wahlfolge ohne Beobachtung (2^k) |
| Strategie, **reduziert** | eine Wahl an jedem Knoten, den die Strategie selbst erreicht: 2^(2^k − 1) |
| Strategie, **nicht reduziert** | eine Wahl an **allen** Entscheidungsknoten: 2^((4^k − 1)/3) |
| Besuch | ein Knoten, den ein Rechenschritt anfasst |

„Strategien“ ohne Zusatz heißt in dieser Demo **reduziert** gezählt.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Mehrere Perioden** (Ergebnis, Experimente 2 bis 4)")
    q_pct = st.slider("Persistenz q der Nachfrage (%)", *bounds("q_slider"), key="q_slider", step=1,
                      help="Wahrscheinlichkeit, dass die Nachfrage der nächsten Periode wie die der Vorperiode ist. 50 % heißt: unabhängige Perioden.")
    w = st.slider("Wechselkosten w (GE)", *bounds("w_slider"), key="w_slider", step=5,
                  help="Kosten, wenn die Wahl gegenüber der Vorperiode wechselt (nicht in Periode 1).")
    k = st.slider("Perioden k", *bounds("k_slider"), key="k_slider", help="Zahl der Perioden im Ergebnis und in Experiment 3.")

# --- Ergebnis -----------------------------------------------------------------------------------------------------------------------------------

plan = _plan(int(q_pct), int(w), int(k))
st.markdown("## 🎯 Ergebnis: beste Strategie gegen festen Plan")
m1, m2, m3 = st.columns(3)
# Delta immer als „mein Wert minus Referenz“ (Vorzeichen-Falle, DEMO-PLAYBOOK §2)
m1.metric("Beste Strategie (Rollback)", f"{ev.de(plan['strategy'])} GE", delta=f"{ev.de(plan['strategy'] - plan['plan'])} gegen besten Plan", delta_color="normal")
m2.metric(f"Bester fester Plan ({ev.plan_text(plan['plan_choices'])})", f"{ev.de(plan['plan'])} GE", delta="Referenz", delta_color="off")
m3.metric("Wert der Anpassung", f"{ev.de(plan['adaptation'])} GE", delta=f"k = {k}, q = {q_pct} %, w = {w} GE", delta_color="off")
st.plotly_chart(V.build_policies(plan), width="stretch", key="main_chart")
st.caption("Erwartete Gesamtauszahlung in GE (Zähleinheit: Erwartungswert über die Nachfragefolgen). Das Beispiel ist ausgedacht; die Zahlen gelten in diesem Modell, bei diesen Reglern.")

# --- Kernfragen ---------------------------------------------------------------------------------------------------------------------------------

S = settings_from_state()
one = _one(S.p, S.gh, S.gl, S.kk)
with st.spinner("Bewerte alle Strategien ..."):
    (enum_a, enum_seconds) = _enum(int(q_pct), int(w), S.k4, S.seed)

st.markdown("## ❓ Kernfragen")
st.markdown("**1. Was heißt „nach dem Erwartungswert entscheiden“?** (Experiment 1)")
show(ev.verdict_one(one))
st.markdown("**2. Was ist eine Strategie, und wie findet der Rollback sie?** (Experiment 4)")
show(ev.verdict_enum(enum_a))
st.markdown("**3. Wann nützt es, auf Beobachtungen zu reagieren?** (Ergebnis oben, Experiment 3)")
show(ev.verdict_plan(plan))

st.markdown("---")

# --- Experiment 1 -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Ein Knoten, Erwartungswert und wahrscheinlichster Ausgang")
st.caption("Eine Periode: ein Entscheidungsknoten, zwei Ereignisknoten, vier Endknoten (7 Knoten). Die vier Regler hier gelten nur für dieses Experiment.")
c1, c2, c3, c4 = st.columns(4)
p_pct = c1.slider("P(hoch) in %", *bounds("p_slider"), key="p_slider", step=1, help="Wahrscheinlichkeit der hohen Nachfrage.")
gh = c2.slider("G bei hoher Nachfrage", *bounds("gh_slider"), key="gh_slider", step=10)
gl = c3.slider("G bei niedriger Nachfrage", *bounds("gl_slider"), key="gl_slider", step=10)
kk = c4.slider("K (sicher)", *bounds("kk_slider"), key="kk_slider", step=5)
one = _one(int(p_pct), int(gh), int(gl), int(kk))
e1, e2, e3 = st.columns(3)
e1.metric("EW(G)", f"{ev.de(one['ew_g'])} GE")
e2.metric("EW(K)", f"{ev.de(one['ew_k'])} GE")
e3.metric("Schwelle p*", ev.bruch(one["p_star"]), delta=f"≈ {ev.de(float(one['p_star']), 4)}", delta_color="off")
left, right = st.columns([3, 2])
with left:
    st.plotly_chart(V.build_rules(one), width="stretch", key="rules_chart")
with right:
    st.graphviz_chart(V.tree_dot(one["cap"], 1, 2))
st.caption(
    "Zwei Regeln: **nach dem Erwartungswert** (G ab p > p*) und **nach dem wahrscheinlichsten Ausgang** (G nur, wenn „hoch“ wahrscheinlicher ist, also p > 1/2). Der Verlust ist der Mehrwert des Erwartungswerts gegenüber der anderen Regel "
    "in GE im Erwartungswert, ein Maß gegen das Optimum des Modells und nicht das Savage-Kriterium („Minimax-Regret“). Raster: p = j/300, j = 0 bis 300 ohne p = 1/2."
)
show(ev.verdict_one(one))

st.markdown("---")

# --- Experiment 2 -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Rollback von Hand")
st.caption("Persistenz q und Wechselkosten w kommen aus der Seitenleiste, die Auszahlungen sind die des Kapazitätsfalls (+200 / −100 / +30). Der Baum wird bis k = 2 gezeichnet; bei k = 3 hat er 127 Knoten, dann zeigt die Tabelle die Zustände.")
h1, h2 = st.columns(2)
k2 = h1.slider("Perioden k", *bounds("k2_slider"), key="k2_slider", help="Eine, zwei oder drei Perioden.")
st.session_state["step_slider"] = min(int(st.session_state["step_slider"]), 2 * int(k2))   # Schritte gibt es nur bis 2·k (vor dem Zeichnen des Reglers)
step = h2.slider("Rechenschritt", 0, 2 * int(k2), key="step_slider", help="0: Endknoten; danach abwechselnd Ereignisknoten (mitteln) und Entscheidungsknoten (maximieren), von der letzten Stufe zur Wurzel.")
hand = _hand(int(q_pct), int(w), int(k2))
st.markdown(f"**Schritt {step}:** {ev.step_text(int(k2), int(step))}")
if int(k2) <= 2:
    st.graphviz_chart(V.tree_dot(hand["cap"], int(k2), int(step)))
else:
    st.info(f"k = {k2}: {N.ints(hand['nodes'])} Knoten sind zu viele zum Zeichnen. Die Tabelle zeigt, was der Rollback je Zustand rechnet.")
rows = [
    {"Stufe": r["stage"], "Zustand (letzte Wahl, letzte Nachfrage)": ev.state_name(r["state"]), "EW(G) inkl. Rest": ev.de(r["ew_g"]), "EW(K) inkl. Rest": ev.de(r["ew_k"]),
     "Wahl": " oder ".join(r["choice"]) + (" (indifferent)" if len(r["choice"]) > 1 else ""), "Wert": ev.de(r["value"])}
    for r in hand["rows"]
]
rows.append({"Stufe": 1, "Zustand (letzte Wahl, letzte Nachfrage)": "Start", "EW(G) inkl. Rest": ev.de(hand["root_g"]), "EW(K) inkl. Rest": ev.de(hand["root_k"]),
             "Wahl": " oder ".join(hand["root_best"]) + (" (indifferent)" if len(hand["root_best"]) > 1 else ""), "Wert": ev.de(hand["sol"].value)})
st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
if hand["strategies"] is not None:
    st.caption(f"Alle {N.ints(hand['n_strategies'])} Strategien (reduziert gezählt), nach Wert sortiert (GE): " + "; ".join(ev.de(v) for v in hand["strategies"]) + ".")
show(ev.verdict_hand(hand))

st.markdown("---")

# --- Experiment 3 -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Plan oder Strategie? Die Falle")
st.caption("Persistenz q, Wechselkosten w und Perioden k stehen in der Seitenleiste; das Balkendiagramm oben zeigt die fünf Wahlregeln. „Gierig“: in jeder Periode die Wahl mit dem besten Erwartungswert dieser einen Periode einschließlich Wechselkosten. "
           "„Münzwurf“: an jedem Knoten fair gewürfelt (sein Wert ist das Mittel über alle Strategien).")
show(ev.verdict_plan(plan))
st.markdown("**Verteilung der Gesamtauszahlung: der Erwartungswert ist ein Mittel, kein Pfad.**")
st.plotly_chart(V.build_distribution(plan), width="stretch", key="dist_chart")
show(ev.verdict_distribution(plan))
st.caption(f"Aufgezählt werden die 2^{k} = {N.ints(2 ** int(k))} Nachfragefolgen. Ob die Strategie öfter unter dem sicheren Wert landet als der feste Plan, wechselt mit k (Basisfall, bis k = 8 gemessen: k = 2 und 4 ja, k = 1 und 3 gleich, ab k = 5 nein); das Verdikt nennt deshalb nur die Zahlen des eingestellten k.")

with st.expander("Wo schlägt der Rollback die gierige Regel? (Raster Persistenz × Wechselkosten)"):
    gr = _greedy_raster()
    st.markdown(f"Abstand **Rollback minus gierig** in GE für k = {k} (Zeilen: q, Spalten: w). Über das ganze Raster q × w × k ∈ {{{', '.join(map(str, C.RASTER_K))}}} ({gr['n']} Zellen): "
                f"Rollback besser in **{gr['better']}**, gleich in {gr['equal']}, schlechter in {gr['worse']}. Im Basisfall (q = 3/4, w = 25) ist die gierige Regel schon optimal.")
    st.dataframe(_greedy_table(int(k)), width="stretch", column_config=_zwei_stellen(_greedy_table(int(k))))
with st.expander("Wann nützt das Anpassen? (Raster Persistenz × Wechselkosten)"):
    ar = _adaptation_raster()
    st.markdown(f"**Wert der Anpassung** (Strategie minus bester fester Plan) in GE für k = {k}. Über das ganze Raster q × w × k = 1 bis 8 ({ar['n']} Zellen): Wert 0 in **{ar['zero']}** Zellen, größer als 0 in {ar['positive']}, negativ in {ar['negative']} "
                "(ein fester Plan ist selbst eine Strategie, der Wert kann nicht negativ sein).")
    st.dataframe(_adaptation_table(int(k)), width="stretch", column_config=_zwei_stellen(_adaptation_table(int(k))))
    st.caption("Bei zwei Perioden wechselt man nach (G, niedrig) zu K genau dann, wenn q > (170 + w)/300; bei w = 25 ist die Schwelle 13/20.")

st.markdown("---")

# --- Experiment 4 -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Aufzählen oder Rollback?")
st.caption("Alle reduzierten Strategien werden bewertet und mit dem Rollback verglichen. Ab k = 5 gibt es 2 147 483 648 Strategien: das ist nur noch eine Zahl, keine Aufzählung.")
a1, a2 = st.columns([1, 1])
k4 = a1.slider("Perioden k", *bounds("k4_slider"), key="k4_slider", help="Aufgezählt wird bis k = 4 (32 768 Strategien).")
with a2:
    st.number_input("Zufalls-Seed für die zufälligen Strategien", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Zufalls-Seed ziehen", width="stretch", on_click=randomize_seed)
with st.spinner(f"Bewerte {N.ints(N.n_strategies_reduced(2, 2, int(k4)))} Strategien ..."):
    enum_a, enum_seconds = _enum(int(q_pct), int(w), int(k4), int(st.session_state["seed_input"]))   # zwischengespeichert: die Zeit gilt für die erste Rechnung
st.plotly_chart(V.build_enum(enum_a), width="stretch", key="enum_chart")
t1, t2 = st.columns(2)
with t1:
    st.markdown("**Knotenbesuche (Zähleinheit: ein Knoten wird angefasst)**")
    st.dataframe(pd.DataFrame([
        {"Verfahren": "Rollback", "Besuche": N.ints(enum_a["visits_rollback"]), "Rechnung": "jeder Knoten einmal: 2·4^k − 1"},
        {"Verfahren": "Aufzählung aller Strategien", "Besuche": N.ints(enum_a["visits_enum"]), "Rechnung": "Strategien × (3·2^k − 2) Knoten je Strategie"},
    ]), width="stretch", hide_index=True)
with t2:
    st.markdown(f"**{C.N_RANDOM_STRATEGIES} zufällig gezogene Strategien** (Zufalls-Seed {st.session_state['seed_input']})")
    st.dataframe(pd.DataFrame([
        {"Nr": i + 1, "Wert (GE)": ev.de(d["value"]), "erste Wahl": d["first"], "über dem besten Plan": "ja" if d["value"] > enum_a["plan"] + 1e-9 else "nein"}
        for i, d in enumerate(enum_a["drawn"])
    ]), width="stretch", hide_index=True)
st.caption(f"Rechenzeit dieser Bewertung: {enum_seconds:.2f} s (vektorisiert, einmal gemessen, Größenordnung). Der Zahl der Besuche liegt der Durchlauf zugrunde, den die Tests mit dem Objektbaum nachzählen.")
show(ev.verdict_enum(enum_a))

st.markdown("---")

# --- Experiment 5 -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Wie groß wird der Baum?")
st.caption("Der Baum wächst um den Faktor 4 je Periode, die Zahl der Strategien doppelt exponentiell. Die Zeit der Feldfassung (der volle Baum als numpy-Felder) wird hier bei jedem neuen k einmal gemessen.")
z1, z2 = st.columns(2)
k5 = z1.slider("Perioden k", *bounds("k5_slider"), key="k5_slider", help="Bis k = 11: 8 388 607 Knoten.")
seite = z2.slider("Knoten je Seite (Konvention)", *bounds("seite_slider"), key="seite_slider", step=10,
                  help="Wie viele Knoten auf eine Seite passen, ist eine Konvention, kein Messwert. Voreinstellung 100.")
with st.spinner("Rechne den vollen Baum ..."):
    size = dict(_size(int(k5), int(q_pct), int(w)))
size["seite"] = int(seite)
size["first_k_over_page"] = N.first_k_over_page(int(seite))
size_rows = [
    {"k": r["k"], "Entscheidungsknoten": N.ints(r["decision"]), "Ereignisknoten": N.ints(r["events"]), "Endknoten": N.ints(r["end"]), "Knoten gesamt": N.ints(r["nodes"]),
     "Pfade": N.ints(r["paths"]), "Pläne": N.ints(r["plans"]), "Strategien (reduziert)": r["strategies_reduced_text"], "Strategien (nicht reduziert)": r["strategies_full_text"],
     "gewählt": "◀" if r["k"] == int(k5) else ""}
    for r in size["rows"]
]
st.dataframe(pd.DataFrame(size_rows), width="stretch", hide_index=True)
s1, s2, s3 = st.columns(3)
s1.metric("Knoten", N.ints(size["nodes"]))
s2.metric("Rechenzeit Feldfassung", f"{size['field_seconds']:.3f} s", delta="jetzt gemessen, Größenordnung", delta_color="off")
s3.metric("Rechenzeit Objektbaum", f"{size['object_seconds']:.3f} s" if size["object_seconds"] is not None else "nicht gebaut", delta="nur bis k = 7", delta_color="off")
st.caption("Dieselbe Rechnung über die vier Zustände (letzte Wahl, letzte Nachfrage) statt über 2·4^k − 1 Knoten steht in `baum-waechst-demo`; dort auch, was ein Einflussdiagramm daran ändert. Der Rollback als Rechnung über Zustände: `bestell-rueckwaerts-demo`.")
show(ev.verdict_size(size))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Wahrscheinlichkeiten sind bekannt und feststehend** | Schon die Schwelle p* = 13/30 zeigt, wie nah die Wahl an der Kante liegt: Der Erwartungswert wählt ab p > 13/30, die Modalregel erst ab p > 1/2. Wie sicher p sein muss, damit die Wahl hält, rechnet die Nachbar-Demo. | [kipp-schwelle-demo](https://github.com/sebastian-hanisch/kipp-schwelle-demo) |
| **Beobachtungen treffen einfach ein** (Information kostenlos und vollkommen) | Der Baum kennt hier nur die Nachfrage der Vorperiode. Ein Test mit Fehlerquote und Preis ist ein eigenes Entscheidungsproblem. | [testwert-evsi-demo](https://github.com/sebastian-hanisch/testwert-evsi-demo) |
| **Das Modell stimmt** (Persistenz, Wechselkosten, Auszahlungen ausgedacht) | Die Zahl der Strategien und der Rollback-Wert ändern sich mit q und w: bei q = 3/5 und w = 25 ist der Wert der Anpassung für k = 1 bis 8 überall 0, bei q = 3/4 und w = 25 sind es für k = 4 57,5 GE. | – |
| **Der Erwartungswert reicht** (Risikoneutralität) | Die beste Strategie hat im Erwartungswert 115 GE bei k = 2 und liegt mit Wahrscheinlichkeit 1/2 unter dem sicheren Wert 60 GE von „immer K“. | [risiko-aequivalent-demo](https://github.com/sebastian-hanisch/risiko-aequivalent-demo) |
| **Der Baum bleibt aufschreibbar** | Bei k = 3 hat er 127 Knoten, bei k = 5 2 047 Knoten und 2 147 483 648 Strategien (reduziert gezählt). Rechenbar bleibt er über die Zustände. | [baum-waechst-demo](https://github.com/sebastian-hanisch/baum-waechst-demo) |
| **Ein Entscheider, nichts wird vergessen** (Howard/Matheson 2005, Abschn. 13) | Mehrere Entscheider oder vergessene Beobachtungen machen aus dem Baum ein anderes Problem; die Demo bildet das nicht ab. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Gegeben ist der Kapazitätsfall (ausgedacht, ein Modell): in jeder von $k$ Perioden wählt man $G$ oder $K$ und sieht danach die Nachfrage. Gesucht ist die Wahlregel mit dem größten Erwartungswert der Gesamtauszahlung.

| Symbol | Bedeutung |
|---|---|
| $g_h,\ g_n$ | Auszahlung von $G$ bei hoher bzw. niedriger Nachfrage (+200, −100 GE) |
| $c$ | sichere Auszahlung von $K$ (+30 GE) |
| $p$ | Wahrscheinlichkeit der hohen Nachfrage (Experiment 1); in Periode 1 gleich 1/2 |
| $q$ | Persistenz: Wahrscheinlichkeit, dass die Nachfrage wie in der Vorperiode ist (Voreinstellung 3/4) |
| $w$ | Wechselkosten, wenn die Wahl von der Vorperiode abweicht (Voreinstellung 25 GE; nicht in Periode 1) |
| $k$ | Zahl der Perioden |
| $s=(a_{t-1},d_{t-1})$ | Zustand vor der Wahl der Periode $t$: letzte Wahl und letzte Nachfrage |
| $V_t(s)$ | bester Erwartungswert der Perioden $t,\dots,k$ ab dem Zustand $s$ (Rollback-Wert), $V_{k+1}=0$ |

**Eine Periode.**

$$\mathrm{EW}(G)=p\,g_h+(1-p)\,g_n,\qquad \mathrm{EW}(K)=c,\qquad p^{*}=\frac{c-g_n}{g_h-g_n}=\frac{30+100}{200+100}=\frac{13}{30}.$$

Die Regel „wahrscheinlichster Ausgang“ wählt $G$ genau für $p>1/2$; beide Regeln wählen verschieden für $13/30<p<1/2$.

**Rollback über die Zustände.** Mit $p_t(s)=1/2$ für $t=1$ und sonst $p_t(s)=q$ nach hoher, $1-q$ nach niedriger Nachfrage gilt

$$V_t(s)=\max_{a\in\{G,K\}}\Big[\,p_t(s)\,r(a,h)+(1-p_t(s))\,r(a,n)-w\,\mathbf 1[a\neq a_{t-1}]+p_t(s)\,V_{t+1}(a,h)+(1-p_t(s))\,V_{t+1}(a,n)\Big],$$

mit $r(G,h)=g_h$, $r(G,n)=g_n$, $r(K,\cdot)=c$. Das ist die Gleichung des Rollback (Mitteln, Maximieren, Zurückfalten) aus Raiffa/Schlaifer 1961, Abschn. 1.2.1, in eigener Schreibweise für dieses Modell. Der Baum hat dieselbe Rechnung an $2\cdot4^k-1$ Knoten; die Zustände fassen
jeweils alle Knoten mit demselben $s$ zusammen (vier je Stufe).

**Fester Plan.** Mit der Randverteilung $m_1=1/2$, $m_{t+1}=q\,m_t+(1-q)(1-m_t)$ ist der Wert einer Wahlfolge $a_1,\dots,a_k$
$$\sum_{t=1}^{k}\big[m_t\,r(a_t,h)+(1-m_t)\,r(a_t,n)-w\,\mathbf 1[a_t\neq a_{t-1}]\big].$$
Der **Wert der Anpassung** ist $V_1(\text{Start})$ minus dem besten Planwert; er ist nie negativ, weil jeder Plan eine Strategie ist.

**Zählweisen** bei $d=2$ Wahlen und $b=2$ Ausgängen:
$$\text{Knoten }2\cdot4^k-1,\qquad R_k=2\,R_{k-1}^{2},\ R_0=1\ \Rightarrow\ R_k=2^{\,2^k-1},\qquad \text{nicht reduziert }2^{(4^k-1)/3}.$$
Die Aufzählung besucht je Strategie $3\cdot2^k-2$ Knoten, insgesamt $R_k\,(3\cdot2^k-2)$; der Rollback besucht jeden Knoten einmal ($2\cdot4^k-1$).

**Literatur.** Raiffa, H., Schlaifer, R. (1961): *Applied Statistical Decision Theory*, Harvard University, Abschn. 1.2.1, S. 7–8, Gl. 1-1 bis 1-4 (Rückwärtsinduktion). Howard, R. A., Matheson, J. E. (2005): „Influence Diagrams“, *Decision Analysis* 2(3), 127–143, Abschn. 13
(einziger Entscheider, no-forgetting). Gelesen nach den eigenen Notizen der Quellenprüfung; Gleichungen hier in eigenen Worten.
        """
    )

sync_query_params({key: int(st.session_state[key]) for key in SETTING_SPECS})

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Entscheidungsanalyse: Information, Risiko, Grenzen](https://sebastianhanisch.net/konzepte-entscheidungsanalyse.html)."
)
