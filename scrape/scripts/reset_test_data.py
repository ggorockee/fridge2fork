#!/usr/bin/env python3
"""
테스트 데이터 초기화 스크립트 (로컬 개발용)

Usage:
    python scripts/reset_test_data.py
    python scripts/reset_test_data.py --confirm

주의: 이 스크립트는 모든 데이터를 삭제합니다!
"""
import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import argparse

# 환경변수 로드
load_dotenv()


async def reset_database(confirm: bool = False):
    """데이터베이스 초기화"""

    # 안전 확인
    if not confirm:
        print("⚠️  경고: 이 작업은 모든 테스트 데이터를 삭제합니다!")
        print("⚠️  운영 환경에서는 절대 실행하지 마세요!")
        print()
        response = input("계속하시겠습니까? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ 취소되었습니다.")
            return

    # DATABASE_URL 구성
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        db = os.getenv('POSTGRES_DB')
        user = os.getenv('POSTGRES_USER')
        password = os.getenv('POSTGRES_PASSWORD')
        server = os.getenv('POSTGRES_SERVER')
        port = os.getenv('POSTGRES_PORT')

        if not all([db, user, password, server, port]):
            print("❌ DATABASE_URL 또는 PostgreSQL 환경변수가 설정되지 않았습니다.")
            return

        database_url = f"postgresql://{user}:{password}@{server}:{port}/{db}"

    # asyncpg용 URL 변환
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')

    print(f"🔗 데이터베이스 연결 중...")
    print(f"   서버: {database_url.split('@')[1].split('/')[0]}")

    try:
        engine = create_async_engine(database_url, echo=False)

        async with engine.begin() as conn:
            print("\n🗑️  데이터 삭제 시작...")

            # 1. recipe_ingredients 삭제
            result = await conn.execute(text("SELECT COUNT(*) FROM recipe_ingredients"))
            count = result.scalar()
            print(f"   1/3. recipe_ingredients: {count:,}개 레코드 삭제 중...")
            await conn.execute(text("TRUNCATE TABLE recipe_ingredients CASCADE"))
            print(f"        ✅ 삭제 완료")

            # 2. ingredients 삭제
            result = await conn.execute(text("SELECT COUNT(*) FROM ingredients"))
            count = result.scalar()
            print(f"   2/3. ingredients: {count:,}개 레코드 삭제 중...")
            await conn.execute(text("TRUNCATE TABLE ingredients CASCADE"))
            print(f"        ✅ 삭제 완료")

            # 3. recipes 삭제
            result = await conn.execute(text("SELECT COUNT(*) FROM recipes"))
            count = result.scalar()
            print(f"   3/3. recipes: {count:,}개 레코드 삭제 중...")
            await conn.execute(text("TRUNCATE TABLE recipes CASCADE"))
            print(f"        ✅ 삭제 완료")

            print("\n✅ 모든 테스트 데이터가 삭제되었습니다!")
            print("\n📝 다음 단계:")
            print("   python scripts/migrate_csv_data.py --max-records 100")

        await engine.dispose()

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset test database")
    parser.add_argument("--confirm", action="store_true",
                       help="Skip confirmation prompt")

    args = parser.parse_args()

    asyncio.run(reset_database(confirm=args.confirm))