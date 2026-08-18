import uuid
import logging
from typing import List, Optional
from research_agent.app.models.plan import ResearchTask, ExecutionPlan, PlanDecompositionSchema
from research_agent.app.services.llm_base import BaseLLMProvider

logger = logging.getLogger(__name__)


class PlannerError(Exception):
    """Exception raised when planning fails."""
    pass


class PlannerAgent:
    """
    Planner Agent responsible for decomposing complex research queries into 
    executable subtasks, estimating required service APIs, and scheduling parallel execution stages.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider

    async def create_plan(self, query: str) -> ExecutionPlan:
        """
        Generates an execution plan for a user query.
        
        Args:
            query: The research topic or question submitted by the user.
            
        Returns:
            ExecutionPlan containing structured tasks and scheduled parallel stages.
            
        Raises:
            PlannerError: If the query is empty or plan creation fails.
        """
        clean_query = query.strip()
        if not clean_query:
            raise PlannerError("Query cannot be empty.")

        logger.info(f"Generating execution plan for query: '{clean_query[:60]}...'")

        # If an LLM provider with structured output capability is supplied, use it
        tasks = await self._decompose_query(clean_query)

        # Compute parallel execution stages based on dependency graph
        execution_order = self.compute_execution_order(tasks)

        plan = ExecutionPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            query=clean_query,
            tasks=tasks,
            execution_order=execution_order
        )

        logger.info(f"Created plan {plan.plan_id} with {len(tasks)} subtasks across {len(execution_order)} stages.")
        return plan

    async def _decompose_query(self, query: str) -> List[ResearchTask]:
        """
        Decomposes the query into subtasks. Uses LLM if available, otherwise falls back to deterministic rule-based decomposition.
        """
        if self.llm_provider:
            try:
                system_prompt = (
                    "You are an expert AI Research Planner. Decompose the user query into 2 to 5 structured "
                    "ResearchTask steps with unique task_ids ('task-1', 'task-2', etc.), clear descriptions, "
                    "expected outputs, estimated services (['search', 'scraper', 'fact_check', 'summary', 'citation']), "
                    "valid dependencies, and priority numbers."
                )
                user_prompt = f"Decompose research query into subtasks:\n'{query}'"
                result = await self.llm_provider.generate_structured(
                    prompt=user_prompt,
                    schema=PlanDecompositionSchema,
                    system_prompt=system_prompt
                )
                if result and result.tasks:
                    logger.info(f"Successfully generated {len(result.tasks)} subtasks via LLM provider.")
                    return result.tasks
            except Exception as e:
                logger.warning(f"LLM provider decomposition failed: {e}. Falling back to rule-based planner.")

        # Rule-based fallback planning logic for keyless/testing setup
        return self._heuristic_decomposition(query)

    def _heuristic_decomposition(self, query: str) -> List[ResearchTask]:
        """
        Deterministic decomposition logic to construct multi-step tasks without needing external LLM calls.
        """
        query_lower = query.lower()

        # Task 1: Background & Literature Search
        task1 = ResearchTask(
            task_id="task-1",
            description=f"Gather foundational information and general search results regarding: '{query}'",
            expected_output="Comprehensive background data summary and key web references.",
            estimated_services=["search"],
            dependencies=[],
            priority=1
        )

        # Check if query suggests a comparative or multi-faceted analysis
        is_comparative = any(kw in query_lower for kw in ["compare", "versus", "vs", "difference", "comparison", "pros and cons"])

        if is_comparative:
            task2 = ResearchTask(
                task_id="task-2",
                description=f"Perform deep-dive domain search on key comparison entities in: '{query}'",
                expected_output="Specific metrics, feature comparisons, and domain data.",
                estimated_services=["search", "fact_check"],
                dependencies=["task-1"],
                priority=2
            )

            task3 = ResearchTask(
                task_id="task-3",
                description="Cross-verify findings, resolve conflicting data points, and validate sources.",
                expected_output="Verified fact table with confidence scores.",
                estimated_services=["fact_check", "summary", "citation"],
                dependencies=["task-1", "task-2"],
                priority=3
            )
            return [task1, task2, task3]
        else:
            task2 = ResearchTask(
                task_id="task-2",
                description=f"Analyze detailed evidence, statistical findings, and expert sources for: '{query}'",
                expected_output="Extracted evidence fragments and detailed analysis.",
                estimated_services=["search", "fact_check", "summary", "citation"],
                dependencies=["task-1"],
                priority=2
            )
            return [task1, task2]

    @staticmethod
    def compute_execution_order(tasks: List[ResearchTask]) -> List[List[str]]:
        """
        Resolves task dependencies into sequential stages. Tasks within the same stage can be executed concurrently.
        
        Args:
            tasks: List of ResearchTask objects.
            
        Returns:
            List of stages, where each stage is a list of task_id strings.
        """
        task_map = {t.task_id: t for t in tasks}
        completed = set()
        unvisited = set(task_map.keys())
        stages: List[List[str]] = []

        while unvisited:
            # Find all tasks whose dependencies are satisfied by completed tasks
            ready_tasks = [
                tid for tid in unvisited
                if all(dep in completed for dep in task_map[tid].dependencies)
            ]

            if not ready_tasks:
                # Cyclic or missing dependency encountered
                raise PlannerError("Cyclic or unresolved dependency detected in tasks.")

            # Sort for deterministic output
            ready_tasks.sort()
            stages.append(ready_tasks)
            completed.update(ready_tasks)
            unvisited.difference_update(ready_tasks)

        return stages

    async def create_delta_plan(self, original_plan: ExecutionPlan, follow_up: str) -> ExecutionPlan:
        """
        Interactive Re-Planning: Generates an execution plan containing only the new / delta
        subtasks required to answer a follow-up query, preserving cached results.
        """
        clean_follow_up = follow_up.strip()
        if not clean_follow_up:
            raise PlannerError("Follow-up query cannot be empty.")

        logger.info(f"Generating Delta Plan for follow-up: '{clean_follow_up[:60]}' relative to plan '{original_plan.plan_id}'")

        # Decompose the follow-up prompt into targeted tasks
        delta_tasks = [
            ResearchTask(
                task_id=f"task-delta-{uuid.uuid4().hex[:4]}",
                description=f"Resolve follow-up: '{clean_follow_up}' relying on previous context.",
                expected_output="Delta findings and source references.",
                estimated_services=["search", "summary"],
                dependencies=[],
                priority=5
            )
        ]

        # Stage calculation for delta tasks
        execution_order = self.compute_execution_order(delta_tasks)

        return ExecutionPlan(
            plan_id=f"plan-delta-{uuid.uuid4().hex[:8]}",
            query=clean_follow_up,
            tasks=delta_tasks,
            execution_order=execution_order
        )

