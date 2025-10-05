"""
재료 정규화 데이터 품질 검증 Management Command

정규화되지 않은 재료, 고아 NormalizedIngredient, 중복 탐지 등
"""

import json
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from recipes.models import Recipe, Ingredient, NormalizedIngredient


class Command(BaseCommand):
    """재료 정규화 데이터 품질 검증 커맨드"""

    help = '재료 정규화 데이터의 품질을 검증하고 리포트를 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='validation_report.json',
            help='검증 리포트 출력 파일 경로'
        )

    def handle(self, *args, **options):
        output_file = options['output']

        self.stdout.write(self.style.SUCCESS('데이터 품질 검증 시작...\n'))

        # 검증 실행
        report = {
            'summary': {},
            'warnings': [],
            'errors': [],
            'suggestions': []
        }

        # 1. 정규화되지 않은 Ingredient 목록
        unnormalized = self.check_unnormalized_ingredients()
        report['unnormalized_ingredients'] = unnormalized
        self.stdout.write(f'정규화되지 않은 재료: {len(unnormalized)}개')

        # 2. 고아 NormalizedIngredient (연결된 Ingredient가 없는 경우)
        orphans = self.check_orphan_normalized_ingredients()
        report['orphan_normalized_ingredients'] = orphans
        self.stdout.write(f'고아 정규화 재료: {len(orphans)}개')

        # 3. 유사한 이름의 NormalizedIngredient 중복 탐지
        duplicates = self.check_duplicate_normalized_ingredients()
        report['duplicate_normalized_ingredients'] = duplicates
        self.stdout.write(f'중복 의심 정규화 재료: {len(duplicates)}개')

        # 4. 범용 조미료로 표시되지 않았지만 높은 빈도로 등장하는 재료
        frequent_ingredients = self.check_frequent_ingredients()
        report['frequent_ingredients'] = frequent_ingredients
        self.stdout.write(f'범용 조미료 의심 재료: {len(frequent_ingredients)}개')

        # 5. 통계 생성
        stats = self.generate_statistics()
        report['statistics'] = stats

        # 경고 및 오류 수준 구분
        self.classify_issues(report)

        # 요약
        report['summary'] = {
            'total_recipes': stats['total_recipes'],
            'total_ingredients': stats['total_ingredients'],
            'total_normalized_ingredients': stats['total_normalized_ingredients'],
            'normalization_rate': f"{stats['normalization_rate']:.2f}%",
            'warnings': len(report['warnings']),
            'errors': len(report['errors']),
            'suggestions': len(report['suggestions'])
        }

        # JSON 파일로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n검증 완료! 리포트: {output_file}\n'
                f'경고: {len(report["warnings"])}개, '
                f'오류: {len(report["errors"])}개, '
                f'제안: {len(report["suggestions"])}개'
            )
        )

    def check_unnormalized_ingredients(self):
        """정규화되지 않은 Ingredient 목록"""
        unnormalized = Ingredient.objects.filter(
            normalized_ingredient__isnull=True
        ).values('id', 'original_name', 'recipe__name')

        return list(unnormalized)

    def check_orphan_normalized_ingredients(self):
        """고아 NormalizedIngredient (연결된 Ingredient가 없는 경우)"""
        orphans = (
            NormalizedIngredient.objects
            .annotate(ingredient_count=Count('ingredients'))
            .filter(ingredient_count=0)
            .values('id', 'name', 'category')
        )

        return list(orphans)

    def check_duplicate_normalized_ingredients(self):
        """유사한 이름의 NormalizedIngredient 중복 탐지"""
        duplicates = []
        normalized_ingredients = NormalizedIngredient.objects.all()

        # 간단한 유사성 체크 (포함 관계)
        checked = set()
        for ingredient in normalized_ingredients:
            if ingredient.id in checked:
                continue

            similar = []
            for other in normalized_ingredients:
                if ingredient.id == other.id:
                    continue
                if other.id in checked:
                    continue

                # 한쪽이 다른쪽을 포함하는 경우
                if (ingredient.name in other.name or
                    other.name in ingredient.name):
                    similar.append({
                        'id': other.id,
                        'name': other.name
                    })
                    checked.add(other.id)

            if similar:
                duplicates.append({
                    'base': {
                        'id': ingredient.id,
                        'name': ingredient.name
                    },
                    'similar': similar
                })
                checked.add(ingredient.id)

        return duplicates

    def check_frequent_ingredients(self, threshold=0.5):
        """
        범용 조미료로 표시되지 않았지만 높은 빈도로 등장하는 재료

        Args:
            threshold: 전체 레시피 대비 빈도 임계값 (기본: 50%)
        """
        total_recipes = Recipe.objects.count()
        if total_recipes == 0:
            return []

        # 각 정규화 재료의 등장 빈도 계산
        frequent = []
        normalized_ingredients = (
            NormalizedIngredient.objects
            .filter(is_common_seasoning=False)
            .annotate(
                recipe_count=Count('ingredients__recipe', distinct=True)
            )
        )

        for ingredient in normalized_ingredients:
            frequency = ingredient.recipe_count / total_recipes

            if frequency >= threshold:
                frequent.append({
                    'id': ingredient.id,
                    'name': ingredient.name,
                    'recipe_count': ingredient.recipe_count,
                    'frequency': round(frequency * 100, 2),
                    'category': ingredient.category
                })

        # 빈도 순으로 정렬
        frequent.sort(key=lambda x: x['frequency'], reverse=True)

        return frequent

    def generate_statistics(self):
        """통계 생성"""
        total_recipes = Recipe.objects.count()
        total_ingredients = Ingredient.objects.count()
        total_normalized_ingredients = NormalizedIngredient.objects.count()

        normalized_count = Ingredient.objects.filter(
            normalized_ingredient__isnull=False
        ).count()

        normalization_rate = (
            (normalized_count / total_ingredients * 100)
            if total_ingredients > 0 else 0
        )

        # 카테고리별 통계
        category_stats = {}
        for category_code, category_name in NormalizedIngredient.CATEGORY_CHOICES:
            count = NormalizedIngredient.objects.filter(
                category=category_code
            ).count()
            category_stats[category_name] = count

        # 범용 조미료 통계
        common_seasoning_count = NormalizedIngredient.objects.filter(
            is_common_seasoning=True
        ).count()

        return {
            'total_recipes': total_recipes,
            'total_ingredients': total_ingredients,
            'total_normalized_ingredients': total_normalized_ingredients,
            'normalized_count': normalized_count,
            'normalization_rate': normalization_rate,
            'category_distribution': category_stats,
            'common_seasonings': common_seasoning_count
        }

    def classify_issues(self, report):
        """경고 및 오류 수준 구분"""
        # 오류: 데이터 무결성 문제
        unnormalized_count = len(report['unnormalized_ingredients'])
        if unnormalized_count > 0:
            report['errors'].append({
                'level': 'ERROR',
                'type': 'unnormalized_ingredients',
                'message': f'{unnormalized_count}개의 재료가 정규화되지 않았습니다',
                'suggestion': 'analyze_ingredients와 apply_normalization 명령을 실행하세요'
            })

        # 경고: 최적화 필요
        orphan_count = len(report['orphan_normalized_ingredients'])
        if orphan_count > 0:
            report['warnings'].append({
                'level': 'WARNING',
                'type': 'orphan_normalized_ingredients',
                'message': f'{orphan_count}개의 정규화 재료가 사용되지 않습니다',
                'suggestion': 'Admin에서 미사용 정규화 재료를 삭제하세요'
            })

        # 제안: 개선 사항
        duplicate_count = len(report['duplicate_normalized_ingredients'])
        if duplicate_count > 0:
            report['suggestions'].append({
                'level': 'INFO',
                'type': 'duplicate_normalized_ingredients',
                'message': f'{duplicate_count}개의 중복 의심 정규화 재료가 있습니다',
                'suggestion': 'Admin에서 유사한 재료를 병합하세요'
            })

        frequent_count = len(report['frequent_ingredients'])
        if frequent_count > 0:
            report['suggestions'].append({
                'level': 'INFO',
                'type': 'frequent_ingredients',
                'message': f'{frequent_count}개의 재료가 범용 조미료 후보입니다',
                'suggestion': 'Admin에서 is_common_seasoning을 True로 설정하세요'
            })
