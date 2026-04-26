from typing import Annotated, Iterable

from fastapi import Depends

from podium.constants import BAD_ACCESS, DEFAULT_ADMIN_PERMISSIONS, PlatformAdminPermission
from podium.db.postgres import User
from podium.routers.auth import get_current_user


def parse_permissions_csv(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


def normalize_permissions_csv(permissions: Iterable[str]) -> str:
    return ",".join(sorted({p.strip() for p in permissions if p and p.strip()}))


def get_effective_admin_permissions(user: User) -> set[str]:
    if user.is_superadmin:
        # Superadmins implicitly have every admin capability.
        return {permission.value for permission in PlatformAdminPermission}

    if not user.is_admin:
        return set()

    return set(DEFAULT_ADMIN_PERMISSIONS) | parse_permissions_csv(user.admin_permissions_csv)


def has_admin_permission(user: User, permission: str) -> bool:
    if user.is_superadmin:
        return True
    return permission in get_effective_admin_permissions(user)


async def require_platform_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_superadmin and not user.is_admin:
        raise BAD_ACCESS
    return user


def require_admin_permission(permission: str):
    async def dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if not has_admin_permission(user, permission):
            raise BAD_ACCESS
        return user

    return dependency
