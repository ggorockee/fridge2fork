"""
데이터 Export 모듈
크롤링된 레시피 데이터를 CSV, JSON 형태로 export
"""

import pandas as pd
import json
import logging
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from config import EXPORT_CONFIG, DATA_DIR
from ingredient_normalizer import NormalizedIngredient

# 로깅 설정
logger = logging.getLogger(__name__)

class DataExporter:
    """데이터 export 클래스"""

    def __init__(self):
        self.data_dir = DATA_DIR
        self.csv_file = EXPORT_CONFIG['csv_file']
        self.json_file = EXPORT_CONFIG['json_file']
        self.encoding = EXPORT_CONFIG['encoding']
        self.include_raw_data = EXPORT_CONFIG['include_raw_data']

        # 디렉토리 생성
        self.data_dir.mkdir(exist_ok=True)

    def export_recipes(self, recipes: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        레시피 데이터를 CSV와 JSON으로 export합니다.

        Args:
            recipes: 레시피 데이터 리스트

        Returns:
            Dict: export된 파일 경로들
        """
        if not recipes:
            logger.warning("Export할 레시피 데이터가 없습니다.")
            return {}

        logger.info(f"총 {len(recipes)}개 레시피 데이터를 export합니다.")

        # 데이터 정제 및 변환
        processed_data = self._process_recipes_for_export(recipes)

        # CSV export
        csv_path = self._export_to_csv(processed_data)

        # JSON export
        json_path = self._export_to_json(recipes)  # 원본 구조 유지

        # 통계 정보 생성
        stats_path = self._generate_statistics(processed_data)

        result = {
            'csv_file': str(csv_path),
            'json_file': str(json_path),
            'stats_file': str(stats_path),
            'total_recipes': len(recipes)
        }

        logger.info(f"Export 완료: {result}")
        return result

    def _process_recipes_for_export(self, recipes: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        레시피 데이터를 pandas DataFrame으로 변환합니다.
        """
        processed_recipes = []

        for idx, recipe in enumerate(recipes):
            try:
                # 기본 레시피 정보
                processed_recipe = {
                    'recipe_id': idx + 1,
                    'title': recipe.get('title', ''),
                    'description': recipe.get('description', ''),
                    'url': recipe.get('url', ''),
                    'image_url': recipe.get('image_url', ''),
                    'cooking_time': self._extract_cooking_time(recipe.get('cooking_time', '')),
                    'servings': self._extract_servings(recipe.get('servings', '')),
                    'difficulty': recipe.get('difficulty', ''),
                    'rating': recipe.get('rating', ''),
                    'category': recipe.get('category', ''),
                    'crawled_at': recipe.get('crawled_at', datetime.now().isoformat())
                }

                # 재료 정보 처리
                ingredients_info = self._process_ingredients(recipe.get('ingredients', []))
                processed_recipe.update(ingredients_info)

                # 조리 단계 처리
                cooking_steps = recipe.get('cooking_steps', [])
                processed_recipe['cooking_steps_count'] = len(cooking_steps)
                processed_recipe['cooking_steps'] = ' | '.join(cooking_steps) if cooking_steps else ''

                processed_recipes.append(processed_recipe)

            except Exception as e:
                logger.error(f"레시피 {idx} 처리 중 오류: {e}")
                continue

        return pd.DataFrame(processed_recipes)

    def _process_ingredients(self, ingredients: List[NormalizedIngredient]) -> Dict[str, Any]:
        """
        정규화된 재료 정보를 처리합니다.
        """
        if not ingredients:
            return {
                'ingredients_count': 0,
                'ingredients_raw': '',
                'ingredients_normalized': '',
                'main_ingredients': ''
            }

        # 원본 재료 텍스트
        raw_ingredients = [ing.original_text for ing in ingredients if ing.original_text]

        # 정규화된 재료 정보
        normalized_ingredients = []
        main_ingredients = []

        for ing in ingredients:
            if ing.name:
                if ing.quantity and ing.unit:
                    normalized_text = f"{ing.name} {ing.quantity}{ing.unit}"
                elif ing.quantity:
                    normalized_text = f"{ing.name} {ing.quantity}"
                else:
                    normalized_text = ing.name

                normalized_ingredients.append(normalized_text)

                # 신뢰도가 높은 재료를 주요 재료로 분류
                if ing.confidence > 0.7:
                    main_ingredients.append(ing.name)

        return {
            'ingredients_count': len(ingredients),
            'ingredients_raw': ' | '.join(raw_ingredients),
            'ingredients_normalized': ' | '.join(normalized_ingredients),
            'main_ingredients': ' | '.join(main_ingredients[:5])  # 상위 5개만
        }

    def _extract_cooking_time(self, time_text: str) -> int:
        """조리 시간을 분 단위 숫자로 추출합니다."""
        if not time_text:
            return None

        import re
        # "30분", "1시간 30분" 등의 패턴 매칭
        minutes = 0

        # 시간 추출
        hour_match = re.search(r'(\d+)시간', time_text)
        if hour_match:
            minutes += int(hour_match.group(1)) * 60

        # 분 추출
        min_match = re.search(r'(\d+)분', time_text)
        if min_match:
            minutes += int(min_match.group(1))

        return minutes if minutes > 0 else None

    def _extract_servings(self, servings_text: str) -> int:
        """인분 정보를 숫자로 추출합니다."""
        if not servings_text:
            return None

        import re
        match = re.search(r'(\d+)', servings_text)
        return int(match.group(1)) if match else None

    def _export_to_csv(self, df: pd.DataFrame) -> Path:
        """DataFrame을 CSV로 export합니다."""
        try:
            csv_path = self.csv_file
            df.to_csv(csv_path, index=False, encoding=self.encoding)
            logger.info(f"CSV export 완료: {csv_path}")
            return csv_path
        except Exception as e:
            logger.error(f"CSV export 실패: {e}")
            raise

    def _export_to_json(self, recipes: List[Dict[str, Any]]) -> Path:
        """레시피 데이터를 JSON으로 export합니다."""
        try:
            # NormalizedIngredient 객체를 딕셔너리로 변환
            json_data = []
            for recipe in recipes:
                recipe_copy = recipe.copy()

                # ingredients가 NormalizedIngredient 객체들의 리스트인 경우 변환
                if 'ingredients' in recipe_copy:
                    ingredients_list = []
                    for ing in recipe_copy['ingredients']:
                        if hasattr(ing, '__dict__'):  # NormalizedIngredient 객체인 경우
                            ingredients_list.append({
                                'name': ing.name,
                                'quantity': ing.quantity,
                                'unit': ing.unit,
                                'original_text': ing.original_text,
                                'confidence': ing.confidence
                            })
                        else:
                            ingredients_list.append(ing)
                    recipe_copy['ingredients'] = ingredients_list

                json_data.append(recipe_copy)

            json_path = self.json_file
            with open(json_path, 'w', encoding=self.encoding) as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            logger.info(f"JSON export 완료: {json_path}")
            return json_path
        except Exception as e:
            logger.error(f"JSON export 실패: {e}")
            raise

    def _generate_statistics(self, df: pd.DataFrame) -> Path:
        """데이터 통계 정보를 생성합니다."""
        try:
            stats = {
                'export_time': datetime.now().isoformat(),
                'total_recipes': len(df),
                'statistics': {
                    'cooking_time': {
                        'mean': df['cooking_time'].mean() if 'cooking_time' in df.columns else None,
                        'median': df['cooking_time'].median() if 'cooking_time' in df.columns else None,
                        'min': df['cooking_time'].min() if 'cooking_time' in df.columns else None,
                        'max': df['cooking_time'].max() if 'cooking_time' in df.columns else None
                    },
                    'ingredients_count': {
                        'mean': df['ingredients_count'].mean() if 'ingredients_count' in df.columns else None,
                        'median': df['ingredients_count'].median() if 'ingredients_count' in df.columns else None,
                        'min': df['ingredients_count'].min() if 'ingredients_count' in df.columns else None,
                        'max': df['ingredients_count'].max() if 'ingredients_count' in df.columns else None
                    },
                    'categories': df['category'].value_counts().to_dict() if 'category' in df.columns else {},
                    'difficulty_levels': df['difficulty'].value_counts().to_dict() if 'difficulty' in df.columns else {}
                }
            }

            stats_path = self.data_dir / 'statistics.json'
            with open(stats_path, 'w', encoding=self.encoding) as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)

            logger.info(f"통계 파일 생성 완료: {stats_path}")
            return stats_path
        except Exception as e:
            logger.error(f"통계 생성 실패: {e}")
            return None

def test_exporter():
    """데이터 export 테스트"""
    from ingredient_normalizer import IngredientNormalizer

    # 테스트 데이터 생성
    normalizer = IngredientNormalizer()

    test_recipes = [
        {
            'title': '김치볶음밥',
            'description': '간단하고 맛있는 김치볶음밥',
            'url': 'https://example.com/recipe/1',
            'cooking_time': '15분',
            'servings': '2인분',
            'difficulty': '쉬움',
            'ingredients': normalizer.normalize_ingredient_list([
                '김치 200g',
                '밥 2공기',
                '대파 1대',
                '참기름 1큰술'
            ]),
            'cooking_steps': [
                '김치를 잘게 썬다',
                '팬에 김치를 볶는다',
                '밥을 넣고 함께 볶는다'
            ]
        },
        {
            'title': '된장찌개',
            'description': '구수한 된장찌개',
            'url': 'https://example.com/recipe/2',
            'cooking_time': '20분',
            'servings': '4인분',
            'difficulty': '보통',
            'ingredients': normalizer.normalize_ingredient_list([
                '된장 2큰술',
                '두부 1/2모',
                '양파 1/2개',
                '애호박 1/4개'
            ]),
            'cooking_steps': [
                '물에 된장을 푼다',
                '야채를 넣고 끓인다',
                '두부를 넣고 마저 끓인다'
            ]
        }
    ]

    # Export 테스트
    exporter = DataExporter()
    result = exporter.export_recipes(test_recipes)

    print("=== 데이터 Export 테스트 결과 ===")
    for key, value in result.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_exporter()