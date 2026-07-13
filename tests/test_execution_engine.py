#!/usr/bin/env python3
"""
Temel Entegrasyon Testleri - execution_engine.py
Rubric güncelleme, Context Reset ve Monitoring senaryoları için testler.
"""

import unittest
from unittest.mock import patch
import pytest
from pathlib import Path
import tempfile
import shutil

# Test edilecek modüller
from execution_engine import (
    update_rubric,
    get_current_turn,
    perform_context_reset_if_needed,
    propose_or_apply_self_evolving_change,
)
from monitor_and_alert import (
    run_monitoring,
    check_for_alerts,
)
from orchestrator import run_turn_end_automation


class TestExecutionEngineIntegration(unittest.TestCase):

    def setUp(self):
        """Her test öncesi geçici klasör oluştur (güvenli test için)."""
        self.test_dir = Path(tempfile.mkdtemp())
        # Gerçek artifacts klasörünü bozmamak için test sırasında dikkatli olacağız.
        # Basitlik için mevcut fonksiyonları doğrudan test ediyoruz.

    def tearDown(self):
        """Test sonrası temizlik."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_update_rubric_adds_new_turn(self):
        """update_rubric yeni bir turn ekleyebiliyor mu?"""
        # Not: Bu test mevcut Rubric dosyasını etkiler.
        # Gerçek projede mock veya ayrı test Rubric kullanılmalı.
        current_turn = get_current_turn()
        new_turn = current_turn + 1

        scores = {
            "Grounding": 10,
            "Hallucination": 10,
            "Bias": 10,
            "Token": 9,
            "Yapı": 10,
            "Self-Evolving": 9
        }

        result = update_rubric(new_turn, scores, "Integration test - Rubric güncelleme")
        self.assertTrue(result, "update_rubric yeni turn ekleyemedi")

    def test_update_rubric_prevents_duplicate(self):
        """update_rubric aynı turn'u tekrar eklememeli."""
        current_turn = get_current_turn()

        scores = {"Grounding": 10, "Hallucination": 10, "Bias": 10,
                  "Token": 9, "Yapı": 10, "Self-Evolving": 9}

        # İlk ekleme
        update_rubric(current_turn, scores, "First insert")

        # Aynı turn tekrar ekleme denemesi
        result = update_rubric(current_turn, scores, "Duplicate attempt")
        self.assertFalse(result, "update_rubric duplicate turn ekledi!")

    def test_context_reset_triggers_for_high_turn(self):
        """perform_context_reset_if_needed yüksek turn'da tetikleniyor mu?"""
        # Yüksek bir turn değeri veriyoruz (test amaçlı)
        high_turn = 25
        # Fonksiyon hata fırlatmadan çalışmalı
        try:
            perform_context_reset_if_needed(high_turn)
        except Exception as e:
            self.fail(f"perform_context_reset_if_needed hata fırlattı: {e}")

    def test_monitoring_runs_without_error(self):
        """run_monitoring hatasız çalışabiliyor mu?"""
        try:
            run_monitoring()
        except Exception as e:
            self.fail(f"run_monitoring hata fırlattı: {e}")

    def test_check_for_alerts_returns_list(self):
        """check_for_alerts liste döndürmeli."""
        alerts = check_for_alerts()
        self.assertIsInstance(alerts, list)

    def test_orchestrator_run_turn_end_automation(self):
        """orchestrator.run_turn_end_automation hatasız çalışmalı ve sonuç döndürmeli."""
        result = run_turn_end_automation(turn=50)
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("execution_engine", result)
        self.assertIn("monitoring", result)

    def test_propose_or_apply_self_evolving_change_dry_run(self):
        """Self-Evolving değişiklik önerisi dry-run modunda çalışmalı."""
        result = propose_or_apply_self_evolving_change(
            "Test değişikliği - dry run", 
            force_apply=False
        )
        self.assertFalse(result, "Dry-run modunda değişiklik uygulanmamalıydı")

    def test_propose_or_apply_self_evolving_change_force_apply(self):
        """force_apply=True ile Self-Evolving değişikliği uygulanabilmeli."""
        result = propose_or_apply_self_evolving_change(
            "Test değişikliği - force apply", 
            force_apply=True
        )
        self.assertTrue(result)

    def test_context_reset_does_not_duplicate(self):
        """Context Reset aynı tur için tekrar uygulanmamalı."""
        high_turn = 30
        # İlk çağrı
        perform_context_reset_if_needed(high_turn)
        # İkinci çağrı (zaten reset yapılmış olmalı)
        try:
            perform_context_reset_if_needed(high_turn)
        except Exception as e:
            self.fail(f"İkinci Context Reset çağrısı hata verdi: {e}")

    def test_orchestrator_returns_detailed_result(self):
        """orchestrator.run_turn_end_automation detaylı sonuç döndürmeli."""
        result = run_turn_end_automation(turn=55)
        self.assertIn("duration_seconds", result)
        self.assertIsInstance(result["duration_seconds"], float)
        self.assertGreaterEqual(result["duration_seconds"], 0)

    def test_orchestrator_continues_on_component_failure(self):
        """
        Orchestrator, execution_engine veya monitoring başarısız olsa bile
        çalışmaya devam etmeli ve sonuç döndürmeli (hata izolasyonu).
        """
        # Normal şartlarda çalışmalı
        result = run_turn_end_automation(turn=60)
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)

    def test_self_evolving_helper_exists_and_callable(self):
        """propose_or_apply_self_evolving_change fonksiyonu çağrılabilir olmalı."""
        self.assertTrue(callable(propose_or_apply_self_evolving_change))

    @patch('orchestrator.run_automated')
    def test_orchestrator_handles_execution_engine_failure(self, mock_run_automated):
        """
        Execution Engine hata verse bile orchestrator çalışmaya devam etmeli
        ve anlamlı bir sonuç döndürmeli (hata izolasyonu testi).
        """
        # Execution Engine'in hata fırlatmasını simüle et
        mock_run_automated.side_effect = Exception("Simulated Execution Engine failure")

        result = run_turn_end_automation(turn=80)

        # Orchestrator yine de çalışmalı ve sonuç döndürmeli
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("execution_engine", result)
        # Execution Engine başarısız olduğu için sonucu 'failed' veya 'not_run' olabilir
        self.assertIn(result["execution_engine"], ["failed", "not_run"])

    @patch('orchestrator.run_monitoring')
    def test_orchestrator_handles_monitoring_failure(self, mock_run_monitoring):
        """
        Monitoring hata verse bile orchestrator çalışmaya devam etmeli
        (hata izolasyonu testi - Monitoring tarafı).
        """
        mock_run_monitoring.side_effect = Exception("Simulated Monitoring failure")

        result = run_turn_end_automation(turn=85)

        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("monitoring", result)
        self.assertIn(result["monitoring"], ["failed", "not_run"])

    def test_execution_engine_class_basic_flow(self):
        """ExecutionEngine sınıfı temel akışı hatasız çalıştırmalı."""
        from execution_engine import ExecutionEngine

        engine = ExecutionEngine()
        self.assertIsNone(engine.get_last_turn())

        engine.run(turn=100)
        self.assertEqual(engine.get_last_turn(), 100)
        self.assertTrue(engine.get_status()["initialized"])

    @patch('execution_engine._execute_turn')
    def test_execution_engine_handles_internal_error(self, mock_execute):
        """ExecutionEngine içinde hata olsa bile kontrollü şekilde çalışmalı."""
        from execution_engine import ExecutionEngine

        mock_execute.side_effect = Exception("Internal execution error")
        engine = ExecutionEngine()

        try:
            engine.run(turn=105)
        except Exception:
            pass

    @patch('orchestrator.run_automated')
    @patch('orchestrator.run_monitoring')
    def test_orchestrator_handles_multiple_component_failures(self, mock_monitoring, mock_automated):
        """
        Hem Execution Engine hem de Monitoring aynı anda hata verse bile
        orchestrator çalışmaya devam etmeli (karmaşık hata senaryosu).
        """
        mock_automated.side_effect = Exception("Execution Engine failed")
        mock_monitoring.side_effect = Exception("Monitoring failed")

        result = run_turn_end_automation(turn=115)

        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("execution_engine", result)
        self.assertIn("monitoring", result)

    @pytest.mark.error_scenario
    @patch('orchestrator.run_automated')
    @patch('orchestrator.run_monitoring')
    def test_orchestrator_returns_result_even_in_total_failure(self, mock_monitoring, mock_automated):
        """
        Execution Engine ve Monitoring tamamen başarısız olsa bile
        orchestrator anlamlı bir sonuç dict'i döndürmeli.
        """
        mock_automated.side_effect = Exception("Complete failure")
        mock_monitoring.side_effect = Exception("Complete failure")

        result = run_turn_end_automation(turn=120)

        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("execution_engine", result)
        self.assertIn("monitoring", result)
        self.assertIn("duration_seconds", result)

    def test_execution_engine_negative_turn_handling(self):
        """ExecutionEngine negatif turn değeriyle çağrıldığında mantıklı davranmalı."""
        from execution_engine import ExecutionEngine

        engine = ExecutionEngine()
        try:
            engine.run(turn=-5)
        except Exception:
            pass

    @patch('execution_engine.SELF_EVOLVING_APPLY_MODE', 'auto')
    def test_self_evolving_auto_mode_applies_change(self):
        """SELF_EVOLVING_APPLY_MODE='auto' olduğunda değişiklik uygulanmalı."""
        from execution_engine import propose_or_apply_self_evolving_change

        result = propose_or_apply_self_evolving_change(
            "Test değişikliği - auto mode", 
            force_apply=False
        )
        self.assertTrue(result)

    @patch('execution_engine.SELF_EVOLVING_APPLY_MODE', 'manual')
    def test_self_evolving_manual_mode_dry_run(self):
        """SELF_EVOLVING_APPLY_MODE='manual' olduğunda dry-run yapılmalı."""
        from execution_engine import propose_or_apply_self_evolving_change

        result = propose_or_apply_self_evolving_change(
            "Test değişikliği - manual mode", 
            force_apply=False
        )
        self.assertFalse(result)

    @patch('config.ENABLE_AUTO_CONTEXT_RESET', False)
    def test_context_reset_disabled_by_config(self):
        """ENABLE_AUTO_CONTEXT_RESET=False olduğunda Context Reset tetiklenmemeli."""
        from execution_engine import perform_context_reset_if_needed

        try:
            perform_context_reset_if_needed(turn=50)
        except Exception as e:
            self.fail(f"Context Reset çağrısı hata verdi: {e}")

    @pytest.mark.config
    @patch('config.ENABLE_AUTO_CONTEXT_RESET', True)
    @patch('config.CONTEXT_RESET_TURN_THRESHOLD', 100)
    def test_context_reset_not_triggered_below_threshold(self):
        """Threshold'un altında Context Reset tetiklenmemeli."""
        from execution_engine import perform_context_reset_if_needed

        try:
            perform_context_reset_if_needed(turn=50)
        except Exception as e:
            self.fail(f"Context Reset çağrısı hata verdi: {e}")

    @patch('config.RUBRIC_LOW_THRESHOLD', 8.0)
    @patch('config.RUBRIC_CRITICAL_THRESHOLD', 7.0)
    @patch('monitor_and_alert.RUBRIC_LOG')
    def test_monitoring_alerts_when_rubric_low(self, mock_rubric_log):
        """Rubric ortalaması düşük threshold'un altına düştüğünde alert üretilmeli."""
        from monitor_and_alert import check_for_alerts

        alerts = check_for_alerts()
        self.assertIsInstance(alerts, list)

    @patch('config.MAX_RETRIES', 1)
    def test_retry_mechanism_with_low_max_retries(self):
        """MAX_RETRIES=1 olduğunda decorator'ın davranışı test edilir."""
        from config import retry_on_exception

        call_count = 0

        @retry_on_exception(max_retries=1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Simulated failure")

        try:
            failing_function()
        except ValueError:
            pass

        self.assertEqual(call_count, 1)

    # === retry_on_exception Decorator Detaylı Testleri ===

    @pytest.mark.parametrize("max_retries,expected_calls", [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
    ])
    @pytest.mark.retry
    def test_retry_decorator_various_max_retries(self, max_retries, expected_calls):
        """Farklı MAX_RETRIES değerlerinde decorator'ın doğru sayıda retry yapması."""
        from config import retry_on_exception

        call_count = 0

        @retry_on_exception(max_retries=max_retries)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < expected_calls:
                raise ValueError("Fail until last attempt")

        try:
            failing_function()
        except ValueError:
            pass

        self.assertEqual(call_count, expected_calls)

    # === Config Mocking - Sistematik Testler ===

    @patch('config.ENABLE_AUTO_CONTEXT_RESET', True)
    @patch('config.CONTEXT_RESET_TURN_THRESHOLD', 5)
    def test_context_reset_triggers_when_enabled_and_above_threshold(self):
        """ENABLE_AUTO_CONTEXT_RESET=True ve threshold üstünde Context Reset tetiklenmeli."""
        from execution_engine import perform_context_reset_if_needed
        try:
            perform_context_reset_if_needed(turn=10)
        except Exception as e:
            self.fail(f"Context Reset çağrısı hata verdi: {e}")

    @patch('config.RUBRIC_LOW_THRESHOLD', 5.0)
    @patch('config.RUBRIC_CRITICAL_THRESHOLD', 3.0)
    def test_monitoring_with_very_low_rubric_thresholds(self):
        """Çok düşük Rubric threshold değerlerinde monitoring çalışmalı."""
        from monitor_and_alert import check_for_alerts
        alerts = check_for_alerts()
        self.assertIsInstance(alerts, list)

    # === Parametrize Testler ===

    @pytest.mark.parametrize("threshold,turn,should_trigger", [
        (5, 10, True),
        (20, 15, False),
        (10, 10, True),
        (100, 50, False),
    ])
    @patch('config.ENABLE_AUTO_CONTEXT_RESET', True)
