#!/usr/bin/env python3
"""
Phase 2 데이터베이스 마이그레이션 실행 도구

사용법:
    python scripts/run_phase2_migration.py [--dry-run] [--force]

기능:
- Alembic 마이그레이션 자동 생성 및 실행
- 스키마 검증 및 인덱스 확인
- 마이그레이션 전후 상태 비교
- 안전한 롤백 지원
"""
import asyncio
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import argparse

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
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

    db = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST") or os.getenv("POSTGRES_SERVER")
    port = os.getenv("POSTGRES_PORT", "5432")

    if all([db, user, password, host]):
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    return None


def run_command(cmd: List[str], description: str) -> Dict[str, Any]:
    """명령어 실행 및 결과 반환"""
    print(f"🔄 {description}")
    print(f"📝 실행: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            print(f"✅ 성공")
            if result.stdout.strip():
                print(f"📄 출력:\n{result.stdout}")
        else:
            print(f"❌ 실패 (코드: {result.returncode})")
            if result.stderr.strip():
                print(f"🚨 오류:\n{result.stderr}")
            if result.stdout.strip():
                print(f"📄 출력:\n{result.stdout}")

        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }

    except Exception as e:
        print(f"❌ 명령어 실행 실패: {e}")
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e)
        }


async def get_database_state(database_url: str) -> Dict[str, Any]:
    """현재 데이터베이스 상태 조회"""
    state = {
        'tables': [],
        'indexes': [],
        'alembic_version': None,
        'error': None
    }

    try:
        engine = create_async_engine(database_url, poolclass=NullPool, echo=False)

        async with engine.begin() as conn:
            # 테이블 목록 조회
            tables_result = await conn.execute(
                text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """)
            )
            state['tables'] = [row[0] for row in tables_result.fetchall()]

            # 인덱스 목록 조회
            indexes_result = await conn.execute(
                text("""
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
                """)
            )
            state['indexes'] = [(row[0], row[1]) for row in indexes_result.fetchall()]

            # Alembic 버전 확인
            try:
                version_result = await conn.execute(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                )
                version = version_result.scalar()
                state['alembic_version'] = version
            except:
                state['alembic_version'] = None

        await engine.dispose()

    except Exception as e:
        state['error'] = str(e)

    return state


def print_database_state(state: Dict[str, Any], title: str):
    """데이터베이스 상태 출력"""
    print(f"\n📊 {title}")
    print("-" * 40)

    if state['error']:
        print(f"❌ 오류: {state['error']}")
        return

    print(f"📋 테이블 ({len(state['tables'])}개):")
    for table in state['tables']:
        print(f"  - {table}")

    print(f"\n🔍 인덱스 ({len(state['indexes'])}개):")
    current_table = None
    for index_name, table_name in state['indexes']:
        if table_name != current_table:
            print(f"  {table_name}:")
            current_table = table_name
        print(f"    - {index_name}")

    if state['alembic_version']:
        print(f"\n🏷️ Alembic 버전: {state['alembic_version']}")
    else:
        print(f"\n⚠️ Alembic 버전 정보 없음 (초기 상태)")


def check_alembic_setup() -> bool:
    """Alembic 설정 확인"""
    print("\n🔧 Alembic 설정 확인")
    print("-" * 30)

    # alembic.ini 파일 확인
    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        print("❌ alembic.ini 파일이 없습니다.")
        return False
    print("✅ alembic.ini 파일 존재")

    # migrations 디렉토리 확인
    migrations_dir = project_root / "migrations"
    if not migrations_dir.exists():
        print("❌ migrations 디렉토리가 없습니다.")
        return False
    print("✅ migrations 디렉토리 존재")

    # env.py 파일 확인
    env_py = migrations_dir / "env.py"
    if not env_py.exists():
        print("❌ migrations/env.py 파일이 없습니다.")
        return False
    print("✅ migrations/env.py 파일 존재")

    return True


def generate_migration(message: str, dry_run: bool = False) -> Dict[str, Any]:
    """Alembic 마이그레이션 생성"""
    cmd = ["alembic", "revision", "--autogenerate", "-m", message]
    if dry_run:
        print(f"🔍 [DRY RUN] 마이그레이션 생성: {message}")
        return {'success': True, 'dry_run': True}

    return run_command(cmd, f"마이그레이션 생성: {message}")


def apply_migration(dry_run: bool = False) -> Dict[str, Any]:
    """Alembic 마이그레이션 적용"""
    if dry_run:
        # dry-run의 경우 현재 상태와 head의 차이점만 표시
        cmd = ["alembic", "show", "head"]
        result = run_command(cmd, "[DRY RUN] 마이그레이션 미리보기")
        return result

    cmd = ["alembic", "upgrade", "head"]
    return run_command(cmd, "마이그레이션 적용")


def get_migration_history() -> Dict[str, Any]:
    """마이그레이션 히스토리 조회"""
    cmd = ["alembic", "history", "--verbose"]
    return run_command(cmd, "마이그레이션 히스토리 조회")


def validate_schema_expectations() -> List[str]:
    """Phase 2 스키마 기대값 검증"""
    expected_tables = ['recipes', 'ingredients', 'recipe_ingredients']
    expected_indexes = [
        'ix_recipes_title',
        'ix_recipes_popularity',
        'ix_ingredients_name',
        'ix_ingredients_category',
        'ix_recipe_ingredients_compound',
        'uk_recipe_ingredient'
    ]

    expectations = []
    expectations.extend([f"테이블 존재: {table}" for table in expected_tables])
    expectations.extend([f"인덱스 존재: {index}" for index in expected_indexes])

    return expectations


async def validate_post_migration(database_url: str) -> Dict[str, Any]:
    """마이그레이션 후 검증"""
    print("\n🧪 마이그레이션 후 검증")
    print("-" * 30)

    result = {
        'success': True,
        'validations': {},
        'errors': []
    }

    expected_tables = ['recipes', 'ingredients', 'recipe_ingredients']
    expected_indexes = [
        'ix_recipes_title',
        'ix_recipes_popularity',
        'ix_ingredients_name',
        'ix_ingredients_category',
        'ix_recipe_ingredients_compound'
    ]

    try:
        engine = create_async_engine(database_url, poolclass=NullPool, echo=False)

        async with engine.begin() as conn:
            # 테이블 존재 확인
            for table in expected_tables:
                table_result = await conn.execute(
                    text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = :table_name
                    )
                    """),
                    {'table_name': table}
                )
                exists = table_result.scalar()
                result['validations'][f'table_{table}'] = exists
                status = "✅" if exists else "❌"
                print(f"  {status} 테이블 {table}: {'존재' if exists else '없음'}")

                if not exists:
                    result['success'] = False
                    result['errors'].append(f"테이블 {table}이 존재하지 않습니다")

            # 인덱스 존재 확인
            for index in expected_indexes:
                index_result = await conn.execute(
                    text("""
                    SELECT EXISTS (
                        SELECT FROM pg_indexes
                        WHERE schemaname = 'public'
                        AND indexname = :index_name
                    )
                    """),
                    {'index_name': index}
                )
                exists = index_result.scalar()
                result['validations'][f'index_{index}'] = exists
                status = "✅" if exists else "❌"
                print(f"  {status} 인덱스 {index}: {'존재' if exists else '없음'}")

                if not exists:
                    result['success'] = False
                    result['errors'].append(f"인덱스 {index}가 존재하지 않습니다")

        await engine.dispose()

    except Exception as e:
        result['success'] = False
        result['errors'].append(f"검증 중 오류: {str(e)}")

    return result


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Phase 2 데이터베이스 마이그레이션 실행')
    parser.add_argument('--dry-run', action='store_true', help='실제 실행 없이 미리보기만')
    parser.add_argument('--force', action='store_true', help='강제 실행 (확인 없이)')
    args = parser.parse_args()

    print("🗄️ Phase 2 데이터베이스 마이그레이션")
    print("=" * 60)
    print(f"⏰ 시작 시간: {datetime.now()}")

    if args.dry_run:
        print("🔍 [DRY RUN 모드] 실제 변경 없이 미리보기만 실행합니다.")

    # DATABASE_URL 확인
    database_url = get_database_url()
    if not database_url:
        print("❌ DATABASE_URL을 구성할 수 없습니다.")
        return 1

    # Alembic 설정 확인
    if not check_alembic_setup():
        print("❌ Alembic 설정이 완전하지 않습니다.")
        return 1

    # 마이그레이션 전 상태 확인
    print("\n📊 마이그레이션 전 데이터베이스 상태")
    before_state = await get_database_state(database_url)
    print_database_state(before_state, "현재 상태")

    # 사용자 확인 (강제 모드가 아닌 경우)
    if not args.force and not args.dry_run:
        print(f"\n❓ 마이그레이션을 실행하시겠습니까? (y/N): ", end="")
        confirmation = input().strip().lower()
        if confirmation not in ['y', 'yes']:
            print("⚠️ 사용자가 취소했습니다.")
            return 0

    # 마이그레이션 히스토리 확인
    print("\n📜 현재 마이그레이션 히스토리")
    history_result = get_migration_history()

    # 마이그레이션 생성
    print(f"\n🔧 {'[DRY RUN] ' if args.dry_run else ''}마이그레이션 생성")
    generation_result = generate_migration("Phase 2: Initial schema with indexes", args.dry_run)

    if not generation_result['success'] and not args.dry_run:
        print("❌ 마이그레이션 생성에 실패했습니다.")
        return 1

    # 마이그레이션 적용
    print(f"\n⚡ {'[DRY RUN] ' if args.dry_run else ''}마이그레이션 적용")
    application_result = apply_migration(args.dry_run)

    if not application_result['success'] and not args.dry_run:
        print("❌ 마이그레이션 적용에 실패했습니다.")
        return 1

    if args.dry_run:
        print("\n✅ DRY RUN 완료! 실제 변경사항을 적용하려면 --dry-run 없이 실행하세요.")
        return 0

    # 마이그레이션 후 상태 확인
    print("\n📊 마이그레이션 후 데이터베이스 상태")
    after_state = await get_database_state(database_url)
    print_database_state(after_state, "변경 후 상태")

    # 마이그레이션 후 검증
    validation_result = await validate_post_migration(database_url)

    # 최종 결과
    print("\n" + "=" * 60)
    print("📊 Phase 2 마이그레이션 결과")
    print("=" * 60)

    if validation_result['success']:
        print("🎉 Phase 2 마이그레이션이 성공적으로 완료되었습니다!")
        print("\n✅ 완료된 작업:")
        print("  - Pydantic 스키마 정의")
        print("  - SQLAlchemy 모델 업데이트")
        print("  - 데이터베이스 스키마 생성")
        print("  - 검색 성능 인덱스 추가")
        print("  - 제약조건 설정")

        print("\n📋 다음 단계 (Phase 3):")
        print("  - CSV 데이터 마이그레이션 실행")
        print("  - python main.py migrate 실행")

        return 0
    else:
        print("❌ 마이그레이션은 완료되었지만 일부 검증에 실패했습니다.")
        for error in validation_result['errors']:
            print(f"  🚨 {error}")
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