"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bst_cap as CAP  # noqa: E402


@pytest.fixture
def basis():
    """Der Kapazitätsfall mit den Voreinstellungen: G +200/−100, K +30, P(hoch) = 1/2, q = 3/4, w = 25."""
    return CAP.BASIS


@pytest.fixture
def mini_tree():
    """Ein Baum von Hand: eine Wahl zwischen A (50 % +10, 50 % −2) und B (sicher +3), danach eine zweite Wahl C (sicher 0) oder D (+4 bei Ausgang 1)."""
    F = Fraction
    c = (("C", ((F(1), 0, None),)), ("D", ((F(1), 4, None),)))
    return (("A", ((F(1, 2), 10, c), (F(1, 2), -2, c))), ("B", ((F(1), 3, c),)))
