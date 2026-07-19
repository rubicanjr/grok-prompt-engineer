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

    def test_append_log_and_clear(self):
        store = ProjectStateStore(self.test_file)
        for i in range(25):
            store.append_log(f"Log {i}")

        # clear_old_logs metodu varsa test et
        if hasattr(store, "clear_old_logs"):
            store.clear_old_logs(keep_last=10)
            state = store.get_state()
            self.assertLessEqual(len(state.get("logs", [])), 10)
        else:
            self.skipTest("clear_old_logs metodu tanımlı değil")


if __name__ == "__main__":
    unittest.main(verbosity=2)
