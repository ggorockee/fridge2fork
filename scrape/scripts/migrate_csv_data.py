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
        logging.FileHandler('/tmp/migration.log'),
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
        
        # 환경변수 디버깅
        print("🔍 환경변수 확인:")
        print(f"POSTGRES_DB: {os.getenv('POSTGRES_DB', 'NOT SET')}")
        print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER', 'NOT SET')}")
        print(f"POSTGRES_PASSWORD: {'SET' if os.getenv('POSTGRES_PASSWORD') else 'NOT SET'}")
        print(f"POSTGRES_SERVER: {os.getenv('POSTGRES_SERVER', 'NOT SET')}")
        print(f"POSTGRES_PORT: {os.getenv('POSTGRES_PORT', 'NOT SET')}")
        print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')}")
        
        # DATABASE_URL이 없으면 환경변수로 구성 시도
        if not os.getenv('DATABASE_URL'):
            db = os.getenv('POSTGRES_DB')
            user = os.getenv('POSTGRES_USER')
            password = os.getenv('POSTGRES_PASSWORD')
            server = os.getenv('POSTGRES_SERVER')
            port = os.getenv('POSTGRES_PORT')
            
            if all([db, user, password, server, port]):
                database_url = f"postgresql://{user}:{password}@{server}:{port}/{db}"
                os.environ['DATABASE_URL'] = database_url
                print(f"✅ DATABASE_URL 자동 구성: postgresql://{user}:***@{server}:{port}/{db}")
            else:
                print("⚠️ DATABASE_URL 구성에 필요한 환경변수가 부족합니다.")

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

        # 캐시 로드 (선택적)
        try:
            await self.load_caches()
        except Exception as e:
            logger.warning(f"캐시 로딩 실패, 나중에 다시 시도: {e}")
            # 캐시 로딩 실패해도 계속 진행

    async def load_caches(self):
        """카테고리와 재료 캐시 로드"""
        async with self.async_session() as session:
            # 카테고리 캐시 로드
            try:
                result = await session.execute(select(IngredientCategory))
                categories = result.scalars().all()
                self.category_cache = {cat.name: cat.id for cat in categories}
                logger.info(f"Loaded {len(self.category_cache)} categories to cache")
            except Exception as e:
                logger.warning(f"카테고리 캐시 로딩 실패: {e}")
                self.category_cache = {}

            # 재료 캐시 로드
            try:
                result = await session.execute(select(Ingredient))
                ingredients = result.scalars().all()
                self.ingredient_cache = {ing.normalized_name: ing.id for ing in ingredients}
                logger.info(f"Loaded {len(self.ingredient_cache)} ingredients to cache")
            except Exception as e:
                logger.warning(f"재료 캐시 로딩 실패: {e}")
                self.ingredient_cache = {}

    def detect_encoding(self, file_path):
        """파일 인코딩 감지"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(100000)
            result = chardet.detect(raw_data)
            return result['encoding']

    def read_csv_file(self, file_path: Path) -> pd.DataFrame:
        """CSV 파일 읽기"""
        logger.info("🔍 파일 인코딩 감지 중...")
        encoding = self.detect_encoding(file_path)
        
        # 한국어 CSV 파일에 일반적인 인코딩들
        encodings_to_try = ['EUC-KR', 'CP949', 'UTF-8', 'UTF-8-SIG']
        if encoding and encoding not in encodings_to_try:
            encodings_to_try.insert(0, encoding)
        
        logger.info(f"📂 CSV 파일 읽기 시작: {file_path.name}")
        logger.info(f"🔤 시도할 인코딩: {', '.join(encodings_to_try)}")
        
        for enc in encodings_to_try:
            try:
                logger.info(f"🔄 {enc} 인코딩으로 시도 중...")
                df = pd.read_csv(file_path, encoding=enc, on_bad_lines='skip')
                logger.info(f"✅ CSV 파일 로드 성공: {enc} 인코딩 사용")
                logger.info(f"📊 데이터 크기: {len(df):,}개 행, {len(df.columns)}개 열")
                logger.info(f"📋 컬럼 목록: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
                return df
            except Exception as e:
                logger.warning(f"❌ {enc} 인코딩 실패: {str(e)[:100]}...")
                continue

        # 마지막 시도: 오류 무시하고 읽기
        try:
            logger.warning("⚠️ 모든 인코딩 실패, 오류 무시하고 읽기 시도...")
            df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', errors='ignore')
            logger.info(f"✅ 오류 무시하고 로드 성공: {len(df):,}개 행")
            return df
        except Exception as e:
            logger.error(f"❌ 최종 읽기 실패: {e}")
            raise ValueError(f"Failed to read {file_path.name} with any encoding")

    async def migrate_file(self, file_path: Path):
        """단일 CSV 파일 마이그레이션"""
        logger.info("=" * 60)
        logger.info(f"📚 CSV 파일 마이그레이션 시작")
        logger.info(f"📄 파일: {file_path.name}")
        logger.info(f"📁 경로: {file_path}")
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"📊 크기: {file_size_mb:.2f} MB")
        logger.info("=" * 60)

        # CSV 파일 읽기
        df = self.read_csv_file(file_path)
        total_rows = len(df)

        # 최대 레코드 수 제한
        if self.max_records:
            df = df.head(self.max_records)
            logger.info(f"⚠️  테스트 모드: {self.max_records:,}개 레코드로 제한")

        # 필요한 컬럼 확인 및 매핑
        logger.info("🔍 컬럼 매핑 검색 중...")
        column_mapping = self.detect_columns(df)
        if not column_mapping:
            logger.error(f"❌ 필수 컬럼을 찾을 수 없음: {file_path.name}")
            return
        logger.info(f"✅ 컬럼 매핑 완료:")
        for key, value in column_mapping.items():
            logger.info(f"    - {key}: {value}")

        # 청크 단위로 처리
        total_chunks = (len(df) + self.chunk_size - 1) // self.chunk_size
        logger.info(f"🔄 마이그레이션 시작:")
        logger.info(f"    - 총 레코드: {len(df):,}개")
        logger.info(f"    - 청크 수: {total_chunks}개")
        logger.info(f"    - 청크 크기: {self.chunk_size}개")

        with tqdm(total=len(df), desc=f"Migrating {file_path.name}") as pbar:
            for chunk_idx in range(0, len(df), self.chunk_size):
                chunk = df.iloc[chunk_idx:chunk_idx + self.chunk_size]
                chunk_num = (chunk_idx // self.chunk_size) + 1
                logger.debug(f"📦 청크 {chunk_num}/{total_chunks} 처리 중...")
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
    logger.info("\n" + "="*70)
    logger.info("🚀 레시피 CSV 데이터 마이그레이션 시작")
    logger.info("="*70)

    # 마이그레이터 초기화
    logger.info("🏭 마이그레이터 초기화 중...")
    migrator = CSVDataMigrator(
        chunk_size=args.chunk_size,
        max_records=args.max_records
    )
    logger.info(f"    - 청크 크기: {args.chunk_size}")
    if args.max_records:
        logger.info(f"    - 최대 레코드: {args.max_records:,}")

    try:
        # 데이터베이스 연결
        logger.info("🔗 데이터베이스 연결 중...")
        await migrator.initialize()
        logger.info("✅ 데이터베이스 연결 성공")

        # CSV 파일 찾기
        logger.info("🔍 CSV 파일 검색 중...")
        datas_dir = project_root / "datas"
        logger.info(f"    - 검색 디렉토리: {datas_dir}")
        
        # 디렉토리 존재 확인
        if not datas_dir.exists():
            logger.error(f"❌ datas 디렉토리가 존재하지 않습니다: {datas_dir}")
            logger.info("현재 작업 디렉토리 내용:")
            for item in project_root.iterdir():
                logger.info(f"    - {item.name} ({'디렉토리' if item.is_dir() else '파일'})")
            return
        
        # 디렉토리 내용 확인
        logger.info(f"datas 디렉토리 내용:")
        for item in datas_dir.iterdir():
            logger.info(f"    - {item.name} ({'디렉토리' if item.is_dir() else '파일'})")
        
        # 여러 패턴으로 CSV 파일 검색
        csv_patterns = [
            "TB_RECIPE_SEARCH*.csv",
            "*.csv"
        ]
        
        csv_files = []
        for pattern in csv_patterns:
            found_files = sorted(datas_dir.glob(pattern))
            csv_files.extend(found_files)
            if found_files:
                logger.info(f"    - 패턴 '{pattern}'으로 {len(found_files)}개 파일 발견")
        
        # 중복 제거 및 정렬
        csv_files = sorted(list(set(csv_files)))

        if not csv_files:
            logger.error("❌ CSV 파일을 찾을 수 없습니다!")
            logger.error(f"    - 검색 경로: {datas_dir}")
            logger.error("    - 패턴: TB_RECIPE_SEARCH*.csv")
            return 1

        logger.info(f"✅ {len(csv_files)}개 CSV 파일 발견:")
        for i, csv_file in enumerate(csv_files, 1):
            logger.info(f"    {i}. {csv_file.name} ({csv_file.stat().st_size / (1024*1024):.2f} MB)")

        # 각 파일 마이그레이션
        logger.info("\n🔄 CSV 파일 처리 시작...")
        for idx, csv_file in enumerate(csv_files, 1):
            logger.info(f"\n[파일 {idx}/{len(csv_files)}] {csv_file.name} 처리 중...")
            await migrator.migrate_file(csv_file)
            logger.info(f"✅ [파일 {idx}/{len(csv_files)}] {csv_file.name} 처리 완료")

        # 통계 출력
        logger.info("\n📊 마이그레이션 통계 출력 중...")
        await migrator.print_statistics()

        logger.info("\n" + "="*70)
        logger.info("🎉 모든 CSV 파일 마이그레이션 성공!")
        logger.info("="*70)
        return 0

    except Exception as e:
        logger.error("\n" + "="*70)
        logger.error("❌ 마이그레이션 실패")
        logger.error(f"🔥 오류: {e}")
        logger.error("="*70)
        import traceback
        logger.error(traceback.format_exc())
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