"""
Hata Enjeksiyon Testleri
Pytest monkeypatch + exception injection ile kritik hata senaryolarını test eder.
"""
import pytest
from unittest.mock import patch


def test_state_corruption_during_run():
    """State dosyası run sırasında bozulursa motorun davranışı."""
    from execution_engine import ExecutionEngine

    engine = ExecutionEngine()

    with patch('state_manager.ProjectStateStore.set_state') as mock_set:
        mock_set.side_effect = Exception("Simüle state corruption")
        result = engine.attempt_self_recovery()
        # Kurtarma mekanizması devreye girmeli
        assert result.get("success") is True or result.get("backup_created") is True


def test_circuit_breaker_with_injected_failure(monkeypatch):
    """Circuit Breaker içine hata enjekte edilerek OPEN durumuna geçmesi test edilir."""
    from circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker(config_name="default")

    call_count = 0

    def failing_func():
        nonlocal call_count
        call_count += 1
        raise ValueError(f"Injected failure #{call_count}")

    for _ in range(6):
        try:
            breaker.call(failing_func)
        except Exception:
            pass

    assert breaker.state.name == "OPEN"
    assert call_count >= 5


def test_monitoring_with_injected_exception():
    """Monitoring sırasında exception enjekte edildiğinde sistemin çökmemesi."""
    with patch('monitor_and_alert.HealthChecker.check_motor_health') as mock_health:
        mock_health.side_effect = Exception("Injected monitoring failure")
        from monitor_and_alert import run_monitoring
        result = run_monitoring()
        assert result.get("success") is False or "error" in result


def test_rubric_update_failure_injection():
    """Rubric güncelleme sırasında hata enjekte edildiğinde motorun devam etmesi."""
    with patch('rubric_store.RubricStore.update_rubric') as mock_update:
        mock_update.side_effect = Exception("Rubric update failed")
        from execution_engine import ExecutionEngine
        engine = ExecutionEngine()
        # Hata fırlatmamalı, sadece loglamalı
        try:
            engine._update_rubric_for_turn(1)
        except Exception:
            pytest.fail("Rubric update hatası motoru çökertmemeli")