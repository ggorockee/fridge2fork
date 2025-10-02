"""
재료 정규화 자동 분석 Management Command

모든 Ingredient의 original_name을 분석하여 정규화 제안 생성
"""

import json
import re
from collections import defaultdict
from django.core.management.base import BaseCommand
from recipes.models import Recipe, Ingredient


class Command(BaseCommand):
    """재료 정규화 분석 커맨드"""

    help = '재료 데이터를 분석하여 정규화 제안을 생성합니다'

    # 제거할 패턴 (수량, 용도, 수식어)
    QUANTITY_PATTERNS = [
        # 숫자 + 단위 패턴 (예: 300g, 1/2개, 2큰술)
        r'\d+\.?\d*\s*(g|kg|ml|L|개|컵|큰술|작은술|T|t|포기|줌|알|쪽|장|봉지|팩|캔|대|뿌리|송이|통|조각|덩어리)',
        r'\d+/\d+\s*(포기|개|대|뿌리|송이|통|조각)',
        # 수량 표현 (예: 약간, 적당량)
        r'약간|조금|적당량|적당히|넉넉히|듬뿍',
        # 특수 문자 (예: \x07)
        r'\x07+',
    ]

    PREFIX_PATTERNS = [
        r'^(수육용|구이용|찜용|볶음용|국거리용|조림용)\s+',
        r'^(신선한|국내산|수입산|냉동|냉장)\s+',
    ]

    SUFFIX_PATTERNS = [
        r'\s+(앞다리살|뒷다리살|목살|삼겹살|등심|안심|갈비|사태|양지|채끝)',
        r'\s+(앞다리|뒷다리)',
        r'\s+(속|겉|대|뿌리|잎|줄기)',
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('재료 데이터 분석 시작...'))

        # 유사 재료 그룹화
        grouped_data = self.group_similar_ingredients()

        # 범용 조미료 탐지
        common_seasonings = self.detect_common_seasonings(threshold=0.8)

        # 정규화 제안 생성
        suggestions = {
            'ingredients': grouped_data,
            'common_seasonings': [s['base_name'] for s in common_seasonings]
        }

        # JSON 파일로 저장
        with open('suggestions.json', 'w', encoding='utf-8') as f:
            json.dump(suggestions, f, ensure_ascii=False, indent=2)

        with open('common_seasonings.json', 'w', encoding='utf-8') as f:
            json.dump(suggestions['common_seasonings'], f, ensure_ascii=False, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n분석 완료!'
                f'\n- 정규화 재료: {len(grouped_data)}개'
                f'\n- 범용 조미료: {len(common_seasonings)}개'
                f'\n- suggestions.json 파일 생성'
                f'\n- common_seasonings.json 파일 생성'
            )
        )

    def extract_base_name(self, original_name):
        """
        원본 재료명에서 기본 재료명 추출

        수량, 용도, 수식어 등을 제거하여 기본 재료명만 추출
        """
        name = original_name

        # 특수 문자 제거 (먼저 처리)
        name = re.sub(r'\x07+', '', name)

        # 수량 표현 제거 (먼저 처리)
        name = re.sub(r'약간|조금|적당량|적당히|넉넉히|듬뿍', '', name, flags=re.IGNORECASE)

        # 숫자 + 단위 패턴 제거 (예: 300g, 1/2개, 2큰술, 1T)
        # 더 포괄적인 패턴으로 수정
        name = re.sub(r'\d+\.?\d*\s*(g|kg|ml|L|cc)', '', name)  # 무게/부피
        name = re.sub(r'\d+/\d+\s*(개|대|포기|뿌리|송이|통|조각|컵|큰술|작은술|T|t)', '', name)  # 분수형
        name = re.sub(r'\d+\.?\d*\s*(개|대|포기|뿌리|송이|통|조각|컵|큰술|작은술|T|t|줌|알|쪽|장|봉지|팩|캔|덩어리)', '', name)  # 일반 숫자형

        # 접두사 패턴 제거 (용도, 수식어)
        for pattern in self.PREFIX_PATTERNS:
            name = re.sub(pattern, '', name)

        # 접미사 패턴 제거 (부위)
        for pattern in self.SUFFIX_PATTERNS:
            name = re.sub(pattern, '', name)

        # 공백 정리
        name = ' '.join(name.split())

        return name.strip()

    def group_similar_ingredients(self):
        """유사 재료 그룹화"""
        ingredients = Ingredient.objects.all()

        grouped = defaultdict(lambda: {
            'base_name': '',
            'variations': [],
            'count': 0,
            'category': None
        })

        for ingredient in ingredients:
            base_name = self.extract_base_name(ingredient.original_name)

            if not base_name:
                continue

            grouped[base_name]['base_name'] = base_name
            grouped[base_name]['variations'].append(ingredient.original_name)
            grouped[base_name]['count'] += 1

            # 카테고리 추론 (가장 많이 사용된 카테고리)
            if not grouped[base_name]['category']:
                grouped[base_name]['category'] = ingredient.category

        # 리스트로 변환 및 빈도순 정렬
        result = sorted(
            [v for v in grouped.values() if v['count'] > 0],
            key=lambda x: x['count'],
            reverse=True
        )

        return result

    def detect_common_seasonings(self, threshold=0.8):
        """
        범용 조미료 탐지

        전체 레시피의 threshold 이상에서 사용되는 재료를 범용 조미료로 판단
        """
        total_recipes = Recipe.objects.count()

        if total_recipes == 0:
            return []

        ingredients = Ingredient.objects.all()
        ingredient_counts = defaultdict(int)

        for ingredient in ingredients:
            base_name = self.extract_base_name(ingredient.original_name)
            if base_name:
                ingredient_counts[base_name] += 1

        common_seasonings = []

        for base_name, count in ingredient_counts.items():
            frequency = count / total_recipes
            if frequency >= threshold:
                common_seasonings.append({
                    'base_name': base_name,
                    'count': count,
                    'frequency': round(frequency * 100, 2)
                })

        return sorted(common_seasonings, key=lambda x: x['frequency'], reverse=True)

    def generate_suggestions(self):
        """정규화 제안 생성 (테스트용 헬퍼 메서드)"""
        grouped_data = self.group_similar_ingredients()
        common_seasonings = self.detect_common_seasonings(threshold=0.8)

        return {
            'ingredients': grouped_data,
            'common_seasonings': [s['base_name'] for s in common_seasonings]
        }
