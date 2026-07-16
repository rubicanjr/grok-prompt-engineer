"""
State Management Katmanı
Bu modül, dosya tabanlı state yönetimini soyutlar ve daha güvenli, test edilebilir hale getirir.
"""
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

from errors import StateError, ErrorCode


class StateManager:
    """
    State yönetimi için temel soyutlama katmanı.
    JSON tabanlı state dosyalarını güvenli şekilde okur ve yazar.
    """

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """State dosyası yoksa oluşturur."""
        if not self.state_file.exists():
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text("{}", encoding="utf-8")

    def read(self) -> Dict[str, Any]:
        """
        State dosyasını okur.
        Dosya bozuksa otomatik olarak sıfırlar ve boş dict döndürür.
        """
        try:
            if not self.state_file.exists():
                return {}

            content = self.state_file.read_text(encoding="utf-8").strip()

            if not content or content.startswith("#") or content.startswith("**"):
                return {}

            return json.loads(content)

        except json.JSONDecodeError:
            # Bozuk dosya durumu
            self.state_file.write_text("{}", encoding="utf-8")
            return {}
        except Exception:
            return {}

    def write(self, data: Dict[str, Any]) -> bool:
        """State'i atomik olarak yazar."""
        temp_file = None
        try:
            temp_file = self.state_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            import os
            os.replace(temp_file, self.state_file)
            return True
        except (OSError, IOError) as e:
            if temp_file and temp_file.exists():
                temp_file.unlink()
            raise StateError(
                message="State dosyasına yazılamadı",
                error_code=ErrorCode.STATE_WRITE_ERROR,
                details={"file": str(self.state_file), "error": str(e)},
                recoverable=True
            )

    def update(self, key: str, value: Any) -> bool:
        """Belirli bir anahtarı günceller."""
        data = self.read()
        data[key] = value
        return self.write(data)

    def get(self, key: str, default: Any = None) -> Any:
        """Belirli bir anahtarı okur."""
        data = self.read()
        return data.get(key, default)


class ProjectStateStore:
    """
    Proje genel state yönetimi (Living_Project_State için).
    """

    def __init__(self, state_file: Path):
        self.manager = StateManager(state_file)

    def get_state(self) -> Dict[str, Any]:
        return self.manager.read()

    def set_state(self, data: Dict[str, Any]) -> bool:
        return self.manager.write(data)

    def append_log(self, message: str) -> bool:
        """State'e log ekler."""
        try:
            data = self.get_state()
            if "logs" not in data:
                data["logs"] = []
            data["logs"].append({
                "timestamp": datetime.now().isoformat(),
                "message": message
            })
            return self.set_state(data)
        except Exception as e:
            raise StateError(
                message="Log eklenemedi",
                error_code=ErrorCode.STATE_WRITE_ERROR,
                details={"error": str(e)},
                recoverable=True
            )

    def record_context_reset(self, turn: int) -> bool:
        """Context Reset kaydı ekler."""
        key = f"context_reset_turn_{turn}"
        return self.manager.update(key, {
            "applied_at": datetime.now().isoformat(),
            "turn": turn
        })

    def get_context_reset_history(self) -> list:
        """Tüm Context Reset kayıtlarını döndürür."""
        state = self.get_state()
        history = [
            value for key, value in state.items()
            if key.startswith("context_reset_turn_") and isinstance(value, dict)
        ]
        history.sort(key=lambda x: x.get("turn", 0))
        return history

    def clear_old_logs(self, keep_last: int = 50) -> bool:
        """Eski logları temizler, son N tanesini tutar."""
        state = self.get_state()
        if "logs" not in state:
            return True
        logs = state["logs"]
        if len(logs) > keep_last:
            state["logs"] = logs[-keep_last:]
            return self.set_state(state)
        return True