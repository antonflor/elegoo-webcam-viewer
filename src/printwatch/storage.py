from __future__ import annotations

import json
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from platformdirs import user_config_dir

from printwatch.models import AppState


class StateRepository:
    """Persists local application state using atomic JSON replacement."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(user_config_dir("PrintWatch", "Monty Labs")) / "state.json"

    def load(self) -> AppState:
        if not self.path.exists():
            return AppState()

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return AppState.from_dict(data)
        except (OSError, ValueError, TypeError):
            self._backup_corrupt_file()
            return AppState()

    def save(self, state: AppState) -> None:
        payload = json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(payload)
            temporary.flush()
            temp_path = Path(temporary.name)

        temp_path.replace(self.path)

    def _backup_corrupt_file(self) -> None:
        try:
            backup = self.path.with_suffix(self.path.suffix + ".corrupt")
            shutil.copy2(self.path, backup)
        except OSError:
            pass
