#!/usr/bin/env python3
"""
성능 최적화된 크롤링 실행 스크립트
"""
import asyncio
import argparse
import sys
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_performance_recommendations():
    """성능 최적화 권장사항 출력"""
    print("🚀 성능 최적화 크롤링 가이드")
    print("=" * 60)
    
    print("\n📊 단계별 크롤링 전략:")
    print("1️⃣  소규모 테스트    : 100개 레시피 (딜레이 1.0초)")
    print("2️⃣  중규모 테스트    : 1,000개 레시피 (딜레이 0.8초)")
    print("3️⃣  대규모 크롤링    : 5,000개 레시피 (딜레이 0.5초)")
    print("4️⃣  최대 규모 크롤링  : 10,000개 레시피 (딜레이 0.3초)")
    
    print("\n⚡ 성능 최적화 옵션:")
    print("• --fast-mode     : 빠른 크롤링 (딜레이 0.3초)")
    print("• --turbo-mode    : 터보 크롤링 (딜레이 0.1초)")
    print("• --safe-mode     : 안전 크롤링 (딜레이 2.0초)")
    print("• --batch-large   : 대용량 배치 (200개씩)")
    print("• --batch-small   : 소용량 배치 (25개씩)")
    
    print("\n🎯 추천 명령어:")
    print("# 🧪 테스트 크롤링")
    print("python scripts/optimized_crawling.py --test")
    print()
    print("# ⚡ 빠른 크롤링 (1,000개)")
    print("python scripts/optimized_crawling.py --fast --target 1000")
    print()
    print("# 🚀 터보 크롤링 (5,000개)")
    print("python scripts/optimized_crawling.py --turbo --target 5000")
    print()
    print("# 🛡️  안전 크롤링 (10,000개)")
    print("python scripts/optimized_crawling.py --safe --target 10000")
    print()
    print("# 🔥 최대 성능 크롤링")
    print("python scripts/optimized_crawling.py --turbo --batch-large --target 10000")

def get_optimized_config(mode: str):
    """최적화 모드별 설정 반환"""
    configs = {
        "test": {
            "target": 100,
            "delay": 1.5,
            "batch_size": 25,
            "description": "🧪 테스트 모드 - 안전한 소규모 테스트"
        },
        "safe": {
            "target": 1000,
            "delay": 2.0,
            "batch_size": 50,
            "description": "🛡️  안전 모드 - 서버 부하 최소화"
        },
        "normal": {
            "target": 2000,
            "delay": 1.0,
            "batch_size": 75,
            "description": "⚖️  일반 모드 - 균형잡힌 성능"
        },
        "fast": {
            "target": 5000,
            "delay": 0.5,
            "batch_size": 100,
            "description": "⚡ 빠른 모드 - 향상된 성능"
        },
        "turbo": {
            "target": 10000,
            "delay": 0.2,
            "batch_size": 150,
            "description": "🚀 터보 모드 - 최고 성능"
        },
        "extreme": {
            "target": 20000,
            "delay": 0.1,
            "batch_size": 200,
            "description": "🔥 익스트림 모드 - 최대 성능 (주의!)"
        }
    }
    
    return configs.get(mode, configs["normal"])

def estimate_time(target: int, delay: float, batch_size: int):
    """예상 소요 시간 계산"""
    # 페이지당 평균 레시피 수: 20개
    # URL 수집 시간: 페이지 수 × 딜레이
    # 상세 크롤링 시간: 레시피 수 × 딜레이
    # 배치 저장 시간: (레시피 수 / 배치 크기) × 2초
    
    pages_needed = target // 20 + 1
    url_collection_time = pages_needed * delay
    detail_crawling_time = target * delay
    batch_save_time = (target // batch_size) * 2
    
    total_seconds = url_collection_time + detail_crawling_time + batch_save_time
    
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    if hours > 0:
        return f"{hours}시간 {minutes}분 {seconds}초"
    elif minutes > 0:
        return f"{minutes}분 {seconds}초"
    else:
        return f"{seconds}초"

async def run_optimized_crawling(config: dict):
    """최적화된 크롤링 실행"""
    print(f"\n🚀 {config['description']}")
    print("=" * 60)
    print(f"📊 목표 레시피: {config['target']:,}개")
    print(f"⏱️  요청 딜레이: {config['delay']}초")
    print(f"📦 배치 크기: {config['batch_size']}개")
    
    estimated_time = estimate_time(config['target'], config['delay'], config['batch_size'])
    print(f"⏰ 예상 소요 시간: {estimated_time}")
    
    print(f"\n⚠️  주의사항:")
    if config['delay'] < 0.5:
        print("• 매우 빠른 크롤링으로 서버 부하 주의")
        print("• IP 차단 위험 - 모니터링 필수")
    if config['batch_size'] > 100:
        print("• 대용량 배치 처리 - 메모리 사용량 증가")
    
    # 사용자 확인
    print(f"\n계속 진행하시겠습니까? (y/N): ", end="")
    response = input().lower().strip()
    
    if response != 'y':
        print("❌ 크롤링이 취소되었습니다.")
        return
    
    print(f"\n🎬 크롤링 시작! ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 60)
    
    # 실제 크롤링 명령어 실행
    import subprocess
    
    cmd = [
        "python", "scripts/run_crawling.py",
        "--target", str(config['target']),
        "--batch-size", str(config['batch_size']),
        "--delay", str(config['delay'])
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode == 0:
            print("\n🎉 크롤링이 성공적으로 완료되었습니다!")
        else:
            print(f"\n❌ 크롤링 중 오류 발생 (종료 코드: {result.returncode})")
    except Exception as e:
        print(f"\n❌ 크롤링 실행 오류: {e}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="성능 최적화된 레시피 크롤링 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python scripts/optimized_crawling.py --help        # 도움말
  python scripts/optimized_crawling.py --guide       # 가이드 출력
  python scripts/optimized_crawling.py --test        # 테스트 크롤링
  python scripts/optimized_crawling.py --fast        # 빠른 크롤링
  python scripts/optimized_crawling.py --turbo       # 터보 크롤링
  python scripts/optimized_crawling.py --custom --target 3000 --delay 0.7
        """
    )
    
    # 모드 선택
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--guide", action="store_true", help="성능 최적화 가이드 출력")
    mode_group.add_argument("--test", action="store_true", help="테스트 모드 (100개, 안전)")
    mode_group.add_argument("--safe", action="store_true", help="안전 모드 (1,000개, 느림)")
    mode_group.add_argument("--normal", action="store_true", help="일반 모드 (2,000개, 보통)")
    mode_group.add_argument("--fast", action="store_true", help="빠른 모드 (5,000개, 빠름)")
    mode_group.add_argument("--turbo", action="store_true", help="터보 모드 (10,000개, 매우 빠름)")
    mode_group.add_argument("--extreme", action="store_true", help="익스트림 모드 (20,000개, 최대 성능)")
    mode_group.add_argument("--custom", action="store_true", help="커스텀 모드")
    
    # 커스텀 옵션
    parser.add_argument("--target", type=int, help="크롤링할 레시피 수")
    parser.add_argument("--delay", type=float, help="요청 간 딜레이 (초)")
    parser.add_argument("--batch-size", type=int, help="배치 크기")
    parser.add_argument("--batch-large", action="store_true", help="대용량 배치 (200개)")
    parser.add_argument("--batch-small", action="store_true", help="소용량 배치 (25개)")
    
    args = parser.parse_args()
    
    # 가이드 출력
    if args.guide:
        print_performance_recommendations()
        return
    
    # 모드 결정
    if args.test:
        mode = "test"
    elif args.safe:
        mode = "safe"
    elif args.normal:
        mode = "normal"
    elif args.fast:
        mode = "fast"
    elif args.turbo:
        mode = "turbo"
    elif args.extreme:
        mode = "extreme"
    elif args.custom:
        mode = "normal"  # 기본값으로 시작
    else:
        print_performance_recommendations()
        return
    
    # 설정 가져오기
    config = get_optimized_config(mode)
    
    # 커스텀 설정 적용
    if args.target:
        config["target"] = args.target
    if args.delay:
        config["delay"] = args.delay
    if args.batch_size:
        config["batch_size"] = args.batch_size
    elif args.batch_large:
        config["batch_size"] = 200
    elif args.batch_small:
        config["batch_size"] = 25
    
    # 크롤링 실행
    asyncio.run(run_optimized_crawling(config))

if __name__ == "__main__":
    main()

