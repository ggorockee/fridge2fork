#!/usr/bin/env python3
"""
대량 레시피 크롤링 실행 스크립트
"""
import asyncio
import argparse
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawling.crawler import crawler
from crawling.config import CrawlingConfig

async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="만개의레시피 크롤링 시스템")
    parser.add_argument(
        "--target", 
        type=int, 
        default=CrawlingConfig.TOTAL_TARGET_RECIPES,
        help=f"크롤링할 레시피 수 (기본값: {CrawlingConfig.TOTAL_TARGET_RECIPES})"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=CrawlingConfig.BATCH_SIZE,
        help=f"배치 크기 (기본값: {CrawlingConfig.BATCH_SIZE})"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=CrawlingConfig.DELAY_BETWEEN_REQUESTS,
        help=f"요청 간 딜레이 (초, 기본값: {CrawlingConfig.DELAY_BETWEEN_REQUESTS})"
    )
    
    args = parser.parse_args()
    
    print("🍳 Fridge2Fork 레시피 크롤링 시스템")
    print("=" * 50)
    print(f"📊 목표 레시피 수: {args.target:,}개")
    print(f"📦 배치 크기: {args.batch_size}개")
    print(f"⏱️  요청 딜레이: {args.delay}초")
    print("=" * 50)
    
    # 설정 업데이트
    crawler.config.TOTAL_TARGET_RECIPES = args.target
    crawler.config.BATCH_SIZE = args.batch_size
    crawler.config.DELAY_BETWEEN_REQUESTS = args.delay
    
    try:
        # 크롤링 시작
        results = await crawler.crawl_recipes(args.target)
        
        print("\n🎉 크롤링 완료!")
        print("=" * 50)
        print(f"✅ 성공적으로 저장된 레시피: {results['success']:,}개")
        print(f"❌ 실패한 레시피: {results['failed']:,}개") 
        print(f"⏭️  건너뛴 레시피: {results['skipped']:,}개")
        print(f"📊 총 처리된 레시피: {results['total_crawled']:,}개")
        
        # 성공률 계산
        if results['total_crawled'] > 0:
            success_rate = (results['success'] / results['total_crawled']) * 100
            print(f"📈 성공률: {success_rate:.1f}%")
        
        print("=" * 50)
        
        # 최종 데이터베이스 통계
        stats = await crawler.storage.get_crawling_stats()
        if stats:
            print("\n📊 데이터베이스 현황:")
            print(f"  • 총 레시피: {stats.get('total_recipes', 0):,}개")
            print(f"  • 총 재료: {stats.get('total_ingredients', 0):,}개")
            
            category_breakdown = stats.get('category_breakdown', {})
            if category_breakdown:
                print("  • 카테고리별 분포:")
                for category, count in category_breakdown.items():
                    print(f"    - {category}: {count:,}개")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자가 크롤링을 중단했습니다.")
        return 1
    except Exception as e:
        print(f"\n❌ 크롤링 중 오류 발생: {e}")
        return 1

if __name__ == "__main__":
    # 비동기 실행
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


