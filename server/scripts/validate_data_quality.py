#!/usr/bin/env python3
"""
데이터 품질 검증 스크립트 (Phase 5.5)

Production 테이블의 데이터 품질 검증:
- Recipe 개수 확인
- Ingredient 개수 및 중복 체크
- RecipeIngredient 관계 개수
- 카테고리별 분포
- 레시피당 평균 재료 개수

사용법:
    python scripts/validate_data_quality.py

    또는 (DB 연결 이슈 시)

    ENVIRONMENT=development python scripts/validate_data_quality.py
"""
import asyncio
import logging
import sys
from pathlib import Path
from collections import Counter

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import async_session, test_database_connection
from app.models.recipe import Recipe, Ingredient, RecipeIngredient
from app.models.admin import IngredientCategory
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


async def validate_production_data():
    """Production 테이블 데이터 품질 검증"""
    logger.info("🔍 데이터 품질 검증 시작")
    logger.info("=" * 80)

    # DB 연결 테스트
    logger.info("🔌 데이터베이스 연결 테스트 중...")
    db_connected = await test_database_connection()

    if not db_connected:
        logger.error("❌ 데이터베이스 연결 실패. 검증 중단")
        return 1

    try:
        async with async_session() as db:
            # 1. Recipe 개수 확인
            logger.info("\n📊 1. Recipe 테이블 검증")
            logger.info("-" * 80)

            recipe_count_result = await db.execute(select(func.count(Recipe.rcp_sno)))
            total_recipes = recipe_count_result.scalar() or 0

            approved_recipe_result = await db.execute(
                select(func.count(Recipe.rcp_sno)).where(Recipe.approval_status == "approved")
            )
            approved_recipes = approved_recipe_result.scalar() or 0

            logger.info(f"  - 총 레시피 개수: {total_recipes:,}개")
            logger.info(f"  - 승인된 레시피 개수: {approved_recipes:,}개")

            # 2. Ingredient 개수 및 중복 체크
            logger.info("\n📊 2. Ingredient 테이블 검증")
            logger.info("-" * 80)

            ingredient_count_result = await db.execute(select(func.count(Ingredient.id)))
            total_ingredients = ingredient_count_result.scalar() or 0

            logger.info(f"  - 총 재료 개수: {total_ingredients:,}개")

            # 재료명 중복 체크 (name 기준 그룹화)
            duplicate_check_result = await db.execute(
                select(Ingredient.name, func.count(Ingredient.id).label('count'))
                .group_by(Ingredient.name)
                .having(func.count(Ingredient.id) > 1)
            )
            duplicates = duplicate_check_result.fetchall()

            if duplicates:
                logger.warning(f"⚠️  중복 재료명 발견: {len(duplicates)}개")
                for name, count in duplicates[:10]:  # 처음 10개만
                    logger.warning(f"    - '{name}': {count}번 중복")
                if len(duplicates) > 10:
                    logger.warning(f"    ... 외 {len(duplicates) - 10}개 더")
            else:
                logger.info("✅ 중복 재료명 없음")

            # 3. 카테고리별 분포
            logger.info("\n📊 3. 카테고리별 재료 분포")
            logger.info("-" * 80)

            category_dist_result = await db.execute(
                select(
                    IngredientCategory.name_ko,
                    func.count(Ingredient.id).label('count')
                )
                .join(Ingredient, Ingredient.category_id == IngredientCategory.id, isouter=True)
                .group_by(IngredientCategory.id, IngredientCategory.name_ko)
                .order_by(func.count(Ingredient.id).desc())
            )
            category_dist = category_dist_result.fetchall()

            total_categorized = sum(count for _, count in category_dist)

            for category_name, count in category_dist:
                percentage = (count / total_categorized * 100) if total_categorized > 0 else 0
                logger.info(f"  - {category_name}: {count:,}개 ({percentage:.1f}%)")

            # 미분류 재료 확인
            uncategorized_result = await db.execute(
                select(func.count(Ingredient.id)).where(Ingredient.category_id.is_(None))
            )
            uncategorized = uncategorized_result.scalar() or 0

            if uncategorized > 0:
                logger.warning(f"⚠️  미분류 재료: {uncategorized:,}개")
            else:
                logger.info("✅ 모든 재료가 카테고리에 분류됨")

            # 4. RecipeIngredient 관계 개수
            logger.info("\n📊 4. RecipeIngredient 관계 검증")
            logger.info("-" * 80)

            relationship_count_result = await db.execute(
                select(func.count(RecipeIngredient.id))
            )
            total_relationships = relationship_count_result.scalar() or 0

            logger.info(f"  - 총 레시피-재료 관계: {total_relationships:,}개")

            # 레시피당 평균 재료 개수
            if total_recipes > 0:
                avg_ingredients = total_relationships / total_recipes
                logger.info(f"  - 레시피당 평균 재료: {avg_ingredients:.2f}개")
            else:
                logger.warning("⚠️  레시피가 없어 평균 계산 불가")

            # 재료가 없는 레시피 확인
            recipes_without_ingredients_result = await db.execute(
                select(func.count(Recipe.rcp_sno))
                .outerjoin(RecipeIngredient, Recipe.rcp_sno == RecipeIngredient.rcp_sno)
                .where(RecipeIngredient.id.is_(None))
            )
            recipes_without_ingredients = recipes_without_ingredients_result.scalar() or 0

            if recipes_without_ingredients > 0:
                logger.warning(
                    f"⚠️  재료가 없는 레시피: {recipes_without_ingredients:,}개 "
                    f"({recipes_without_ingredients/total_recipes*100:.1f}%)"
                )
            else:
                logger.info("✅ 모든 레시피에 재료가 연결됨")

            # 5. 무작위 샘플링 검증 (10개)
            logger.info("\n📊 5. 무작위 샘플 검증 (10개)")
            logger.info("-" * 80)

            sample_recipes_result = await db.execute(
                select(Recipe)
                .options(selectinload(Recipe.recipe_ingredients).selectinload(RecipeIngredient.ingredient))
                .limit(10)
            )
            sample_recipes = sample_recipes_result.scalars().all()

            for i, recipe in enumerate(sample_recipes, 1):
                ingredient_count = len(recipe.recipe_ingredients)
                logger.info(f"  샘플 {i}: {recipe.rcp_ttl}")
                logger.info(f"    - 재료 개수: {ingredient_count}개")
                if ingredient_count > 0:
                    ingredient_names = [ri.ingredient.name for ri in recipe.recipe_ingredients[:5]]
                    logger.info(f"    - 재료 예시: {', '.join(ingredient_names)}...")

            # 6. 최종 요약
            logger.info("\n" + "=" * 80)
            logger.info("📊 검증 결과 요약")
            logger.info("=" * 80)
            logger.info(f"✅ 레시피: {total_recipes:,}개 (승인: {approved_recipes:,}개)")
            logger.info(f"✅ 재료: {total_ingredients:,}개")
            logger.info(f"✅ 레시피-재료 관계: {total_relationships:,}개")

            if total_recipes > 0:
                logger.info(f"📈 평균 재료/레시피: {avg_ingredients:.2f}개")

            # 경고 요약
            warnings_count = 0
            if duplicates:
                warnings_count += len(duplicates)
            if uncategorized > 0:
                warnings_count += 1
            if recipes_without_ingredients > 0:
                warnings_count += 1

            if warnings_count > 0:
                logger.warning(f"\n⚠️  총 {warnings_count}개의 경고 발견")
                logger.warning("상세 내용은 위 섹션 참조")
            else:
                logger.info("\n✅ 모든 검증 통과! 데이터 품질 양호")

            logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"❌ 데이터 품질 검증 실패: {e}", exc_info=True)
        return 1


async def main():
    """메인 함수"""
    exit_code = await validate_production_data()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
