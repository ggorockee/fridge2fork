#!/usr/bin/env python3
"""
테스트 커버리지 분석 및 리포트 생성 스크립트
"""
import os
import sys
import subprocess
import webbrowser
from pathlib import Path


def run_command(command, description):
    """명령어 실행"""
    print(f"\n📊 {description}")
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
    print("📊 Fridge2Fork API 테스트 커버리지 분석을 시작합니다...")
    
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
    
    # 기존 커버리지 데이터 삭제
    coverage_files = ['.coverage', 'htmlcov']
    for file in coverage_files:
        if os.path.exists(file):
            if os.path.isdir(file):
                import shutil
                shutil.rmtree(file)
            else:
                os.remove(file)
    
    # 테스트 실행 (커버리지 포함)
    if not run_command(
        "python -m pytest --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-fail-under=70",
        "테스트 실행 및 커버리지 측정"
    ):
        print("❌ 테스트 실행 중 오류가 발생했습니다.")
        return False
    
    # HTML 리포트 생성 확인
    html_report_path = Path("htmlcov/index.html")
    if html_report_path.exists():
        print(f"\n✅ HTML 커버리지 리포트 생성 완료: {html_report_path.absolute()}")
        
        # 브라우저에서 리포트 열기 (선택사항)
        try:
            user_input = input("\n🌐 브라우저에서 커버리지 리포트를 열까요? (y/N): ")
            if user_input.lower() in ['y', 'yes']:
                webbrowser.open(f"file://{html_report_path.absolute()}")
                print("📖 브라우저에서 커버리지 리포트를 열었습니다.")
        except KeyboardInterrupt:
            print("\n취소되었습니다.")
    
    # XML 리포트 생성 확인 (CI/CD용)
    xml_report_path = Path("coverage.xml")
    if xml_report_path.exists():
        print(f"✅ XML 커버리지 리포트 생성 완료: {xml_report_path.absolute()}")
    
    # 커버리지 요약 정보 표시
    print("\n📋 커버리지 분석 완료!")
    print("📁 생성된 파일:")
    print("   - htmlcov/index.html: 상세 HTML 리포트")
    print("   - coverage.xml: CI/CD용 XML 리포트")
    print("   - .coverage: 커버리지 데이터베이스")
    
    print("\n💡 커버리지 개선 팁:")
    print("   1. 빨간색으로 표시된 라인은 테스트되지 않은 코드입니다")
    print("   2. 새로운 기능 추가 시 반드시 테스트 케이스도 함께 작성하세요")
    print("   3. 목표 커버리지: 80% 이상")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
