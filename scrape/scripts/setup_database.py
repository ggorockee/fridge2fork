#!/usr/bin/env python3
"""
Phase 2 전체 데이터베이스 설정 스크립트

이 스크립트는 Phase 2의 모든 단계를 순차적으로 실행합니다:
1. 첫 번째 마이그레이션 생성
2. 마이그레이션 실행 (테이블 생성)
3. 기본 카테고리 데이터 삽입
4. 전문검색 마이그레이션 생성
5. 전문검색 마이그레이션 실행

Usage:
    python scripts/setup_database.py

Prerequisites:
    - DATABASE_URL이 .env 파일에 설정되어 있어야 함
    - PostgreSQL 서버가 실행 중이어야 함
"""
import asyncio
import subprocess
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

async def run_script(script_name, description):
    """스크립트 실행"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")

    script_path = project_root / "scripts" / script_name

    try:
        if script_name.endswith('.py'):
            result = subprocess.run([
                sys.executable, str(script_path)
            ], check=True, text=True, capture_output=True)
        else:
            result = subprocess.run([
                str(script_path)
            ], check=True, text=True, capture_output=True)

        print(result.stdout)
        if result.stderr:
            print(f"경고: {result.stderr}")

        print(f"✅ {description} 완료")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 실패: {e}")
        if e.stdout:
            print(f"출력: {e.stdout}")
        if e.stderr:
            print(f"에러: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

async def check_environment():
    """환경 확인"""
    print("🔧 환경 설정 확인 중...")

    # DATABASE_URL 확인
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        from dotenv import load_dotenv
        load_dotenv()
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL이 설정되지 않았습니다.")
        print("💡 .env 파일에 DATABASE_URL을 설정해주세요.")
        return False

    print(f"✅ DATABASE_URL 확인: {database_url.split('@')[0]}@***")

    # 필수 디렉토리 확인
    required_dirs = ["migrations", "app/models", "app/db"]
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            print(f"❌ 필수 디렉토리가 없습니다: {dir_path}")
            return False

    print("✅ 필수 디렉토리 확인 완료")
    return True

async def main():
    """메인 실행 함수"""
    print("🌟 Phase 2: 데이터베이스 스키마 구축 시작")
    print("=" * 60)

    # 환경 확인
    if not await check_environment():
        return 1

    # 실행할 스크립트 목록
    tasks = [
        ("create_initial_migration.py", "1. 첫 번째 마이그레이션 생성"),
        ("run_migration.py", "2. 마이그레이션 실행 (테이블 생성)"),
        ("insert_basic_data.py", "3. 기본 카테고리 데이터 삽입"),
        ("create_fulltext_migration.py", "4. 전문검색 마이그레이션 생성"),
        ("run_migration.py", "5. 전문검색 마이그레이션 실행"),
    ]

    success_count = 0
    total_count = len(tasks)

    for script_name, description in tasks:
        success = await run_script(script_name, description)
        if success:
            success_count += 1
        else:
            print(f"\n💥 {description} 단계에서 실패했습니다.")
            print("🛑 Phase 2 설정을 중단합니다.")
            break

    # 결과 요약
    print(f"\n{'='*60}")
    print("📊 Phase 2 실행 결과")
    print(f"{'='*60}")
    print(f"✅ 성공: {success_count}/{total_count}")
    print(f"❌ 실패: {total_count - success_count}/{total_count}")

    if success_count == total_count:
        print("\n🎉 Phase 2: 데이터베이스 스키마 구축이 완료되었습니다!")
        print("\n📋 완료된 작업:")
        print("  - Alembic 마이그레이션 환경 설정")
        print("  - 데이터베이스 테이블 생성 (recipes, ingredients, etc.)")
        print("  - 기본 카테고리 데이터 삽입 (8개 카테고리)")
        print("  - 전문검색 인덱스 생성 (GIN, 트라이그램)")
        print("  - 성능 최적화 인덱스 생성")
        print("\n🚀 이제 Phase 3: 로컬 데이터 마이그레이션을 진행할 수 있습니다.")
        return 0
    else:
        print("\n⚠️  일부 작업이 실패했습니다.")
        print("💡 실패한 단계를 개별적으로 다시 실행해보세요.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))