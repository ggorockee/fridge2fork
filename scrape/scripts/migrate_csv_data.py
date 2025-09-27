#!/usr/bin/env python3
"""
CSV 데이터를 PostgreSQL 데이터베이스로 마이그레이션하는 스크립트

Usage:
    python scripts/migrate_csv_data.py [--chunk-size 100] [--max-records 1000]

Prerequisites:
    - DATABASE_URL이 .env 파일에 설정되어 있어야 함
    - PostgreSQL 서버가 실행 중이어야 함
    - Phase 2 (데이터베이스 스키마)가 완료되어야 함
"""
import asyncio
import sys
import os
import pandas as pd
import chardet
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from tqdm import tqdm
import argparse

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from app.models.recipe import Recipe, Ingredient, IngredientCategory, RecipeIngredient
from app.utils.ingredient_parser import IngredientParser, parse_ingredients_list

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CSVDataMigrator:
    """CSV 데이터 마이그레이션 클래스"""

    def __init__(self, chunk_size: int = 100, max_records: Optional[int] = None):
        """
        Args:
            chunk_size: 배치 처리 크기
            max_records: 최대 처리 레코드 수 (None이면 전체)
        """
        self.chunk_size = chunk_size
        self.max_records = max_records
        self.engine = None
        self.async_session = None
        self.parser = IngredientParser()

        # 캐시
        self.category_cache = {}  # 카테고리 ID 캐시
        self.ingredient_cache = {}  # 재료 ID 캐시

        # 통계
        self.stats = {
            'total_processed': 0,
            'recipes_created': 0,
            'ingredients_created': 0,
            'recipe_ingredients_created': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }

    async def initialize(self):
        """데이터베이스 연결 초기화"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")

        # asyncpg를 사용하도록 URL 변환
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        logger.info(f"Connecting to database...")
        self.engine = create_async_engine(
            database_url,
            echo=False,  # SQL 쿼리 출력 비활성화
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

        # 캐시 로드
        await self.load_caches()

    async def load_caches(self):
        """카테고리와 재료 캐시 로드"""
        async with self.async_session() as session:
            # 카테고리 캐시 로드
            result = await session.execute(select(IngredientCategory))
            categories = result.scalars().all()
            self.category_cache = {cat.name: cat.id for cat in categories}
            logger.info(f"Loaded {len(self.category_cache)} categories to cache")

            # 재료 캐시 로드
            result = await session.execute(select(Ingredient))
            ingredients = result.scalars().all()
            self.ingredient_cache = {ing.normalized_name: ing.id for ing in ingredients}
            logger.info(f"Loaded {len(self.ingredient_cache)} ingredients to cache")

    def detect_encoding(self, file_path):
        """파일 인코딩 감지"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(100000)
            result = chardet.detect(raw_data)
            return result['encoding']

    def read_csv_file(self, file_path: Path) -> pd.DataFrame:
        """CSV 파일 읽기"""
        encoding = self.detect_encoding(file_path)
        encodings_to_try = [encoding] if encoding else []
        encodings_to_try.extend(['EUC-KR', 'UTF-8', 'CP949'])

        for enc in encodings_to_try:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                logger.info(f"Successfully read {file_path.name} with {enc} encoding")
                return df
            except:
                continue

        raise ValueError(f"Failed to read {file_path.name} with any encoding")

    async def migrate_file(self, file_path: Path):
        """단일 CSV 파일 마이그레이션"""
        logger.info(f"Starting migration of {file_path.name}")

        # CSV 파일 읽기
        df = self.read_csv_file(file_path)
        total_rows = len(df)

        # 최대 레코드 수 제한
        if self.max_records:
            df = df.head(self.max_records)
            logger.info(f"Limited to {self.max_records} records")

        # 필요한 컬럼 확인 및 매핑
        column_mapping = self.detect_columns(df)
        if not column_mapping:
            logger.error(f"Required columns not found in {file_path.name}")
            return

        # 청크 단위로 처리
        total_chunks = (len(df) + self.chunk_size - 1) // self.chunk_size

        with tqdm(total=len(df), desc=f"Migrating {file_path.name}") as pbar:
            for chunk_idx in range(0, len(df), self.chunk_size):
                chunk = df.iloc[chunk_idx:chunk_idx + self.chunk_size]
                await self.process_chunk(chunk, column_mapping)
                pbar.update(len(chunk))

                # 메모리 정리
                if chunk_idx % (self.chunk_size * 10) == 0:
                    await asyncio.sleep(0.1)  # 다른 작업에 CPU 양보

    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """데이터프레임에서 필요한 컬럼 감지"""
        column_mapping = {}

        # 레시피명 컬럼 찾기
        for col in df.columns:
            if 'RCP_NM' in col or '레시피' in col and '명' in col:
                column_mapping['title'] = col
                break

        # 재료 컬럼 찾기
        for col in df.columns:
            if 'RCP_PARTS_DTLS' in col or '재료' in col:
                column_mapping['ingredients'] = col
                break

        # 요리방법 컬럼 찾기
        for col in df.columns:
            if 'RCP_WAY2' in col or '요리방법' in col or '조리방법' in col:
                column_mapping['cooking_method'] = col
                break

        # 이미지 URL 컬럼 찾기
        for col in df.columns:
            if 'ATT_FILE' in col or 'IMG' in col or '이미지' in col:
                column_mapping['image_url'] = col
                break

        # 필수 컬럼 확인
        if 'title' not in column_mapping:
            return None

        return column_mapping

    async def process_chunk(self, chunk: pd.DataFrame, column_mapping: Dict[str, str]):
        """데이터 청크 처리"""
        async with self.async_session() as session:
            try:
                for _, row in chunk.iterrows():
                    await self.process_recipe(session, row, column_mapping)

                await session.commit()
                self.stats['total_processed'] += len(chunk)

            except Exception as e:
                logger.error(f"Error processing chunk: {e}")
                await session.rollback()
                self.stats['errors'] += len(chunk)

    async def process_recipe(self, session: AsyncSession, row: pd.Series, column_mapping: Dict[str, str]):
        """단일 레시피 처리"""
        try:
            # 레시피 데이터 추출
            title = str(row[column_mapping['title']]) if pd.notna(row[column_mapping['title']]) else None
            if not title:
                return

            # URL 생성 (실제 URL이 없으므로 임시로 생성)
            recipe_url = f"recipe_{self.stats['total_processed'] + 1}"

            # 중복 체크
            result = await session.execute(
                select(Recipe).where(Recipe.url == recipe_url)
            )
            existing = result.scalar_one_or_none()
            if existing:
                self.stats['duplicates_skipped'] += 1
                return

            # 레시피 생성
            recipe = Recipe(
                url=recipe_url,
                title=title,
                image_url=str(row[column_mapping['image_url']]) if 'image_url' in column_mapping and pd.notna(row[column_mapping['image_url']]) else None,
                cooking_method=str(row[column_mapping['cooking_method']]) if 'cooking_method' in column_mapping and pd.notna(row[column_mapping['cooking_method']]) else None,
            )
            session.add(recipe)
            await session.flush()  # ID 생성을 위해 flush
            self.stats['recipes_created'] += 1

            # 재료 처리
            if 'ingredients' in column_mapping and pd.notna(row[column_mapping['ingredients']]):
                ingredients_text = str(row[column_mapping['ingredients']])
                await self.process_ingredients(session, recipe.id, ingredients_text)

        except Exception as e:
            logger.error(f"Error processing recipe: {e}")
            self.stats['errors'] += 1

    async def process_ingredients(self, session: AsyncSession, recipe_id: int, ingredients_text: str):
        """재료 처리"""
        parsed_ingredients = parse_ingredients_list(ingredients_text)

        for idx, parsed_ing in enumerate(parsed_ingredients):
            try:
                # 재료 찾기 또는 생성
                ingredient_id = await self.get_or_create_ingredient(
                    session,
                    parsed_ing.normalized_name,
                    parsed_ing.name
                )

                # 레시피-재료 연결 생성
                recipe_ingredient = RecipeIngredient(
                    recipe_id=recipe_id,
                    ingredient_id=ingredient_id,
                    quantity_from=parsed_ing.quantity_from,
                    quantity_to=parsed_ing.quantity_to,
                    unit=parsed_ing.unit,
                    original_text=parsed_ing.original_text[:200] if parsed_ing.original_text else None,
                    is_vague=parsed_ing.is_vague,
                    vague_description=parsed_ing.vague_description[:50] if parsed_ing.vague_description else None,
                    importance=parsed_ing.importance,
                    display_order=idx
                )
                session.add(recipe_ingredient)
                self.stats['recipe_ingredients_created'] += 1

            except Exception as e:
                logger.error(f"Error processing ingredient '{parsed_ing.name}': {e}")

    async def get_or_create_ingredient(self, session: AsyncSession, normalized_name: str, original_name: str) -> int:
        """재료 찾기 또는 생성"""
        # 캐시에서 확인
        if normalized_name in self.ingredient_cache:
            return self.ingredient_cache[normalized_name]

        # 데이터베이스에서 확인
        result = await session.execute(
            select(Ingredient).where(Ingredient.normalized_name == normalized_name)
        )
        ingredient = result.scalar_one_or_none()

        if ingredient:
            self.ingredient_cache[normalized_name] = ingredient.id
            return ingredient.id

        # 새 재료 생성
        category_name = self.parser.categorize_ingredient(normalized_name)
        category_id = self.category_cache.get(category_name)

        ingredient = Ingredient(
            name=original_name,
            normalized_name=normalized_name,
            category_id=category_id,
            is_ambiguous=False
        )
        session.add(ingredient)
        await session.flush()

        self.ingredient_cache[normalized_name] = ingredient.id
        self.stats['ingredients_created'] += 1

        return ingredient.id

    async def print_statistics(self):
        """마이그레이션 통계 출력"""
        logger.info("\n" + "="*60)
        logger.info("📊 마이그레이션 통계")
        logger.info("="*60)
        logger.info(f"총 처리 레코드: {self.stats['total_processed']:,}")
        logger.info(f"생성된 레시피: {self.stats['recipes_created']:,}")
        logger.info(f"생성된 재료: {self.stats['ingredients_created']:,}")
        logger.info(f"생성된 레시피-재료 연결: {self.stats['recipe_ingredients_created']:,}")
        logger.info(f"건너뛴 중복: {self.stats['duplicates_skipped']:,}")
        logger.info(f"오류: {self.stats['errors']:,}")

        # 데이터베이스 통계
        async with self.async_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM recipes"))
            total_recipes = result.scalar()
            result = await session.execute(text("SELECT COUNT(*) FROM ingredients"))
            total_ingredients = result.scalar()
            result = await session.execute(text("SELECT COUNT(*) FROM recipe_ingredients"))
            total_relations = result.scalar()

            logger.info("\n📊 데이터베이스 현황")
            logger.info(f"총 레시피 수: {total_recipes:,}")
            logger.info(f"총 재료 수: {total_ingredients:,}")
            logger.info(f"총 레시피-재료 연결 수: {total_relations:,}")

    async def cleanup(self):
        """리소스 정리"""
        if self.engine:
            await self.engine.dispose()


async def main(args):
    """메인 함수"""
    # 마이그레이터 초기화
    migrator = CSVDataMigrator(
        chunk_size=args.chunk_size,
        max_records=args.max_records
    )

    try:
        # 초기화
        await migrator.initialize()

        # CSV 파일 찾기
        datas_dir = project_root / "datas"
        csv_files = sorted(datas_dir.glob("TB_RECIPE_SEARCH*.csv"))

        if not csv_files:
            logger.error("No CSV files found")
            return 1

        logger.info(f"Found {len(csv_files)} CSV files")

        # 각 파일 마이그레이션
        for csv_file in csv_files:
            await migrator.migrate_file(csv_file)

        # 통계 출력
        await migrator.print_statistics()

        logger.info("\n🎉 마이그레이션 완료!")
        return 0

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1

    finally:
        await migrator.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate CSV data to PostgreSQL")
    parser.add_argument("--chunk-size", type=int, default=100,
                       help="Number of records to process in each batch")
    parser.add_argument("--max-records", type=int, default=None,
                       help="Maximum number of records to process (for testing)")

    args = parser.parse_args()

    sys.exit(asyncio.run(main(args)))