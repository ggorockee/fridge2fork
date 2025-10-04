"""
관리자 페이지 추천 설정 표시 테스트
"""

from django.test import TestCase
from recipes.models import RecommendationSettings


class AdminRecommendationSettingsTest(TestCase):
    """관리자 페이지 추천 설정 기본 레코드 생성 테스트"""

    def test_default_settings_exists_after_migration(self):
        """
        마이그레이션 후 기본 설정 레코드가 생성되었는지 확인

        관리자 페이지에서 "0 추천 설정" 문제 해결을 위해
        데이터 마이그레이션으로 기본 레코드를 자동 생성합니다.
        """
        # 정확히 1개의 설정 레코드가 존재해야 함 (Singleton)
        self.assertEqual(RecommendationSettings.objects.count(), 1)
        self.assertTrue(RecommendationSettings.objects.filter(pk=1).exists())

        # 기본값 검증
        settings = RecommendationSettings.objects.get(pk=1)
        self.assertEqual(settings.min_match_rate, 0.3)
        self.assertEqual(settings.default_algorithm, 'jaccard')
        self.assertEqual(settings.default_limit, 20)
        self.assertTrue(settings.exclude_seasonings_default)

    def test_get_settings_class_method(self):
        """
        get_settings() 클래스 메서드가 정상 작동하는지 확인
        """
        settings = RecommendationSettings.get_settings()

        self.assertIsNotNone(settings)
        self.assertEqual(settings.pk, 1)
        self.assertEqual(settings.min_match_rate, 0.3)

    def test_singleton_pattern_enforced(self):
        """
        Singleton 패턴이 적용되어 있는지 확인
        """
        # 기존 레코드 존재
        self.assertEqual(RecommendationSettings.objects.count(), 1)

        # 새로운 레코드 생성 시도
        new_settings = RecommendationSettings(
            min_match_rate=0.5,
            default_algorithm='cosine',
            default_limit=30
        )
        new_settings.save()

        # 여전히 1개만 존재 (pk=1로 덮어씀)
        self.assertEqual(RecommendationSettings.objects.count(), 1)

        # 값이 업데이트됨
        settings = RecommendationSettings.objects.get(pk=1)
        self.assertEqual(settings.min_match_rate, 0.5)
        self.assertEqual(settings.default_algorithm, 'cosine')
