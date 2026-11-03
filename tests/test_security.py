"""No action or category can grant Phase 1 execution."""

import pytest

from backend.core.security import Permission, is_execution_allowed


@pytest.mark.parametrize("permission", [*Permission, "unknown", "", "admin"])
@pytest.mark.parametrize("action", ["status", "launch_application", "delete_files", "unknown", ""])
def test_every_action_is_denied(action: str, permission: Permission | str) -> None:
    assert is_execution_allowed(action, permission) is False
