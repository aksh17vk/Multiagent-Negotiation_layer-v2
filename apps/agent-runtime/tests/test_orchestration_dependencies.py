import pytest
from pydantic import ValidationError

from app.orchestration.models import PlanStep, TaskPlan
from app.orchestration.models import get_execution_order


def test_task_plan_rejects_unknown_dependency():
    with pytest.raises(ValidationError):
        TaskPlan(
            task_id="task-101",
            reasoning="Security depends on a missing agent.",
            steps=[
                PlanStep(
                    agent_name="backend",
                    objective="Review backend implementation.",
                ),
                PlanStep(
                    agent_name="security",
                    objective="Review security risks.",
                    depends_on=["database"],
                ),
            ],
        )


def test_task_plan_rejects_self_dependency():
    with pytest.raises(ValidationError):
        TaskPlan(
            task_id="task-102",
            reasoning="An agent cannot depend on itself.",
            steps=[
                PlanStep(
                    agent_name="backend",
                    objective="Review backend implementation.",
                    depends_on=["backend"],
                ),
            ],
        )


def test_task_plan_accepts_valid_dependency():
    plan = TaskPlan(
        task_id="task-103",
        reasoning="Security review follows backend review.",
        steps=[
            PlanStep(
                agent_name="backend",
                objective="Review backend implementation.",
            ),
            PlanStep(
                agent_name="security",
                objective="Review security risks.",
                depends_on=["backend"],
            ),
        ],
    )

    assert len(plan.steps) == 2


def test_task_plan_rejects_two_agent_cycle():
    with pytest.raises(ValidationError):
        TaskPlan(
            task_id="task-201",
            reasoning="Agents depend on each other.",
            steps=[
                PlanStep(
                    agent_name="backend",
                    objective="Review backend implementation.",
                    depends_on=["security"],
                ),
                PlanStep(
                    agent_name="security",
                    objective="Review security risks.",
                    depends_on=["backend"],
                ),
            ],
        )


def test_task_plan_rejects_long_dependency_cycle():
    with pytest.raises(ValidationError):
        TaskPlan(
            task_id="task-202",
            reasoning="Three agents form a dependency cycle.",
            steps=[
                PlanStep(
                    agent_name="backend",
                    objective="Review backend.",
                    depends_on=["security"],
                ),
                PlanStep(
                    agent_name="security",
                    objective="Review security.",
                    depends_on=["database"],
                ),
                PlanStep(
                    agent_name="database",
                    objective="Review database.",
                    depends_on=["backend"],
                ),
            ],
        )


def test_task_plan_accepts_valid_dependency_chain():
    plan = TaskPlan(
        task_id="task-203",
        reasoning="Agents execute in dependency order.",
        steps=[
            PlanStep(
                agent_name="backend",
                objective="Review backend.",
            ),
            PlanStep(
                agent_name="security",
                objective="Review security.",
                depends_on=["backend"],
            ),
            PlanStep(
                agent_name="database",
                objective="Review database.",
                depends_on=["security"],
            ),
        ],
    )

    assert len(plan.steps) == 3


def test_execution_order_respects_dependencies():
    plan = TaskPlan(
        task_id="task-301",
        reasoning="Security depends on backend.",
        steps=[
            PlanStep(
                agent_name="security",
                objective="Review security risks.",
                depends_on=["backend"],
            ),
            PlanStep(
                agent_name="backend",
                objective="Review backend implementation.",
            ),
        ],
    )

    order = get_execution_order(plan)

    assert order.index("backend") < order.index("security")


def test_execution_order_handles_independent_agents():
    plan = TaskPlan(
        task_id="task-302",
        reasoning="Both agents can start independently.",
        steps=[
            PlanStep(
                agent_name="security",
                objective="Review security risks.",
            ),
            PlanStep(
                agent_name="backend",
                objective="Review backend implementation.",
            ),
        ],
    )

    order = get_execution_order(plan)

    assert set(order) == {"backend", "security"}
    assert len(order) == 2