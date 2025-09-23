"""
만개의 레시피 크롤링 메인 스크립트
Playwright를 사용한 레시피 데이터 수집
Phase 1: 100개 샘플 데이터 크롤링
"""

import asyncio
import logging
import time
import random
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import traceback

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from config import (
    TARGET_SITE, CRAWLING_CONFIG, SELECTORS,
    VALIDATION_RULES, LOGGING_CONFIG, create_directories
)
from ingredient_normalizer import IngredientNormalizer, NormalizedIngredient
from data_exporter import DataExporter

# 로깅 설정
def setup_logging():
    create_directories()
    logging.basicConfig(
        level=getattr(logging, LOGGING_CONFIG['level']),
        format=LOGGING_CONFIG['format'],
        handlers=[
            logging.FileHandler(LOGGING_CONFIG['file'], encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

class RecipeCrawler:
    """만개의 레시피 크롤러 클래스"""

    def __init__(self):
        self.base_url = TARGET_SITE['base_url']
        self.config = CRAWLING_CONFIG
        self.selectors = SELECTORS
        self.max_recipes = self.config['max_recipes']

        self.normalizer = IngredientNormalizer()
        self.exporter = DataExporter()

        # 상태 관리
        self.crawled_recipes = []
        self.failed_urls = []
        self.start_time = None

        # 브라우저 설정
        self.browser = None
        self.context = None

    async def run(self) -> Dict[str, Any]:
        """
        크롤링을 실행합니다.

        Returns:
            Dict: 크롤링 결과 통계
        """
        self.start_time = datetime.now()
        logger.info(f"크롤링 시작: {self.start_time}")
        logger.info(f"목표 레시피 수: {self.max_recipes}개")

        try:
            # 브라우저 시작
            await self._setup_browser()

            # 레시피 URL 수집
            recipe_urls = await self._collect_recipe_urls()
            logger.info(f"수집된 레시피 URL: {len(recipe_urls)}개")

            # 레시피 상세 정보 크롤링
            await self._crawl_recipes(recipe_urls[:self.max_recipes])

            # 데이터 export
            export_result = self._export_data()

            # 결과 통계
            result = self._generate_result_stats(export_result)

            return result

        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {e}")
            logger.error(traceback.format_exc())
            raise
        finally:
            await self._cleanup()

    async def _setup_browser(self):
        """브라우저를 설정합니다."""
        playwright = await async_playwright().start()

        # 브라우저 시작
        self.browser = await playwright.chromium.launch(
            headless=self.config['headless'],
            slow_mo=1000 if not self.config['headless'] else 0
        )

        # 컨텍스트 생성
        self.context = await self.browser.new_context(
            user_agent=self.config['user_agent'],
            viewport={'width': 1280, 'height': 720}
        )

        # 페이지 타임아웃 설정
        self.context.set_default_timeout(self.config['timeout'])

        logger.info("브라우저 설정 완료")

    async def _collect_recipe_urls(self) -> List[str]:
        """레시피 URL들을 수집합니다."""
        recipe_urls = []
        page = await self.context.new_page()

        try:
            # 메인 레시피 리스트 페이지로 이동
            list_url = f"{self.base_url}{TARGET_SITE['recipe_list_url']}"
            logger.info(f"레시피 리스트 페이지 접근: {list_url}")

            await page.goto(list_url)
            await page.wait_for_load_state('networkidle')

            # 페이지 스크린샷으로 구조 확인
            await page.screenshot(path='page_structure.png')

            # 페이지 소스 획득 및 파싱
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # 레시피 링크 추출 (여러 셀렉터 시도)
            possible_selectors = [
                'a[href*="/recipe/"]',
                '.common_sp_list_ul a',
                '.list_recipe a',
                '.recipe_list a',
                '.recipe-item a'
            ]

            recipe_links = []
            for selector in possible_selectors:
                links = soup.select(selector)
                if links:
                    logger.info(f"셀렉터 '{selector}'로 {len(links)}개 링크 발견")
                    recipe_links = links
                    break

            # URL 정규화 및 수집
            for link in recipe_links:
                href = link.get('href')
                if href:
                    # 상대 URL을 절대 URL로 변환
                    full_url = urljoin(self.base_url, href)

                    # 중복 제거 및 유효성 검사 (실제 레시피 페이지만 수집)
                    # 실제 레시피 페이지는 /recipe/숫자 형태
                    if (full_url not in recipe_urls and
                        '/recipe/' in full_url and
                        re.search(r'/recipe/\d+$', full_url)):
                        recipe_urls.append(full_url)

                        # 목표 수량에 도달하면 중단
                        if len(recipe_urls) >= self.max_recipes * 2:  # 여유분 확보
                            break

            logger.info(f"총 {len(recipe_urls)}개 레시피 URL 수집 완료")

        except Exception as e:
            logger.error(f"레시피 URL 수집 중 오류: {e}")
            # 대안: 샘플 URL들 사용
            recipe_urls = self._get_sample_urls()

        finally:
            await page.close()

        return recipe_urls

    def _get_sample_urls(self) -> List[str]:
        """샘플 레시피 URL들을 반환합니다. (실제 사이트 구조 확인 후 업데이트 필요)"""
        # 실제 만개의 레시피 URL 패턴 예시
        sample_urls = []
        base_recipe_url = f"{self.base_url}/recipe/"

        # 임시로 ID 기반 URL 생성
        for i in range(6900000, 6900000 + self.max_recipes * 2):
            sample_urls.append(f"{base_recipe_url}{i}")

        logger.warning(f"샘플 URL {len(sample_urls)}개 생성 (실제 사이트 구조 확인 필요)")
        return sample_urls

    async def _crawl_recipes(self, recipe_urls: List[str]):
        """레시피 상세 정보를 크롤링합니다."""
        logger.info(f"{len(recipe_urls)}개 레시피 크롤링 시작")

        for i, url in enumerate(recipe_urls):
            if len(self.crawled_recipes) >= self.max_recipes:
                break

            try:
                logger.info(f"레시피 크롤링 ({i+1}/{len(recipe_urls)}): {url}")

                recipe_data = await self._crawl_single_recipe(url)
                if recipe_data and self._validate_recipe(recipe_data):
                    self.crawled_recipes.append(recipe_data)
                    logger.info(f"레시피 수집 성공: {recipe_data.get('title', 'Unknown')}")
                else:
                    self.failed_urls.append(url)

                # 요청 간 지연
                await asyncio.sleep(random.uniform(1, 3))

            except Exception as e:
                logger.error(f"레시피 크롤링 실패 ({url}): {e}")
                self.failed_urls.append(url)
                continue

        logger.info(f"크롤링 완료: 성공 {len(self.crawled_recipes)}개, 실패 {len(self.failed_urls)}개")

    async def _crawl_single_recipe(self, url: str) -> Optional[Dict[str, Any]]:
        """개별 레시피를 크롤링합니다."""
        page = await self.context.new_page()

        try:
            await page.goto(url)
            await page.wait_for_load_state('networkidle')

            # 페이지 콘텐츠 추출
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # 레시피 데이터 추출
            recipe_data = {
                'url': url,
                'crawled_at': datetime.now().isoformat(),
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'image_url': self._extract_image_url(soup),
                'cooking_time': self._extract_cooking_time(soup),
                'servings': self._extract_servings(soup),
                'difficulty': self._extract_difficulty(soup),
                'rating': self._extract_rating(soup),
                'ingredients': self._extract_and_normalize_ingredients(soup),
                'cooking_steps': self._extract_cooking_steps(soup),
                'category': self._extract_category(soup)
            }

            return recipe_data

        except Exception as e:
            logger.error(f"레시피 상세 크롤링 실패 ({url}): {e}")
            return None
        finally:
            await page.close()

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """레시피 제목을 추출합니다."""
        selectors = [
            'h1.recipe-title',
            '.view_recipe h3',
            'h1',
            '.recipe_title',
            '.view_recipe .recipe_name'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """레시피 설명을 추출합니다."""
        selectors = [
            '.view_recipe_intro',
            '.recipe_intro',
            '.recipe_summary',
            '.recipe_description'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        return ""

    def _extract_image_url(self, soup: BeautifulSoup) -> str:
        """레시피 이미지 URL을 추출합니다."""
        selectors = [
            '.view_recipe .centeredcrop img',
            '.recipe_img img',
            '.main_thumbs img',
            'img[src*="recipe"]'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                src = element.get('src') or element.get('data-src')
                if src:
                    return urljoin(self.base_url, src)

        return ""

    def _extract_cooking_time(self, soup: BeautifulSoup) -> str:
        """조리 시간을 추출합니다."""
        # "조리시간" 텍스트가 포함된 요소 찾기
        time_element = soup.find(text=lambda text: text and '조리시간' in text)
        if time_element:
            parent = time_element.parent
            if parent:
                return parent.get_text(strip=True).replace('조리시간', '').strip()

        # 대안 셀렉터들
        selectors = [
            '.recipe_info_time',
            '.cooking_time',
            '.recipe_time'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        return ""

    def _extract_servings(self, soup: BeautifulSoup) -> str:
        """인분 정보를 추출합니다."""
        # "인분" 텍스트가 포함된 요소 찾기
        serving_element = soup.find(text=lambda text: text and '인분' in text)
        if serving_element:
            parent = serving_element.parent
            if parent:
                return parent.get_text(strip=True)

        return ""

    def _extract_difficulty(self, soup: BeautifulSoup) -> str:
        """난이도 정보를 추출합니다."""
        # "난이도" 텍스트가 포함된 요소 찾기
        difficulty_element = soup.find(text=lambda text: text and '난이도' in text)
        if difficulty_element:
            parent = difficulty_element.parent
            if parent:
                return parent.get_text(strip=True).replace('난이도', '').strip()

        return ""

    def _extract_rating(self, soup: BeautifulSoup) -> str:
        """평점 정보를 추출합니다."""
        selectors = [
            '.recipe_rating',
            '.star_rating',
            '.rating_score'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        return ""

    def _extract_and_normalize_ingredients(self, soup: BeautifulSoup) -> List[NormalizedIngredient]:
        """재료 정보를 추출하고 정규화합니다."""
        selectors = [
            '.ready_ingre3 li',
            '.recipe_ingredient li',
            '.ingredients_list li',
            '.ingredient_list li'
        ]

        ingredients_text = []

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 1:
                        ingredients_text.append(text)
                break  # 첫 번째로 찾은 셀렉터만 사용

        # 재료 정규화
        if ingredients_text:
            return self.normalizer.normalize_ingredient_list(ingredients_text)

        return []

    def _extract_cooking_steps(self, soup: BeautifulSoup) -> List[str]:
        """조리 과정을 추출합니다."""
        selectors = [
            '.view_step_cont',
            '.recipe_step',
            '.cooking_step',
            '.step_content'
        ]

        steps = []

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                for i, element in enumerate(elements):
                    text = element.get_text(strip=True)
                    if text and len(text) > 5:  # 너무 짧은 텍스트 제외
                        steps.append(f"{i+1}. {text}")
                break

        return steps

    def _extract_category(self, soup: BeautifulSoup) -> str:
        """카테고리 정보를 추출합니다."""
        # 브레드크럼이나 카테고리 링크에서 추출
        selectors = [
            '.breadcrumb a',
            '.category_link',
            '.recipe_category'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements and len(elements) > 1:  # 첫 번째는 보통 "홈"
                return elements[-1].get_text(strip=True)

        return ""

    def _validate_recipe(self, recipe_data: Dict[str, Any]) -> bool:
        """레시피 데이터의 유효성을 검증합니다."""
        rules = VALIDATION_RULES

        # 제목 검증
        title = recipe_data.get('title', '')
        if not title or len(title) < rules['recipe_title']['min_length']:
            return False

        # 재료 검증
        ingredients = recipe_data.get('ingredients', [])
        if len(ingredients) < rules['ingredients']['min_count']:
            return False

        return True

    def _export_data(self) -> Dict[str, Any]:
        """크롤링된 데이터를 export합니다."""
        if not self.crawled_recipes:
            logger.warning("Export할 데이터가 없습니다.")
            return {}

        try:
            return self.exporter.export_recipes(self.crawled_recipes)
        except Exception as e:
            logger.error(f"데이터 export 실패: {e}")
            return {}

    def _generate_result_stats(self, export_result: Dict[str, Any]) -> Dict[str, Any]:
        """크롤링 결과 통계를 생성합니다."""
        end_time = datetime.now()
        duration = end_time - self.start_time

        return {
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'target_recipes': self.max_recipes,
            'successful_recipes': len(self.crawled_recipes),
            'failed_urls': len(self.failed_urls),
            'success_rate': len(self.crawled_recipes) / self.max_recipes * 100,
            'export_files': export_result
        }

    async def _cleanup(self):
        """리소스를 정리합니다."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("브라우저 리소스 정리 완료")

async def main():
    """메인 실행 함수"""
    setup_logging()

    try:
        # 크롤러 실행
        crawler = RecipeCrawler()
        result = await crawler.run()

        # 결과 출력
        print("\n" + "="*50)
        print("크롤링 완료!")
        print("="*50)
        print(f"목표 레시피 수: {result['target_recipes']}개")
        print(f"수집 성공: {result['successful_recipes']}개")
        print(f"실패: {result['failed_urls']}개")
        print(f"성공률: {result['success_rate']:.1f}%")
        print(f"소요 시간: {result['duration_seconds']:.1f}초")

        if result.get('export_files'):
            print("\nExport된 파일:")
            for key, path in result['export_files'].items():
                if key.endswith('_file'):
                    print(f"  {key}: {path}")

        return result

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
        print("\n크롤링이 중단되었습니다.")
    except Exception as e:
        logger.error(f"크롤링 실행 중 오류: {e}")
        print(f"\n크롤링 실행 중 오류가 발생했습니다: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())