#!/usr/bin/env python3
"""
운영 서버 실행 스크립트
conda 환경 'fridge2fork'에서 실행
"""
import os
import sys
import subprocess


def main():
    print("🚀 Fridge2Fork API 운영 서버를 시작합니다...")
    
    # conda 환경 확인
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env != 'fridge2fork':
        print(f"⚠️  현재 conda 환경: {conda_env}")
        print("❗ 'fridge2fork' conda 환경에서 실행해주세요:")
        print("   conda activate fridge2fork")
        return False
    
    print(f"✅ conda 환경 확인: {conda_env}")
    
    # 환경 변수 설정
    os.environ['ENVIRONMENT'] = 'production'
    
    # 환경 파일 확인
    required_files = ['.env.common', '.env.prod']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 환경 파일 {file}이 없습니다.")
            return False
    
    print("✅ 환경 파일 확인 완료")
    
    # 서버 시작 (Gunicorn 사용)
    print("\n🌟 운영 서버 시작 중...")
    print("📡 주소: http://0.0.0.0:8000")
    print("🔧 Ctrl+C로 종료")
    
    try:
        subprocess.run([
            "gunicorn", "main:app",
            "-w", "4",  # 워커 프로세스 수
            "-k", "uvicorn.workers.UvicornWorker",
            "--bind", "0.0.0.0:8000",
            "--log-level", "info",
            "--access-logfile", "-",
            "--error-logfile", "-"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 서버가 종료되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 서버 시작 오류: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
