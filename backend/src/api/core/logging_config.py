import logging
import sys
from pydantic import BaseModel
import json
from typing import Dict, Any, Optional


class LogConfig(BaseModel):
    """Logging configuration"""

    LOGGER_NAME: str = "restaurant_api"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: Dict[str, Dict[str, str]] = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "src.api.core.logging_config.JSONFormatter",
        },
    }
    handlers: Dict[str, Dict[str, Any]] = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "json": {
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    }
    loggers: Dict[str, Dict[str, Any]] = {
        LOGGER_NAME: {
            "handlers": ["json"],
            "level": LOG_LEVEL,
            "propagate": False
        },
    }


class JSONFormatter(logging.Formatter):
    """JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra") and record.extra:
            log_record.update(record.extra)

        return json.dumps(log_record)


def get_logger(name: str) -> logging.Logger:
    """Get logger with the given name."""
    return logging.getLogger(name)