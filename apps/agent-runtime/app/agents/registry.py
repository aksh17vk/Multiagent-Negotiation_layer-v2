
from app.agents.base import BaseAgent


class AgentRegistry:
    """Stores and resolves agent implementations by name."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        name = self._validate_name(agent.agent_name)

        if name in self._agents:
            raise ValueError(f"Agent already registered: {name}")

        self._agents[name] = agent

    def get(self, name: str) -> BaseAgent:
        name = self._validate_name(name)

        try:
            return self._agents[name]
        except KeyError:
            raise KeyError(f"Agent not registered: {name}") from None

    def list_agents(self) -> list[str]:
        return sorted(self._agents.keys())

    def unregister(self, name: str) -> None:
        name = self._validate_name(name)

        if name not in self._agents:
            raise KeyError(f"Agent not registered: {name}")

        del self._agents[name]

    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Agent name must be a non-empty string.")

        return name.strip()
