
import pytest

from app.agents.base import BaseAgent


def test_base_agent_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseAgent()
