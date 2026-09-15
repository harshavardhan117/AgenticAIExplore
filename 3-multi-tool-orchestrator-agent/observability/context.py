"""One shared run ID, readable from anywhere, without passing it through every call."""

import contextvars
import uuid

_run_id: contextvars.ContextVar[str] = contextvars.ContextVar("run_id", default="no-run")


def new_run_id() -> str:
    run_id = uuid.uuid4().hex[:8]
    _run_id.set(run_id)
    return run_id


def current_run_id() -> str:
    return _run_id.get()
