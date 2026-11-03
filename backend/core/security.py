"""Non-executing authorization foundation, not an authentication system."""

from enum import StrEnum


class Permission(StrEnum):
    """Future action categories; none grants execution in Phase 1."""

    READ_ONLY = "read_only"
    ROUTINE = "routine"
    HIGH_RISK = "high_risk"


def is_execution_allowed(action: str, permission: Permission | str) -> bool:
    """Deny all execution, including unknown actions and permission values."""
    return False
