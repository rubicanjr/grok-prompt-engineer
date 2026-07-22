"""
Unit Tests for StateManager ve ProjectStateStore
"""

import unittest
import tempfile
from pathlib import Path
from state_manager import StateManager, ProjectStateStore


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
        self.assertEqual(result.get("key1"), "value1")

    def test_update(self):
        manager = StateManager(self.test_file)
        manager.write({"initial": True})
        self.assertTrue(manager.update("new_key", "new_value"))
        result = manager.read()
        self.assertEqual(result.get("new_key"), "new_value")

    def test_project_state_store_basic(self):
        store = ProjectStateStore(self.test_file)
        store.set_state({"test": "value"})
        result = store.get_state()
        self.assertEqual(result.get("test"), "value")

    def test_append_log(self):
        """append_log Markdown log dosyasına yazabilmeli."""
        store = ProjectStateStore(self.test_file)
        result = store.append_log("Test log message")
        self.assertTrue(result)

class TestRubricStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test_rubric.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_update_and_get_rubric(self):
        from rubric_store import RubricStore
        store = RubricStore(self.test_file)
        scores = {"Grounding": 10, "Hallucination": 9}
        self.assertTrue(store.update_rubric(1, scores, "test note"))
        data = store.get_rubric_for_turn(1)
        self.assertEqual(data.get("turn"), 1)
        self.assertEqual(data.get("scores"), scores)

    def test_duplicate_rubric_returns_false(self):
        from rubric_store import RubricStore
        store = RubricStore(self.test_file)
        scores = {"Grounding": 10}
        self.assertTrue(store.update_rubric(5, scores, "first"))
        self.assertFalse(store.update_rubric(5, scores, "duplicate"))

    def test_get_latest_and_all_rubrics(self):
        from rubric_store import RubricStore
        store = RubricStore(self.test_file)
        store.update_rubric(1, {"Grounding": 8}, "t1")
        store.update_rubric(2, {"Grounding": 9}, "t2")
        latest = store.get_latest_rubric()
        self.assertEqual(latest.get("turn"), 2)
        all_rubrics = store.get_all_rubrics()
        self.assertEqual(len(all_rubrics), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
