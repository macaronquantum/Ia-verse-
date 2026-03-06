from collections import deque
import time

import pytest

from app.api_gateway.gateway import _check_quota, quotas, reputation


def test_quota_exceeded_hits_reputation():
    agent_id = "quota-agent"
    tool_id = "tool-1"
    now = time.time()
    quotas[(agent_id, tool_id)] = deque([now] * 30)
    before = reputation[agent_id]
    with pytest.raises(Exception):
        _check_quota(agent_id, tool_id)
    assert reputation[agent_id] < before
