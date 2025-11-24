from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    PROJECT_NAME: str = "Sentinel"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_VERSION: str = "v1"
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS - Changed to handle comma-separated string
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Admin
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_PASSWORD: str
    FORCE_ADMIN_PASSWORD_CHANGE: bool = True
    
    # Data Retention
    ACTIVITY_RETENTION_DAYS: int = 90
    LOG_RETENTION_DAYS: int = 30
    
    # Compliance
    REQUIRE_EMPLOYEE_CONSENT: bool = True
    ENABLE_AUDIT_LOGGING: bool = True
    
    # Redis
    REDIS_URL: Optional[str] = None
    
    # TLS
    REQUIRE_HTTPS: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_allowed_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS
    
    def validate_settings(self) -> List[str]:
        """Validate critical settings"""
        errors = []
        
        if self.SECRET_KEY == "CHANGE_THIS_TO_A_SECURE_RANDOM_KEY_AT_LEAST_32_CHARS":
            errors.append("SECRET_KEY must be changed from default value")
        
        if len(self.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be at least 32 characters")
        
        if self.INITIAL_ADMIN_PASSWORD == "CHANGE_THIS_IMMEDIATELY":
            errors.append("INITIAL_ADMIN_PASSWORD must be changed")
        
        if not self.DATABASE_URL.startswith("postgresql://"):
            errors.append("DATABASE_URL must be PostgreSQL")
        
        if self.ENVIRONMENT == "production" and self.DEBUG:
            errors.append("DEBUG must be False in production")
        
        if self.ENVIRONMENT == "production" and "*" in self.ALLOWED_ORIGINS:
            errors.append("ALLOWED_ORIGINS cannot contain '*' in production")
        
        return errors


settings = Settings()

# Validate settings on startup
validation_errors = settings.validate_settings()
if validation_errors and settings.ENVIRONMENT == "production":
    raise ValueError(f"Configuration errors: {', '.join(validation_errors)}")
elif validation_errors:
    print("⚠️  Configuration warnings:")
    for error in validation_errors:
        print(f"  - {error}")