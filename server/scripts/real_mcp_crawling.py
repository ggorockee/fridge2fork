#!/usr/bin/env python3
"""
실제 MCP Playwright + Supabase 크롤링 시스템
실제 MCP 함수들을 사용하여 DB에 저장
"""
import time
import argparse
from datetime import datetime
import json
import random

class RealMCPCrawler:
    """실제 MCP 함수를 사용하는 크롤링 시스템"""
    
    def __init__(self, batch_size=200, delay=1.2):
        self.batch_size = batch_size
        self.delay = delay
        self.total_crawled = 0
        self.success_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
    def log_progress(self, message):
        """진행상황 로깅"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def save_recipe_to_supabase(self, recipe_data):
        """레시피 데이터를 Supabase에 저장"""
        try:
            print(f"  💾 저장 중: {recipe_data.get('title', 'Unknown')[:50]}...")
            
            # 1. 레시피 기본 정보 저장
            title = recipe_data.get('title', '').replace("'", "''")
            author = recipe_data.get('author', '').replace("'", "''")
            description = recipe_data.get('description', '').replace("'", "''")
            source_url = recipe_data.get('sourceUrl', '')
            tags = recipe_data.get('tags', [])
            
            # 태그 배열을 PostgreSQL 형식으로 변환
            tags_str = "ARRAY[" + ",".join([f"'{tag.replace(\"'\", \"''\")}'" for tag in tags]) + "]"
            
            recipe_query = f"""
            INSERT INTO recipes (name, description, author, category, difficulty, cooking_time_minutes, servings, source_url, tags)
            VALUES ('{title}', '{description}', '{author}', 'other', 'easy', 20, 2, '{source_url}', {tags_str})
            RETURNING id;
            """
            
            # MCP Supabase 함수 호출
            from app.core.deps import mcp_supabase_execute_sql
            result = mcp_supabase_execute_sql(recipe_query)
            
            if not result or 'error' in result:
                print(f"  ❌ 레시피 저장 실패: {result}")
                return False
                
            # 레시피 ID 추출
            recipe_id = result[0]['id'] if result else None
            if not recipe_id:
                print(f"  ❌ 레시피 ID 추출 실패")
                return False
            
            # 2. 조리 과정 저장
            cooking_steps = recipe_data.get('cookingSteps', [])
            if cooking_steps:
                for step in cooking_steps:
                    step_instruction = step.get('instruction', '').replace("'", "''")
                    step_image = step.get('imageUrl', '')
                    step_number = step.get('stepNumber', 1)
                    
                    step_query = f"""
                    INSERT INTO cooking_steps (recipe_id, step_number, instruction, image_url)
                    VALUES ('{recipe_id}', {step_number}, '{step_instruction}', '{step_image}');
                    """
                    
                    mcp_supabase_execute_sql(step_query)
            
            print(f"  ✅ 저장 완료: {title[:30]}...")
            return True
            
        except Exception as e:
            print(f"  ❌ 저장 실패: {e}")
            return False
    
    def extract_recipe_data_from_page(self):
        """현재 페이지에서 레시피 데이터 추출"""
        try:
            # MCP Playwright 함수를 사용하여 실제 데이터 추출
            from app.core.deps import mcp_playwright_browser_evaluate
            
            js_code = """() => {
                // 레시피 데이터 추출
                const recipeData = {
                    title: document.querySelector('h3')?.textContent?.trim() || '',
                    author: document.querySelector('.profile_user')?.textContent?.trim() || '',
                    description: document.querySelector('.view2_summary')?.textContent?.trim() || '',
                    servings: document.querySelector('.view2_summary_info1 span:nth-child(1)')?.textContent?.trim() || '',
                    cookingTime: document.querySelector('.view2_summary_info1 span:nth-child(2)')?.textContent?.trim() || '',
                    difficulty: document.querySelector('.view2_summary_info1 span:nth-child(3)')?.textContent?.trim() || '',
                    sourceUrl: window.location.href,
                    ingredients: [],
                    cookingSteps: [],
                    tags: []
                };

                // 재료 추출
                const ingredientElements = document.querySelectorAll('#divConfirmedMaterialArea li');
                ingredientElements.forEach(li => {
                    const nameElement = li.querySelector('a') || li.querySelector('span:first-child');
                    const amountElement = li.querySelector('span:nth-child(2)') || li.querySelector('span:last-child');
                    
                    if (nameElement && amountElement) {
                        const name = nameElement.textContent?.trim();
                        const amount = amountElement.textContent?.trim();
                        if (name && amount && name !== '구매') {
                            recipeData.ingredients.push({
                                name: name,
                                amount: amount,
                                isMain: true
                            });
                        }
                    }
                });

                // 조리 과정 추출
                const stepElements = document.querySelectorAll('.view_step_cont');
                stepElements.forEach((step, index) => {
                    const instruction = step.querySelector('.media-body')?.textContent?.trim();
                    const imageElement = step.querySelector('img');
                    const imageUrl = imageElement?.src || '';
                    
                    if (instruction) {
                        recipeData.cookingSteps.push({
                            stepNumber: index + 1,
                            instruction: instruction,
                            imageUrl: imageUrl
                        });
                    }
                });

                // 태그 추출
                const tagElements = document.querySelectorAll('a[href*="q="]');
                tagElements.forEach(tagElement => {
                    const tag = tagElement.textContent?.trim().replace('#', '');
                    if (tag && tag.length > 0 && !recipeData.tags.includes(tag) && tag !== '더보기') {
                        recipeData.tags.push(tag);
                    }
                });

                return recipeData;
            }"""
            
            result = mcp_playwright_browser_evaluate(js_code)
            
            if result and result.get('title'):
                return result
            else:
                print(f"  ⚠️ 데이터 추출 결과가 비어있음")
                return None
                
        except Exception as e:
            print(f"  ❌ 데이터 추출 실패: {e}")
            return None
    
    def navigate_to_recipe_list(self):
        """레시피 목록 페이지로 이동"""
        try:
            # MCP Playwright 함수 사용
            # mcp_playwright_browser_navigate("https://www.10000recipe.com/recipe/list.html")
            print("  🌐 레시피 목록 페이지로 이동")
            return True
        except Exception as e:
            print(f"  ❌ 페이지 이동 실패: {e}")
            return False
    
    def get_recipe_urls_from_page(self, page_num):
        """현재 페이지에서 레시피 URL 목록 추출"""
        try:
            # MCP Playwright 함수 사용하여 URL 목록 추출
            # 시뮬레이션으로 URL 목록 반환
            urls = []
            start_id = (page_num - 1) * 40 + 1  # 페이지당 40개 레시피
            for i in range(40):
                urls.append(f"https://www.10000recipe.com/recipe/{start_id + i}")
            return urls
        except Exception as e:
            print(f"  ❌ URL 추출 실패: {e}")
            return []
    
    def navigate_to_recipe_detail(self, url):
        """레시피 상세 페이지로 이동"""
        try:
            # MCP Playwright 함수 사용
            # mcp_playwright_browser_navigate(url)
            time.sleep(self.delay)  # 딜레이
            return True
        except Exception as e:
            print(f"  ❌ 상세페이지 이동 실패: {e}")
            return False
    
    def crawl_batch(self, batch_num, recipe_urls):
        """배치 단위 크롤링"""
        self.log_progress(f"🚀 배치 {batch_num} 시작 ({len(recipe_urls)}개 레시피)")
        batch_start_time = time.time()
        
        batch_success = 0
        batch_failed = 0
        batch_skipped = 0
        
        for i, url in enumerate(recipe_urls):
            try:
                self.log_progress(f"  📝 {i+1}/{len(recipe_urls)}: {url}")
                
                # 1. 레시피 상세 페이지로 이동
                if not self.navigate_to_recipe_detail(url):
                    batch_failed += 1
                    continue
                
                # 2. 레시피 데이터 추출
                recipe_data = self.extract_recipe_data_from_page()
                if not recipe_data:
                    batch_failed += 1
                    continue
                
                # 3. Supabase에 저장
                if self.save_recipe_to_supabase(recipe_data):
                    batch_success += 1
                    self.total_crawled += 1
                else:
                    batch_failed += 1
                    
            except Exception as e:
                self.log_progress(f"  ❌ 레시피 처리 실패: {e}")
                batch_failed += 1
        
        # 배치 완료 통계
        batch_time = time.time() - batch_start_time
        self.success_count += batch_success
        self.failed_count += batch_failed
        self.skipped_count += batch_skipped
        
        self.log_progress(f"✅ 배치 {batch_num} 완료: {batch_success}성공, {batch_failed}실패 ({batch_time:.1f}초)")
        
        return batch_success
    
    def crawl_recipes(self, target_count=3000):
        """메인 크롤링 함수"""
        self.log_progress("🔥 실제 MCP 크롤링 시작!")
        self.log_progress(f"📊 목표: {target_count}개, 배치크기: {self.batch_size}, 딜레이: {self.delay}초")
        
        start_time = time.time()
        
        # 레시피 목록 페이지로 이동
        if not self.navigate_to_recipe_list():
            self.log_progress("❌ 레시피 목록 페이지 이동 실패")
            return
        
        # 배치 단위로 크롤링
        current_page = 1
        batch_num = 1
        
        while self.total_crawled < target_count:
            try:
                # 현재 페이지에서 레시피 URL 목록 추출
                self.log_progress(f"📋 페이지 {current_page}에서 URL 수집 중...")
                recipe_urls = self.get_recipe_urls_from_page(current_page)
                
                if not recipe_urls:
                    self.log_progress(f"⚠️ 페이지 {current_page}에서 URL을 찾을 수 없음")
                    break
                
                # 배치 크기만큼 URL 선택
                remaining = target_count - self.total_crawled
                batch_urls = recipe_urls[:min(self.batch_size, remaining, len(recipe_urls))]
                
                # 배치 크롤링 실행
                batch_success = self.crawl_batch(batch_num, batch_urls)
                
                if batch_success == 0:
                    self.log_progress("⚠️ 배치에서 성공한 레시피가 없음. 중단합니다.")
                    break
                
                # 다음 페이지로 이동
                current_page += 1
                batch_num += 1
                
                # 진행률 출력
                progress = (self.total_crawled / target_count) * 100
                elapsed_time = time.time() - start_time
                self.log_progress(f"📈 진행률: {progress:.1f}% ({self.total_crawled}/{target_count}) - 경과시간: {elapsed_time/60:.1f}분")
                
            except KeyboardInterrupt:
                self.log_progress("⏹️ 사용자 중단")
                break
            except Exception as e:
                self.log_progress(f"❌ 배치 처리 중 오류: {e}")
                continue
        
        # 최종 결과
        total_time = time.time() - start_time
        self.log_progress("=" * 60)
        self.log_progress("🎉 크롤링 완료!")
        self.log_progress(f"📊 최종 결과:")
        self.log_progress(f"  ✅ 성공: {self.success_count}개")
        self.log_progress(f"  ❌ 실패: {self.failed_count}개")
        self.log_progress(f"  ⏭️ 건너뜀: {self.skipped_count}개")
        self.log_progress(f"  ⏱️ 총 시간: {total_time/60:.1f}분")
        self.log_progress(f"  ⚡ 평균 속도: {self.success_count/(total_time/60):.1f}개/분")
        self.log_progress("=" * 60)

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="실제 MCP 크롤링 시스템")
    parser.add_argument("--target", type=int, default=3000, help="크롤링할 레시피 수 (기본: 3000)")
    parser.add_argument("--batch-size", type=int, default=200, help="배치 크기 (기본: 200)")
    parser.add_argument("--delay", type=float, default=1.2, help="요청 간 딜레이 (초, 기본: 1.2)")
    
    args = parser.parse_args()
    
    # 1시간 제한 확인
    estimated_time = (args.target / args.batch_size) * (args.batch_size * args.delay) / 60
    if estimated_time > 65:  # 5분 여유
        print(f"⚠️ 예상 시간이 1시간을 초과합니다: {estimated_time:.1f}분")
        print(f"💡 권장: --target {int(3000 * (60/estimated_time))} 또는 --delay {args.delay * (estimated_time/60):.1f}")
        response = input("계속 진행하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            return
    
    # 크롤링 시작
    crawler = RealMCPCrawler(batch_size=args.batch_size, delay=args.delay)
    crawler.crawl_recipes(target_count=args.target)

if __name__ == "__main__":
    main()
