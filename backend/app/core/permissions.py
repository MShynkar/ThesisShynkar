"""Enums for roles and document access levels."""
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"


class AccessLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


# Hierarchy: which access levels each role can read.
# Higher role = sees more sensitive material.
ROLE_ACCESS_MATRIX: dict[Role, list[AccessLevel]] = {
    Role.GUEST: [AccessLevel.PUBLIC],
    Role.USER: [AccessLevel.PUBLIC, AccessLevel.INTERNAL],
    Role.MANAGER: [
        AccessLevel.PUBLIC,
        AccessLevel.INTERNAL,
        AccessLevel.CONFIDENTIAL,
    ],
    Role.ADMIN: [
        AccessLevel.PUBLIC,
        AccessLevel.INTERNAL,
        AccessLevel.CONFIDENTIAL,
        AccessLevel.RESTRICTED,
    ],
}


def allowed_levels_for_role(role: Role | str) -> list[str]:
    """Return the list of access level strings a role can see."""
    if isinstance(role, str):
        role = Role(role)
    return [lvl.value for lvl in ROLE_ACCESS_MATRIX[role]]
