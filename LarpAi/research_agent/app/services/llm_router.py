"""
LLM Router
----------
Dynamic Cost & Latency LLM Router.
Selects and returns the optimal LLM provider and model size based on the
operational category (Planning, Verification, Critique, Formatting).

Optimizes:
    - Planning (needs fast structured generation) → gemini-2.0-flash / gpt-4o-mini
    - Verification (needs high logical reasoning) → Claude 3.5 Sonnet / o1-mini
    - Critique (needs adversarial analysis) → Claude 3.5 Sonnet / GPT-4o
    - Formatting (needs cheap text formatting) → gemini-2.0-flash / gpt-4o-mini
"""

import os
import logging
from typing import Optional, Dict
from research_agent.app.services.llm_base import BaseLLMProvider
from research_agent.app.services.llm_adapters import (
    OpenAIProvider,
    GeminiProvider,
    AnthropicProvider,
    get_llm_provider
)
from research_agent.app.config.config import settings

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    LLM Router responsible for directing tasks to specific LLM endpoints
    to optimize token costs, response latency, and reasoning capability.
    """

    def __init__(self):
        # Cache active providers to avoid redundant instantiations
        self._providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider = get_llm_provider()

    def get_provider_for_task(self, task_type: str) -> BaseLLMProvider:
        """
        Returns the optimal LLM provider instance for a specific task category.

        Args:
            task_type: One of 'planning', 'verification', 'critique', 'formatting'.

        Returns:
            An instance of BaseLLMProvider.
        """
        task_key = task_type.lower().strip()
        logger.debug(f"LLMRouter: Selecting provider for task category: '{task_key}'")

        # Fallback to default auto-detected provider if any issues occur
        try:
            if task_key == "planning":
                return self._get_planning_provider()
            elif task_key in ("verification", "fact_check"):
                return self._get_verification_provider()
            elif task_key in ("critique", "adversarial"):
                return self._get_critique_provider()
            elif task_key in ("formatting", "citation", "summary"):
                return self._get_formatting_provider()
        except Exception as e:
            logger.warning(f"LLMRouter: Error selecting routed provider for '{task_key}': {e}. Falling back to default.")

        return self.default_provider

    # ------------------------------------------------------------------
    # Routed Provider Factories
    # ------------------------------------------------------------------

    def _get_planning_provider(self) -> BaseLLMProvider:
        """Planning needs fast, structured JSON generation. Prefers Gemini Flash."""
        if "planning" in self._providers:
            return self._providers["planning"]

        # 1. Try Gemini (default fast model)
        has_gemini = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if has_gemini:
            provider = GeminiProvider(model="gemini-2.0-flash")
            self._providers["planning"] = provider
            return provider

        # 2. Try OpenAI (mini model)
        has_openai = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        if has_openai:
            provider = OpenAIProvider(model="gpt-4o-mini")
            self._providers["planning"] = provider
            return provider

        return self.default_provider

    def _get_verification_provider(self) -> BaseLLMProvider:
        """Verification requires high reasoning capacity. Prefers Anthropic/GPT-4o."""
        if "verification" in self._providers:
            return self._providers["verification"]

        # 1. Try Anthropic (Claude 3.5 Sonnet or similar)
        has_anthropic = settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
        if has_anthropic:
            provider = AnthropicProvider(model="claude-3-5-sonnet-20241022")
            self._providers["verification"] = provider
            return provider

        # 2. Try OpenAI (GPT-4o or o1-mini if configured)
        has_openai = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        if has_openai:
            provider = OpenAIProvider(model="gpt-4o")
            self._providers["verification"] = provider
            return provider

        return self.default_provider

    def _get_critique_provider(self) -> BaseLLMProvider:
        """Critique needs deep analytical reasoning. Prefers Anthropic/GPT-4o."""
        if "critique" in self._providers:
            return self._providers["critique"]

        # 1. Try Anthropic
        has_anthropic = settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
        if has_anthropic:
            provider = AnthropicProvider(model="claude-3-5-sonnet-20241022")
            self._providers["critique"] = provider
            return provider

        # 2. Try OpenAI
        has_openai = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        if has_openai:
            provider = OpenAIProvider(model="gpt-4o")
            self._providers["critique"] = provider
            return provider

        return self.default_provider

    def _get_formatting_provider(self) -> BaseLLMProvider:
        """Formatting is a simple translation/rendering task. Prefers cheap Gemini Flash."""
        if "formatting" in self._providers:
            return self._providers["formatting"]

        # 1. Try Gemini
        has_gemini = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if has_gemini:
            provider = GeminiProvider(model="gemini-2.0-flash")
            self._providers["formatting"] = provider
            return provider

        # 2. Try OpenAI
        has_openai = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        if has_openai:
            provider = OpenAIProvider(model="gpt-4o-mini")
            self._providers["formatting"] = provider
            return provider

        return self.default_provider
