#!/usr/bin/env python3
"""
기본 카테고리 데이터 삽입 스크립트

Usage:
    python scripts/insert_basic_data.py

Prerequisites:
    - DATABASE_URL이 .env 파일에 설정되어 있어야 함
    - PostgreSQL 서버가 실행 중이어야 함
    - 마이그레이션이 실행되어 테이블이 생성되어 있어야 함
"""
import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.recipe import IngredientCategory

# 환경변수 로드
load_dotenv()

async def insert_basic_categories():
    """8개 기본 카테고리를 데이터베이스에 삽입"""

    # 데이터베이스 URL 확인
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    # asyncpg를 사용하도록 URL 변환
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not database_url.startswith("postgresql+asyncpg://"):
        database_url = f"postgresql+asyncpg://{database_url}"

    print(f"🔗 데이터베이스 연결: {database_url.split('@')[0]}@***")

    # 비동기 엔진 및 세션 생성
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 기본 카테고리 데이터
    basic_categories = [
        {"name": "육류", "description": "소고기, 돼지고기, 닭고기 등", "sort_order": 1},
        {"name": "해산물", "description": "생선, 새우, 조개, 오징어 등", "sort_order": 2},
        {"name": "채소류", "description": "각종 채소와 나물류", "sort_order": 3},
        {"name": "양념류", "description": "간장, 고추장, 마늘, 생강 등", "sort_order": 4},
        {"name": "곡류", "description": "쌀, 밀가루, 면류 등", "sort_order": 5},
        {"name": "유제품", "description": "우유, 치즈, 버터 등", "sort_order": 6},
        {"name": "가공식품", "description": "햄, 소시지, 통조림 등", "sort_order": 7},
        {"name": "조미료", "description": "소금, 설탕, 후추, 식용유 등", "sort_order": 8},
    ]

    try:
        async with async_session() as session:
            print("📦 기본 카테고리 데이터 삽입 시작...")

            # 기존 카테고리 확인
            result = await session.execute(select(IngredientCategory))
            existing_categories = result.scalars().all()
            existing_names = {cat.name for cat in existing_categories}

            print(f"📋 기존 카테고리 수: {len(existing_categories)}")

            # 새로운 카테고리만 삽입
            new_categories = []
            for cat_data in basic_categories:
                if cat_data["name"] not in existing_names:
                    category = IngredientCategory(**cat_data)
                    new_categories.append(category)
                    session.add(category)
                    print(f"➕ 새 카테고리 추가: {cat_data['name']}")
                else:
                    print(f"⏭️  이미 존재하는 카테고리: {cat_data['name']}")

            if new_categories:
                # 트랜잭션 커밋
                await session.commit()
                print(f"✅ {len(new_categories)}개의 새 카테고리가 성공적으로 추가되었습니다.")
            else:
                print("ℹ️  추가할 새 카테고리가 없습니다.")

            # 최종 상태 확인
            result = await session.execute(select(IngredientCategory).order_by(IngredientCategory.sort_order))
            all_categories = result.scalars().all()

            print(f"\n📊 최종 카테고리 목록 (총 {len(all_categories)}개):")
            for i, category in enumerate(all_categories, 1):
                print(f"  {i}. {category.name} - {category.description}")

    except Exception as e:
        print(f"❌ 기본 데이터 삽입 실패: {e}")
        raise
    finally:
        await engine.dispose()

async def main():
    """메인 함수"""
    try:
        await insert_basic_categories()
        print("\n🎉 기본 데이터 삽입이 완료되었습니다!")
        return 0
    except Exception as e:
        print(f"\n💥 실행 중 오류 발생: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))