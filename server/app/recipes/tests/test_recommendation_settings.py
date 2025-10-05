"""
추천 설정 모델 및 API 테스트
"""

from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from recipes.models import RecommendationSettings, Recipe, Ingredient, NormalizedIngredient
from .base import CategoryTestCase


class RecommendationSettingsModelTest(TestCase):
    """추천 설정 모델 테스트"""

    def setUp(self):
        """각 테스트 전 RecommendationSettings 초기화"""
        RecommendationSettings.objects.filter(pk=1).delete()

    def test_create_default_settings(self):
        """
        기본 설정 생성 테스트
        """
        settings = RecommendationSettings.objects.create(
            min_match_rate=0.3,
            default_algorithm='jaccard',
            default_limit=20,
            exclude_seasonings_default=True
        )

        self.assertEqual(settings.min_match_rate, 0.3)
        self.assertEqual(settings.default_algorithm, 'jaccard')
        self.assertEqual(settings.default_limit, 20)
        self.assertTrue(settings.exclude_seasonings_default)

    def test_min_match_rate_validation_min(self):
        """
        min_match_rate 최솟값 검증 (0.0 이상)
        """
        settings = RecommendationSettings(min_match_rate=-0.1)

        with self.assertRaises(ValidationError):
            settings.full_clean()

    def test_min_match_rate_validation_max(self):
        """
        min_match_rate 최댓값 검증 (1.0 이하)
        """
        settings = RecommendationSettings(min_match_rate=1.1)

        with self.assertRaises(ValidationError):
            settings.full_clean()

    def test_min_match_rate_valid_range(self):
        """
        min_match_rate 유효 범위 (0.0-1.0)
        """
        for value in [0.0, 0.3, 0.5, 0.7, 1.0]:
            settings = RecommendationSettings(min_match_rate=value)
            settings.full_clean()  # ValidationError 발생하지 않아야 함

    def test_default_limit_validation_min(self):
        """
        default_limit 최솟값 검증 (1 이상)
        """
        settings = RecommendationSettings(default_limit=0)

        with self.assertRaises(ValidationError):
            settings.full_clean()

    def test_default_limit_validation_max(self):
        """
        default_limit 최댓값 검증 (100 이하)
        """
        settings = RecommendationSettings(default_limit=101)

        with self.assertRaises(ValidationError):
            settings.full_clean()


class RecommendationSettingsAPITest(CategoryTestCase):
    """추천 설정 API 통합 테스트"""

    def setUp(self):
        """테스트용 데이터 생성"""
        self.client = Client()
        self.url = "/fridge2fork/v1/recipes/recommendations"

        # RecommendationSettings 초기화 (싱글톤 패턴으로 id=1 고정)
        RecommendationSettings.objects.filter(pk=1).delete()

        # 레시피 생성
        self.recipe1 = Recipe.objects.create(
            recipe_sno="RCP800",
            title="김치찌개",
            name="김치찌개",
            servings="4.0",
            difficulty="아무나",
            cooking_time="30.0"
        )
        self.recipe2 = Recipe.objects.create(
            recipe_sno="RCP801",
            title="제육볶음",
            name="제육볶음",
            servings="2.0",
            difficulty="초보환영",
            cooking_time="25.0"
        )

        # 정규화 재료 생성
        self.pork = NormalizedIngredient.objects.create(
            name="돼지고기",
            category=self.meat_category
        )
        self.cabbage = NormalizedIngredient.objects.create(
            name="배추",
            category=self.vegetable_category
        )
        self.kimchi = NormalizedIngredient.objects.create(
            name="김치",
            category=self.vegetable_category
        )

        # 김치찌개: 돼지고기, 배추, 김치
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="돼지고기",
            normalized_name="돼지고기",
            normalized_ingredient=self.pork,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="배추",
            normalized_name="배추",
            normalized_ingredient=self.cabbage,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="김치",
            normalized_name="김치",
            normalized_ingredient=self.kimchi,
            category=self.essential_category
        )

        # 제육볶음: 돼지고기, 배추
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name="돼지고기",
            normalized_name="돼지고기",
            normalized_ingredient=self.pork,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name="배추",
            normalized_name="배추",
            normalized_ingredient=self.cabbage,
            category=self.essential_category
        )

    def test_use_admin_settings_when_no_parameter(self):
        """
        TC-1: 관리자 설정값 사용

        API 파라미터 없을 때 관리자 설정값 사용
        """
        # 관리자 설정: min_match_rate=0.8
        RecommendationSettings.objects.create(
            id=1,
            min_match_rate=0.8,
            default_algorithm='jaccard',
            default_limit=20
        )

        # 사용자 재료: 돼지고기 (김치찌개 2/3=0.67, 제육볶음 1/2=0.5)
        response = self.client.get(self.url, {
            'ingredients': '돼지고기'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # min_match_rate=0.8이므로 둘 다 필터링됨
        self.assertEqual(len(data['recipes']), 0)

    def test_api_parameter_overrides_admin_settings(self):
        """
        TC-2: API 파라미터 우선

        API 파라미터가 관리자 설정보다 우선
        """
        # 관리자 설정: min_match_rate=0.8
        RecommendationSettings.objects.create(
            id=1,
            min_match_rate=0.8,
            default_algorithm='jaccard',
            default_limit=20
        )

        # API 파라미터: min_match_rate=0.5
        response = self.client.get(self.url, {
            'ingredients': '돼지고기',
            'min_match_rate': 0.5
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # min_match_rate=0.5이므로 제육볶음 포함
        self.assertGreater(len(data['recipes']), 0)

    def test_fallback_to_default_when_no_settings(self):
        """
        TC-3: 기본값 폴백

        DB에 설정 없을 때 하드코딩 기본값 사용
        """
        # DB에 설정 없음 (get_or_create가 기본값으로 생성)
        response = self.client.get(self.url, {
            'ingredients': '돼지고기'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 기본값 min_match_rate=0.3 사용
        self.assertGreater(len(data['recipes']), 0)

    def test_admin_algorithm_setting(self):
        """
        TC-4: 기본 알고리즘 설정

        관리자가 기본 알고리즘 설정 가능
        """
        # 관리자 설정: default_algorithm='cosine'
        RecommendationSettings.objects.create(
            id=1,
            min_match_rate=0.3,
            default_algorithm='cosine',
            default_limit=20
        )

        response = self.client.get(self.url, {
            'ingredients': '돼지고기,배추'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 응답에 cosine 알고리즘 사용됨
        self.assertEqual(data['algorithm'], 'cosine')

    def test_admin_limit_setting(self):
        """
        TC-5: 기본 limit 설정

        관리자가 기본 추천 개수 설정 가능
        """
        # 관리자 설정: default_limit=5
        RecommendationSettings.objects.create(
            id=1,
            min_match_rate=0.3,
            default_algorithm='jaccard',
            default_limit=5
        )

        # 많은 레시피 추가 (총 10개 이상)
        for i in range(10):
            recipe = Recipe.objects.create(
                recipe_sno=f"RCP90{i}",
                title=f"레시피{i}",
                name=f"레시피{i}",
                servings="2.0",
                difficulty="아무나",
                cooking_time="20.0"
            )
            Ingredient.objects.create(
                recipe=recipe,
                original_name="돼지고기",
                normalized_name="돼지고기",
                normalized_ingredient=self.pork,
                category=self.essential_category
            )

        # limit 파라미터 없이 요청
        response = self.client.get(self.url, {
            'ingredients': '돼지고기'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 최대 5개만 반환 (default_limit=5)
        self.assertLessEqual(len(data['recipes']), 5)

    def test_settings_persistence(self):
        """
        설정 지속성 테스트

        설정 변경 후 다음 요청에 반영
        """
        # 초기 설정
        settings = RecommendationSettings.objects.create(
            id=1,
            min_match_rate=0.3
        )

        # 첫 번째 요청
        response1 = self.client.get(self.url, {
            'ingredients': '돼지고기'
        })
        count1 = len(response1.json()['recipes'])

        # 설정 변경
        settings.min_match_rate = 0.9
        settings.save()

        # 두 번째 요청
        response2 = self.client.get(self.url, {
            'ingredients': '돼지고기'
        })
        count2 = len(response2.json()['recipes'])

        # min_match_rate 증가로 결과 감소
        self.assertLessEqual(count2, count1)
