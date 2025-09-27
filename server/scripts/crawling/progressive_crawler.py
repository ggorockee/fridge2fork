#!/usr/bin/env python3
"""
진행형 크롤러 - 페이지 진행 상태를 저장하여 중복 없이 새로운 레시피 수집
"""
import json
import os
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

class ProgressiveCrawler:
    """진행형 크롤러 - 페이지 상태 저장"""
    
    def __init__(self):
        self.progress_file = "crawling_progress.json"
        self.crawled_urls_file = "crawled_urls.json"
        self.logger = logging.getLogger(__name__)
        
        # 진행 상태 로드
        self.progress = self.load_progress()
        self.crawled_urls = self.load_crawled_urls()
    
    def load_progress(self) -> Dict:
        """크롤링 진행 상태 로드"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"진행 상태 로드 오류: {e}")
        
        return {
            "current_category": 0,
            "current_page": 1,
            "total_crawled": 0,
            "categories_completed": [],
            "last_update": datetime.now().isoformat()
        }
    
    def save_progress(self):
        """크롤링 진행 상태 저장"""
        try:
            self.progress["last_update"] = datetime.now().isoformat()
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"진행 상태 저장 오류: {e}")
    
    def load_crawled_urls(self) -> set:
        """이미 크롤링한 URL 목록 로드"""
        if os.path.exists(self.crawled_urls_file):
            try:
                with open(self.crawled_urls_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except Exception as e:
                print(f"URL 목록 로드 오류: {e}")
        return set()
    
    def save_crawled_urls(self):
        """크롤링한 URL 목록 저장"""
        try:
            with open(self.crawled_urls_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.crawled_urls), f, indent=2)
        except Exception as e:
            print(f"URL 목록 저장 오류: {e}")
    
    def get_next_urls_to_crawl(self, target_count: int) -> List[str]:
        """다음에 크롤링할 URL 목록 반환"""
        categories = [
            "", "1", "2", "3", "4", "5", "6", "7", "8", "9", 
            "10", "11", "12", "13", "14", "15", "16", "17"
        ]
        
        new_urls = []
        current_category_idx = self.progress["current_category"]
        current_page = self.progress["current_page"]
        
        print(f"📍 현재 위치: 카테고리 {current_category_idx}, 페이지 {current_page}")
        print(f"🎯 목표: {target_count}개 새 URL")
        
        while len(new_urls) < target_count and current_category_idx < len(categories):
            category = categories[current_category_idx]
            
            print(f"🔍 카테고리 '{category}' 페이지 {current_page} 탐색 중...")
            
            # 현재 페이지의 URL 수집 (시뮬레이션)
            page_urls = self.simulate_get_page_urls(category, current_page)
            
            if not page_urls:
                print(f"❌ 카테고리 '{category}' 완료 - 다음 카테고리로")
                self.progress["categories_completed"].append(category)
                current_category_idx += 1
                current_page = 1
                continue
            
            # 새로운 URL만 필터링
            fresh_urls = [url for url in page_urls if url not in self.crawled_urls]
            
            if not fresh_urls:
                print(f"⏭️ 페이지 {current_page} - 모두 크롤링됨, 다음 페이지로")
                current_page += 1
                
                # 페이지가 너무 많으면 다음 카테고리로
                if current_page > 100:
                    print(f"📄 카테고리 '{category}' 최대 페이지 도달 - 다음 카테고리로")
                    self.progress["categories_completed"].append(category)
                    current_category_idx += 1
                    current_page = 1
                continue
            
            # 새 URL 추가
            needed = min(len(fresh_urls), target_count - len(new_urls))
            selected_urls = fresh_urls[:needed]
            
            new_urls.extend(selected_urls)
            self.crawled_urls.update(selected_urls)
            
            print(f"✅ 페이지 {current_page}: {len(selected_urls)}개 새 URL 추가 (총 {len(new_urls)}개)")
            
            # 다음 페이지로
            current_page += 1
        
        # 진행 상태 업데이트
        self.progress["current_category"] = current_category_idx
        self.progress["current_page"] = current_page
        self.progress["total_crawled"] += len(new_urls)
        
        # 상태 저장
        self.save_progress()
        self.save_crawled_urls()
        
        print(f"🎉 총 {len(new_urls)}개 새 URL 준비 완료!")
        return new_urls
    
    def simulate_get_page_urls(self, category: str, page: int) -> List[str]:
        """페이지에서 URL 수집 시뮬레이션"""
        # 실제로는 MCP Playwright로 페이지 접속하여 URL 수집
        # 여기서는 시뮬레이션
        
        # 각 페이지당 약 20개 레시피가 있다고 가정
        base_id = (int(category) if category.isdigit() else 0) * 10000 + page * 20
        
        urls = []
        for i in range(20):
            recipe_id = base_id + i
            url = f"https://www.10000recipe.com/recipe/{recipe_id}"
            urls.append(url)
        
        # 일부 카테고리는 페이지가 적을 수 있음
        if page > 50 and category in ["14", "15", "16", "17"]:
            return []  # 마지막 카테고리들은 페이지가 적음
        
        return urls
    
    def get_crawling_stats(self) -> Dict:
        """크롤링 통계 반환"""
        return {
            "current_category": self.progress["current_category"],
            "current_page": self.progress["current_page"],
            "total_urls_found": len(self.crawled_urls),
            "categories_completed": len(self.progress["categories_completed"]),
            "estimated_remaining": max(0, 200000 - len(self.crawled_urls))
        }
    
    def reset_progress(self):
        """진행 상태 초기화"""
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        if os.path.exists(self.crawled_urls_file):
            os.remove(self.crawled_urls_file)
        
        self.progress = self.load_progress()
        self.crawled_urls = set()
        
        print("🔄 진행 상태 초기화 완료")

def main():
    """테스트 실행"""
    crawler = ProgressiveCrawler()
    
    print("🧪 진행형 크롤러 테스트")
    print("=" * 50)
    
    # 현재 상태
    stats = crawler.get_crawling_stats()
    print(f"📊 현재 상태:")
    print(f"  • 현재 카테고리: {stats['current_category']}")
    print(f"  • 현재 페이지: {stats['current_page']}")
    print(f"  • 발견한 URL: {stats['total_urls_found']:,}개")
    print(f"  • 완료 카테고리: {stats['categories_completed']}개")
    print()
    
    # 1차 크롤링 시뮬레이션
    print("1️⃣ 첫 번째 100개 URL 수집:")
    urls1 = crawler.get_next_urls_to_crawl(100)
    print(f"결과: {len(urls1)}개 URL")
    print()
    
    # 2차 크롤링 시뮬레이션
    print("2️⃣ 두 번째 100개 URL 수집:")
    urls2 = crawler.get_next_urls_to_crawl(100)
    print(f"결과: {len(urls2)}개 URL")
    print()
    
    # 3차 크롤링 시뮬레이션
    print("3️⃣ 세 번째 100개 URL 수집:")
    urls3 = crawler.get_next_urls_to_crawl(100)
    print(f"결과: {len(urls3)}개 URL")
    print()
    
    # 중복 확인
    all_urls = set(urls1 + urls2 + urls3)
    print(f"🔍 중복 확인:")
    print(f"  • 1차: {len(urls1)}개")
    print(f"  • 2차: {len(urls2)}개") 
    print(f"  • 3차: {len(urls3)}개")
    print(f"  • 총합: {len(urls1) + len(urls2) + len(urls3)}개")
    print(f"  • 고유: {len(all_urls)}개")
    print(f"  • 중복: {len(urls1) + len(urls2) + len(urls3) - len(all_urls)}개")
    
    if len(all_urls) == len(urls1) + len(urls2) + len(urls3):
        print("✅ 완벽! 중복 없이 새로운 URL만 수집됨!")
    else:
        print("❌ 중복 발생")

if __name__ == "__main__":
    main()


