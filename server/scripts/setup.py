#!/usr/bin/env python3
"""
Fridge2Fork API 설정 스크립트
conda 환경에서 실행하도록 설계됨
"""
import os
import subprocess
import sys


def run_command(command, description):
    """명령어 실행"""
    print(f"\n🔧 {description}")
    print(f"명령어: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 오류 발생: {e}")
        if e.stderr:
            print(f"오류 메시지: {e.stderr}")
        return False


def main():
    print("🍳 Fridge2Fork API 설정을 시작합니다...")
    print("📋 conda 환경 'fridge2fork'에서 실행되는지 확인해주세요.")
    
    # 현재 conda 환경 확인
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env != 'fridge2fork':
        print(f"⚠️  현재 conda 환경: {conda_env}")
        print("❗ 'fridge2fork' conda 환경에서 실행해주세요:")
        print("   conda activate fridge2fork")
        return False
    
    print(f"✅ conda 환경 확인: {conda_env}")
    
    # 의존성 설치
    env = os.environ.get('ENVIRONMENT', 'development')
    requirements_file = f"requirements.{env}.txt" if env in ['dev', 'prod'] else "requirements.dev.txt"
    
    if not run_command(f"pip install -r {requirements_file}", f"의존성 설치 ({requirements_file})"):
        return False
    
    # 환경 파일 확인
    env_file = f"env.{env}" if env in ['dev', 'prod'] else "env.dev"
    if not os.path.exists(env_file):
        print(f"⚠️  환경 파일 {env_file}이 없습니다.")
        print("env.dev 또는 env.prod 파일을 생성해주세요.")
        return False
    
    print(f"✅ 환경 파일 확인: {env_file}")
    
    # Alembic 초기화 (이미 있으면 스킵)
    if not os.path.exists("alembic/versions"):
        if not run_command("alembic init alembic", "Alembic 초기화"):
            return False
    
    print("\n✅ 설정 완료!")
    print("\n📋 다음 단계:")
    print("1. PostgreSQL 및 Redis 서버 시작")
    print("2. 데이터베이스 마이그레이션: python scripts/migrate.py")
    print("3. 서버 시작: python main.py")
    print("   또는: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
