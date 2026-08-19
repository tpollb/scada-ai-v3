"""Pydantic схемы для аутентификации и авторизации"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from .models import RoleType


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    role: RoleType = RoleType.OPERATOR
    is_active: bool = True


class UserCreate(UserBase):
    """Схема создания пользователя"""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Схема обновления пользователя"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[RoleType] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""
    id: int
    created_at: datetime | None = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    """Схема создания роли"""
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None
    permissions: List[str] = []


class RoleResponse(BaseModel):
    """Схема ответа с данными роли"""
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    created_at: datetime | None = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Схема токена доступа"""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class TokenData(BaseModel):
    """Данные из токена"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[RoleType] = None


class LoginRequest(BaseModel):
    """Запрос на вход"""
    username: str
    password: str


class AuditLogCreate(BaseModel):
    """Схема создания записи аудита"""
    user_id: int
    action: str
    resource: str
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None


class AuditLogResponse(AuditLogCreate):
    """Схема ответа с записью аудита"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True
