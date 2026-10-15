
from app.agents.base import BaseAgent
from app.observability.events import (
    ExecutionEvent,
    ExecutionTimer,
    emit_event,
)
from app.schemas.agent import AgentResult, TaskRequest


async def run_agent(
    agent: BaseAgent,
    task: TaskRequest,
) -> AgentResult:
    """Execute an agent and record its lifecycle events."""

    emit_event(
        ExecutionEvent.AGENT_STARTED,
        metadata={"agent_name": agent.agent_name},
    )

    timer = ExecutionTimer()

    try:
        with timer:
            result = await agent.execute(task)
            
            if result.agent_name != agent.agent_name:
              raise ValueError(
                "Agent result identity does not match the executing agent."
            )

        metadata = {
            "agent_name": agent.agent_name,
            "status": result.status,
            "duration_ms": timer.duration_ms,
        }

        if result.status == "failed":
            emit_event(
                ExecutionEvent.AGENT_FAILED,
                metadata={
                    **metadata,
                    "error_code": "AGENT_REPORTED_FAILURE",
                },
            )
        else:
            emit_event(
                ExecutionEvent.AGENT_COMPLETED,
                metadata=metadata,
            )

        return result

    except Exception:
        emit_event(
            ExecutionEvent.AGENT_FAILED,
            metadata={
                "agent_name": agent.agent_name,
                "status": "failed",
                "duration_ms": getattr(timer, "duration_ms", None),
                "error_code": "AGENT_EXECUTION_ERROR",
            },
        )
        raise
