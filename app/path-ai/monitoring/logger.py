import logging, json, sys
from datetime import datetime, timezone
from typing import Any


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "_extra"):
            log_entry["context"] = record._extra
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ContextLogger:
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        extra = {"_extra": kwargs} if kwargs else {}
        self._logger.log(level, message, extra=extra)

    def debug(self, msg: str, **kw): self._log(logging.DEBUG, msg, **kw)
    def info(self, msg: str, **kw): self._log(logging.INFO, msg, **kw)
    def warning(self, msg: str, **kw): self._log(logging.WARNING, msg, **kw)
    def error(self, msg: str, **kw): self._log(logging.ERROR, msg, **kw)


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger("app.path_ai")
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        root.addHandler(handler)


def get_logger(name: str) -> ContextLogger:
    return ContextLogger(name)
