
import pytest

from app.agents.base import BaseAgent
from app.agents.registry import AgentRegistry
from app.agents.service import AgentExecutionService
from app.schemas.agent import AgentResult, TaskRequest


class BackendTestAgent(BaseAgent):
    agent_name = "backend"

    async def execute(self, task: TaskRequest) -> AgentResult:
        return AgentResult(
            agent_name="backend",
            status="completed",
            summary=f"Processed task: {task.task_id}",
        )


def make_task() -> TaskRequest:
    return TaskRequest(
        task_id="task-001",
        description="Review the backend implementation.",
    )


@pytest.mark.asyncio
async def test_service_executes_registered_agent():
    registry = AgentRegistry()
    agent = BackendTestAgent()
    registry.register(agent)

    service = AgentExecutionService(registry)

    result = await service.execute("backend", make_task())

    assert result.agent_name == "backend"
    assert result.status == "completed"
    assert result.summary == "Processed task: task-001"


@pytest.mark.asyncio
async def test_service_rejects_unknown_agent():
    registry = AgentRegistry()
    service = AgentExecutionService(registry)

    with pytest.raises(KeyError, match="not registered"):
        await service.execute("unknown", make_task())
