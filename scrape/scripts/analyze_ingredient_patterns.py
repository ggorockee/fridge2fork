#!/usr/bin/env python3
"""
재료명 패턴 분석 스크립트

데이터베이스의 모든 재료명을 분석하여 정제가 필요한 패턴들을 찾습니다.

Usage:
    python scripts/analyze_ingredient_patterns.py
"""
import asyncio
import sys
import os
import re
from pathlib import Path
from collections import defaultdict, Counter

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, text

from app.models.recipe import Recipe, Ingredient, RecipeIngredient

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


class IngredientAnalyzer:
    """재료명 패턴 분석기"""

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

    async def analyze_control_characters(self):
        """제어문자 패턴 분석"""
        print("\n" + "="*60)
        print("🔍 제어문자 분석")
        print("="*60)

        async with self.async_session() as session:
            # ingredients 테이블에서 \x07 포함 재료명 찾기
            result = await session.execute(
                select(Ingredient.name, Ingredient.original_name, Ingredient.id)
                .where(Ingredient.name.contains('\x07'))
            )
            x07_ingredients = result.all()

            print(f"\\x07 포함 재료 수: {len(x07_ingredients):,}")

            if x07_ingredients:
                print("\n📝 \\x07 포함 재료 예시 (처음 10개):")
                for i, (name, original, ing_id) in enumerate(x07_ingredients[:10]):
                    print(f"  {i+1:2d}. ID:{ing_id:5d} | '{name}' | 원본: '{original}'")

            # recipe_ingredients 테이블에서 \x07 포함 quantity_text 찾기
            result = await session.execute(
                select(RecipeIngredient.quantity_text, RecipeIngredient.unit, RecipeIngredient.id)
                .where(RecipeIngredient.quantity_text.contains('\x07'))
                .limit(10)
            )
            x07_quantities = result.all()

            print(f"\n\\x07 포함 수량텍스트 수: (샘플 10개)")
            for i, (qty_text, unit, ri_id) in enumerate(x07_quantities):
                print(f"  {i+1:2d}. ID:{ri_id:5d} | '{qty_text}' | 단위: '{unit}'")

    async def analyze_normalization_patterns(self):
        """정규화가 필요한 패턴 분석"""
        print("\n" + "="*60)
        print("📋 재료명 정규화 패턴 분석")
        print("="*60)

        async with self.async_session() as session:
            # 모든 재료명 가져오기
            result = await session.execute(
                select(Ingredient.name, Ingredient.original_name, Ingredient.id)
            )
            all_ingredients = result.all()

            print(f"총 재료 수: {len(all_ingredients):,}")

            # 패턴별 분류
            patterns = {
                'brand_names': [],      # 브랜드명 포함
                'descriptions': [],     # 설명 포함 [xxx 재료]
                'control_chars': [],    # 제어문자 포함
                'duplicates': defaultdict(list),  # 중복 가능성
            }

            for name, original, ing_id in all_ingredients:
                cleaned_name = name.strip()

                # 제어문자 체크
                if '\x07' in cleaned_name or any(ord(c) < 32 for c in cleaned_name if c != '\n'):
                    patterns['control_chars'].append((cleaned_name, original, ing_id))

                # 대괄호 설명 체크 [xxx 재료]
                if '[' in cleaned_name and ']' in cleaned_name:
                    patterns['descriptions'].append((cleaned_name, original, ing_id))

                # 브랜드명 패턴 체크 (특정 키워드 포함)
                brand_keywords = ['맛', '브랜드', '제품', '회사']
                if any(keyword in cleaned_name for keyword in brand_keywords):
                    patterns['brand_names'].append((cleaned_name, original, ing_id))

            # 결과 출력
            print(f"\n🏷️  브랜드명 포함: {len(patterns['brand_names']):,}")
            for i, (name, original, ing_id) in enumerate(patterns['brand_names'][:5]):
                print(f"     {i+1}. '{name}'")

            print(f"\n📝 설명 포함 [xxx]: {len(patterns['descriptions']):,}")
            for i, (name, original, ing_id) in enumerate(patterns['descriptions'][:5]):
                print(f"     {i+1}. '{name}'")

            print(f"\n🔧 제어문자 포함: {len(patterns['control_chars']):,}")
            for i, (name, original, ing_id) in enumerate(patterns['control_chars'][:5]):
                print(f"     {i+1}. '{name}' (원본: '{original}')")

    async def analyze_core_ingredients(self):
        """핵심 재료별 통계"""
        print("\n" + "="*60)
        print("🥬 핵심 재료 추출 분석")
        print("="*60)

        async with self.async_session() as session:
            result = await session.execute(select(Ingredient.name))
            all_names = [row[0] for row in result.all()]

            # 핵심 재료 추출 로직
            core_ingredients = Counter()

            for name in all_names:
                # 정제된 이름 추출
                cleaned = self.extract_core_ingredient(name)
                if cleaned:
                    core_ingredients[cleaned] += 1

            print("가장 많이 나타나는 핵심 재료 TOP 20:")
            for ingredient, count in core_ingredients.most_common(20):
                print(f"  {ingredient:15s}: {count:3d}개 변형")

    def extract_core_ingredient(self, name: str) -> str:
        """재료명에서 핵심 재료 추출"""
        if not name:
            return ""

        # 제어문자 제거
        cleaned = re.sub(r'[\x00-\x1f\x7f]', '', name)

        # 대괄호 설명 제거 [xxx 재료], [xxx용]
        cleaned = re.sub(r'\[.*?\]', '', cleaned)

        # 브랜드명/제품명 패턴 제거
        # "xxx맛 yyy" -> "yyy"
        cleaned = re.sub(r'.*맛\s+', '', cleaned)

        # 공백 정리
        cleaned = cleaned.strip()

        return cleaned

    async def generate_cleaning_preview(self):
        """정제 미리보기"""
        print("\n" + "="*60)
        print("🧹 정제 미리보기 (샘플 20개)")
        print("="*60)

        async with self.async_session() as session:
            result = await session.execute(
                select(Ingredient.name, Ingredient.original_name, Ingredient.id)
                .limit(20)
            )
            samples = result.all()

            print(f"{'ID':>5} | {'원본 재료명':30} | {'정제된 재료명':20}")
            print("-" * 60)

            for name, original, ing_id in samples:
                cleaned = self.extract_core_ingredient(name)
                print(f"{ing_id:5d} | {name[:30]:30} | {cleaned[:20]:20}")

    async def cleanup(self):
        """리소스 정리"""
        if self.engine:
            await self.engine.dispose()


async def main():
    """메인 함수"""
    analyzer = IngredientAnalyzer()

    try:
        print("🔍 재료명 패턴 분석 시작")
        await analyzer.initialize()

        await analyzer.analyze_control_characters()
        await analyzer.analyze_normalization_patterns()
        await analyzer.analyze_core_ingredients()
        await analyzer.generate_cleaning_preview()

        print("\n" + "="*60)
        print("✅ 분석 완료")
        print("="*60)

        return 0

    except Exception as e:
        print(f"\n❌ 분석 실패: {e}")
        return 1

    finally:
        await analyzer.cleanup()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))