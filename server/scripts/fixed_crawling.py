#!/usr/bin/env python3
"""
수정된 크롤링 시스템 - 실제 사용 가능한 버전
"""
import asyncio
import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.crawling.progressive_crawler import ProgressiveCrawler

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="스마트 크롤링 시스템 - 중복 없이 연속 크롤링")
    parser.add_argument("--target", type=int, default=100, help="크롤링할 레시피 수")
    parser.add_argument("--reset", action="store_true", help="진행 상태 초기화")
    parser.add_argument("--status", action="store_true", help="현재 진행 상태 확인")
    
    args = parser.parse_args()
    
    crawler = ProgressiveCrawler()
    
    if args.reset:
        crawler.reset_progress()
        print("🔄 진행 상태가 초기화되었습니다.")
        return
    
    if args.status:
        stats = crawler.get_crawling_stats()
        print("📊 현재 크롤링 진행 상태:")
        print(f"  • 현재 카테고리: {stats['current_category']}")
        print(f"  • 현재 페이지: {stats['current_page']}")
        print(f"  • 발견한 URL: {stats['total_urls_found']:,}개")
        print(f"  • 완료 카테고리: {stats['categories_completed']}개")
        print(f"  • 예상 남은 레시피: {stats['estimated_remaining']:,}개")
        return
    
    print("🧠 스마트 크롤링 시스템")
    print("=" * 50)
    print(f"🎯 목표: {args.target}개 레시피")
    
    # 현재 상태 확인
    stats = crawler.get_crawling_stats()
    print(f"📍 시작 위치: 카테고리 {stats['current_category']}, 페이지 {stats['current_page']}")
    
    # 새로운 URL 수집
    print(f"🔍 {args.target}개 새 URL 수집 중...")
    new_urls = crawler.get_next_urls_to_crawl(args.target)
    
    if not new_urls:
        print("❌ 더 이상 새로운 레시피를 찾을 수 없습니다.")
        print("💡 다른 카테고리나 사이트를 시도해보세요.")
        return
    
    print(f"✅ {len(new_urls)}개 새 URL 수집 완료!")
    
    # 실제 크롤링은 여기서 진행
    print("🚀 실제 크롤링을 시작하려면 다음 명령어를 사용하세요:")
    print(f"python scripts/massive_crawling.py --target {len(new_urls)}")
    
    # 최종 상태
    final_stats = crawler.get_crawling_stats()
    print(f"\n📈 업데이트된 진행 상태:")
    print(f"  • 현재 카테고리: {final_stats['current_category']}")
    print(f"  • 현재 페이지: {final_stats['current_page']}")
    print(f"  • 총 발견 URL: {final_stats['total_urls_found']:,}개")

if __name__ == "__main__":
    main()
