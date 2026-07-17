#!/usr/bin/env python3
"""
Temel Entegrasyon Testleri - execution_engine.py
"""
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import shutil

from execution_engine import update_rubric

# === Rubric Testleri (Tamamen Fixture ile İzole) ===

def test_update_rubric_adds_new_turn(isolated_artifacts):

    # Yüksek turn numarası kullan (get_current_turn sorununu bypass eder)
    new_turn = 9999
    scores = {
        "Grounding": 10, "Hallucination": 10, "Bias": 10,
        "Token": 9, "Yapı": 10, "Self-Evolving": 9
    }

    result = update_rubric(new_turn, scores, "Integration test")
    assert result is True


def test_update_rubric_prevents_duplicate(isolated_artifacts):

    turn = 10000
    scores = {
        "Grounding": 10, "Hallucination": 10, "Bias": 10,
        "Token": 9, "Yapı": 10, "Self-Evolving": 9
    }

    first_result = update_rubric(turn, scores, "First")
    assert first_result is True

    second_result = update_rubric(turn, scores, "Duplicate")
    assert second_result is False


class TestExecutionEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)


    @patch('config.ENABLE_AUTO_CONTEXT_RESET', False)
    def test_context_reset_disabled_by_config(self):
        from execution_engine import ExecutionEngine

        engine = ExecutionEngine()
        try:
            engine._perform_context_reset_if_needed(turn=50)
        except Exception as e:
            self.fail(f"Context Reset çağrısı hata verdi: {e}")