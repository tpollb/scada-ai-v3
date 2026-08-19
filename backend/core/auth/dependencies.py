"""Зависимости для аутентификации"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .service import auth_service, decode_access_token
from .schemas import TokenData, UserResponse
from .models import RoleType


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    """Получение текущего пользователя из токена"""
    token_data = decode_access_token(token)
    
    if token_data is None or token_data.username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Заменить на получение из БД
    # Пока используем захардкоженных пользователей
    for user_data in auth_service.default_users:
        if user_data["username"] == token_data.username:
            return UserResponse(
                id=1,
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=True,
                created_at=None,
            )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Пользователь не найден",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Проверка что пользователь активен"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь не активен")
    return current_user


def require_role(required_role: RoleType):
    """Декоратор для проверки роли"""
    async def role_checker(current_user: UserResponse = Depends(get_current_active_user)):
        if current_user.role != required_role and current_user.role != RoleType.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется роль {required_role.value}",
            )
        return current_user
    return role_checker


def require_permission(permission: str):
    """Декоратор для проверки разрешения"""
    from .models import PermissionType
    
    async def permission_checker(current_user: UserResponse = Depends(get_current_active_user)):
        try:
            perm = PermissionType(permission)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Неизвестное разрешение: {permission}",
            )
        
        if not auth_service.check_permission(current_user.role, perm):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется: {permission}",
            )
        return current_user
    return permission_checker


async def get_db_session():
    """Заглушка для сессии БД (будет реализовано позже)"""
    # TODO: Реализовать получение сессии SQLAlchemy/asyncpg
    yield None
