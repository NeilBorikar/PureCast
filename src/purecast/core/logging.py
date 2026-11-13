"""Structured JSON logging with request ID tracking using structlog (with stdlib fallback)."""

import logging
import sys
from contextvars import ContextVar
from typing import Any

try:
    import structlog
except ImportError:
    structlog = None  # type: ignore

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Return the current request ID from context."""
    return _request_id_ctx.get()


def set_request_id(request_id: str | None) -> None:
    """Set the request ID in the current context."""
    _request_id_ctx.set(request_id)


def add_request_id(_logger: Any, _method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Inject request_id from contextvar into every log record."""
    req_id = get_request_id()
    if req_id is not None:
        event_dict["request_id"] = req_id
    return event_dict


class _StdlibLoggerWrapper:
    """Fallback logger wrapper with structlog-compatible interface."""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.exception(msg)

    def bind(self, **kwargs: Any) -> "_StdlibLoggerWrapper":
        return self

    def _log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        extra_str = f" {kwargs}" if kwargs else ""
        self._logger.log(level, f"{msg}{extra_str}", *args)


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """Configure structlog or standard library logging."""
    if structlog is not None:
        shared_processors = [
            structlog.contextvars.merge_contextvars,
            add_request_id,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]

        if json_format:
            renderer = structlog.processors.JSONRenderer()
        else:
            renderer = structlog.dev.ConsoleRenderer()  # type: ignore[assignment]

        structlog.configure(
            processors=[
                *shared_processors,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(log_level.upper())
    else:
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )


def get_logger(name: str | None = None) -> Any:
    """Get a bound logger."""
    if structlog is not None:
        return structlog.get_logger(name)
    return _StdlibLoggerWrapper(logging.getLogger(name or "purecast"))
