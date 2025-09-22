"""
인증 API 테스트
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, RefreshToken
from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD, TEST_USER_NAME


class TestAuth:
    """인증 API 테스트 클래스"""

    def test_register_success(self, client: TestClient):
        """회원가입 성공 테스트"""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "newpassword123",
                "name": "새로운 사용자"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 응답 데이터 검증
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert "user" in data
        assert data["expires_in"] == 1800  # 30분
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["name"] == "새로운 사용자"

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """중복 이메일 회원가입 실패 테스트"""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": TEST_USER_EMAIL,
                "password": "anotherpassword123",
                "name": "다른 사용자"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "이미 등록된 이메일입니다" in data["detail"]

    def test_register_invalid_email(self, client: TestClient):
        """잘못된 이메일 형식 회원가입 실패 테스트"""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "password123",
                "name": "사용자"
            }
        )
        
        assert response.status_code == 422

    def test_login_success(self, client: TestClient, test_user: User):
        """로그인 성공 테스트"""
        response = client.post(
            "/v1/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 응답 데이터 검증
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_USER_EMAIL

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """잘못된 비밀번호 로그인 실패 테스트"""
        response = client.post(
            "/v1/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "이메일 또는 비밀번호가 올바르지 않습니다" in data["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """존재하지 않는 사용자 로그인 실패 테스트"""
        response = client.post(
            "/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401

    def test_get_profile_success(self, client: TestClient, test_user: User, test_user_token: str):
        """프로필 조회 성공 테스트"""
        response = client.get(
            "/v1/auth/profile",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_profile_no_token(self, client: TestClient):
        """토큰 없이 프로필 조회 실패 테스트"""
        response = client.get("/v1/auth/profile")
        
        assert response.status_code == 403  # HTTPBearer가 403을 반환

    def test_get_profile_invalid_token(self, client: TestClient):
        """잘못된 토큰으로 프로필 조회 실패 테스트"""
        response = client.get(
            "/v1/auth/profile",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401

    def test_update_profile_success(self, client: TestClient, test_user: User, test_user_token: str):
        """프로필 수정 성공 테스트"""
        response = client.put(
            "/v1/auth/profile",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"name": "수정된 이름"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "수정된 이름"

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, async_client: AsyncClient, db_session: AsyncSession, test_user: User):
        """토큰 갱신 성공 테스트"""
        # 먼저 로그인하여 refresh_token 획득
        login_response = await async_client.post(
            "/v1/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # 토큰 갱신 요청
        response = await async_client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "expires_in" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """잘못된 리프레시 토큰 갱신 실패 테스트"""
        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"}
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_success(self, async_client: AsyncClient, test_user: User, test_user_token: str):
        """로그아웃 성공 테스트"""
        response = await async_client.post(
            "/v1/auth/logout",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "성공적으로 로그아웃되었습니다" in data["message"]

    def test_forgot_password_success(self, client: TestClient, test_user: User):
        """비밀번호 재설정 요청 성공 테스트"""
        response = client.post(
            "/v1/auth/forgot-password",
            json={"email": TEST_USER_EMAIL}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "비밀번호 재설정 이메일이 발송되었습니다" in data["message"]

    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """존재하지 않는 이메일 비밀번호 재설정 테스트"""
        response = client.post(
            "/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )
        
        # 보안상 동일한 응답 반환
        assert response.status_code == 200
        data = response.json()
        assert "비밀번호 재설정 이메일이 발송되었습니다" in data["message"]
