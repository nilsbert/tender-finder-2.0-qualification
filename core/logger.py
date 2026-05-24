import json
import logging
import os
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """
    Standardized JSON formatter for microservices.
    Optimized for ingestion by Azure Monitor / OpenTelemetry.
    """

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra fields if provided via 'extra' argument
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def setup_logger(name: str, service_name: str = None) -> logging.Logger:
    """
    Configures and returns a logger with standardized formatting.

    Environment Variables:
    - LOG_LEVEL: INFO, DEBUG, WARNING, ERROR (default: INFO)
    - LOG_FORMAT: JSON or TEXT (default: TEXT)
    """
    if service_name is None:
        service_name = os.getenv("SERVICE_NAME", "unknown-service")

    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid adding multiple handlers if setup_logger is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        log_format = os.getenv("LOG_FORMAT", "TEXT").upper()
        if log_format == "JSON":
            handler.setFormatter(JsonFormatter(service_name))
        else:
            # Clean, human-readable format for local dev
            fmt = f"%(asctime)s [%(levelname)s] {service_name} [%(name)s]: %(message)s"
            handler.setFormatter(logging.Formatter(fmt))

        logger.addHandler(handler)

    return logger
