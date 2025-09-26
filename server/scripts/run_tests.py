#!/usr/bin/env python3
"""
테스트 실행 스크립트
conda 환경 'fridge2fork'에서 실행
"""
import os
import sys
import subprocess
import argparse


def run_command(command, description):
    """명령어 실행"""
    print(f"\n🧪 {description}")
    print(f"명령어: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 오류 발생: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Fridge2Fork API 테스트 실행")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "all"], 
        default="all",
        help="실행할 테스트 타입"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="커버리지 리포트 생성"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세한 출력"
    )
    parser.add_argument(
        "--file",
        help="특정 테스트 파일만 실행"
    )
    parser.add_argument(
        "--function",
        help="특정 테스트 함수만 실행"
    )
    
    args = parser.parse_args()
    
    print("🧪 Fridge2Fork API 테스트를 시작합니다...")
    
    # conda 환경 확인
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env != 'fridge2fork':
        print(f"⚠️  현재 conda 환경: {conda_env}")
        print("❗ 'fridge2fork' conda 환경에서 실행해주세요:")
        print("   conda activate fridge2fork")
        return False
    
    print(f"✅ conda 환경 확인: {conda_env}")
    
    # 환경 변수 설정
    os.environ['ENVIRONMENT'] = 'test'
    
    # 테스트 명령어 구성
    cmd_parts = ["python", "-m", "pytest"]
    
    # 상세 출력
    if args.verbose:
        cmd_parts.append("-v")
    
    # 커버리지
    if args.coverage:
        cmd_parts.extend([
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    # 테스트 타입별 필터링
    if args.type == "unit":
        cmd_parts.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd_parts.extend(["-m", "integration"])
    
    # 특정 파일 또는 함수
    if args.file:
        if args.function:
            cmd_parts.append(f"{args.file}::{args.function}")
        else:
            cmd_parts.append(args.file)
    elif args.function:
        cmd_parts.extend(["-k", args.function])
    
    # 테스트 실행
    command = " ".join(cmd_parts)
    
    print(f"\n🚀 테스트 실행 중...")
    print(f"명령어: {command}")
    
    try:
        result = subprocess.run(command, shell=True)
        
        if result.returncode == 0:
            print("\n✅ 모든 테스트가 성공했습니다!")
            
            if args.coverage:
                print("\n📊 커버리지 리포트:")
                print("   - 터미널: 위 출력 참조")
                print("   - HTML: htmlcov/index.html")
        else:
            print(f"\n❌ 일부 테스트가 실패했습니다. (종료 코드: {result.returncode})")
            
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  테스트가 중단되었습니다.")
        return False
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
