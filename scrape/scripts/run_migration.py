#!/usr/bin/env python3
"""
마이그레이션 실행 스크립트

Usage:
    python scripts/run_migration.py

Prerequisites:
    - DATABASE_URL이 .env 파일에 설정되어 있어야 함
    - PostgreSQL 서버가 실행 중이어야 함
    - 마이그레이션 파일이 migrations/versions/ 디렉토리에 있어야 함
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """마이그레이션을 데이터베이스에 실행"""
    # 프로젝트 루트로 이동
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("🔄 마이그레이션 실행 중...")

    try:
        # 현재 마이그레이션 상태 확인
        print("📊 현재 마이그레이션 상태:")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "current"
        ], capture_output=True, text=True)
        print(f"현재 리비전: {result.stdout.strip() or '(없음)'}")

        # 마이그레이션 실행
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True, check=True)

        print("✅ 마이그레이션 실행 완료")
        print(f"출력: {result.stdout}")

        # 마이그레이션 후 상태 확인
        print("\n📊 마이그레이션 후 상태:")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "current"
        ], capture_output=True, text=True)
        print(f"현재 리비전: {result.stdout.strip()}")

        # 마이그레이션 히스토리 출력
        print("\n📚 마이그레이션 히스토리:")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "history"
        ], capture_output=True, text=True)
        print(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"❌ 마이그레이션 실행 실패: {e}")
        print(f"에러 출력: {e.stderr}")
        return 1
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())