import logging
from pathlib import Path

from printwatch.logging_config import configure_logging, get_logger


def test_configure_logging_writes_redacted_events(tmp_path: Path) -> None:
    path = tmp_path / "logs" / "printwatch.log"
    try:
        configured = configure_logging(path)
        logger = get_logger("test")
        logger.info("diagnostic event without a camera URL")
        logger.error(
            "connection failed url=%s ip=%s home=%s",
            "http://192.168.1.20:3031/video",
            "192.168.1.20",
            Path.home(),
        )

        assert configured == path
        assert path.exists()
        contents = path.read_text(encoding="utf-8")
        assert "application logging initialized" in contents
        assert "diagnostic event without a camera URL" in contents
        assert "192.168.1.20" not in contents
        assert "http://" not in contents
        assert str(Path.home()) not in contents
        assert "<redacted-url>" in contents
        assert "<redacted-ip>" in contents
        assert "<home>" in contents
    finally:
        logging.shutdown()
