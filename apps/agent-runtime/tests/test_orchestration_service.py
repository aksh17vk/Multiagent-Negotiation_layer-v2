
import pytest

from app.agents.registry import AgentRegistry
from app.agents.service import AgentExecutionService
from app.orchestration.models import PlanStep, TaskPlan
from app.orchestration.service import OrchestrationService


class FakeAgent:
    def __init__(self, name: str) -> None:
        self.agent_name = name


def make_plan(*agent_names: str) -> TaskPlan:
    return TaskPlan(
        task_id="task-registry-001",
        reasoning="Validate agents against the registry.",
        steps=[
            PlanStep(
                agent_name=name,
                objective=f"Execute {name} review.",
            )
            for name in agent_names
        ],
    )


def make_service(registry: AgentRegistry) -> OrchestrationService:
    execution_service = AgentExecutionService(registry)
    return OrchestrationService(registry, execution_service)


def test_service_accepts_registered_agents():
    registry = AgentRegistry()
    registry.register(FakeAgent("backend"))
    registry.register(FakeAgent("security"))

    service = make_service(registry)

    assert service.validate_plan(
        make_plan("backend", "security")
    ) is None


def test_service_rejects_unregistered_agent():
    registry = AgentRegistry()
    registry.register(FakeAgent("backend"))

    service = make_service(registry)

    with pytest.raises(
        ValueError,
        match="unregistered agents",
    ):
        service.validate_plan(make_plan("backend", "security"))


def test_service_rejects_plan_when_registry_is_empty():
    registry = AgentRegistry()
    service = make_service(registry)

    with pytest.raises(
        ValueError,
        match="unregistered agents",
    ):
        service.validate_plan(make_plan("backend"))
