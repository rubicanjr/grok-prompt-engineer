"""
Pytest Konfigürasyonu ve Ortak Fixture'lar
Test izolasyonunu ve mimarisini güçlendirmek için kullanılır.
"""

import pytest
from unittest.mock import patch

from state_manager import ProjectStateStore
from rubric_store import RubricStore


# === Custom Mark Kayıtları ===
def pytest_configure(config):
    config.addinivalue_line("markers", "retry: mark test as retry related")
    config.addinivalue_line("markers", "config: mark test as config related")
    config.addinivalue_line("markers", "error_scenario: mark test as error scenario")


# === Geçici Dosya Fixture'ları ===


@pytest.fixture
def temp_state_file(tmp_path):
    """Her test için izole geçici state dosyası sağlar."""
    return tmp_path / "test_state.json"


@pytest.fixture
def temp_rubric_file(tmp_path):
    """Her test için izole geçici rubric dosyası sağlar."""
    return tmp_path / "test_rubric.json"


@pytest.fixture
def project_state_store(temp_state_file):
    """İzole ProjectStateStore instance'ı sağlar."""
    return ProjectStateStore(temp_state_file)


@pytest.fixture
def rubric_store(temp_rubric_file):
    """İzole RubricStore instance'ı sağlar."""
    return RubricStore(temp_rubric_file)


# === Mock Fixture'ları ===


@pytest.fixture
def mock_orchestrator():
    """orchestrator modülünü mock'lar."""
    with patch("orchestrator") as mock:
        yield mock


@pytest.fixture
def mock_execution_engine():
    """execution_engine modülünü mock'lar."""
    with patch("execution_engine") as mock:
        yield mock


# === En Önemli Fixture: Tam İzolasyon ===
@pytest.fixture
def isolated_artifacts(monkeypatch, tmp_path):
    """
    execution_engine.ARTIFACTS_DIR, RUBRIC_STATE_FILE ve RUBRIC_LOG
    değerlerini test başına tamamen izole eder.

    Bu sayede testler global artifacts/ klasörüne yazmaz ve
    birbirlerini etkilemez.
    """
    import execution_engine

    # Test için geçici artifacts klasörü oluştur
    fake_artifacts = tmp_path / "artifacts"
    fake_artifacts.mkdir(parents=True, exist_ok=True)

    # Ana klasörü değiştir
    monkeypatch.setattr(execution_engine, "ARTIFACTS_DIR", fake_artifacts)

    # RUBRIC_STATE_FILE ve RUBRIC_LOG'u da güncelle
    monkeypatch.setattr(
        execution_engine, "RUBRIC_STATE_FILE", fake_artifacts / "rubric_state.json"
    )
    monkeypatch.setattr(
        execution_engine, "RUBRIC_LOG", fake_artifacts / "Rubric_Tracking_Log_v1.0.md"
    )

    return fake_artifacts
