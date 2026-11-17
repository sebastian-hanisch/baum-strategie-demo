"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, verschiedene Presets, je Preset die erwartete Verdikt-Zeile (DEMO-PLAYBOOK §11a Punkt 7)."""

import pytest

import bst_constants as C
import bst_evaluation as ev
import bst_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert spec.lo <= preset[key] <= spec.hi, (name, key)
        assert preset["step"] <= 2 * preset["k2"], name                       # der Rechenschritt gibt es nur bis 2·k


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Vier Perioden (Basis)"]) == ev.Settings()
    assert next(iter(C.PRESETS)) == "Vier Perioden (Basis)"


def test_presets_unterscheiden_sich_paarweise():
    seen = {}
    for name, preset in C.PRESETS.items():
        key = tuple(sorted(preset.items()))
        assert key not in seen, f"{name} gleicht {seen.get(key)}"
        seen[key] = name


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS) == set(C.DEFAULTS)


def _plan(name):
    return ev.verdict_plan(ev.analyse_plan(ev.Settings(**C.PRESETS[name])))


def test_verdikt_je_preset_basis_zeigt_den_wert_der_anpassung_aber_nicht_die_gierige_regel():
    kind, text = _plan("Vier Perioden (Basis)")
    assert kind == "success" and "Wert der Anpassung 57,5 GE" in text and "gierige" not in text


def test_verdikt_je_preset_eine_periode_hat_nichts_zu_beobachten():
    kind, text = _plan("Kapazitätsfall (eine Periode)")
    assert kind == "info" and "nichts zu beobachten" in text


def test_verdikt_je_preset_unabhaengige_perioden_melden_keinen_effekt():
    kind, text = _plan("Unabhängige Perioden (q = 1/2)")
    assert kind == "info" and "Wert der Anpassung 0 GE" in text and "lohnt es" not in text


def test_verdikt_je_preset_anpassung_lohnt_nicht_meldet_wert_null():
    kind, text = _plan("Anpassung lohnt nicht (q = 3/5)")
    assert kind == "info" and "Wert der Anpassung 0 GE" in text and "Beobachten bringt hier nichts" in text


def test_verdikt_je_preset_hohe_wechselkosten_der_rollback_schlaegt_die_gierige_regel():
    kind, text = _plan("Hohe Wechselkosten (w = 75)")
    assert kind == "success" and "schlägt hier sogar die gierige Regel: 210 gegen 200 GE" in text


def test_verdikt_je_preset_knapp_wahlen_die_regeln_verschieden():
    kind, text = ev.verdict_one(ev.analyse_one(ev.Settings(**C.PRESETS["Knapp (p = 0,45)"])))
    assert kind == "warning" and "verschenkt 5 GE" in text


@pytest.mark.parametrize("name", ["Vier Perioden (Basis)", "Kapazitätsfall (eine Periode)", "Zwei Perioden von Hand"])
def test_verdikt_eins_bei_p_gleich_einhalb_die_modalregel_kann_nicht_entscheiden(name):
    kind, text = ev.verdict_one(ev.analyse_one(ev.Settings(**C.PRESETS[name])))
    assert kind == "info" and "Bei p = 0,5: EW(G) = 50, EW(K) = 30 GE." in text and "kann nicht entscheiden" in text and "verschenkt" not in text
