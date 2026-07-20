"""
State Management Katmanı
JSON tabanlı state yönetimi + Markdown log ayrımı.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class StateManager:
    """
    Güvenli JSON state yönetimi.
    - Atomic write
    - Otomatik backup
    - Bozulma durumunda otomatik sıfırlama
    """

    def __init__(self, state_file: Path):
        self.state_file = Path(state_file)
        self.backup_file = self.state_file.with_suffix(self.state_file.suffix + ".bak")
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        if not self.state_file.exists():
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text("{}", encoding="utf-8")

    def read(self) -> Dict[str, Any]:
        try:
            content = self.state_file.read_text(encoding="utf-8").strip()
            if not content:
                return {}
            return json.loads(content)
        except (json.JSONDecodeError, OSError):
            # Bozulduysa yedek al ve sıfırla
            if self.state_file.exists():
                try:
                    shutil.copy2(self.state_file, self.backup_file)
                except Exception:
                    pass
            self.state_file.write_text("{}", encoding="utf-8")
            return {}

    def write(self, data: Dict[str, Any]) -> bool:
        try:
            temp_file = self.state_file.with_suffix(".tmp")
            temp_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            os.replace(temp_file, self.state_file)
            return True
        except Exception:
            if "temp_file" in locals() and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False

    def update(self, key: str, value: Any) -> bool:
        data = self.read()
        data[key] = value
        return self.write(data)


class ProjectStateStore:
    """
    Proje state yönetimi.
    - State → artifacts/state.json (JSON)
    - Log → artifacts/Living_Project_State.md (Markdown, append-only)
    """

    def __init__(self, state_file: Optional[Path] = None):
        if state_file is None:
            state_file = Path("artifacts/state.json")
        self.manager = StateManager(state_file)

    def get_state(self) -> Dict[str, Any]:
        return self.manager.read()

    def set_state(self, data: Dict[str, Any]) -> bool:
        return self.manager.write(data)

    def append_log(self, message: str) -> bool:
        """Sadece insan okunabilir Markdown log'a yazar."""
        try:
            log_file = Path("artifacts/Living_Project_State.md")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().isoformat()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"- {timestamp} | {message}\n")
            return True
        except Exception:
            return False

    def record_context_reset(self, turn: int) -> bool:
        key = f"context_reset_turn_{turn}"
        return self.manager.update(
            key,
            {
                "applied_at": datetime.now().isoformat(),
                "turn": turn,
            },
        )

    def get_context_reset_history(self) -> List[Dict[str, Any]]:
        state = self.get_state()
        history = [
            value
            for key, value in state.items()
            if key.startswith("context_reset_turn_") and isinstance(value, dict)
        ]
        history.sort(key=lambda x: x.get("turn", 0))
        return history