
import pytest

from app.agents.base import BaseAgent
from app.agents.registry import AgentRegistry
from app.schemas.agent import AgentResult, TaskRequest


class TestAgent(BaseAgent):
    agent_name = "backend"

    async def execute(self, task: TaskRequest) -> AgentResult:
        return AgentResult(
            agent_name="backend",
            status="completed",
            summary="Test execution completed.",
        )


class SecurityTestAgent(TestAgent):
    agent_name = "security"

    async def execute(self, task: TaskRequest) -> AgentResult:
        return AgentResult(
            agent_name="security",
            status="completed",
            summary="Security test completed.",
        )


def test_register_and_get_agent():
    registry = AgentRegistry()
    agent = TestAgent()

    registry.register(agent)

    assert registry.get("backend") is agent


def test_duplicate_registration_is_rejected():
    registry = AgentRegistry()
    registry.register(TestAgent())

    with pytest.raises(ValueError, match="already registered"):
        registry.register(TestAgent())


def test_unknown_agent_is_rejected():
    registry = AgentRegistry()

    with pytest.raises(KeyError, match="not registered"):
        registry.get("unknown")


def test_list_agents_returns_sorted_names():
    registry = AgentRegistry()
    registry.register(SecurityTestAgent())
    registry.register(TestAgent())

    assert registry.list_agents() == ["backend", "security"]


def test_unregister_agent():
    registry = AgentRegistry()
    registry.register(TestAgent())

    registry.unregister("backend")

    assert registry.list_agents() == []


def test_empty_agent_name_is_rejected():
    registry = AgentRegistry()

    with pytest.raises(ValueError, match="non-empty"):
        registry.get("   ")
