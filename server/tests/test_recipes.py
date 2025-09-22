"""
레시피 API 테스트
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe
from tests.conftest import TEST_RECIPE_DATA


class TestRecipes:
    """레시피 API 테스트 클래스"""

    def test_get_recipes_success(self, client: TestClient, test_recipe: Recipe):
        """레시피 목록 조회 성공 테스트"""
        response = client.get("/v1/recipes")
        
        assert response.status_code == 200
        data = response.json()
        
        # 응답 구조 검증
        assert "recipes" in data
        assert "pagination" in data
        assert isinstance(data["recipes"], list)
        
        # 페이지네이션 검증
        pagination = data["pagination"]
        assert "total" in pagination
        assert "page" in pagination
        assert "limit" in pagination
        assert "totalPages" in pagination

    def test_get_recipes_with_pagination(self, client: TestClient, test_recipe: Recipe):
        """페이지네이션 파라미터 테스트"""
        response = client.get("/v1/recipes?page=1&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["limit"] == 5

    def test_get_recipes_with_search(self, client: TestClient, test_recipe: Recipe):
        """검색 파라미터 테스트"""
        response = client.get("/v1/recipes?search=김치")
        
        assert response.status_code == 200
        data = response.json()
        
        # 검색 결과 검증 (테스트 레시피가 포함되어야 함)
        assert len(data["recipes"]) > 0

    def test_get_recipes_with_category(self, client: TestClient, test_recipe: Recipe):
        """카테고리 필터 테스트"""
        response = client.get("/v1/recipes?category=stew")
        
        assert response.status_code == 200
        data = response.json()
        
        # 카테고리 필터 결과 검증
        if data["recipes"]:
            for recipe in data["recipes"]:
                assert recipe["category"] == "stew"

    def test_get_recipes_with_difficulty(self, client: TestClient, test_recipe: Recipe):
        """난이도 필터 테스트"""
        response = client.get("/v1/recipes?difficulty=easy")
        
        assert response.status_code == 200
        data = response.json()
        
        # 난이도 필터 결과 검증
        if data["recipes"]:
            for recipe in data["recipes"]:
                assert recipe["difficulty"] == "easy"

    def test_get_recipes_with_ingredients(self, client: TestClient, test_recipe: Recipe):
        """재료 매칭 테스트"""
        response = client.get('/v1/recipes?ingredients=["김치","돼지고기"]')
        
        assert response.status_code == 200
        data = response.json()
        
        # 매칭율 정보가 포함되어야 함
        assert "matching_rates" in data
        if data["matching_rates"]:
            assert isinstance(data["matching_rates"], dict)

    def test_get_recipes_with_sort(self, client: TestClient, test_recipe: Recipe):
        """정렬 옵션 테스트"""
        response = client.get("/v1/recipes?sort=rating")
        
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data

    def test_get_recipe_detail_success(self, client: TestClient, test_recipe: Recipe):
        """레시피 상세 조회 성공 테스트"""
        response = client.get(f"/v1/recipes/{test_recipe.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # 상세 정보 검증
        assert data["id"] == test_recipe.id
        assert data["name"] == test_recipe.name
        assert data["description"] == test_recipe.description
        assert "ingredients" in data
        assert "cooking_steps" in data
        assert isinstance(data["ingredients"], list)
        assert isinstance(data["cooking_steps"], list)

    def test_get_recipe_detail_not_found(self, client: TestClient):
        """존재하지 않는 레시피 조회 실패 테스트"""
        response = client.get("/v1/recipes/nonexistent_recipe")
        
        assert response.status_code == 404
        data = response.json()
        assert "레시피를 찾을 수 없습니다" in data["detail"]

    def test_get_related_recipes_success(self, client: TestClient, test_recipe: Recipe):
        """관련 레시피 조회 성공 테스트"""
        response = client.get(f"/v1/recipes/{test_recipe.id}/related")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recipes" in data
        assert isinstance(data["recipes"], list)

    def test_get_related_recipes_with_limit(self, client: TestClient, test_recipe: Recipe):
        """관련 레시피 조회 제한 수 테스트"""
        response = client.get(f"/v1/recipes/{test_recipe.id}/related?limit=3")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["recipes"]) <= 3

    def test_get_related_recipes_not_found(self, client: TestClient):
        """존재하지 않는 레시피의 관련 레시피 조회 실패 테스트"""
        response = client.get("/v1/recipes/nonexistent_recipe/related")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_categories_success(self, async_client: AsyncClient, test_recipe: Recipe):
        """카테고리 목록 조회 성공 테스트"""
        response = await async_client.get("/v1/recipes/categories")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        assert isinstance(data["categories"], list)
        
        # 카테고리 구조 검증
        if data["categories"]:
            category = data["categories"][0]
            assert "name" in category
            assert "display_name" in category
            assert "count" in category

    def test_get_popular_recipes_success(self, client: TestClient, test_recipe: Recipe):
        """인기 레시피 조회 성공 테스트"""
        response = client.get("/v1/recipes/popular")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recipes" in data
        assert isinstance(data["recipes"], list)

    def test_get_popular_recipes_with_limit(self, client: TestClient, test_recipe: Recipe):
        """인기 레시피 조회 제한 수 테스트"""
        response = client.get("/v1/recipes/popular?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["recipes"]) <= 5

    def test_get_popular_recipes_with_period(self, client: TestClient, test_recipe: Recipe):
        """인기 레시피 조회 기간 필터 테스트"""
        response = client.get("/v1/recipes/popular?period=month")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recipes" in data

    def test_recipes_pagination_edge_cases(self, client: TestClient):
        """페이지네이션 경계값 테스트"""
        # 페이지 번호 0 (최소값 1로 조정됨)
        response = client.get("/v1/recipes?page=0")
        assert response.status_code == 422
        
        # 제한 수 초과 (최대 50으로 제한)
        response = client.get("/v1/recipes?limit=100")
        assert response.status_code == 422

    def test_recipes_invalid_category(self, client: TestClient):
        """잘못된 카테고리 필터 테스트"""
        response = client.get("/v1/recipes?category=invalid_category")
        
        assert response.status_code == 200
        data = response.json()
        
        # 잘못된 카테고리는 무시되고 전체 결과 반환
        assert "recipes" in data

    def test_recipes_invalid_difficulty(self, client: TestClient):
        """잘못된 난이도 필터 테스트"""
        response = client.get("/v1/recipes?difficulty=invalid_difficulty")
        
        assert response.status_code == 200
        data = response.json()
        
        # 잘못된 난이도는 무시되고 전체 결과 반환
        assert "recipes" in data

    def test_recipes_invalid_sort(self, client: TestClient):
        """잘못된 정렬 옵션 테스트"""
        response = client.get("/v1/recipes?sort=invalid_sort")
        
        assert response.status_code == 200
        data = response.json()
        
        # 잘못된 정렬은 기본값(popularity)으로 처리
        assert "recipes" in data
