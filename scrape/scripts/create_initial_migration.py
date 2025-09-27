#!/usr/bin/env python3
"""
첫 번째 마이그레이션 생성 스크립트

Usage:
    python scripts/create_initial_migration.py

Prerequisites:
    - DATABASE_URL이 .env 파일에 설정되어 있어야 함
    - PostgreSQL 서버가 실행 중이어야 함
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """첫 번째 마이그레이션 생성"""
    # 프로젝트 루트로 이동
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("🔄 첫 번째 마이그레이션 생성 중...")

    try:
        # Alembic autogenerate 실행
        result = subprocess.run([
            sys.executable, "-m", "alembic", "revision",
            "--autogenerate", "-m", "Create initial tables"
        ], capture_output=True, text=True, check=True)

        print("✅ 마이그레이션 파일 생성 완료")
        print(f"출력: {result.stdout}")

        # 생성된 마이그레이션 파일 확인
        versions_dir = project_root / "migrations" / "versions"
        migration_files = list(versions_dir.glob("*.py"))

        if migration_files:
            latest_migration = max(migration_files, key=lambda p: p.stat().st_mtime)
            print(f"📄 생성된 마이그레이션 파일: {latest_migration.name}")

    except subprocess.CalledProcessError as e:
        print(f"❌ 마이그레이션 생성 실패: {e}")
        print(f"에러 출력: {e.stderr}")
        return 1
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())