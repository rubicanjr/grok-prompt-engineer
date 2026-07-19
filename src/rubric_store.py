"""
RubricStore - Rubric verilerinin yönetimi için state store.
state_manager.py ile entegre çalışır.
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import logging

from state_manager import StateManager

logger = logging.getLogger(__name__)


class RubricStore:
    """
    Rubric skorlarının yönetimi için özel store.
    """

    def __init__(self, rubric_log_path: Path):
        self.manager = StateManager(rubric_log_path)
        self.rubric_log_path = rubric_log_path

    def get_rubric_for_turn(self, turn: int) -> Dict[str, Any]:
        """Belirli bir turn için Rubric verisini getirir."""
        state = self.manager.read()
        key = f"rubric_turn_{turn}"
        return state.get(key, {})

    def update_rubric(self, turn: int, scores: Dict[str, int], note: str = "") -> bool:
        """Belirli bir turn için Rubric skorlarını günceller."""
        key = f"rubric_turn_{turn}"

        # Duplicate kontrolü
        existing = self.get_rubric_for_turn(turn)
        if existing:
            logger.warning(f"Turn {turn} zaten mevcut. Güncelleme yapılmadı.")
            return False

        data = {
            "turn": turn,
            "scores": scores,
            "note": note,
            "updated_at": datetime.now().isoformat(),
        }
        return self.manager.update(key, data)

    def get_latest_rubric(self) -> Dict[str, Any]:
        """En son güncellenen Rubric verisini döndürür."""
        state = self.manager.read()
        if not state:
            return {}

        # En yüksek turn numaralı kaydı bul
        latest_turn = -1
        latest_data = {}
        for key, value in state.items():
            if key.startswith("rubric_turn_") and isinstance(value, dict):
                turn_num = value.get("turn", -1)
                if turn_num > latest_turn:
                    latest_turn = turn_num
                    latest_data = value

        return latest_data

    def get_all_rubrics(self) -> list:
        """Tüm Rubric kayıtlarını turn sırasına göre döndürür."""
        state = self.manager.read()
        rubrics = []
        for key, value in state.items():
            if key.startswith("rubric_turn_") and isinstance(value, dict):
                rubrics.append(value)
        rubrics.sort(key=lambda x: x.get("turn", 0))
        return rubrics
