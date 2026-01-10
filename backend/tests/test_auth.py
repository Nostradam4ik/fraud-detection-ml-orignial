"""
Authentication Tests

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import pytest


class TestAuthentication:
    """Test authentication endpoints"""

    def test_register_user(self, client):
        """Test user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "Password123!",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "password" not in data

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "another@example.com",
                "password": "Password123!"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "anotheruser",
                "email": "test@example.com",
                "password": "Password123!"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "Password123!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password123"}
        )
        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user profile"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403

    def test_refresh_token(self, client, test_user):
        """Test token refresh"""
        # First login to get a refresh token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "Password123!"}
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


class TestPasswordReset:
    """Test password reset functionality"""

    def test_forgot_password_existing_user(self, client, test_user):
        """Test forgot password for existing user"""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "reset_token" in data
        assert data["reset_token"] is not None

    def test_forgot_password_nonexistent_user(self, client):
        """Test forgot password for nonexistent user"""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )
        # Should return 200 for security (don't reveal if email exists)
        assert response.status_code == 200
        data = response.json()
        assert data["reset_token"] is None

    def test_reset_password_success(self, client, test_user):
        """Test successful password reset"""
        # First get reset token
        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"}
        )
        token = forgot_response.json()["reset_token"]

        # Reset password
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NewPassword123!"}
        )
        assert response.status_code == 200

        # Try logging in with new password
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "NewPassword123!"}
        )
        assert login_response.status_code == 200

    def test_reset_password_invalid_token(self, client):
        """Test password reset with invalid token"""
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "invalid_token", "new_password": "NewPassword123!"}
        )
        assert response.status_code == 400
