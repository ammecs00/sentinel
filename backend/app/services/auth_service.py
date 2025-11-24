from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging
from fastapi import Request

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    validate_password_strength,
)
from app.models.user import User
from app.models.api_key import ApiKey
from app.core.security import hash_api_key, verify_api_key, generate_api_key
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(
        self,
        username: str,
        password: str,
        request: Optional[Request] = None,
    ) -> Tuple[Optional[User], str]:
        """
        Authenticate a user by username + password.
        Uses constant-time comparison principles where possible to reduce timing leaks.
        """
        user = self.db.query(User).filter(User.username == username).first()
        
        # If user doesn't exist, we still verify a dummy password to prevent timing attacks
        if not user:
            # This is a dummy verify to take up time
            verify_password(password, "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWrn.96pprCtk.iYF3d4.n.n.n.n")
            logger.warning(f"Login attempt for non-existent user: {username}")
            return None, "Invalid credentials"

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            self.db.commit()
            logger.warning(f"Failed login attempt for user: {username}")
            return None, "Invalid credentials"

        # Check status after password verification to verify credentials first
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username}")
            return None, "Account is disabled"

        if user.failed_login_attempts >= 5:
            logger.warning(f"Account locked due to failed attempts: {username}")
            return None, "Account is temporarily locked. Contact administrator."

        # Successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        self.db.commit()

        # Inject user_id for rate limiting if request context is provided
        if request is not None:
            request.state.user_id = user.id

        logger.info(f"Successful login: {username}")
        return user, ""

    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        is_admin: bool = False,
    ) -> Tuple[Optional[User], str]:

        existing_user = self.db.query(User).filter(User.username == username).first()
        if existing_user:
            return None, "Username already exists"

        if email:
            existing_email = self.db.query(User).filter(User.email == email).first()
            if existing_email:
                return None, "Email already exists"

        is_valid, error = validate_password_strength(password)
        if not is_valid:
            return None, error

        try:
            user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                is_admin=is_admin,
                is_active=True,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info(f"User created: {username}")
            return user, ""
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {e}")
            return None, "Error creating user"

    def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> Tuple[bool, str]:
        if not verify_password(current_password, user.hashed_password):
            logger.warning(f"Failed password change attempt for user: {user.username}")
            return False, "Current password is incorrect"

        is_valid, error = validate_password_strength(new_password)
        if not is_valid:
            return False, error

        if verify_password(new_password, user.hashed_password):
            return False, "New password must be different from current password"

        try:
            user.hashed_password = get_password_hash(new_password)
            user.force_password_change = False
            self.db.commit()

            logger.info(f"Password changed for user: {user.username}")
            return True, ""
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error changing password: {e}")
            return False, "Error changing password"

    def create_access_token_for_user(self, user: User) -> str:
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": user.username, "admin": user.is_admin},
            expires_delta=access_token_expires,
        )
        return access_token

    def create_api_key(
        self,
        name: str,
        created_by: int,
        allowed_ips: Optional[str] = None,
        rate_limit: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> Tuple[Optional[ApiKey], Optional[str], str]:

        try:
            plain_key = generate_api_key()
            key_hash = hash_api_key(plain_key)
            key_prefix = plain_key[:10]

            api_key = ApiKey(
                name=name,
                key_hash=key_hash,
                key_prefix=key_prefix,
                created_by=created_by,
                allowed_ips=allowed_ips,
                rate_limit=rate_limit,
                expires_at=expires_at,
                is_active=True,
            )

            self.db.add(api_key)
            self.db.commit()
            self.db.refresh(api_key)

            logger.info(f"API key created: {name}")
            return api_key, plain_key, ""
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating API key: {e}")
            return None, None, "Error creating API key"

    def verify_api_key(self, api_key: str) -> Tuple[Optional[ApiKey], str]:
        if not api_key or not api_key.startswith("sk_"):
            return None, "Invalid API key format"

        key_hash = hash_api_key(api_key)

        db_api_key = (
            self.db.query(ApiKey)
            .filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
            .first()
        )

        if not db_api_key:
            logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
            return None, "Invalid API key"

        if db_api_key.expires_at and db_api_key.expires_at < datetime.utcnow():
            logger.warning(f"Expired API key used: {db_api_key.name}")
            return None, "API key has expired"

        db_api_key.last_used = datetime.utcnow()
        db_api_key.usage_count += 1
        self.db.commit()

        return db_api_key, ""

    def revoke_api_key(self, key_id: int) -> Tuple[bool, str]:
        api_key = self.db.query(ApiKey).filter(ApiKey.id == key_id).first()
        if not api_key:
            return False, "API key not found"

        try:
            api_key.is_active = False
            self.db.commit()
            logger.info(f"API key revoked: {api_key.name}")
            return True, ""
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error revoking API key: {e}")
            return False, "Error revoking API key"

    def list_api_keys(self) -> list[ApiKey]:
        return (
            self.db.query(ApiKey)
            .filter(ApiKey.is_active == True)  # <--- Add this filter
            .order_by(ApiKey.created_at.desc())
            .all()
        )


def create_initial_admin():
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        admin = (
            db.query(User)
            .filter(User.username == settings.INITIAL_ADMIN_USERNAME)
            .first()
        )
        if not admin:
            is_valid, error = validate_password_strength(
                settings.INITIAL_ADMIN_PASSWORD
            )
            if not is_valid:
                logger.error(
                    f"Initial admin password not strong enough: {error}"
                )
                return

            admin = User(
                username=settings.INITIAL_ADMIN_USERNAME,
                email=None,
                hashed_password=get_password_hash(
                    settings.INITIAL_ADMIN_PASSWORD
                ),
                is_admin=True,
                is_active=True,
                force_password_change=settings.FORCE_ADMIN_PASSWORD_CHANGE,
            )
            db.add(admin)
            db.commit()
            logger.info(
                f"Created initial admin user: {settings.INITIAL_ADMIN_USERNAME}"
            )
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating initial admin: {e}")
    finally:
        db.close()