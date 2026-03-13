import asyncio
import time
from contextlib import contextmanager
from functools import wraps
from typing import (
    Any,
    Callable,
    Generator,
    TypeVar,
)

from loguru import logger

T = TypeVar("T")


async def safe_sleep(seconds: float = 2.0) -> None:
    """Helper to avoid flood limits."""
    await asyncio.sleep(seconds)


def setup_logging() -> None:
    """Configure logging with both human-readable and structured outputs."""
    import sys

    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )
    logger.add(
        "bot.json.log",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        level="DEBUG",
        serialize=True,
    )
    logger.add("bot.log", rotation="10 MB", retention="7 days", compression="zip", level="INFO")


@contextmanager
def timed_operation(name: str, **kwargs: Any) -> Generator[None, None, None]:
    """Context manager to time an operation and log its duration."""
    start_time = time.perf_counter()
    try:
        yield
    except Exception as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"Operation {name} failed after {elapsed:.2f}ms: {e}",
            duration_ms=round(elapsed, 2),
            operation=name,
            status="error",
            **kwargs,
        )
        raise
    else:
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Operation {name} completed in {elapsed:.2f}ms",
            duration_ms=round(elapsed, 2),
            operation=name,
            status="success",
            **kwargs,
        )


def observe(name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to automatically time and log an async function."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        op_name = name or func.__name__

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            with timed_operation(op_name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
