from typing import Literal
import heapq

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

class PlanStep(BaseModel):
    """One agent assignment in an execution plan."""

    agent_name: str = Field(min_length=1, max_length=100)
    objective: str = Field(min_length=1, max_length=2_000)
    depends_on: list[str] = Field(default_factory=list)

    @field_validator("agent_name")
    @classmethod
    def agent_name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("agent_name must not be blank")

        return value


class TaskPlan(BaseModel):
    """Structured execution plan created by the orchestrator."""

    task_id: str = Field(min_length=1, max_length=100)
    status: Literal["planned", "rejected"] = "planned"
    reasoning: str = Field(min_length=1, max_length=2_000)
    steps: list[PlanStep] = Field(min_length=1, max_length=50)


    @model_validator(mode="after")
    def validate_dependencies(self):
        agent_names = [step.agent_name for step in self.steps]

        if len(agent_names) != len(set(agent_names)):
            raise ValueError("Agent names must be unique within a plan")

        known_agents = set(agent_names)
        dependency_graph: dict[str, list[str]] = {}

        for step in self.steps:
            if step.agent_name in step.depends_on:
                raise ValueError(
                    f"Agent '{step.agent_name}' cannot depend on itself"
                )

            unknown_dependencies = set(step.depends_on) - known_agents

            if unknown_dependencies:
                raise ValueError(
                    f"Agent '{step.agent_name}' has unknown dependencies: "
                    f"{sorted(unknown_dependencies)}"
                )

            dependency_graph[step.agent_name] = step.depends_on

        # 0 = not visited, 1 = currently visiting, 2 = completed
        state = {name: 0 for name in agent_names}

        def visit(agent_name: str) -> None:
            if state[agent_name] == 1:
                raise ValueError(
                    f"Dependency cycle detected involving '{agent_name}'"
                )

            if state[agent_name] == 2:
                return

            state[agent_name] = 1

            for dependency in dependency_graph[agent_name]:
                visit(dependency)

            state[agent_name] = 2

        for agent_name in agent_names:
            if state[agent_name] == 0:
                visit(agent_name)

        return self


def get_execution_order(plan: TaskPlan) -> list[str]:
    """Return a deterministic execution order respecting dependencies."""

    dependencies = {
        step.agent_name: set(step.depends_on)
        for step in plan.steps
    }

    dependents = {name: [] for name in dependencies}
    in_degree = {
        name: len(required)
        for name, required in dependencies.items()
    }

    for agent_name, required_agents in dependencies.items():
        for required_agent in required_agents:
            dependents[required_agent].append(agent_name)

    ready = [
        name for name, degree in in_degree.items()
        if degree == 0
    ]
    heapq.heapify(ready)

    order = []

    while ready:
        current = heapq.heappop(ready)
        order.append(current)

        for dependent in sorted(dependents[current]):
            in_degree[dependent] -= 1

            if in_degree[dependent] == 0:
                heapq.heappush(ready, dependent)

    if len(order) != len(dependencies):
        raise ValueError("Cannot order agents: dependency cycle detected")

    return order