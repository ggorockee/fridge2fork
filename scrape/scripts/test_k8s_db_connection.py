#!/usr/bin/env python3
"""
Kubernetes PostgreSQL 연결 테스트 도구

사용법:
    python scripts/test_k8s_db_connection.py

기능:
- K8s 환경에서 PostgreSQL 컨테이너 연결 테스트
- 환경변수 기반 연결 설정 검증
- 데이터베이스 스키마 존재 여부 확인
- 연결 성능 및 상태 점검
"""
import asyncio
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # K8s 환경에서는 dotenv 없이도 동작
    pass

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text, select
    from sqlalchemy.pool import NullPool
except ImportError:
    print("❌ SQLAlchemy 관련 패키지가 설치되지 않았습니다.")
    print("pip install sqlalchemy[asyncio] asyncpg 를 실행하세요.")
    sys.exit(1)


def get_database_url() -> str:
    """환경변수에서 DATABASE_URL 구성"""
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
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    return None


def print_environment_info():
    """환경변수 정보 출력"""
    print("🔧 환경변수 설정 상태")
    print("=" * 50)

    env_vars = [
        'POSTGRES_SERVER', 'POSTGRES_HOST', 'POSTGRES_PORT',
        'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
        'DATABASE_URL'
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                print(f"  ✅ {var}: ***")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: (미설정)")

    print()


async def test_basic_connection(database_url: str) -> Dict[str, Any]:
    """기본 데이터베이스 연결 테스트"""
    result = {
        'success': False,
        'error': None,
        'connection_time': None,
        'server_version': None
    }

    try:
        start_time = time.time()

        # 엔진 생성 (연결 풀 사용 안 함 - 테스트용)
        engine = create_async_engine(
            database_url,
            poolclass=NullPool,
            echo=False
        )

        # 연결 테스트
        async with engine.begin() as conn:
            # PostgreSQL 버전 확인
            version_result = await conn.execute(text("SELECT version()"))
            version = version_result.scalar()

            result['server_version'] = version
            result['connection_time'] = round((time.time() - start_time) * 1000, 2)
            result['success'] = True

        await engine.dispose()

    except Exception as e:
        result['error'] = str(e)

    return result


async def test_database_exists(database_url: str) -> Dict[str, Any]:
    """데이터베이스 존재 및 접근 가능성 테스트"""
    result = {
        'success': False,
        'error': None,
        'database_name': None,
        'current_user': None,
        'schema_count': 0
    }

    try:
        engine = create_async_engine(database_url, poolclass=NullPool, echo=False)

        async with engine.begin() as conn:
            # 현재 데이터베이스명 확인
            db_result = await conn.execute(text("SELECT current_database()"))
            result['database_name'] = db_result.scalar()

            # 현재 사용자 확인
            user_result = await conn.execute(text("SELECT current_user"))
            result['current_user'] = user_result.scalar()

            # 스키마 개수 확인
            schema_result = await conn.execute(
                text("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'information_schema'")
            )
            result['schema_count'] = schema_result.scalar()

            result['success'] = True

        await engine.dispose()

    except Exception as e:
        result['error'] = str(e)

    return result


async def test_table_existence(database_url: str) -> Dict[str, Any]:
    """Phase 2 관련 테이블 존재 여부 확인"""
    result = {
        'success': False,
        'error': None,
        'tables': {}
    }

    expected_tables = ['recipes', 'ingredients', 'recipe_ingredients']

    try:
        engine = create_async_engine(database_url, poolclass=NullPool, echo=False)

        async with engine.begin() as conn:
            for table_name in expected_tables:
                table_result = await conn.execute(
                    text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = :table_name
                    )
                    """),
                    {'table_name': table_name}
                )
                exists = table_result.scalar()
                result['tables'][table_name] = exists

            result['success'] = True

        await engine.dispose()

    except Exception as e:
        result['error'] = str(e)

    return result


async def test_alembic_version(database_url: str) -> Dict[str, Any]:
    """Alembic 마이그레이션 상태 확인"""
    result = {
        'success': False,
        'error': None,
        'version_table_exists': False,
        'current_version': None
    }

    try:
        engine = create_async_engine(database_url, poolclass=NullPool, echo=False)

        async with engine.begin() as conn:
            # alembic_version 테이블 존재 여부 확인
            version_table_result = await conn.execute(
                text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'alembic_version'
                )
                """)
            )
            version_table_exists = version_table_result.scalar()
            result['version_table_exists'] = version_table_exists

            if version_table_exists:
                # 현재 버전 확인
                current_version_result = await conn.execute(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                )
                current_version = current_version_result.scalar()
                result['current_version'] = current_version

            result['success'] = True

        await engine.dispose()

    except Exception as e:
        result['error'] = str(e)

    return result


async def test_performance(database_url: str) -> Dict[str, Any]:
    """기본 성능 테스트"""
    result = {
        'success': False,
        'error': None,
        'connection_pool_test': None,
        'simple_query_time': None,
        'concurrent_connections': 0
    }

    try:
        # 연결 풀 테스트
        start_time = time.time()
        engine = create_async_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            echo=False
        )

        # 동시 연결 테스트
        async def simple_query():
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

        # 5개 동시 연결 테스트
        tasks = [simple_query() for _ in range(5)]
        await asyncio.gather(*tasks)

        result['concurrent_connections'] = 5
        result['connection_pool_test'] = round((time.time() - start_time) * 1000, 2)

        # 단순 쿼리 성능 테스트
        start_time = time.time()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
        result['simple_query_time'] = round((time.time() - start_time) * 1000, 2)

        result['success'] = True
        await engine.dispose()

    except Exception as e:
        result['error'] = str(e)

    return result


def print_test_results(test_name: str, result: Dict[str, Any]):
    """테스트 결과 출력"""
    print(f"🧪 {test_name}")
    print("-" * 40)

    if result['success']:
        print("  ✅ 성공")
        for key, value in result.items():
            if key not in ['success', 'error'] and value is not None:
                if isinstance(value, dict):
                    print(f"  📊 {key}:")
                    for sub_key, sub_value in value.items():
                        status = "✅" if sub_value else "❌"
                        print(f"    {status} {sub_key}: {sub_value}")
                else:
                    print(f"  📊 {key}: {value}")
    else:
        print("  ❌ 실패")
        if result['error']:
            print(f"  🚨 오류: {result['error']}")

    print()


async def main():
    """메인 함수"""
    print("🐘 Kubernetes PostgreSQL 연결 테스트")
    print("=" * 60)
    print(f"⏰ 테스트 시작: {datetime.now()}")
    print()

    # 환경변수 확인
    print_environment_info()

    # DATABASE_URL 구성
    database_url = get_database_url()
    if not database_url:
        print("❌ DATABASE_URL을 구성할 수 없습니다.")
        print("💡 필요한 환경변수: POSTGRES_SERVER, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD")
        return 1

    # DATABASE_URL 마스킹 출력
    masked_url = database_url
    if '@' in masked_url and ':' in masked_url:
        parts = masked_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            if len(user_pass) >= 3:  # postgresql+asyncpg://user:pass
                user_pass[-1] = '***'
                parts[0] = ':'.join(user_pass)
            masked_url = '@'.join(parts)

    print(f"🔗 연결 URL: {masked_url}")
    print()

    # 테스트 실행
    tests = [
        ("기본 연결 테스트", test_basic_connection),
        ("데이터베이스 접근 테스트", test_database_exists),
        ("테이블 존재 확인", test_table_existence),
        ("Alembic 버전 확인", test_alembic_version),
        ("성능 테스트", test_performance)
    ]

    total_tests = len(tests)
    passed_tests = 0

    for test_name, test_func in tests:
        try:
            result = await test_func(database_url)
            print_test_results(test_name, result)
            if result['success']:
                passed_tests += 1
        except Exception as e:
            print_test_results(test_name, {'success': False, 'error': str(e)})

    # 최종 결과
    print("=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"총 테스트: {total_tests}개")
    print(f"성공: {passed_tests}개")
    print(f"실패: {total_tests - passed_tests}개")

    if passed_tests == total_tests:
        print("\n🎉 모든 테스트가 성공했습니다!")
        print("✅ K8s PostgreSQL 연결이 정상적으로 설정되었습니다.")
        return 0
    else:
        print(f"\n⚠️ {total_tests - passed_tests}개의 테스트가 실패했습니다.")
        print("🔧 연결 설정을 확인하고 다시 시도하세요.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n🚨 예상치 못한 오류: {e}")
        sys.exit(1)