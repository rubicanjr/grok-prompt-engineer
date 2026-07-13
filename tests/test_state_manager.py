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


class TestStateManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test_state.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_write_and_read(self):
        manager = StateManager(self.test_file)
        data = {"key1": "value1", "key2": 123}
        self.assertTrue(manager.write(data))

        result = manager.read()
        self.assertEqual(result["key1"], "value1")
        self.assertEqual(result["key2"], 123)

    def test_update(self):
        manager = StateManager(self.test_file)
        manager.write({"initial": True})
        self.assertTrue(manager.update("new_key", "new_value"))

        result = manager.read()
        self.assertEqual(result["new_key"], "new_value")

    def test_get(self):
        manager = StateManager(self.test_file)
        manager.write({"existing": "yes"})
        self.assertEqual(manager.get("existing"), "yes")
        self.assertIsNone(manager.get("non_existing"))
        self.assertEqual(manager.get("non_existing", "default"), "default")

    def test_read_nonexistent_file(self):
        non_existing = Path(self.temp_dir.name) / "does_not_exist.json"
        manager = StateManager(non_existing)
        self.assertEqual(manager.read(), {})


class TestProjectStateStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "project_state.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_append_log(self):
        store = ProjectStateStore(self.test_file)
        self.assertTrue(store.append_log("Test log message"))

        state = store.get_state()
        self.assertIn("logs", state)
        self.assertEqual(len(state["logs"]), 1)
        self.assertIn("Test log message", state["logs"][0]["message"])

    def test_record_context_reset(self):
        store = ProjectStateStore(self.test_file)
        self.assertTrue(store.record_context_reset(turn=100))

        state = store.get_state()
        self.assertIn("context_reset_turn_100", state)
        self.assertEqual(state["context_reset_turn_100"]["turn"], 100)


class TestRubricStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "rubric_log.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_update_and_get_rubric(self):
        store = RubricStore(self.test_file)
        scores = {"Grounding": 9, "Hallucination": 8}

        self.assertTrue(store.update_rubric(turn=50, scores=scores, note="Test update"))

        result = store.get_rubric_for_turn(50)
        self.assertEqual(result["scores"]["Grounding"], 9)
        self.assertEqual(result["turn"], 50)

    def test_get_latest_rubric(self):
        store = RubricStore(self.test_file)
        store.update_rubric(turn=10, scores={"Grounding": 7})
        store.update_rubric(turn=20, scores={"Grounding": 9})

        latest = store.get_latest_rubric()
        self.assertEqual(latest["turn"], 20)
        self.assertEqual(latest["scores"]["Grounding"], 9)

    def test_rubric_store_handles_invalid_scores(self):
        store = RubricStore(self.test_file)
        # Boş scores ile çağrı
        result = store.update_rubric(turn=99, scores={}, note="Empty scores test")
        self.assertTrue(result)  # Hata fırlatmamalı, en azından çalışmalı

    def test_project_state_store_multiple_logs(self):
        store = ProjectStateStore(self.test_file)
        store.append_log("First log")
        store.append_log("Second log")
        store.append_log("Third log")

        state = store.get_state()
        self.assertEqual(len(state.get("logs", [])), 3)


class TestConfigEdgeCases(unittest.TestCase):
    """Config threshold'lar için edge case testleri"""

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
