
from abc import ABC, abstractmethod

from app.schemas.agent import AgentResult, TaskRequest


class BaseAgent(ABC):
    """Common contract that every MNL agent must implement."""

    agent_name: str

    @abstractmethod
    async def execute(self, task: TaskRequest) -> AgentResult:
        """Execute a task and return a structured result."""
        raise NotImplementedError
