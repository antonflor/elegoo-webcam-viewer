from pathlib import Path

from printwatch.models import AppState, CameraProfile
from printwatch.storage import StateRepository


def test_repository_round_trip(tmp_path: Path) -> None:
    repository = StateRepository(tmp_path / "state.json")
    state = AppState(cameras=[CameraProfile(name="FDM", url="http://printer.local/video")])
    repository.save(state)
    restored = repository.load()
    assert restored.to_dict() == state.to_dict()


def test_corrupt_state_is_backed_up(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text("not-json", encoding="utf-8")
    state = StateRepository(path).load()
    assert state.cameras == []
    assert path.with_suffix(".json.corrupt").exists()
