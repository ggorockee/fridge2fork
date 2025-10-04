"""
알고리즘 설명 표시 테스트
"""

from django.test import TestCase
from recipes.models import RecommendationSettings
from recipes.admin import RecommendationSettingsAdmin


class AlgorithmExplanationTest(TestCase):
    """관리자 페이지에서 알고리즘 설명이 올바르게 표시되는지 테스트"""

    def setUp(self):
        """테스트용 설정 생성"""
        self.admin = RecommendationSettingsAdmin(RecommendationSettings, None)

    def test_jaccard_algorithm_choice_description(self):
        """
        Jaccard 알고리즘 선택지에 한글 설명이 포함되어 있는지 확인
        """
        choices = RecommendationSettings.ALGORITHM_CHOICES

        # Jaccard 선택지 확인
        jaccard_choice = next((c for c in choices if c[0] == 'jaccard'), None)
        self.assertIsNotNone(jaccard_choice)

        # 한글 설명 포함 확인
        self.assertIn('자카드', jaccard_choice[1])
        self.assertIn('교집합', jaccard_choice[1])
        self.assertIn('권장', jaccard_choice[1])

    def test_cosine_algorithm_choice_description(self):
        """
        Cosine 알고리즘 선택지에 한글 설명이 포함되어 있는지 확인
        """
        choices = RecommendationSettings.ALGORITHM_CHOICES

        # Cosine 선택지 확인
        cosine_choice = next((c for c in choices if c[0] == 'cosine'), None)
        self.assertIsNotNone(cosine_choice)

        # 한글 설명 포함 확인
        self.assertIn('코사인', cosine_choice[1])
        self.assertIn('벡터', cosine_choice[1])
        self.assertIn('민감', cosine_choice[1])

    def test_get_algorithm_explanation_jaccard(self):
        """
        Jaccard 알고리즘 선택 시 두 알고리즘 설명이 모두 표시되는지 확인
        """
        settings = RecommendationSettings(
            default_algorithm='jaccard',
            min_match_rate=0.3
        )

        explanation = self.admin.get_algorithm_explanation(settings)

        # Jaccard 알고리즘 설명 확인
        self.assertIn('Jaccard', explanation)
        self.assertIn('자카드', explanation)
        self.assertIn('교집합', explanation)
        self.assertIn('합집합', explanation)
        self.assertIn('0.4', explanation)  # Jaccard 예시 계산 결과
        self.assertIn('직관적', explanation)

        # Cosine 알고리즘 설명도 함께 표시되는지 확인
        self.assertIn('Cosine', explanation)
        self.assertIn('코사인', explanation)
        self.assertIn('벡터', explanation)
        self.assertIn('각도', explanation)
        self.assertIn('0.577', explanation)  # Cosine 예시 계산 결과

        # 공통 요소 확인
        self.assertIn('예시', explanation)
        self.assertIn('돼지고기', explanation)
        self.assertIn('장점', explanation)
        self.assertIn('비교 요약', explanation)  # 비교 표 확인

    def test_get_algorithm_explanation_cosine(self):
        """
        Cosine 알고리즘 선택 시 두 알고리즘 설명이 모두 표시되는지 확인
        """
        settings = RecommendationSettings(
            default_algorithm='cosine',
            min_match_rate=0.3
        )

        explanation = self.admin.get_algorithm_explanation(settings)

        # Cosine 알고리즘 설명 확인
        self.assertIn('Cosine', explanation)
        self.assertIn('코사인', explanation)
        self.assertIn('벡터', explanation)
        self.assertIn('각도', explanation)
        self.assertIn('0.577', explanation)  # Cosine 예시 계산 결과
        self.assertIn('민감', explanation)

        # Jaccard 알고리즘 설명도 함께 표시되는지 확인
        self.assertIn('Jaccard', explanation)
        self.assertIn('자카드', explanation)
        self.assertIn('교집합', explanation)
        self.assertIn('합집합', explanation)
        self.assertIn('0.4', explanation)  # Jaccard 예시 계산 결과

        # 공통 요소 확인
        self.assertIn('예시', explanation)
        self.assertIn('돼지고기', explanation)
        self.assertIn('장점', explanation)
        self.assertIn('비교 요약', explanation)  # 비교 표 확인

    def test_algorithm_explanation_html_styling(self):
        """
        알고리즘 설명이 적절한 HTML 스타일링을 포함하는지 확인
        """
        settings = RecommendationSettings(default_algorithm='jaccard')
        explanation = self.admin.get_algorithm_explanation(settings)

        # 스타일 요소 확인
        self.assertIn('<div', explanation)
        self.assertIn('style=', explanation)
        self.assertIn('<h3', explanation)
        self.assertIn('<p>', explanation)
        self.assertIn('<ul', explanation)
        self.assertIn('<li>', explanation)

    def test_min_match_rate_help_text_improvement(self):
        """
        최소 매칭률 필드의 help_text가 개선되었는지 확인
        """
        field = RecommendationSettings._meta.get_field('min_match_rate')

        # 개선된 설명 포함 확인
        self.assertIn('낮을수록', field.help_text)
        self.assertIn('다양한', field.help_text)
        self.assertIn('높을수록', field.help_text)
        self.assertIn('엄격', field.help_text)

    def test_default_algorithm_help_text_improvement(self):
        """
        기본 알고리즘 필드의 help_text가 개선되었는지 확인
        """
        field = RecommendationSettings._meta.get_field('default_algorithm')

        # 개선된 설명 포함 확인
        self.assertIn('유사도', field.help_text)
        self.assertIn('사용자', field.help_text)

    def test_admin_readonly_fields_include_explanation(self):
        """
        Admin의 readonly_fields에 설명 필드가 포함되어 있는지 확인
        """
        self.assertIn('get_algorithm_explanation', self.admin.readonly_fields)

    def test_admin_fieldsets_include_explanation(self):
        """
        Admin의 fieldsets에 설명 필드가 올바른 위치에 있는지 확인
        """
        # 첫 번째 fieldset (알고리즘 설정)
        algorithm_fieldset = self.admin.fieldsets[0]

        # 필드 순서 확인: default_algorithm -> get_algorithm_explanation -> min_match_rate
        fields = algorithm_fieldset[1]['fields']
        self.assertEqual(fields[0], 'default_algorithm')
        self.assertEqual(fields[1], 'get_algorithm_explanation')
        self.assertEqual(fields[2], 'min_match_rate')

    def test_admin_limit_display(self):
        """
        Admin의 get_limit_display 메서드가 올바르게 동작하는지 확인
        """
        settings = RecommendationSettings(default_limit=20)
        limit_display = self.admin.get_limit_display(settings)

        # HTML 포맷 확인
        self.assertIn('20', limit_display)
        self.assertIn('개', limit_display)
        self.assertIn('📊', limit_display)

    def test_admin_list_display_includes_limit(self):
        """
        Admin의 list_display에 기본 추천 개수가 포함되어 있는지 확인
        """
        self.assertIn('get_limit_display', self.admin.list_display)

    def test_admin_default_limit_fieldset(self):
        """
        Admin의 fieldsets에 default_limit이 올바른 위치에 있는지 확인
        """
        # 두 번째 fieldset (기본 추천 옵션)
        options_fieldset = self.admin.fieldsets[1]

        # 제목 확인
        self.assertIn('기본', options_fieldset[0])

        # 필드 확인
        fields = options_fieldset[1]['fields']
        self.assertIn('default_limit', fields)
        self.assertIn('exclude_seasonings_default', fields)
