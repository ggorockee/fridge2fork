#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트
conda 환경 'fridge2fork'에서 실행
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
    print("🗃️  데이터베이스 마이그레이션을 시작합니다...")
    
    # conda 환경 확인
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env != 'fridge2fork':
        print(f"⚠️  현재 conda 환경: {conda_env}")
        print("❗ 'fridge2fork' conda 환경에서 실행해주세요:")
        print("   conda activate fridge2fork")
        return False
    
    print(f"✅ conda 환경 확인: {conda_env}")
    
    # 환경 설정
    env = os.environ.get('ENVIRONMENT', 'development')
    print(f"📋 환경: {env}")
    
    # 환경 파일 확인
    env_files = ['.env.common']
    if env == 'development':
        env_files.append('.env.dev')
    elif env == 'production':
        env_files.append('.env.prod')
    else:
        env_files.append('.env.dev')  # 기본값
    
    for env_file in env_files:
        if not os.path.exists(env_file):
            print(f"❌ 환경 파일 {env_file}이 없습니다.")
            return False
    
    print(f"✅ 환경 파일 확인: {', '.join(env_files)}")
    
    # 마이그레이션 파일이 없으면 초기 마이그레이션 생성
    if not os.listdir("alembic/versions"):
        print("\n📝 초기 마이그레이션 파일을 생성합니다...")
        if not run_command("alembic revision --autogenerate -m 'Initial migration'", "초기 마이그레이션 생성"):
            return False
    
    # 마이그레이션 실행
    if not run_command("alembic upgrade head", "데이터베이스 마이그레이션 적용"):
        return False
    
    print("\n✅ 데이터베이스 마이그레이션 완료!")
    print("\n📋 다음 단계:")
    print("1. 서버 시작: python main.py")
    print("2. 또는: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print("3. API 문서: http://localhost:8000/docs")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
