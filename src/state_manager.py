"""
State Management Katmanı
Bu modül, dosya tabanlı state yönetimini soyutlar ve daha güvenli, test edilebilir hale getirir.
"""
import json
import shutil
from pathlib import Path
from typing import Any, Dict


class StateManager:
    """
    State yönetimi için temel soyutlama katmanı.
    JSON tabanlı state dosyalarını güvenli şekilde okur ve yazar.
    """

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.backup_file = state_file.with_suffix(".bak.json")
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.state_file.exists():
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text("{}", encoding="utf-8")

    def read(self) -> Dict[str, Any]:
        try:
            content = self.state_file.read_text(encoding="utf-8").strip()
            if not content:
                return {}
            return json.loads(content)
        except (json.JSONDecodeError, Exception):
            if self.state_file.exists():
                shutil.copy2(self.state_file, self.backup_file)
            self.state_file.write_text("{}", encoding="utf-8")
            return {}

    def write(self, data: Dict[str, Any]) -> bool:
        try:
            temp_file = self.state_file.with_suffix(".tmp")
            temp_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            import os
            os.replace(temp_file, self.state_file)
            return True
        except Exception:
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink()
            return False

    def update(self, key: str, value: Any) -> bool:
        data = self.read()
        data[key] = value
        return self.write(data)


class ProjectStateStore:
    """
    Proje genel state yönetimi.
    state.json dosyası üzerinden çalışır.
    Living_Project_State.md ise sadece log için kullanılır.
    """

    def __init__(self, state_file: Path = None):
        if state_file is None:
            state_file = Path("artifacts/state.json")
        self.manager = StateManager(state_file)

    def get_state(self) -> Dict[str, Any]:
        return self.manager.read()

    def set_state(self, data: Dict[str, Any]) -> bool:
        return self.manager.write(data)

    def append_log(self, message: str) -> bool:
        try:
            from pathlib import Path as P
            log_file = P("artifacts/Living_Project_State.md")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"- {__import__('datetime').datetime.now().isoformat()} | {message}\n")
            return True
        except Exception:
            return False

    def record_context_reset(self, turn: int) -> bool:
        key = f"context_reset_turn_{turn}"
        return self.manager.update(key, {
            "applied_at": __import__("datetime").datetime.now().isoformat(),
            "turn": turn
        })

    def get_context_reset_history(self) -> list:
        state = self.get_state()
        history = [
            value for key, value in state.items()
            if key.startswith("context_reset_turn_") and isinstance(value, dict)
        ]
        history.sort(key=lambda x: x.get("turn", 0))
        return history

    def clear_old_logs(self, keep_last: int = 50) -> bool:
        state = self.get_state()
        if "logs" not in state:
            return True
        logs = state["logs"]
        if len(logs) > keep_last:
            state["logs"] = logs[-keep_last:]
            return self.set_state(state)
        return True