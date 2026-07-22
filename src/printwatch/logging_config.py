from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from platformdirs import user_log_dir

from printwatch.diagnostics import redact_text

LOGGER_NAME = "printwatch"


class PrivacyFormatter(logging.Formatter):
    """Redact URLs, network addresses, and the user's home directory."""

    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        rendered = redact_text(rendered)
        home = str(Path.home())
        return rendered.replace(home, "<home>") if home else rendered


def default_log_path() -> Path:
    return Path(user_log_dir("PrintWatch", "Monty Labs")) / "printwatch.log"


def configure_logging(path: Path | None = None) -> Path:
    """Configure bounded local logs without enabling network telemetry."""

    log_path = path or default_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        PrivacyFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.info("application logging initialized")
    return log_path


def get_logger(component: str | None = None) -> logging.Logger:
    name = LOGGER_NAME if not component else f"{LOGGER_NAME}.{component}"
    return logging.getLogger(name)
