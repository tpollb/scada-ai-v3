"""API маршруты для аутентификации и управления пользователями"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from core.auth.schemas import (
    LoginRequest, 
    Token, 
    UserResponse, 
    UserCreate, 
    UserUpdate,
    RoleResponse,
)
from core.auth.service import auth_service
from core.auth.dependencies import get_current_active_user, require_permission
from core.auth.models import RoleType


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token, summary="Вход в систему")
async def login(login_data: LoginRequest):
    """
    Аутентификация пользователя и получение JWT токена.
    
    **Предустановленные пользователи:**
    - admin / admin123 (полный доступ)
    - engineer / engineer123 (настройки и конфигурация)
    - operator / operator123 (мониторинг и управление)
    - boss / boss123 (отчеты и аналитика)
    """
    token = await auth_service.login(login_data.username, login_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@router.get("/me", response_model=UserResponse, summary="Текущий пользователь")
async def get_me(current_user: UserResponse = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе"""
    return current_user


@router.get(
    "/permissions", 
    response_model=List[str],
    summary="Разрешения текущего пользователя",
)
async def get_my_permissions(current_user: UserResponse = Depends(get_current_active_user)):
    """Получение списка разрешений для роли текущего пользователя"""
    permissions = auth_service.get_role_permissions(current_user.role)
    return [p.value for p in permissions]


# Маршруты для управления пользователями (только admin)
users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: UserResponse = Depends(require_permission("users:view"))
):
    """Список всех пользователей (требуется роль admin)"""
    # TODO: Заменить на запрос к БД
    return [
        UserResponse(
            id=1,
            username=u["username"],
            email=u["email"],
            full_name=u["full_name"],
            role=u["role"],
            is_active=True,
            created_at=None,
        )
        for u in auth_service.default_users
    ]


@users_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: UserResponse = Depends(require_permission("users:create"))
):
    """Создание нового пользователя (требуется роль admin)"""
    # TODO: Реализовать создание в БД
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Функционал создания пользователей будет доступен в следующей версии"
    )


# Маршруты для управления ролями
roles_router = APIRouter(prefix="/roles", tags=["Roles"])


@roles_router.get("/", response_model=List[dict])
async def list_roles(
    current_user: UserResponse = Depends(require_permission("users:view"))
):
    """Список всех ролей с разрешениями"""
    return [
        {
            "name": role.value,
            "permissions": [p.value for p in permissions],
        }
        for role, permissions in auth_service.ROLE_PERMISSIONS.items()
    ]


@roles_router.get("/{role_name}/permissions", response_model=List[str])
async def get_role_permissions(
    role_name: str,
    current_user: UserResponse = Depends(require_permission("users:view"))
):
    """Получение разрешений для конкретной роли"""
    try:
        role = RoleType(role_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Роль {role_name} не найдена"
        )
    
    permissions = auth_service.get_role_permissions(role)
    return [p.value for p in permissions]
