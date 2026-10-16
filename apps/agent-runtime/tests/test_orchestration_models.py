
import pytest
from pydantic import ValidationError

from app.orchestration.models import PlanStep, TaskPlan


def test_task_plan_accepts_valid_plan():
    plan = TaskPlan(
        task_id="task-001",
        reasoning="The task needs backend and security review.",
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

    assert plan.status == "planned"
    assert len(plan.steps) == 2
    assert plan.steps[1].depends_on == ["backend"]


def test_task_plan_rejects_empty_steps():
    with pytest.raises(ValidationError):
        TaskPlan(
            task_id="task-002",
            reasoning="No execution steps provided.",
            steps=[],
        )


def test_plan_step_rejects_empty_agent_name():
    with pytest.raises(ValidationError):
        PlanStep(
            agent_name=" ",
            objective="Review the code.",
        )

