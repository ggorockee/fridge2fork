#!/usr/bin/env python3
"""
마이그레이션 검증 스크립트

데이터베이스에 마이그레이션된 데이터를 검증합니다.

Usage:
    python scripts/verify_migration.py
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, text

from app.models.recipe import Recipe, Ingredient, IngredientCategory, RecipeIngredient

# 환경변수 로드
load_dotenv()

def get_database_url():
    """환경변수에서 DATABASE_URL 가져오기 또는 구성"""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # DATABASE_URL이 없으면 개별 환경변수로 구성
    db = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST") or os.getenv("POSTGRES_SERVER")
    port = os.getenv("POSTGRES_PORT", "5432")

    if all([db, user, password, host]):
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        os.environ["DATABASE_URL"] = database_url
        return database_url

    return None


class MigrationVerifier:
    """마이그레이션 검증 클래스"""

    def __init__(self):
        self.engine = None
        self.async_session = None

    async def initialize(self):
        """데이터베이스 연결 초기화"""
        database_url = get_database_url()
        if not database_url:
            raise ValueError("DATABASE_URL could not be determined from environment variables")

        # asyncpg를 사용하도록 URL 변환
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def verify_basic_stats(self):
        """기본 통계 검증"""
        print("\n" + "="*60)
        print("📊 기본 데이터 통계")
        print("="*60)

        async with self.async_session() as session:
            # 레시피 수
            result = await session.execute(select(func.count(Recipe.id)))
            recipe_count = result.scalar()
            print(f"총 레시피 수: {recipe_count:,}")

            # 재료 수
            result = await session.execute(select(func.count(Ingredient.id)))
            ingredient_count = result.scalar()
            print(f"총 재료 수: {ingredient_count:,}")

            # 카테고리 수
            result = await session.execute(select(func.count(IngredientCategory.id)))
            category_count = result.scalar()
            print(f"총 카테고리 수: {category_count:,}")

            # 레시피-재료 연결 수
            result = await session.execute(select(func.count(RecipeIngredient.id)))
            relation_count = result.scalar()
            print(f"총 레시피-재료 연결 수: {relation_count:,}")

            # 평균 재료 수
            if recipe_count > 0:
                avg_ingredients = relation_count / recipe_count
                print(f"레시피당 평균 재료 수: {avg_ingredients:.1f}")

    async def verify_data_quality(self):
        """데이터 품질 검증"""
        print("\n" + "="*60)
        print("🔍 데이터 품질 검증")
        print("="*60)

        async with self.async_session() as session:
            # 제목이 없는 레시피
            result = await session.execute(
                select(func.count(Recipe.id)).where(
                    (Recipe.title == None) | (Recipe.title == '')
                )
            )
            empty_titles = result.scalar()
            print(f"❌ 제목이 없는 레시피: {empty_titles:,}")

            # 재료가 없는 레시피
            subquery = select(RecipeIngredient.recipe_id).distinct()
            result = await session.execute(
                select(func.count(Recipe.id)).where(
                    ~Recipe.id.in_(subquery)
                )
            )
            no_ingredients = result.scalar()
            print(f"❌ 재료가 없는 레시피: {no_ingredients:,}")

            # 중복 레시피 (제목 기준)
            result = await session.execute(
                select(Recipe.title, func.count(Recipe.id).label('cnt'))
                .group_by(Recipe.title)
                .having(func.count(Recipe.id) > 1)
            )
            duplicates = result.all()
            print(f"⚠️  중복 레시피 (제목 기준): {len(duplicates):,} 종류")

            # 카테고리가 없는 재료
            result = await session.execute(
                select(func.count(Ingredient.id)).where(
                    Ingredient.category_id == None
                )
            )
            no_category = result.scalar()
            print(f"⚠️  카테고리가 없는 재료: {no_category:,}")

    async def verify_categories(self):
        """카테고리별 통계"""
        print("\n" + "="*60)
        print("📦 카테고리별 재료 통계")
        print("="*60)

        async with self.async_session() as session:
            result = await session.execute(
                select(
                    IngredientCategory.name,
                    func.count(Ingredient.id).label('count')
                )
                .join(Ingredient, IngredientCategory.id == Ingredient.category_id, isouter=True)
                .group_by(IngredientCategory.id, IngredientCategory.name)
                .order_by(IngredientCategory.sort_order)
            )
            categories = result.all()

            for cat_name, count in categories:
                print(f"{cat_name:10s}: {count:5,} 개")

            # 카테고리 없는 재료
            result = await session.execute(
                select(func.count(Ingredient.id)).where(
                    Ingredient.category_id == None
                )
            )
            no_cat_count = result.scalar()
            if no_cat_count > 0:
                print(f"{'미분류':10s}: {no_cat_count:5,} 개")

    async def verify_search_functionality(self):
        """검색 기능 테스트"""
        print("\n" + "="*60)
        print("🔎 검색 기능 테스트")
        print("="*60)

        async with self.async_session() as session:
            # 한국어 전문검색 테스트
            test_keywords = ['김치', '된장', '고추장', '밥']

            for keyword in test_keywords:
                # 제목 검색
                result = await session.execute(
                    select(func.count(Recipe.id)).where(
                        Recipe.title.contains(keyword)
                    )
                )
                count = result.scalar()
                print(f"'{keyword}' 포함 레시피: {count:,} 개")

            # 재료 검색 테스트
            test_ingredients = ['마늘', '양파', '고추', '소금']

            for ing_name in test_ingredients:
                result = await session.execute(
                    select(func.count(Ingredient.id)).where(
                        Ingredient.name.contains(ing_name) |
                        Ingredient.normalized_name.contains(ing_name)
                    )
                )
                count = result.scalar()
                print(f"'{ing_name}' 재료: {count:,} 개")

    async def verify_sample_data(self):
        """샘플 데이터 출력"""
        print("\n" + "="*60)
        print("📝 샘플 데이터")
        print("="*60)

        async with self.async_session() as session:
            # 샘플 레시피
            result = await session.execute(
                select(Recipe).limit(3)
            )
            recipes = result.scalars().all()

            for recipe in recipes:
                print(f"\n🍳 레시피: {recipe.title}")
                print(f"   URL: {recipe.url}")
                print(f"   조리방법: {recipe.cooking_method}")

                # 레시피의 재료
                result = await session.execute(
                    select(RecipeIngredient, Ingredient)
                    .join(Ingredient)
                    .where(RecipeIngredient.recipe_id == recipe.id)
                    .order_by(RecipeIngredient.display_order)
                    .limit(5)
                )
                ingredients = result.all()

                if ingredients:
                    print(f"   재료 ({len(ingredients)}개 중 일부):")
                    for ri, ing in ingredients:
                        quantity_str = ""
                        if ri.quantity_from:
                            quantity_str = f"{ri.quantity_from}"
                            if ri.quantity_to:
                                quantity_str += f"~{ri.quantity_to}"
                            if ri.unit:
                                quantity_str += f" {ri.unit}"
                        elif ri.vague_description:
                            quantity_str = ri.vague_description

                        print(f"     - {ing.name}: {quantity_str}")

    async def verify_indexes(self):
        """인덱스 상태 확인"""
        print("\n" + "="*60)
        print("🔧 인덱스 상태")
        print("="*60)

        async with self.async_session() as session:
            # pg_trgm 확장 확인
            result = await session.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')")
            )
            has_trgm = result.scalar()
            print(f"pg_trgm 확장: {'✅ 설치됨' if has_trgm else '❌ 설치 안 됨'}")

            # 주요 인덱스 확인
            indexes_to_check = [
                'ix_recipes_url',
                'ix_recipes_title',
                'ix_ingredients_name',
                'ix_ingredients_normalized_name',
                'ix_recipe_ingredients_recipe_id',
                'ix_recipe_ingredients_ingredient_id'
            ]

            for index_name in indexes_to_check:
                result = await session.execute(
                    text(f"SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname = :name)"),
                    {'name': index_name}
                )
                exists = result.scalar()
                print(f"{index_name}: {'✅' if exists else '❌'}")

    async def cleanup(self):
        """리소스 정리"""
        if self.engine:
            await self.engine.dispose()


async def main():
    """메인 함수"""
    verifier = MigrationVerifier()

    try:
        print("🔍 마이그레이션 검증 시작")
        print(f"⏰ 시작 시간: {datetime.now()}")

        await verifier.initialize()

        # 각 검증 수행
        await verifier.verify_basic_stats()
        await verifier.verify_data_quality()
        await verifier.verify_categories()
        await verifier.verify_search_functionality()
        await verifier.verify_sample_data()
        await verifier.verify_indexes()

        print("\n" + "="*60)
        print("✅ 마이그레이션 검증 완료")
        print(f"⏰ 종료 시간: {datetime.now()}")
        print("="*60)

        return 0

    except Exception as e:
        print(f"\n❌ 검증 실패: {e}")
        return 1

    finally:
        await verifier.cleanup()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))