from pathlib import Path

from printwatch.logging_config import configure_logging, get_logger


def test_configure_logging_writes_to_requested_path(tmp_path: Path) -> None:
    path = tmp_path / "logs" / "printwatch.log"
    configured = configure_logging(path)
    get_logger("test").info("diagnostic event without a camera URL")

    assert configured == path
    assert path.exists()
    contents = path.read_text(encoding="utf-8")
    assert "application logging initialized" in contents
    assert "diagnostic event without a camera URL" in contents
