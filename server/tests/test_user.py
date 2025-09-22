"""
사용자 API 테스트
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.recipe import Recipe, UserFavorite, CookingHistory
from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD


class TestUser:
    """사용자 API 테스트 클래스"""

    def test_get_favorites_empty(self, client: TestClient, test_user: User, test_user_token: str):
        """빈 즐겨찾기 목록 조회 테스트"""
        response = client.get(
            "/v1/user/favorites",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recipes" in data
        assert "pagination" in data
        assert len(data["recipes"]) == 0
        assert data["pagination"]["total"] == 0

    def test_get_favorites_unauthorized(self, client: TestClient):
        """인증 없이 즐겨찾기 조회 실패 테스트"""
        response = client.get("/v1/user/favorites")
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_add_favorite_success(self, async_client: AsyncClient, db_session: AsyncSession, test_user: User, test_recipe: Recipe, test_user_token: str):
        """즐겨찾기 추가 성공 테스트"""
        response = await async_client.post(
            f"/v1/user/favorites/{test_recipe.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "즐겨찾기에 추가되었습니다" in data["message"]
        
        # 데이터베이스에 실제로 추가되었는지 확인
        from sqlalchemy import select
        result = await db_session.execute(
            select(UserFavorite).where(
                UserFavorite.user_id == test_user.id,
                UserFavorite.recipe_id == test_recipe.id
            )
        )
        favorite = result.scalar_one_or_none()
        assert favorite is not None

    @pytest.mark.asyncio
    async def test_add_favorite_recipe_not_found(self, async_client: AsyncClient, test_user: User, test_user_token: str):
        """존재하지 않는 레시피 즐겨찾기 추가 실패 테스트"""
        response = await async_client.post(
            "/v1/user/favorites/nonexistent_recipe",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "레시피를 찾을 수 없습니다" in data["detail"]

    @pytest.mark.asyncio
    async def test_add_favorite_duplicate(self, async_client: AsyncClient, db_session: AsyncSession, test_user: User, test_recipe: Recipe, test_user_token: str):
        """중복 즐겨찾기 추가 실패 테스트"""
        # 먼저 즐겨찾기 추가
        favorite = UserFavorite(user_id=test_user.id, recipe_id=test_recipe.id)
        db_session.add(favorite)
        await db_session.commit()
        
        # 동일한 레시피 다시 추가 시도
        response = await async_client.post(
            f"/v1/user/favorites/{test_recipe.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "이미 즐겨찾기에 추가된 레시피입니다" in data["detail"]

    @pytest.mark.asyncio
    async def test_remove_favorite_success(self, async_client: AsyncClient, db_session: AsyncSession, test_user: User, test_recipe: Recipe, test_user_token: str):
        """즐겨찾기 제거 성공 테스트"""
        # 먼저 즐겨찾기 추가
        favorite = UserFavorite(user_id=test_user.id, recipe_id=test_recipe.id)
        db_session.add(favorite)
        await db_session.commit()
        
        # 즐겨찾기 제거
        response = await async_client.delete(
            f"/v1/user/favorites/{test_recipe.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "즐겨찾기에서 제거되었습니다" in data["message"]

    @pytest.mark.asyncio
    async def test_remove_favorite_not_found(self, async_client: AsyncClient, test_user: User, test_recipe: Recipe, test_user_token: str):
        """존재하지 않는 즐겨찾기 제거 실패 테스트"""
        response = await async_client.delete(
            f"/v1/user/favorites/{test_recipe.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "즐겨찾기에서 레시피를 찾을 수 없습니다" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_favorites_with_data(self, async_client: AsyncClient, db_session: AsyncSession, test_user: User, test_recipe: Recipe, test_user_token: str):
        """즐겨찾기가 있는 상태에서 목록 조회 테스트"""
        # 즐겨찾기 추가
        favorite = UserFavorite(user_id=test_user.id, recipe_id=test_recipe.id)
        db_session.add(favorite)
        await db_session.commit()
        
        response = await async_client.get(
            "/v1/user/favorites",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["recipes"]) == 1
        assert data["recipes"][0]["id"] == test_recipe.id
        assert data["pagination"]["total"] == 1

    def test_get_cooking_history_empty(self, client: TestClient, test_user: User, test_user_token: str):
        """빈 요리 히스토리 조회 테스트"""
        response = client.get(
            "/v1/user/cooking-history",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data
        assert "pagination" in data
        assert "statistics" in data
        assert len(data["history"]) == 0
        assert data["statistics"]["total_cooking"] == 0

    @pytest.mark.asyncio
    async def test_get_cooking_history_with_data(self, async_client: AsyncClient, db_session: AsyncSession, test_user: User, test_recipe: Recipe, test_user_token: str):
        """요리 히스토리가 있는 상태에서 조회 테스트"""
        # 요리 히스토리 추가
        history = CookingHistory(
            user_id=test_user.id,
            recipe_id=test_recipe.id,
            used_ingredients=["김치", "돼지고기"]
        )
        db_session.add(history)
        await db_session.commit()
        
        response = await async_client.get(
            "/v1/user/cooking-history",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["history"]) == 1
        assert data["history"][0]["recipe"]["id"] == test_recipe.id
        assert data["history"][0]["used_ingredients"] == ["김치", "돼지고기"]
        assert data["statistics"]["total_cooking"] == 1

    def test_get_cooking_history_with_period(self, client: TestClient, test_user: User, test_user_token: str):
        """기간 필터로 요리 히스토리 조회 테스트"""
        response = client.get(
            "/v1/user/cooking-history?period=week",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data
        assert "pagination" in data
        assert "statistics" in data

    def test_get_recommendations_empty(self, client: TestClient, test_user: User, test_user_token: str):
        """빈 상태에서 맞춤 추천 조회 테스트"""
        response = client.get(
            "/v1/user/recommendations",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recipes" in data
        assert "recommendation_reason" in data
        assert isinstance(data["recipes"], list)
        assert isinstance(data["recommendation_reason"], list)

    def test_get_recommendations_with_type(self, client: TestClient, test_user: User, test_user_token: str):
        """추천 타입별 맞춤 추천 조회 테스트"""
        # favorite_based
        response = client.get(
            "/v1/user/recommendations?type=favorite_based",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        
        # history_based
        response = client.get(
            "/v1/user/recommendations?type=history_based",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        
        # mixed
        response = client.get(
            "/v1/user/recommendations?type=mixed",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200

    def test_get_recommendations_with_limit(self, client: TestClient, test_user: User, test_user_token: str):
        """제한 수로 맞춤 추천 조회 테스트"""
        response = client.get(
            "/v1/user/recommendations?limit=5",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["recipes"]) <= 5

    @pytest.mark.asyncio
    async def test_submit_feedback_member(self, async_client: AsyncClient, test_user: User, test_user_token: str):
        """회원 피드백 제출 테스트"""
        response = await async_client.post(
            "/v1/user/feedback",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "type": "feature",
                "title": "새로운 기능 제안",
                "content": "레시피 평점 기능을 추가해주세요",
                "rating": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "feedback_id" in data
        assert "성공적으로 제출되었습니다" in data["message"]

    @pytest.mark.asyncio
    async def test_submit_feedback_anonymous(self, async_client: AsyncClient):
        """비회원 피드백 제출 테스트"""
        response = await async_client.post(
            "/v1/user/feedback",
            json={
                "type": "bug",
                "title": "버그 신고",
                "content": "검색이 안됩니다",
                "contact_email": "user@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "feedback_id" in data

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_type(self, async_client: AsyncClient):
        """잘못된 타입으로 피드백 제출 테스트"""
        response = await async_client.post(
            "/v1/user/feedback",
            json={
                "type": "invalid_type",
                "title": "테스트",
                "content": "테스트 내용"
            }
        )
        
        # 현재 구현에서는 타입 검증이 없으므로 성공
        # 실제로는 enum 등으로 제한할 수 있음
        assert response.status_code == 200

    def test_user_api_pagination(self, client: TestClient, test_user: User, test_user_token: str):
        """사용자 API 페이지네이션 테스트"""
        # 즐겨찾기 페이지네이션
        response = client.get(
            "/v1/user/favorites?page=1&limit=5",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 5
        
        # 요리 히스토리 페이지네이션
        response = client.get(
            "/v1/user/cooking-history?page=1&limit=5",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 5

    def test_user_api_unauthorized_access(self, client: TestClient):
        """인증되지 않은 사용자의 API 접근 테스트"""
        endpoints = [
            "/v1/user/favorites",
            "/v1/user/cooking-history",
            "/v1/user/recommendations"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 403

        # POST/DELETE 엔드포인트도 테스트
        response = client.post("/v1/user/favorites/test_recipe")
        assert response.status_code == 403
        
        response = client.delete("/v1/user/favorites/test_recipe")
        assert response.status_code == 403
