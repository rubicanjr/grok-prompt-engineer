"""
Chaos / fault-injection tests for long-term resilience.
"""

import tempfile
import unittest
from pathlib import Path

from state_manager import StateManager
from circuit_breaker import CircuitBreaker, CircuitState


class TestChaosStateCorruption(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "chaos_state.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_corrupted_json_recovers_to_empty_dict(self):
        """Bozuk JSON okunduğunda sistem çökmeden {} dönmeli."""
        self.state_file.write_text("{ invalid json !!!", encoding="utf-8")
        manager = StateManager(self.state_file)
        result = manager.read()
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_partial_write_does_not_crash(self):
        """Yarım kalmış / boş dosya güvenli okunmalı."""
        self.state_file.write_text("", encoding="utf-8")
        manager = StateManager(self.state_file)
        result = manager.read()
        self.assertEqual(result, {})


class TestChaosCircuitBreaker(unittest.TestCase):
    def test_repeated_failures_open_circuit(self):
        # state_error config: failure_threshold=2
        breaker = CircuitBreaker(config_name="state_error")

        def always_fail():
            raise ValueError("chaos failure")

        with self.assertRaises(ValueError):
            breaker.call(always_fail)
        with self.assertRaises(ValueError):
            breaker.call(always_fail)

        self.assertEqual(breaker.state, CircuitState.OPEN)

        from errors import ResilienceError

        with self.assertRaises(ResilienceError):
            breaker.call(lambda: "should not run")


if __name__ == "__main__":
    unittest.main(verbosity=2)
