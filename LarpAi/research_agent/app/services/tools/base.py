from abc import ABC, abstractmethod
import time
import logging
from typing import Any, Dict
from research_agent.app.models.tools import ToolResult

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Abstract Base Class for all Larp AI tools.
    Enforces clean interface contracts and standardized result packaging.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def _run(self, **kwargs) -> Any:
        """
        Subclasses must implement their specific async execution logic here.
        """
        pass

    async def execute(self, **kwargs) -> ToolResult:
        """
        Standardized execution wrapper that captures runtime, logs output, and formats errors into ToolResult.
        """
        start_time = time.perf_counter()
        logger.info(f"Executing tool '{self.name}' with arguments: {kwargs}")

        try:
            result_data = await self._run(**kwargs)
            elapsed = time.perf_counter() - start_time
            logger.info(f"Tool '{self.name}' completed successfully in {elapsed:.3f}s.")
            return ToolResult(
                success=True,
                data=result_data,
                metadata={"tool_name": self.name, "execution_time_seconds": round(elapsed, 4)}
            )
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Tool '{self.name}' failed after {elapsed:.3f}s with error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"tool_name": self.name, "execution_time_seconds": round(elapsed, 4)}
            )
