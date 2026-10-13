from contextvars import ContextVar
from uuid import uuid4

trace_id_var: ContextVar[str | None] = ContextVar(
    "mnl_trace_id",
    default=None,
)

task_id_var: ContextVar[str | None] = ContextVar(
    "mnl_task_id",
    default=None,
)


def new_trace_id() -> str:
    """Generate a unique identifier for one execution trace."""
    return str(uuid4())


def get_trace_id() -> str | None:
    return trace_id_var.get()


def get_task_id() -> str | None:
    return task_id_var.get()


def set_execution_context(
    task_id: str,
    trace_id: str | None = None,
) -> tuple[object, object]:
    """Set context and return tokens for safe restoration."""
    task_token = task_id_var.set(task_id)
    trace_token = trace_id_var.set(trace_id or new_trace_id())
    return task_token, trace_token


def reset_execution_context(
    tokens: tuple[object, object],
) -> None:
    task_token, trace_token = tokens
    trace_id_var.reset(trace_token)
    task_id_var.reset(task_token)