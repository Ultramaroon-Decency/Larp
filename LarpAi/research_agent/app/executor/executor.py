import asyncio
import re
import time
import logging
from typing import Dict, Any, Optional, List
from research_agent.app.models.plan import ExecutionPlan, ResearchTask
from research_agent.app.models.executor import TaskExecutionResult, PlanExecutionResult
from research_agent.app.services.tools import (
    BaseTool,
    MockSearchTool,
    MockFactCheckTool,
    MockSummaryTool,
    MockCitationTool,
    ArxivSearchTool,
    WikipediaTool,
)

from research_agent.app.memory import BaseCache, InMemoryCache
from research_agent.app.config import settings

logger = logging.getLogger(__name__)


class ExecutorError(Exception):
    """Exception raised when execution fails."""
    pass


class ResearchExecutorAgent:
    """
    Research Executor Agent responsible for taking an ExecutionPlan,
    executing tasks in parallel stage-by-stage using asyncio.gather,
    routing service requests to registered tool components, and caching results.
    """

    def __init__(
        self,
        tool_registry: Optional[Dict[str, BaseTool]] = None,
        cache: Optional[BaseCache] = None,
        on_event: Optional[Any] = None
    ):
        if tool_registry is not None:
            self.tools = tool_registry
        else:
            from research_agent.app.services.tools.scraper_tool import WebScraperTool
            from research_agent.app.services.tools.real_search_tool import RealWebSearchTool

            has_search_key = bool(settings.SERPER_API_KEY or settings.TAVILY_API_KEY)
            search_tool: BaseTool = RealWebSearchTool(
                serper_key=settings.SERPER_API_KEY or "",
                tavily_key=settings.TAVILY_API_KEY or ""
            ) if has_search_key else MockSearchTool()

            self.tools: Dict[str, BaseTool] = {
                "search": search_tool,
                "scraper": WebScraperTool(),
                "fact_check": MockFactCheckTool(),
                "summary": MockSummaryTool(),
                "citation": MockCitationTool(),
                # NEW: Academic and background context tools (free, no API key required)
                "arxiv": ArxivSearchTool(),
                "wikipedia": WikipediaTool(),
            }
        self.cache = cache if cache is not None else InMemoryCache()
        self.on_event = on_event

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self.on_event:
            try:
                self.on_event(event_type, payload)
            except Exception as e:
                logger.warning(f"Error in executor on_event callback: {e}")

    def register_tool(self, service_name: str, tool: BaseTool) -> None:
        """
        Registers or updates a tool implementation in the executor registry.
        """
        self.tools[service_name] = tool
        logger.info(f"Registered tool '{tool.name}' for service '{service_name}'.")

    async def execute_plan(self, plan: ExecutionPlan, max_depth: int = 1) -> PlanExecutionResult:
        """
        Executes an entire ExecutionPlan stage-by-stage. Tasks within each stage run concurrently.
        Supports multi-turn recursive depth execution when max_depth > 1.
        """
        if not plan.tasks:
            raise ExecutorError("Execution plan contains no tasks.")

        logger.info(f"Starting execution for plan '{plan.plan_id}' (depth={max_depth}) with {len(plan.tasks)} subtasks across {len(plan.execution_order)} stages.")
        start_time = time.perf_counter()

        task_map: Dict[str, ResearchTask] = {t.task_id: t for t in plan.tasks}
        stage_results: List[List[TaskExecutionResult]] = []
        total_executed = 0
        total_completed = 0

        for stage_idx, stage_task_ids in enumerate(plan.execution_order):
            logger.info(f"Executing Stage {stage_idx + 1}/{len(plan.execution_order)} with tasks: {stage_task_ids}")
            self._emit("stage_start", {"stage": stage_idx + 1, "task_ids": stage_task_ids})

            stage_tasks = [task_map[tid] for tid in stage_task_ids if tid in task_map]
            if not stage_tasks:
                continue

            # Execute all tasks within current stage in parallel using asyncio.gather
            results: List[TaskExecutionResult] = await asyncio.gather(
                *[self._execute_single_task(task, plan.query) for task in stage_tasks],
                return_exceptions=False
            )

            for res in results:
                self._emit("task_complete", {"task_id": res.task_id, "status": res.status})

            stage_results.append(results)
            total_executed += len(results)
            total_completed += sum(1 for r in results if r.status == "completed")

        # Handle multi-turn recursive deep dive if max_depth > 1
        if max_depth > 1:
            logger.info(f"Executing recursive deep-dive level (depth={max_depth})...")
            deep_task = ResearchTask(
                task_id=f"task-deep-{max_depth}",
                description=f"Deep dive follow-up analysis resolving unresolved questions for: '{plan.query}'",
                expected_output="Deepened evidence fragments and verified references.",
                estimated_services=["search", "fact_check", "summary", "citation"],
                dependencies=[],
                priority=99
            )
            deep_res = await self._execute_single_task(deep_task, plan.query)
            self._emit("task_complete", {"task_id": deep_res.task_id, "status": deep_res.status})
            stage_results.append([deep_res])
            total_executed += 1
            if deep_res.status == "completed":
                total_completed += 1

        total_elapsed = time.perf_counter() - start_time

        overall_status = "completed"
        if total_completed == 0:
            overall_status = "failed"
        elif total_completed < total_executed:
            overall_status = "partial_success"

        logger.info(f"Plan '{plan.plan_id}' execution finished in {total_elapsed:.3f}s with status '{overall_status}'. ({total_completed}/{total_executed} completed)")

        return PlanExecutionResult(
            plan_id=plan.plan_id,
            query=plan.query,
            status=overall_status,
            stage_results=stage_results,
            total_tasks=total_executed,
            completed_tasks=total_completed,
            total_execution_time_seconds=round(total_elapsed, 4)
        )

    async def _execute_single_task(self, task: ResearchTask, query: str) -> TaskExecutionResult:
        """
        Executes a single ResearchTask by concurrently dispatching to estimated services via asyncio.gather.
        """
        task_start = time.perf_counter()
        logger.info(f"Executing Task '{task.task_id}': {task.description}")

        services_to_call = task.estimated_services if task.estimated_services else ["search"]

        # Run tool dispatches concurrently across requested services
        dispatched_results = await asyncio.gather(
            *[self._dispatch_service(service, task, query) for service in services_to_call],
            return_exceptions=True
        )

        service_outputs: Dict[str, Any] = {}
        has_errors = False
        error_messages = []

        for service, res in zip(services_to_call, dispatched_results):
            if isinstance(res, Exception):
                has_errors = True
                error_messages.append(f"{service}: {str(res)}")
            elif res:
                s_name, s_data, s_err = res
                if s_data is not None:
                    service_outputs[s_name] = s_data
                if s_err:
                    has_errors = True
                    error_messages.append(f"{s_name}: {s_err}")

        task_elapsed = time.perf_counter() - task_start
        status = "failed" if (has_errors and not service_outputs) else "completed"

        return TaskExecutionResult(
            task_id=task.task_id,
            status=status,
            service_results=service_outputs,
            error="; ".join(error_messages) if error_messages else None,
            execution_time_seconds=round(task_elapsed, 4)
        )

    async def _dispatch_service(self, service: str, task: ResearchTask, query: str) -> tuple[str, Optional[Any], Optional[str]]:
        """
        Helper method to dispatch an individual tool execution with caching support.
        Includes self-healing retry with query reformulation for search services.
        """
        cache_key = InMemoryCache.generate_key("cache", service, query, task.description)
        if self.cache and self.cache.has(cache_key):
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache hit for service '{service}' in task '{task.task_id}'.")
                return (service, cached_data, None)

        tool = self.tools.get(service)
        if not tool:
            tool = self.tools.get("search")

        if tool:
            if service == "fact_check":
                tool_res = await tool.execute(claims=[task.description])
            elif service == "summary":
                tool_res = await tool.execute(text=task.description)
            elif service == "citation":
                tool_res = await tool.execute(raw_sources=[{"title": task.description, "url": "https://example.org"}])
            elif service == "scraper":
                tool_res = await tool.execute(url=f"https://example.org/search?q={query}")
            else:
                # Self-healing: try exact query first, reformulate on empty results
                combined_query = f"{query} {task.description}"
                tool_res = await tool.execute(query=combined_query)

                # Self-Healing Layer: if search returned 0 results, reformulate and retry
                if (
                    tool_res.success
                    and hasattr(tool_res.data, "total_results")
                    and tool_res.data.total_results == 0
                ):
                    tool_res = await self._self_healing_search(tool, combined_query, service)

            if tool_res.success:
                dumped_data = tool_res.data.model_dump() if hasattr(tool_res.data, "model_dump") else tool_res.data
                if self.cache:
                    self.cache.set(cache_key, dumped_data)
                return (service, dumped_data, None)
            else:
                return (service, None, tool_res.error)

        return (service, None, f"Tool for '{service}' not found.")

    async def _self_healing_search(self, tool: BaseTool, original_query: str, service: str) -> Any:
        """
        Self-Healing Search: autonomously reformulates a zero-result query and
        cascades through fallback strategies before giving up.

        Strategy cascade:
            1. Simplified query  — strip short words and punctuation
            2. ArXiv fallback    — academic paper search (for research-heavy topics)
            3. Wikipedia fallback — broad background context
        """
        logger.info(f"Self-Healing: Zero results from '{service}'. Attempting query reformulation.")

        # Strategy 1: Simplified keyword query (strip words shorter than 4 chars)
        simplified = " ".join([
            w for w in re.sub(r'["\']', '', original_query).split()
            if len(w) > 3
        ])
        if simplified and simplified != original_query:
            logger.info(f"Self-Healing Strategy 1: Simplified query → '{simplified[:50]}'")
            retry_res = await tool.execute(query=simplified)
            if retry_res.success and hasattr(retry_res.data, "total_results") and retry_res.data.total_results > 0:
                return retry_res

        # Strategy 2: ArXiv academic fallback
        arxiv_tool = self.tools.get("arxiv")
        if arxiv_tool:
            logger.info("Self-Healing Strategy 2: Falling back to ArXiv academic search.")
            arxiv_res = await arxiv_tool.execute(query=simplified or original_query, max_results=3)
            if arxiv_res.success and hasattr(arxiv_res.data, "total_results") and arxiv_res.data.total_results > 0:
                return arxiv_res

        # Strategy 3: Wikipedia background context fallback
        wiki_tool = self.tools.get("wikipedia")
        if wiki_tool:
            logger.info("Self-Healing Strategy 3: Falling back to Wikipedia context.")
            wiki_res = await wiki_tool.execute(query=simplified or original_query)
            if wiki_res.success:
                return wiki_res

        # All strategies exhausted — return original (empty) result
        logger.warning("Self-Healing: All fallback strategies exhausted. Returning empty search results.")
        return await tool.execute(query=original_query)

