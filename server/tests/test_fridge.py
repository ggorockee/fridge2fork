"""
냉장고 API 테스트
"""
import pytest
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.models.recipe import Recipe


class TestFridge:
    """냉장고 API 테스트 클래스"""

    @patch('app.api.v1.fridge.get_redis')
    def test_get_fridge_ingredients_new_session(self, mock_get_redis, client: TestClient):
        """새 세션 냉장고 재료 조회 테스트"""
        # Redis 모킹
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        response = client.get("/v1/fridge/ingredients")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "ingredients" in data
        assert "categories" in data
        assert "session_id" in data
        assert isinstance(data["ingredients"], list)
        assert isinstance(data["categories"], dict)
        assert len(data["ingredients"]) == 0  # 새 세션이므로 빈 배열

    @patch('app.api.v1.fridge.get_redis')
    def test_get_fridge_ingredients_existing_session(self, mock_get_redis, client: TestClient):
        """기존 세션 냉장고 재료 조회 테스트"""
        # 기존 세션 데이터 모킹
        session_data = {
            "ingredients": [
                {
                    "name": "배추",
                    "category": "vegetables",
                    "added_at": "2024-01-01T00:00:00",
                    "expires_at": "2024-01-31T23:59:59"
                }
            ],
            "created_at": "2024-01-01T00:00:00"
        }
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(session_data, default=str)
        mock_get_redis.return_value = mock_redis
        
        response = client.get("/v1/fridge/ingredients?session_id=test_session_id")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["ingredients"]) == 1
        assert data["ingredients"][0]["name"] == "배추"
        assert data["categories"]["vegetables"] == 1

    @patch('app.api.v1.fridge.get_redis')
    def test_add_fridge_ingredients_success(self, mock_get_redis, client: TestClient):
        """냉장고 재료 추가 성공 테스트"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({"ingredients": []})
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        response = client.post(
            "/v1/fridge/ingredients",
            json={
                "session_id": "test_session_id",
                "ingredients": [
                    {
                        "name": "배추",
                        "category": "vegetables",
                        "expires_at": "2024-01-31T23:59:59"
                    },
                    {
                        "name": "돼지고기",
                        "category": "meat"
                    }
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "added_count" in data
        assert "session_id" in data
        assert data["added_count"] == 2

    @patch('app.api.v1.fridge.get_redis')
    def test_add_fridge_ingredients_new_session(self, mock_get_redis, client: TestClient):
        """새 세션에서 재료 추가 테스트"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        response = client.post(
            "/v1/fridge/ingredients",
            json={
                "ingredients": [
                    {
                        "name": "김치",
                        "category": "vegetables"
                    }
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["added_count"] == 1
        assert "session_id" in data

    @patch('app.api.v1.fridge.get_redis')
    def test_remove_fridge_ingredient_success(self, mock_get_redis, client: TestClient):
        """특정 재료 제거 성공 테스트"""
        # 기존 재료가 있는 세션 데이터
        session_data = {
            "ingredients": [
                {
                    "name": "배추",
                    "category": "vegetables",
                    "added_at": "2024-01-01T00:00:00"
                }
            ]
        }
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(session_data)
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        response = client.delete(
            "/v1/fridge/ingredients/배추?session_id=test_session_id"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "removed_count" in data
        assert "배추이(가) 제거되었습니다" in data["message"]
        assert data["removed_count"] == 1

    @patch('app.api.v1.fridge.get_redis')
    def test_remove_fridge_ingredient_not_found(self, mock_get_redis, client: TestClient):
        """존재하지 않는 재료 제거 실패 테스트"""
        session_data = {"ingredients": []}
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(session_data)
        mock_get_redis.return_value = mock_redis
        
        response = client.delete(
            "/v1/fridge/ingredients/존재하지않는재료?session_id=test_session_id"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "재료를 찾을 수 없습니다" in data["detail"]

    @patch('app.api.v1.fridge.get_redis')
    def test_remove_all_fridge_ingredients(self, mock_get_redis, client: TestClient):
        """냉장고 전체 비우기 테스트"""
        session_data = {
            "ingredients": [
                {"name": "배추", "category": "vegetables", "added_at": "2024-01-01T00:00:00"},
                {"name": "돼지고기", "category": "meat", "added_at": "2024-01-01T00:00:00"}
            ]
        }
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(session_data)
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        response = client.request(
            "DELETE",
            "/v1/fridge/ingredients",
            json={"session_id": "test_session_id"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["removed_count"] == 2
        assert "냉장고가 비워졌습니다" in data["message"]

    @patch('app.api.v1.fridge.get_redis')
    def test_remove_selected_fridge_ingredients(self, mock_get_redis, client: TestClient):
        """선택한 재료들 제거 테스트"""
        session_data = {
            "ingredients": [
                {"name": "배추", "category": "vegetables", "added_at": "2024-01-01T00:00:00"},
                {"name": "돼지고기", "category": "meat", "added_at": "2024-01-01T00:00:00"},
                {"name": "두부", "category": "processed", "added_at": "2024-01-01T00:00:00"}
            ]
        }
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(session_data)
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        response = client.request(
            "DELETE",
            "/v1/fridge/ingredients",
            json={
                "session_id": "test_session_id",
                "ingredients": ["배추", "돼지고기"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["removed_count"] == 2
        assert "2개의 재료가 제거되었습니다" in data["message"]

    def test_get_ingredient_categories_success(self, client: TestClient):
        """재료 카테고리 조회 성공 테스트"""
        response = client.get("/v1/fridge/ingredients/categories")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        assert isinstance(data["categories"], dict)
        
        # 예상되는 카테고리들이 있는지 확인
        categories = data["categories"]
        assert "meat" in categories
        assert "seafood" in categories
        assert "vegetables" in categories
        assert "seasonings" in categories
        
        # 각 카테고리에 재료 목록이 있는지 확인
        for category, ingredients in categories.items():
            assert isinstance(ingredients, list)
            assert len(ingredients) > 0

    @patch('app.api.v1.fridge.get_redis')
    @pytest.mark.asyncio
    async def test_cooking_complete_success(self, mock_get_redis, async_client: AsyncClient, test_recipe: Recipe):
        """요리 완료 성공 테스트"""
        # 재료가 있는 세션 데이터
        session_data = {
            "ingredients": [
                {"name": "김치", "category": "vegetables", "added_at": "2024-01-01T00:00:00"},
                {"name": "돼지고기", "category": "meat", "added_at": "2024-01-01T00:00:00"},
                {"name": "두부", "category": "processed", "added_at": "2024-01-01T00:00:00"}
            ]
        }
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(session_data)
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        response = await async_client.post(
            "/v1/fridge/cooking-complete",
            json={
                "session_id": "test_session_id",
                "recipe_id": test_recipe.id,
                "used_ingredients": ["김치", "돼지고기"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "removed_ingredients" in data
        assert len(data["removed_ingredients"]) == 2
        assert "김치" in data["removed_ingredients"]
        assert "돼지고기" in data["removed_ingredients"]

    @patch('app.api.v1.fridge.get_redis')
    @pytest.mark.asyncio
    async def test_cooking_complete_recipe_not_found(self, mock_get_redis, async_client: AsyncClient):
        """존재하지 않는 레시피로 요리 완료 실패 테스트"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({"ingredients": []})
        mock_get_redis.return_value = mock_redis
        
        response = await async_client.post(
            "/v1/fridge/cooking-complete",
            json={
                "session_id": "test_session_id",
                "recipe_id": "nonexistent_recipe",
                "used_ingredients": ["김치"]
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "레시피를 찾을 수 없습니다" in data["detail"]

    @patch('app.api.v1.fridge.get_redis')
    @pytest.mark.asyncio
    async def test_cooking_complete_partial_ingredients(self, mock_get_redis, async_client: AsyncClient, test_recipe: Recipe):
        """일부 재료만 있는 상태에서 요리 완료 테스트"""
        # 일부 재료만 있는 세션 데이터
        session_data = {
            "ingredients": [
                {"name": "김치", "category": "vegetables", "added_at": "2024-01-01T00:00:00"}
            ]
        }
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(session_data)
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        response = await async_client.post(
            "/v1/fridge/cooking-complete",
            json={
                "session_id": "test_session_id",
                "recipe_id": test_recipe.id,
                "used_ingredients": ["김치", "돼지고기"]  # 돼지고기는 냉장고에 없음
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 실제로 냉장고에 있던 재료만 제거됨
        assert len(data["removed_ingredients"]) == 1
        assert "김치" in data["removed_ingredients"]
