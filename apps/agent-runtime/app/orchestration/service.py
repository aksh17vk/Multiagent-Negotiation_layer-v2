
from app.agents.registry import AgentRegistry
from app.agents.service import AgentExecutionService
from app.orchestration.models import TaskPlan, get_execution_order
from app.schemas.agent import AgentResult, TaskRequest


class OrchestrationService:
    """Validate and execute agent plans in dependency order."""

    def __init__(
        self,
        registry: AgentRegistry,
        execution_service: AgentExecutionService,
    ) -> None:
        self._registry = registry
        self._execution_service = execution_service

    def validate_plan(self, plan: TaskPlan) -> None:
        registered_agents = set(self._registry.list_agents())
        planned_agents = {step.agent_name for step in plan.steps}
        unknown_agents = planned_agents - registered_agents

        if unknown_agents:
            raise ValueError(
                "Execution plan contains unregistered agents: "
                f"{sorted(unknown_agents)}"
            )

    async def execute_plan(
        self,
        plan: TaskPlan,
        task: TaskRequest,
    ) -> dict[str, AgentResult]:
        self.validate_plan(plan)

        execution_order = get_execution_order(plan)
        steps_by_name = {
            step.agent_name: step for step in plan.steps
        }
        results: dict[str, AgentResult] = {}

        for agent_name in execution_order:
            step = steps_by_name[agent_name]

            failed_dependencies = [
                dependency
                for dependency in step.depends_on
                if results[dependency].status != "completed"
            ]

            if failed_dependencies:
                results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    status="skipped",
                    summary=(
                        "Skipped because dependencies did not complete: "
                        + ", ".join(sorted(failed_dependencies))
                    ),
                )
                continue

            try:
                result = await self._execution_service.execute(
                    agent_name,
                    task,
                )
            except Exception:
                results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    status="failed",
                    summary="Agent execution raised an exception.",
                )
                continue

            results[agent_name] = result

        return results
