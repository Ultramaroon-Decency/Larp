from abc import ABC, abstractmethod
from typing import Type, TypeVar, Any, Optional
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM providers (OpenAI, Gemini, Anthropic, Mock).
    Ensures clean architecture and decouples core business logic from specific cloud LLM vendors.
    """

    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generates text output from the provider for a given prompt.
        """
        pass

    @abstractmethod
    async def generate_structured(
        self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None
    ) -> T:
        """
        Generates structured response matching a given Pydantic schema.
        """
        pass

    @abstractmethod
    async def generate_vision_text(self, image_bytes: bytes, prompt: str) -> str:
        """
        Processes image inputs (charts, tables, diagrams) and generates structured markdown text.
        """
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Offline/Fallback LLM provider for local testing and initial development phases.
    Operates with zero external network overhead and zero memory footprint.
    """

    def __init__(self, mock_response: Optional[Any] = None):
        self.mock_response = mock_response

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if isinstance(self.mock_response, str):
            return self.mock_response
        return f"Mock response for prompt: {prompt[:50]}..."

    async def generate_structured(
        self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None
    ) -> T:
        if isinstance(self.mock_response, schema):
            return self.mock_response
        elif isinstance(self.mock_response, dict):
            return schema.model_validate(self.mock_response)

        # Fallback structured generation for PlanDecompositionSchema
        if schema.__name__ == "PlanDecompositionSchema":
            from research_agent.app.models.plan import ResearchTask, PlanDecompositionSchema
            tasks = [
                ResearchTask(
                    task_id="task-1",
                    description=f"Gather foundational information and domain specs for: '{prompt[:60]}'",
                    expected_output="Background domain references and initial search results.",
                    estimated_services=["search"],
                    dependencies=[],
                    priority=1
                ),
                ResearchTask(
                    task_id="task-2",
                    description=f"Deep dive analytical evaluation and evidence synthesis for: '{prompt[:60]}'",
                    expected_output="Detailed domain findings and verified evidence fragments.",
                    estimated_services=["search", "fact_check"],
                    dependencies=["task-1"],
                    priority=2
                ),
                ResearchTask(
                    task_id="task-3",
                    description="Synthesize comparative analysis, resolve contradictory points, and cite sources.",
                    expected_output="Synthesized findings and citation list.",
                    estimated_services=["fact_check", "summary", "citation"],
                    dependencies=["task-1", "task-2"],
                    priority=3
                )
            ]
            return PlanDecompositionSchema(tasks=tasks) # type: ignore

        raise NotImplementedError(f"MockLLMProvider requires a pre-set mock_response for schema {schema.__name__}.")

    async def generate_vision_text(self, image_bytes: bytes, prompt: str) -> str:
        """Mock vision response for charts and tables parsing."""
        if "table" in prompt.lower() or "chart" in prompt.lower():
            return (
                "| Category | Baseline | Improved | % Change |\n"
                "| :--- | :---: | :---: | :---: |\n"
                "| Solar Efficiency | 15.2% | 22.8% | +50.0% |\n"
                "| Cost per Watt | $1.20 | $0.80 | -33.3% |"
            )
        return "Mock vision description of chart visual elements."

