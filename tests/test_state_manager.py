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


if __name__ == "__main__":
    unittest.main(verbosity=2)
