
from app.agents.registry import AgentRegistry
from app.agents.runner import run_agent
from app.schemas.agent import AgentResult, TaskRequest


class AgentExecutionService:
    """Resolve registered agents and execute their tasks."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    async def execute(
        self,
        agent_name: str,
        task: TaskRequest,
    ) -> AgentResult:
        agent = self._registry.get(agent_name)
        return await run_agent(agent, task)
