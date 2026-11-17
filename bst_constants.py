"""Konstanten: Regler-Grenzen, Voreinstellungen, Farben und Presets.

Das Beispiel ist der **Kapazitätsfall**: ausgedacht, ein Modell und kein Fall (Einheit Geldeinheiten GE). Die festen Auszahlungen stehen in `bst_cap.BASIS`;
im ersten Experiment sind sie verstellbar."""

# --- Regler (Name -> (Minimum, Maximum, Voreinstellung)) ----------------------------------------------------------------------------------------

P_MIN, P_MAX, DEFAULT_P = 0, 100, 50            # P(hoch) in Prozent (Experiment 1)
GH_MIN, GH_MAX, DEFAULT_GH = 100, 300, 200      # Auszahlung von G bei hoher Nachfrage (Experiment 1)
GL_MIN, GL_MAX, DEFAULT_GL = -200, 0, -100      # Auszahlung von G bei niedriger Nachfrage (Experiment 1)
KK_MIN, KK_MAX, DEFAULT_KK = 0, 100, 30         # sichere Auszahlung von K (Experiment 1)
Q_MIN, Q_MAX, DEFAULT_Q = 50, 95, 75            # Persistenz q der Nachfrage in Prozent (Seitenleiste)
W_MIN, W_MAX, DEFAULT_W = 0, 200, 25            # Wechselkosten w in GE (Seitenleiste)
K_MIN, K_MAX, DEFAULT_K = 1, 10, 4              # Perioden (Seitenleiste, Experiment 3)
K2_MIN, K2_MAX, DEFAULT_K2 = 1, 3, 2            # Perioden im Rollback von Hand (Experiment 2)
STEP_MIN, STEP_MAX, DEFAULT_STEP = 0, 6, 4      # Rechenschritt (Experiment 2); wirksam bis 2·k2
K4_MIN, K4_MAX, DEFAULT_K4 = 1, 4, 4            # Perioden bei der Aufzählung (Experiment 4); k = 5 hätte 2 147 483 648 Strategien
K5_MIN, K5_MAX, DEFAULT_K5 = 1, 11, 4           # Perioden bei der Baumgröße (Experiment 5)
SEITE_MIN, SEITE_MAX, DEFAULT_SEITE = 20, 500, 100   # Konvention „Knoten je Seite“ (Experiment 5)
SEED_MAX, DEFAULT_SEED = 99999999, 20261116     # Zufalls-Seed für die zufälligen Strategien (Experiment 4)

N_RANDOM_STRATEGIES = 10                         # so viele zufällige Strategien zieht Experiment 4
DIST_K_MAX = 10                                  # die Verteilung der Gesamtauszahlung wird bis hierher aufgezählt (2^k Nachfragefolgen)

# Raster der Befunde (Tests und Experiment 3)
RASTER_Q = ((1, 2), (3, 5), (2, 3), (3, 4), (4, 5), (9, 10), (19, 20))
RASTER_W = (0, 10, 25, 40, 50, 75, 100, 150, 200)
RASTER_K = (2, 3, 4, 6)
ADAPT_Q = ((1, 2), (3, 5), (2, 3), (3, 4), (9, 10))
ADAPT_W = (0, 25, 50)
ADAPT_K = tuple(range(1, 9))

COLOR_STRATEGY = "#2F6B65"
COLOR_PLAN = "#c0762b"
COLOR_GREEDY = "#4c78a8"
COLOR_REACTIVE = "#8c6bb1"
COLOR_COIN = "rgba(150,150,150,0.8)"
COLOR_RULE = "rgba(200,60,60,0.18)"

DEFAULTS = {
    "p_slider": DEFAULT_P,
    "gh_slider": DEFAULT_GH,
    "gl_slider": DEFAULT_GL,
    "kk_slider": DEFAULT_KK,
    "q_slider": DEFAULT_Q,
    "w_slider": DEFAULT_W,
    "k_slider": DEFAULT_K,
    "k2_slider": DEFAULT_K2,
    "step_slider": DEFAULT_STEP,
    "k4_slider": DEFAULT_K4,
    "seed_input": DEFAULT_SEED,
    "k5_slider": DEFAULT_K5,
    "seite_slider": DEFAULT_SEITE,
}


def _preset(**changes):
    """Ein vollständiges Preset: Voreinstellung plus die genannten Änderungen (Schlüssel wie in DEFAULTS, ohne den Zusatz `_slider` bzw. `_input`)."""
    full = {key.rsplit("_", 1)[0]: value for key, value in DEFAULTS.items()}
    unknown = set(changes) - set(full)
    assert not unknown, unknown
    full.update(changes)
    return full


PRESETS = {
    "Vier Perioden (Basis)": _preset(),
    "Kapazitätsfall (eine Periode)": _preset(k=1, k2=1, step=2, k4=1, k5=1),
    "Knapp (p = 0,45)": _preset(p=45),
    "Zwei Perioden von Hand": _preset(k=2, k2=2, step=4, k4=2, k5=2),
    "Unabhängige Perioden (q = 1/2)": _preset(q=50),
    "Anpassung lohnt nicht (q = 3/5)": _preset(q=60),
    "Hohe Wechselkosten (w = 75)": _preset(w=75),
}
PRESET_HELP = {
    "Vier Perioden (Basis)": "Der Kapazitätsfall mit vier Perioden, Persistenz 3/4 und Wechselkosten 25 GE: die Voreinstellung aller Experimente.",
    "Kapazitätsfall (eine Periode)": "Eine Periode, P(hoch) = 1/2: G (+200 oder −100) gegen K (sicher +30). Ein Baum mit 7 Knoten, es gibt nur eine Wahl und keine Beobachtung.",
    "Knapp (p = 0,45)": "P(hoch) = 0,45: der Erwartungswert wählt noch G (35 gegen 30), der wahrscheinlichste Ausgang (niedrig) wählt K. Betrifft Experiment 1.",
    "Zwei Perioden von Hand": "Zwei Perioden, 31 Knoten: der Rollback von Hand, Schritt für Schritt. Alle Experimente auf k = 2.",
    "Unabhängige Perioden (q = 1/2)": "Persistenz 1/2: die Nachfrage jeder Periode ist unabhängig von der Vorperiode. Die Beobachtung sagt nichts voraus, der feste Plan ist schon eine beste Strategie.",
    "Anpassung lohnt nicht (q = 3/5)": "Persistenz 3/5 bei Wechselkosten 25 GE: die Nachfrage ist zu wenig vorhersagbar, um den Wechsel zu bezahlen; der Wert der Anpassung ist 0.",
    "Hohe Wechselkosten (w = 75)": "Wechselkosten 75 GE: hier schlägt der Rollback sogar die gierige Regel (die Wahl mit dem besten Erwartungswert der einen Periode).",
}
