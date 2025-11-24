import pytest
from app.core.security import get_password_hash, verify_password, validate_password_strength


def test_password_hashing():
    """Test password hashing and verification"""
    password = "TestPassword123!@#"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_password_strength_validation():
    """Test password strength validation"""
    # Valid password
    is_valid, error = validate_password_strength("ValidPass123!@#")
    assert is_valid is True
    assert error == ""
    
    # Too short
    is_valid, error = validate_password_strength("Short1!")
    assert is_valid is False
    assert "at least 8 characters" in error
    
    # No uppercase
    is_valid, error = validate_password_strength("lowercase123!")
    assert is_valid is False
    assert "uppercase" in error
    
    # No lowercase
    is_valid, error = validate_password_strength("UPPERCASE123!")
    assert is_valid is False
    assert "lowercase" in error
    
    # No number
    is_valid, error = validate_password_strength("NoNumber!@#")
    assert is_valid is False
    assert "number" in error
    
    # No special character
    is_valid, error = validate_password_strength("NoSpecial123")
    assert is_valid is False
    assert "special character" in error


def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "Test123!@#"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "WrongPassword"}
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "Password123!"}
    )
    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user information"""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403  # No credentials provided


def test_change_password_success(client, auth_headers):
    """Test successful password change"""
    response = client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "current_password": "Test123!@#",
            "new_password": "NewPassword123!@#"
        }
    )
    assert response.status_code == 200


def test_change_password_wrong_current(client, auth_headers):
    """Test password change with wrong current password"""
    response = client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "current_password": "WrongPassword",
            "new_password": "NewPassword123!@#"
        }
    )
    assert response.status_code == 400


def test_change_password_weak_new(client, auth_headers):
    """Test password change with weak new password"""
    response = client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "current_password": "Test123!@#",
            "new_password": "weak"
        }
    )
    assert response.status_code == 422  # Validation error