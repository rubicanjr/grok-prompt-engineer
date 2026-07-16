"""
Unit Tests for StateManager, ProjectStateStore ve RubricStore
"""
import unittest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from state_manager import StateManager, ProjectStateStore
from rubric_store import RubricStore

class TestConfigEdgeCases(unittest.TestCase):
    """Config threshold'lar için edge case testleri"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "config_edge_state.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_negative_context_reset_threshold(self):
        """CONTEXT_RESET_TURN_THRESHOLD negatif değer aldığında sistem çökmemeli."""
        import config as config_module
        original_value = config_module.CONTEXT_RESET_TURN_THRESHOLD
        try:
            config_module.CONTEXT_RESET_TURN_THRESHOLD = -5
            self.assertEqual(config_module.CONTEXT_RESET_TURN_THRESHOLD, -5)
        finally:
            config_module.CONTEXT_RESET_TURN_THRESHOLD = original_value

    def test_zero_max_retries(self):
        """MAX_RETRIES sıfır olduğunda sistem çökmemeli."""
        import config as config_module
        original_value = config_module.MAX_RETRIES
        try:
            config_module.MAX_RETRIES = 0
            self.assertEqual(config_module.MAX_RETRIES, 0)
        finally:
            config_module.MAX_RETRIES = original_value

    def test_very_high_rubric_threshold(self):
        """RUBRIC_CRITICAL_THRESHOLD çok yüksek değer aldığında sistem çökmemeli."""
        import config as config_module
        original_value = config_module.RUBRIC_CRITICAL_THRESHOLD
        try:
            config_module.RUBRIC_CRITICAL_THRESHOLD = 9999
            self.assertEqual(config_module.RUBRIC_CRITICAL_THRESHOLD, 9999)
        finally:
            config_module.RUBRIC_CRITICAL_THRESHOLD = original_value

    def test_string_in_max_retries(self):
        """MAX_RETRIES string değer aldığında (tip güvenliği kontrolü)."""
        import config as config_module
        original_value = config_module.MAX_RETRIES
        try:
            config_module.MAX_RETRIES = "invalid"
            self.assertEqual(config_module.MAX_RETRIES, "invalid")
        finally:
            config_module.MAX_RETRIES = original_value

    def test_none_in_auto_context_reset(self):
        """ENABLE_AUTO_CONTEXT_RESET None olduğunda."""
        import config as config_module
        original_value = config_module.ENABLE_AUTO_CONTEXT_RESET
        try:
            config_module.ENABLE_AUTO_CONTEXT_RESET = None
            self.assertIsNone(config_module.ENABLE_AUTO_CONTEXT_RESET)
        finally:
            config_module.ENABLE_AUTO_CONTEXT_RESET = original_value

    def test_clear_old_logs(self):
        store = ProjectStateStore(self.test_file)
        for i in range(60):
            store.append_log(f"Log {i}")
        self.assertTrue(store.clear_old_logs(keep_last=20))
        state = store.get_state()
        self.assertEqual(len(state.get("logs", [])), 20)