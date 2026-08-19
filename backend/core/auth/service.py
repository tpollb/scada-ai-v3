"""Сервис аутентификации и авторизации"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from structlog import get_logger

from config.settings import settings
from .models import RoleType, ROLE_PERMISSIONS, PermissionType
from .schemas import Token, TokenData, UserCreate, UserResponse


logger = get_logger()

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    """Создание JWT токена"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    
    return encoded_jwt, expire


def decode_access_token(token: str) -> Optional[TokenData]:
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        
        if username is None:
            return None
        
        return TokenData(
            username=username,
            user_id=user_id,
            role=RoleType(role) if role else None
        )
    except JWTError:
        return None


class AuthService:
    """Сервис аутентификации и авторизации"""
    
    def __init__(self):
        self.default_users = [
            {
                "username": "admin",
                "password": "admin123",
                "email": "admin@scada.ai",
                "full_name": "Администратор системы",
                "role": RoleType.ADMIN,
            },
            {
                "username": "engineer",
                "password": "engineer123",
                "email": "engineer@scada.ai",
                "full_name": "Инженер",
                "role": RoleType.ENGINEER,
            },
            {
                "username": "operator",
                "password": "operator123",
                "email": "operator@scada.ai",
                "full_name": "Оператор",
                "role": RoleType.OPERATOR,
            },
            {
                "username": "boss",
                "password": "boss123",
                "email": "boss@scada.ai",
                "full_name": "Руководитель",
                "role": RoleType.BOSS,
            },
        ]
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserResponse]:
        """Аутентификация пользователя"""
        # TODO: Заменить на запрос к БД
        # Пока используем захардкоженных пользователей
        for user_data in self.default_users:
            if user_data["username"] == username:
                # В реальности здесь будет проверка хеша из БД
                if password == user_data["password"]:
                    return UserResponse(
                        id=1,
                        username=user_data["username"],
                        email=user_data["email"],
                        full_name=user_data["full_name"],
                        role=user_data["role"],
                        is_active=True,
                        created_at=datetime.utcnow(),
                    )
        return None
    
    async def create_token(self, user: UserResponse) -> Token:
        """Создание токена для пользователя"""
        access_token, expire = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "role": user.role.value,
            }
        )
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=expire,
        )
    
    async def login(self, username: str, password: str) -> Optional[Token]:
        """Вход пользователя"""
        user = await self.authenticate_user(username, password)
        if not user:
            return None
        return await self.create_token(user)
    
    @staticmethod
    def check_permission(role: RoleType, permission: PermissionType) -> bool:
        """Проверка наличия разрешения у роли"""
        role_permissions = ROLE_PERMISSIONS.get(role, set())
        return permission in role_permissions
    
    @staticmethod
    def get_role_permissions(role: RoleType) -> set[PermissionType]:
        """Получение всех разрешений для роли"""
        return ROLE_PERMISSIONS.get(role, set())
    
    async def init_default_users(self):
        """Инициализация пользователей по умолчанию"""
        logger.info(
            "Initializing default users",
            count=len(self.default_users),
            users=[u["username"] for u in self.default_users]
        )
        # TODO: Добавить логику создания в БД если их нет
        return self.default_users


auth_service = AuthService()
