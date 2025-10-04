"""
재료 기반 레시피 추천 시스템
사용자가 입력한 재료와 데이터베이스의 유사도 매칭
"""

import pandas as pd
from typing import List, Set, Dict, Tuple
from ingredient_normalizer import IngredientNormalizer
from collections import Counter


class RecipeRecommender:
    """재료 기반 레시피 추천 엔진"""

    def __init__(self, csv_path: str):
        """
        Args:
            csv_path: TB_RECIPE_SEARCH_NEW_1.csv 경로
        """
        self.normalizer = IngredientNormalizer()
        self.df = pd.read_csv(csv_path)
        self._preprocess_recipes()

    def _preprocess_recipes(self):
        """전체 레시피 재료 전처리 (1회만 실행)"""
        print("📦 레시피 데이터 전처리 중...")

        # 각 레시피의 핵심 재료 추출
        self.df['normalized_ingredients'] = self.df['CKG_MTRL_CN'].apply(
            lambda x: self.normalizer.get_primary_ingredients(x)
        )

        # 빈 재료 레시피 제거
        self.df = self.df[self.df['normalized_ingredients'].apply(len) > 0]

        print(f"✅ 전처리 완료: {len(self.df):,}개 레시피")

    def recommend(self, user_ingredients: List[str], top_k: int = 10) -> List[Dict]:
        """
        재료 기반 레시피 추천

        Args:
            user_ingredients: 사용자 보유 재료 ['돼지고기', '양파', '감자']
            top_k: 추천할 레시피 개수

        Returns:
            [
                {
                    'recipe_id': 7016813,
                    'title': '멸치육수 소고기 떡국',
                    'match_score': 0.75,  # 매칭 점수 (0~1)
                    'matched_ingredients': ['소고기', '계란'],
                    'missing_ingredients': ['떡국떡'],
                    'url': 'https://...'
                },
                ...
            ]
        """

        # 1. 사용자 재료 정규화
        normalized_user = set(
            self.normalizer._normalize_name(ing) for ing in user_ingredients
        )

        # 2. 각 레시피와 유사도 계산
        scores = []
        for idx, row in self.df.iterrows():
            recipe_ingredients = set(row['normalized_ingredients'])

            # Jaccard 유사도 계산
            matched = normalized_user & recipe_ingredients  # 교집합
            total = normalized_user | recipe_ingredients    # 합집합

            if not total:
                similarity = 0
            else:
                similarity = len(matched) / len(total)

            # 매칭된 재료 개수에 가중치 부여 (더 많이 매칭되면 높은 점수)
            match_count_bonus = len(matched) / len(recipe_ingredients) if recipe_ingredients else 0

            # 최종 점수 = Jaccard 유사도 + 매칭 개수 보너스
            final_score = similarity * 0.5 + match_count_bonus * 0.5

            scores.append({
                'index': idx,
                'score': final_score,
                'matched': list(matched),
                'missing': list(recipe_ingredients - normalized_user)
            })

        # 3. 점수 기준 정렬
        scores.sort(key=lambda x: x['score'], reverse=True)

        # 4. 상위 K개 추출
        recommendations = []
        for item in scores[:top_k]:
            row = self.df.loc[item['index']]

            recommendations.append({
                'recipe_id': row['RCP_SNO'],
                'title': row['RCP_TTL'],
                'match_score': round(item['score'], 3),
                'matched_ingredients': item['matched'],
                'missing_ingredients': item['missing'],
                'url': row.get('RCP_IMG_URL', ''),
                'servings': row.get('CKG_INBUN_NM', ''),
                'cooking_method': row.get('CKG_MTH_ACTO_NM', '')
            })

        return recommendations

    def find_recipes_by_exact_match(self, user_ingredients: List[str],
                                     min_match_count: int = 2) -> List[Dict]:
        """
        정확히 매칭되는 레시피 검색 (빠른 필터링)

        Args:
            user_ingredients: 사용자 재료
            min_match_count: 최소 매칭 재료 개수

        Returns:
            완전 매칭 레시피 리스트
        """

        # 사용자 재료 정규화
        normalized_user = set(
            self.normalizer._normalize_name(ing) for ing in user_ingredients
        )

        results = []
        for idx, row in self.df.iterrows():
            recipe_ingredients = set(row['normalized_ingredients'])

            # 교집합 계산
            matched = normalized_user & recipe_ingredients

            # 최소 매칭 개수 조건
            if len(matched) >= min_match_count:
                results.append({
                    'recipe_id': row['RCP_SNO'],
                    'title': row['RCP_TTL'],
                    'matched_count': len(matched),
                    'matched_ingredients': list(matched),
                    'missing_ingredients': list(recipe_ingredients - normalized_user),
                    'url': row.get('RCP_IMG_URL', '')
                })

        # 매칭 개수 기준 정렬
        results.sort(key=lambda x: x['matched_count'], reverse=True)
        return results

    def get_popular_ingredients(self, top_k: int = 20) -> List[Tuple[str, int]]:
        """가장 많이 사용되는 재료 통계"""

        all_ingredients = []
        for ingredients_list in self.df['normalized_ingredients']:
            all_ingredients.extend(ingredients_list)

        counter = Counter(all_ingredients)
        return counter.most_common(top_k)


# 사용 예시
if __name__ == "__main__":
    print("=" * 80)
    print("🍽️  레시피 추천 시스템 테스트")
    print("=" * 80)

    # 추천 엔진 초기화
    recommender = RecipeRecommender("datas/TB_RECIPE_SEARCH_NEW_1.csv")

    # 테스트 시나리오 1: 냉장고에 있는 재료로 추천
    print("\n[시나리오 1] 냉장고 재료: 돼지고기, 양파, 감자")
    print("-" * 80)

    user_ingredients = ['돼지고기', '양파', '감자']
    recommendations = recommender.recommend(user_ingredients, top_k=5)

    for i, recipe in enumerate(recommendations, 1):
        print(f"\n{i}. {recipe['title']}")
        print(f"   매칭 점수: {recipe['match_score']:.2%}")
        print(f"   ✅ 있는 재료: {', '.join(recipe['matched_ingredients'])}")
        if recipe['missing_ingredients']:
            print(f"   ❌ 필요한 재료: {', '.join(recipe['missing_ingredients'][:5])}")
        print(f"   조리법: {recipe['cooking_method']} | 인분: {recipe['servings']}")

    # 테스트 시나리오 2: 정확히 매칭되는 레시피 찾기
    print("\n" + "=" * 80)
    print("[시나리오 2] 2개 이상 재료가 정확히 매칭되는 레시피")
    print("-" * 80)

    exact_matches = recommender.find_recipes_by_exact_match(
        user_ingredients=['닭고기', '감자', '당근'],
        min_match_count=2
    )

    print(f"총 {len(exact_matches)}개 레시피 발견")
    for i, recipe in enumerate(exact_matches[:5], 1):
        print(f"\n{i}. {recipe['title']}")
        print(f"   매칭: {recipe['matched_count']}개 - {', '.join(recipe['matched_ingredients'])}")

    # 테스트 시나리오 3: 인기 재료 통계
    print("\n" + "=" * 80)
    print("[시나리오 3] 가장 많이 사용되는 핵심 재료 TOP 20")
    print("-" * 80)

    popular = recommender.get_popular_ingredients(top_k=20)
    for i, (ingredient, count) in enumerate(popular, 1):
        percentage = (count / len(recommender.df)) * 100
        print(f"{i:2d}. {ingredient:10s}: {count:4d}회 ({percentage:5.2f}%)")