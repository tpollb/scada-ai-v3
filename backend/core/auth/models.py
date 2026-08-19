"""Модели данных для аутентификации и авторизации"""
from datetime import datetime
from typing import Optional
from enum import Enum


class RoleType(str, Enum):
    """Предопределенные роли системы"""
    ADMIN = "admin"  # Полный доступ ко всем функциям
    ENGINEER = "engineer"  # Доступ к настройкам и конфигурации
    OPERATOR = "operator"  # Доступ к мониторингу и управлению
    BOSS = "boss"  # Доступ к отчетам и аналитике


class PermissionType(str, Enum):
    """Типы разрешений"""
    # Health модуль
    HEALTH_VIEW = "health:view"
    HEALTH_CONFIGURE = "health:configure"
    
    # Analytics модуль
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_CONFIGURE = "analytics:configure"
    
    # Energy модуль
    ENERGY_VIEW = "energy:view"
    ENERGY_CONFIGURE = "energy:configure"
    
    # Logs модуль
    LOGS_VIEW = "logs:view"
    LOGS_CONFIGURE = "logs:configure"
    
    # Config модуль
    CONFIG_VIEW = "config:view"
    CONFIG_EDIT = "config:edit"
    
    # Users модуль
    USERS_VIEW = "users:view"
    USERS_CREATE = "users:create"
    USERS_EDIT = "users:edit"
    USERS_DELETE = "users:delete"
    
    # Audit модуль
    AUDIT_VIEW = "audit:view"


# Маппинг ролей и разрешений
ROLE_PERMISSIONS = {
    RoleType.ADMIN: {
        PermissionType.HEALTH_VIEW,
        PermissionType.HEALTH_CONFIGURE,
        PermissionType.ANALYTICS_VIEW,
        PermissionType.ANALYTICS_CONFIGURE,
        PermissionType.ENERGY_VIEW,
        PermissionType.ENERGY_CONFIGURE,
        PermissionType.LOGS_VIEW,
        PermissionType.LOGS_CONFIGURE,
        PermissionType.CONFIG_VIEW,
        PermissionType.CONFIG_EDIT,
        PermissionType.USERS_VIEW,
        PermissionType.USERS_CREATE,
        PermissionType.USERS_EDIT,
        PermissionType.USERS_DELETE,
        PermissionType.AUDIT_VIEW,
    },
    RoleType.ENGINEER: {
        PermissionType.HEALTH_VIEW,
        PermissionType.HEALTH_CONFIGURE,
        PermissionType.ANALYTICS_VIEW,
        PermissionType.ANALYTICS_CONFIGURE,
        PermissionType.ENERGY_VIEW,
        PermissionType.ENERGY_CONFIGURE,
        PermissionType.LOGS_VIEW,
        PermissionType.LOGS_CONFIGURE,
        PermissionType.CONFIG_VIEW,
        PermissionType.CONFIG_EDIT,
        PermissionType.USERS_VIEW,
        PermissionType.AUDIT_VIEW,
    },
    RoleType.OPERATOR: {
        PermissionType.HEALTH_VIEW,
        PermissionType.ANALYTICS_VIEW,
        PermissionType.ENERGY_VIEW,
        PermissionType.LOGS_VIEW,
        PermissionType.CONFIG_VIEW,
    },
    RoleType.BOSS: {
        PermissionType.ANALYTICS_VIEW,
        PermissionType.ENERGY_VIEW,
        PermissionType.AUDIT_VIEW,
    },
}
