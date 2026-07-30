"""Resilience utility providing retry logic with exponential backoff, timeout enforcement, and fallback support for agent executions."""

import asyncio
from typing import Any, Callable, Optional, TypeVar

from app.core.logging import get_logger

logger = get_logger("resilience")

T = TypeVar("T")


async def execute_with_resilience(
    coro_fn: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    timeout_seconds: float = 30.0,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    agent_name: str = "Agent",
    fallback_factory: Optional[Callable[[], T]] = None,
    **kwargs: Any,
) -> T:
    """Execute an asynchronous agent task with retry logic, exponential backoff, timeout, and fallback.

    Args:
        coro_fn: The async function to execute.
        *args: Positional arguments for coro_fn.
        max_retries: Maximum number of execution attempts (default 3).
        timeout_seconds: Timeout per attempt in seconds (default 30.0s).
        initial_delay: Initial delay in seconds before first retry (default 0.5s).
        backoff_factor: Multiplier for exponential backoff (default 2.0).
        agent_name: Name of agent for log context.
        fallback_factory: Optional callable returning a fallback result if all retries fail.
        **kwargs: Keyword arguments for coro_fn.

    Returns:
        Result of coro_fn or fallback_factory() on failure.

    Raises:
        Exception: If all retries fail/time out and no fallback_factory is provided.
    """
    last_exception: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Executing agent attempt",
                agent=agent_name,
                attempt=attempt,
                max_retries=max_retries,
                timeout_seconds=timeout_seconds,
            )
            # Enforce timeout per attempt
            result = await asyncio.wait_for(
                coro_fn(*args, **kwargs), timeout=timeout_seconds
            )
            if attempt > 1:
                logger.info(
                    "Agent recovered after retry",
                    agent=agent_name,
                    successful_attempt=attempt,
                )
            return result

        except asyncio.TimeoutError as exc:
            last_exception = exc
            logger.warning(
                "Agent execution timed out",
                agent=agent_name,
                attempt=attempt,
                max_retries=max_retries,
                timeout_seconds=timeout_seconds,
            )

        except Exception as exc:
            last_exception = exc
            logger.warning(
                "Agent execution failed with error",
                agent=agent_name,
                attempt=attempt,
                max_retries=max_retries,
                error=str(exc),
            )

        # Apply exponential backoff delay if retries remain
        if attempt < max_retries:
            delay = initial_delay * (backoff_factor ** (attempt - 1))
            logger.info(
                "Backoff delay before next retry",
                agent=agent_name,
                next_attempt=attempt + 1,
                delay_seconds=delay,
            )
            await asyncio.sleep(delay)

    # ── Retries Exhausted ────────────────────────────────────────────────
    logger.error(
        "Agent execution retries exhausted",
        agent=agent_name,
        total_attempts=max_retries,
        last_error=str(last_exception),
    )

    if fallback_factory is not None:
        logger.info(
            "Executing fallback handler for agent",
            agent=agent_name,
        )
        try:
            if asyncio.iscoroutinefunction(fallback_factory):
                return await fallback_factory()
            return fallback_factory()
        except Exception as fallback_exc:
            logger.error("Fallback handler failed", agent=agent_name, error=str(fallback_exc))
            raise fallback_exc

    if isinstance(last_exception, asyncio.TimeoutError):
        raise TimeoutError(
            f"{agent_name} timed out after {timeout_seconds}s across {max_retries} attempts"
        ) from last_exception

    raise last_exception or RuntimeError(f"{agent_name} failed after {max_retries} attempts")
