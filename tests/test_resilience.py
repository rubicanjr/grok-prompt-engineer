"""
Resilience Testleri
Circuit Breaker, Self-Healing, Graceful Degradation ve hata toleransı senaryoları.
"""
import unittest
from unittest.mock import patch
from execution_engine import ExecutionEngine


class TestResilience(unittest.TestCase):

    def test_circuit_breaker_opens_after_threshold(self):
        """Circuit Breaker belirli hata sayısından sonra OPEN duruma geçmeli."""
        from circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker(config_name="default")

        def failing_func():
            raise ValueError("Simüle hata")

        for _ in range(5):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        self.assertEqual(breaker.state.name, "OPEN")

    def test_self_healing_recovers_from_state_corruption(self):
        """State bozulması durumunda self-healing mekanizması çalışmalı."""
        engine = ExecutionEngine()
        result = engine.attempt_self_recovery()
        self.assertTrue(result.get("success"))
        self.assertTrue(result.get("backup_created"))
        self.assertTrue(result.get("new_state_created"))

    def test_graceful_degradation_when_state_store_fails(self):
        """State Store başarısız olduğunda sistem çökmemeli."""
        with patch('state_manager.ProjectStateStore') as mock_store:
            mock_store.side_effect = Exception("State store down")
            from orchestrator import run_turn_end_automation
            result = run_turn_end_automation(turn=100)
            self.assertIsInstance(result, dict)
            self.assertIn("success", result)

    def test_circuit_breaker_half_open_recovery(self):
        """HALF_OPEN durumunda başarılı çağrı sonrası CLOSED duruma dönmeli."""
        from circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker(config_name="default")

        def failing_func():
            raise ValueError("Hata")

        # OPEN durumuna getir
        for _ in range(5):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        # Manuel olarak HALF_OPEN yap (test için)
        breaker._state = breaker._state.__class__.HALF_OPEN
        breaker._half_open_test_done = False

        def success_func():
            return "success"

        result = breaker.call(success_func)
        self.assertEqual(result, "success")
        self.assertEqual(breaker.state.name, "CLOSED")


if __name__ == "__main__":
    unittest.main(verbosity=2)