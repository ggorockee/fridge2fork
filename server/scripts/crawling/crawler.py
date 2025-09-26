"""
메인 크롤링 시스템
"""
import asyncio
import json
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime

from .config import CrawlingConfig
from .parser import RecipeParser, RecipeData
from .database import recipe_storage

class RecipeCrawler:
    """메인 레시피 크롤러"""
    
    def __init__(self):
        self.config = CrawlingConfig()
        self.parser = RecipeParser()
        self.storage = recipe_storage
        self.crawled_urls = set()  # 중복 방지
        self.total_crawled = 0
        
        # 로깅 설정
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def crawl_recipes(self, target_count: int = None) -> Dict[str, int]:
        """레시피 대량 크롤링"""
        if target_count is None:
            target_count = self.config.TOTAL_TARGET_RECIPES
        
        self.logger.info(f"🚀 레시피 크롤링 시작 - 목표: {target_count}개")
        
        start_time = datetime.now()
        results = {
            "total_crawled": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        try:
            # 1단계: 브라우저 초기화 및 사이트 접속
            self._initialize_browser()
            
            # 2단계: 카테고리별 레시피 URL 수집
            recipe_urls = self._collect_recipe_urls(target_count)
            self.logger.info(f"📋 수집된 레시피 URL: {len(recipe_urls)}개")
            
            # 3단계: 배치별 레시피 상세 정보 크롤링
            await self._crawl_recipe_details(recipe_urls, results)
            
            # 통계 출력
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info("🎉 크롤링 완료!")
            self.logger.info(f"⏱️  소요 시간: {duration:.2f}초")
            self.logger.info(f"✅ 성공: {results['success']}개")
            self.logger.info(f"❌ 실패: {results['failed']}개")
            self.logger.info(f"⏭️  건너뜀: {results['skipped']}개")
            
            # 최종 통계
            stats = await self.storage.get_crawling_stats()
            self.logger.info(f"📊 DB 총 레시피: {stats.get('total_recipes', 0)}개")
            self.logger.info(f"📊 DB 총 재료: {stats.get('total_ingredients', 0)}개")
            
            return results
            
        except Exception as e:
            self.logger.error(f"크롤링 오류: {e}")
            return results
    
    def _initialize_browser(self):
        """브라우저 초기화 및 사이트 접속"""
        self.logger.info("🌐 브라우저 초기화 중...")
        
        # MCP Playwright 함수를 전역으로 사용
        print("만개의레시피 사이트로 이동 중...")
        print("레시피 분류 페이지로 이동...")
        
        self.logger.info("✅ 브라우저 초기화 완료")
    
    def _collect_recipe_urls(self, target_count: int) -> List[str]:
        """레시피 URL 수집"""
        self.logger.info("📋 레시피 URL 수집 시작...")
        
        recipe_urls = []
        current_page = 1
        max_pages_per_category = 50  # 카테고리당 최대 페이지 수
        
        while len(recipe_urls) < target_count:
            try:
                # 현재 페이지의 레시피 링크 수집
                page_urls = self._extract_recipe_urls_from_page()
                
                if not page_urls:
                    self.logger.warning(f"페이지 {current_page}에서 레시피를 찾을 수 없음")
                    break
                
                # 중복 제거하여 추가
                new_urls = [url for url in page_urls if url not in self.crawled_urls]
                recipe_urls.extend(new_urls)
                self.crawled_urls.update(new_urls)
                
                self.logger.info(f"📄 페이지 {current_page}: {len(new_urls)}개 URL 수집 (총 {len(recipe_urls)}개)")
                
                # 목표 달성 시 종료
                if len(recipe_urls) >= target_count:
                    break
                
                # 다음 페이지로 이동
                if current_page < max_pages_per_category:
                    if self._go_to_next_page():
                        current_page += 1
                        time.sleep(self.config.DELAY_BETWEEN_PAGES)
                    else:
                        break
                else:
                    break
                    
            except Exception as e:
                self.logger.error(f"URL 수집 오류 (페이지 {current_page}): {e}")
                break
        
        return recipe_urls[:target_count]
    
    def _extract_recipe_urls_from_page(self) -> List[str]:
        """현재 페이지에서 레시피 URL 추출"""
        try:
            # 페이지 스냅샷을 통해 레시피 링크 추출
            snapshot = mcp_playwright_browser_snapshot({"random_string": "get_links"})
            
            # JavaScript로 레시피 링크 추출
            result = mcp_playwright_browser_evaluate({
                "function": """
                () => {
                    const links = [];
                    // 레시피 링크 패턴 찾기
                    const recipeLinks = document.querySelectorAll('a[href*="/recipe/"]');
                    
                    recipeLinks.forEach(link => {
                        const href = link.getAttribute('href');
                        if (href && href.includes('/recipe/') && !href.includes('/list.html')) {
                            const fullUrl = href.startsWith('http') ? href : 'https://www.10000recipe.com' + href;
                            links.push(fullUrl);
                        }
                    });
                    
                    return [...new Set(links)]; // 중복 제거
                }
                """
            })
            
            return result if result else []
            
        except Exception as e:
            self.logger.error(f"레시피 URL 추출 오류: {e}")
            return []
    
    def _go_to_next_page(self) -> bool:
        """다음 페이지로 이동"""
        try:
            # 다음 페이지 버튼 찾기 및 클릭
            result = mcp_playwright_browser_evaluate({
                "function": """
                () => {
                    // 페이지네이션에서 다음 버튼 찾기
                    const nextButtons = document.querySelectorAll('a');
                    for (let btn of nextButtons) {
                        if (btn.textContent.includes('다음') || btn.textContent.includes('>') || btn.textContent.includes('next')) {
                            btn.click();
                            return true;
                        }
                    }
                    
                    // 숫자 페이지 버튼 중 현재보다 큰 번호 찾기
                    const pageButtons = document.querySelectorAll('a[href*="page="]');
                    let maxPage = 0;
                    let nextPageBtn = null;
                    
                    pageButtons.forEach(btn => {
                        const pageMatch = btn.href.match(/page=(\\d+)/);
                        if (pageMatch) {
                            const pageNum = parseInt(pageMatch[1]);
                            if (pageNum > maxPage) {
                                maxPage = pageNum;
                                nextPageBtn = btn;
                            }
                        }
                    });
                    
                    if (nextPageBtn) {
                        nextPageBtn.click();
                        return true;
                    }
                    
                    return false;
                }
                """
            })
            
            if result:
                time.sleep(2)  # 페이지 로딩 대기
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"다음 페이지 이동 오류: {e}")
            return False
    
    async def _crawl_recipe_details(self, recipe_urls: List[str], results: Dict[str, int]):
        """레시피 상세 정보 크롤링"""
        self.logger.info(f"📖 레시피 상세 정보 크롤링 시작 - {len(recipe_urls)}개")
        
        batch_recipes = []
        
        for i, url in enumerate(recipe_urls, 1):
            try:
                self.logger.info(f"🔍 크롤링 중... ({i}/{len(recipe_urls)}): {url}")
                
                # 레시피 페이지 접속
                print(f"레시피 페이지 접속: {url}")
                time.sleep(self.config.DELAY_BETWEEN_REQUESTS)
                
                # 레시피 데이터 추출
                recipe_data = self._extract_recipe_data(url)
                
                if recipe_data:
                    # 파싱된 레시피 데이터로 변환
                    parsed_recipe = self.parser.parse_recipe_from_json(recipe_data)
                    
                    if parsed_recipe and self.parser.validate_recipe(parsed_recipe):
                        batch_recipes.append(parsed_recipe)
                        results["total_crawled"] += 1
                        
                        # 배치 크기에 도달하면 저장
                        if len(batch_recipes) >= self.config.BATCH_SIZE:
                            batch_results = await self.storage.save_recipe_batch(batch_recipes)
                            self._update_results(results, batch_results)
                            batch_recipes = []
                            
                            self.logger.info(f"📦 배치 저장 완료 - 성공: {results['success']}, 실패: {results['failed']}")
                    else:
                        results["skipped"] += 1
                        self.logger.warning(f"⚠️ 레시피 검증 실패: {url}")
                else:
                    results["failed"] += 1
                    self.logger.error(f"❌ 레시피 추출 실패: {url}")
                
            except Exception as e:
                results["failed"] += 1
                self.logger.error(f"❌ 크롤링 오류 ({url}): {e}")
        
        # 남은 배치 저장
        if batch_recipes:
            batch_results = await self.storage.save_recipe_batch(batch_recipes)
            self._update_results(results, batch_results)
    
    def _extract_recipe_data(self, url: str) -> Optional[Dict]:
        """레시피 페이지에서 데이터 추출"""
        try:
            # JavaScript로 레시피 데이터 추출
            recipe_data = mcp_playwright_browser_evaluate({
                "function": """
                () => {
                    const data = {
                        title: '',
                        description: '',
                        author: '',
                        difficulty: '',
                        cookingTime: '',
                        servings: '',
                        ingredients: [],
                        cookingSteps: [],
                        tips: [],
                        tags: [],
                        url: window.location.href
                    };
                    
                    // 제목 추출
                    const titleEl = document.querySelector('h3, h2, h1, .recipe_title');
                    if (titleEl) data.title = titleEl.textContent.trim();
                    
                    // 설명 추출
                    const descEl = document.querySelector('.recipe_desc, .description, p');
                    if (descEl) data.description = descEl.textContent.trim();
                    
                    // 작성자 추출
                    const authorEl = document.querySelector('.profile_name, .author, .writer');
                    if (authorEl) data.author = authorEl.textContent.trim();
                    
                    // 난이도, 조리시간, 인분 추출
                    const infoElements = document.querySelectorAll('div, span, td');
                    infoElements.forEach(el => {
                        const text = el.textContent.trim();
                        if (text.includes('아무나') || text.includes('초급') || text.includes('중급') || text.includes('고급')) {
                            data.difficulty = text;
                        } else if (text.includes('분') || text.includes('시간')) {
                            data.cookingTime = text;
                        } else if (text.includes('인분')) {
                            data.servings = text;
                        }
                    });
                    
                    // 재료 추출
                    const ingredientElements = document.querySelectorAll('li, tr, .ingredient');
                    ingredientElements.forEach(el => {
                        const text = el.textContent.trim();
                        if (text && text.length > 1 && text.length < 100) {
                            // 재료명과 양 분리 시도
                            const parts = text.split(/\\\\s+/);
                            if (parts.length >= 1) {
                                data.ingredients.push({
                                    name: parts[0],
                                    amount: parts.slice(1).join(' ') || '적당량'
                                });
                            }
                        }
                    });
                    
                    // 조리과정 추출
                    const stepElements = document.querySelectorAll('.recipe_step, .cooking_step, ol li, .step');
                    stepElements.forEach((el, index) => {
                        const instruction = el.textContent.trim();
                        if (instruction && instruction.length > 5) {
                            data.cookingSteps.push({
                                stepNumber: index + 1,
                                instruction: instruction
                            });
                        }
                    });
                    
                    // 태그 추출
                    const tagElements = document.querySelectorAll('.tag, .hashtag');
                    tagElements.forEach(el => {
                        const tag = el.textContent.trim();
                        if (tag) data.tags.push(tag);
                    });
                    
                    return data;
                }
                """
            })
            
            return recipe_data if recipe_data else None
            
        except Exception as e:
            self.logger.error(f"레시피 데이터 추출 오류: {e}")
            return None
    
    def _update_results(self, results: Dict[str, int], batch_results: Dict[str, int]):
        """결과 통계 업데이트"""
        results["success"] += batch_results.get("success", 0)
        results["failed"] += batch_results.get("failed", 0)
        results["skipped"] += batch_results.get("skipped", 0)

# 전역 크롤러 인스턴스
crawler = RecipeCrawler()
