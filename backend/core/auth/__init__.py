"""Модуль аутентификации и авторизации SCADA.AI v3.3.0"""
from .models import RoleType, PermissionType, ROLE_PERMISSIONS
from .schemas import (
    UserCreate, 
    UserUpdate, 
    UserResponse, 
    RoleCreate, 
    RoleResponse,
    Token,
    TokenData,
)
from .service import AuthService
from .dependencies import get_db_session, get_current_user, get_current_active_user

__all__ = [
    "RoleType",
    "PermissionType", 
    "ROLE_PERMISSIONS",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "RoleCreate",
    "RoleResponse",
    "Token",
    "TokenData",
    "AuthService",
    "get_current_user",
    "get_current_active_user",
    "get_db_session",
    "auth_service",
]

from .service import auth_service