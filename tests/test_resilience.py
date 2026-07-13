"""
Resilience ve Multi-Component Failure Testleri
"""

import unittest
from unittest.mock import patch


class TestMultiComponentFailure(unittest.TestCase):

    def test_orchestrator_handles_execution_and_monitoring_failure(self):
        """Execution Engine + Monitoring aynı anda hata verdiğinde orchestrator davranışı."""
        with patch('orchestrator.run_automated') as mock_exec, \
             patch('orchestrator.run_monitoring') as mock_mon:

            mock_exec.side_effect = Exception("Execution failed")
            mock_mon.side_effect = Exception("Monitoring failed")

            from orchestrator import run_turn_end_automation
            result = run_turn_end_automation(turn=300)

            self.assertIsInstance(result, dict)
            self.assertIn("success", result)
            self.assertIn("execution_engine", result)
            self.assertIn("monitoring", result)

    def test_orchestrator_handles_execution_monitoring_and_context_reset_failure(self):
        """Execution + Monitoring + Context Reset aynı anda hata verdiğinde orchestrator davranışı."""
        with patch('orchestrator.run_automated') as mock_exec, \
             patch('orchestrator.run_monitoring') as mock_mon, \
             patch('execution_engine.perform_context_reset_if_needed') as mock_reset:

            mock_exec.side_effect = Exception("Execution failed")
            mock_mon.side_effect = Exception("Monitoring failed")
            mock_reset.side_effect = Exception("Context Reset failed")

            from orchestrator import run_turn_end_automation
            result = run_turn_end_automation(turn=310)

            self.assertIsInstance(result, dict)
            self.assertIn("success", result)

    def test_system_continues_when_only_monitoring_fails(self):
        """Sadece Monitoring başarısız olduğunda sistem devam etmeli (Graceful Degradation)."""
        with patch('orchestrator.run_monitoring') as mock_mon:
            mock_mon.side_effect = Exception("Monitoring down")

            from orchestrator import run_turn_end_automation
            result = run_turn_end_automation(turn=320)

            self.assertIsInstance(result, dict)
            self.assertIn("execution_engine", result)

    def test_graceful_degradation_when_state_store_fails(self):
        """State Store başarısız olduğunda sistemin devam edebilmesi (Graceful Degradation)."""
        with patch('state_manager.ProjectStateStore') as mock_store:
            mock_store.side_effect = Exception("State store down")

            from orchestrator import run_turn_end_automation
            result = run_turn_end_automation(turn=330)

            self.assertIsInstance(result, dict)
            self.assertIn("success", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
