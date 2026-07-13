"""
Pytest Konfigürasyonu ve Ortak Fixture'lar
Test izolasyonunu ve mimarisini güçlendirmek için kullanılır.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from state_manager import ProjectStateStore
from rubric_store import RubricStore


@pytest.fixture
def temp_state_file():
    """Her test için izole geçici state dosyası sağlar."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_state.json"
        yield file_path


@pytest.fixture
def temp_rubric_file():
    """Her test için izole geçici rubric dosyası sağlar."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test_rubric.json"
        yield file_path


@pytest.fixture
def project_state_store(temp_state_file):
    """İzole ProjectStateStore instance'ı sağlar."""
    return ProjectStateStore(temp_state_file)


@pytest.fixture
def rubric_store(temp_rubric_file):
    """İzole RubricStore instance'ı sağlar."""
    return RubricStore(temp_rubric_file)


@pytest.fixture
def mock_orchestrator():
    """orchestrator modülünü mock'lar."""
    with patch('orchestrator') as mock:
        yield mock


@pytest.fixture
def mock_execution_engine():
    """execution_engine modülünü mock'lar."""
    with patch('execution_engine') as mock:
        yield mock
