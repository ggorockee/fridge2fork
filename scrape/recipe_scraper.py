#!/usr/bin/env python3
"""
만개의레시피 크롤링 스크립트

이 스크립트는 MCP Playwright를 사용하여 만개의레시피 사이트에서
레시피 데이터를 추출하는 기능을 제공합니다.

사용법:
    python recipe_scraper.py <recipe_url>

예시:
    python recipe_scraper.py https://www.10000recipe.com/recipe/7063127
"""

import json
import sys
import re
from datetime import datetime
from typing import Dict, List, Any, Optional


class RecipeScraper:
    """만개의레시피 크롤링 클래스"""
    
    def __init__(self):
        self.base_url = "https://www.10000recipe.com"
        
    def extract_recipe_id(self, url: str) -> Optional[str]:
        """URL에서 레시피 ID 추출"""
        match = re.search(r'/recipe/(\d+)', url)
        return match.group(1) if match else None
    
    def get_scraping_script(self) -> str:
        """Playwright에서 실행할 JavaScript 코드 반환"""
        return """
        () => {
            // 레시피 데이터 추출 함수
            const recipeData = {
                title: '',
                description: '',
                servings: '',
                time: '',
                difficulty: '',
                ingredients: [],
                steps: [],
                author: '',
                tags: [],
                images: [],
                recipeId: '',
                url: window.location.href
            };

            // 레시피 ID 추출
            const urlMatch = window.location.href.match(/\\/recipe\\/(\\d+)/);
            recipeData.recipeId = urlMatch ? urlMatch[1] : '';

            // 제목 추출
            const titleElement = document.querySelector('h3');
            recipeData.title = titleElement?.textContent?.trim() || '';

            // 설명 추출 - 제목 바로 아래 텍스트
            const descContainer = titleElement?.parentElement?.nextElementSibling;
            if (descContainer) {
                const descTexts = descContainer.querySelectorAll('div');
                if (descTexts.length >= 2) {
                    recipeData.description = descTexts[1].textContent?.trim() || '';
                }
            }

            // 메타 정보 추출 (인분, 시간, 난이도)
            const metaContainer = document.querySelector('h3')?.parentElement?.nextElementSibling?.nextElementSibling;
            if (metaContainer) {
                const metaElements = metaContainer.querySelectorAll('div');
                metaElements.forEach((el, index) => {
                    const text = el.textContent?.trim() || '';
                    if (index === 0) recipeData.servings = text;
                    else if (index === 1) recipeData.time = text;
                    else if (index === 2) recipeData.difficulty = text;
                });
            }

            // 재료 추출
            const ingredientLinks = document.querySelectorAll('a[href*="javascript:viewMaterial"]');
            ingredientLinks.forEach(link => {
                const name = link.textContent?.trim() || '';
                const amountElement = link.parentElement?.nextElementSibling;
                const amount = amountElement?.textContent?.trim() || '';
                if (name && amount) {
                    recipeData.ingredients.push({ name, amount });
                }
            });

            // 조리순서 추출 - 더 정확한 방법
            const stepsContainer = document.querySelector('.view_step');
            if (stepsContainer) {
                const stepElements = stepsContainer.querySelectorAll('div');
                let stepNumber = 1;
                stepElements.forEach((step, index) => {
                    const text = step.textContent?.trim() || '';
                    // 조리순서 관련 텍스트만 필터링
                    if (text && 
                        !text.includes('조리순서') && 
                        !text.includes('이미지크게보기') && 
                        !text.includes('텍스트만보기') && 
                        !text.includes('이미지작게보기') &&
                        text.length > 10 && // 너무 짧은 텍스트 제외
                        !text.includes('더보기') &&
                        !text.includes('맛보장') &&
                        !text.includes('등록일') &&
                        !text.includes('저작자') &&
                        !text.includes('레시피 작성자') &&
                        !text.includes('요리 후기') &&
                        !text.includes('댓글')) {
                        recipeData.steps.push({ 
                            step: stepNumber, 
                            description: text.replace(/\\s+/g, ' ').trim() 
                        });
                        stepNumber++;
                    }
                });
            }

            // 작성자 추출
            const authorLink = document.querySelector('a[href*="/profile/index.html"]');
            recipeData.author = authorLink?.textContent?.trim() || '';

            // 태그 추출 (해시태그만)
            const tagLinks = document.querySelectorAll('a[href*="/recipe/list.html?q="]');
            tagLinks.forEach(link => {
                const tag = link.textContent?.replace('#', '').trim();
                if (tag && tag.length > 1 && !tag.includes('더보기')) {
                    recipeData.tags.push(tag);
                }
            });

            // 이미지 추출 (레시피 관련 이미지만)
            const images = document.querySelectorAll('img[src*="cache/recipe"]');
            images.forEach(img => {
                if (img.src && !img.src.includes('icon') && !img.src.includes('btn')) {
                    recipeData.images.push(img.src);
                }
            });

            // 중복 제거
            recipeData.images = [...new Set(recipeData.images)];
            recipeData.tags = [...new Set(recipeData.tags)];

            return recipeData;
        }
        """
    
    def process_scraped_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """크롤링된 데이터 후처리"""
        # 메타 정보 추가
        processed_data = raw_data.copy()
        processed_data['scrapingInfo'] = {
            'scrapedAt': datetime.now().isoformat() + 'Z',
            'source': '10000recipe.com',
            'method': 'Playwright DOM extraction',
            'totalIngredients': len(processed_data.get('ingredients', [])),
            'totalSteps': len(processed_data.get('steps', [])),
            'totalImages': len(processed_data.get('images', [])),
            'totalTags': len(processed_data.get('tags', []))
        }
        
        return processed_data
    
    def save_to_json(self, data: Dict[str, Any], filename: str = None) -> str:
        """데이터를 JSON 파일로 저장"""
        if filename is None:
            recipe_id = data.get('recipeId', 'unknown')
            filename = f"recipe_{recipe_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def validate_url(self, url: str) -> bool:
        """URL 유효성 검증"""
        return url.startswith(self.base_url) and '/recipe/' in url
    
    def get_usage_instructions(self) -> str:
        """사용법 안내 반환"""
        return """
만개의레시피 크롤링 스크립트 사용법:

1. MCP Playwright 도구가 필요합니다.
2. 브라우저를 열고 레시피 페이지로 이동합니다.
3. 제공된 JavaScript 코드를 page.evaluate()로 실행합니다.
4. 결과를 JSON 파일로 저장합니다.

예시 코드:
    # 브라우저 열기 및 페이지 이동
    await page.goto('https://www.10000recipe.com/recipe/7063127')
    
    # 데이터 추출
    recipe_data = await page.evaluate(scraper.get_scraping_script())
    
    # 데이터 후처리 및 저장
    processed_data = scraper.process_scraped_data(recipe_data)
    filename = scraper.save_to_json(processed_data)
    
    print(f"레시피 데이터가 {filename}에 저장되었습니다.")
        """


def main():
    """메인 함수"""
    if len(sys.argv) != 2:
        print("사용법: python recipe_scraper.py <recipe_url>")
        print("예시: python recipe_scraper.py https://www.10000recipe.com/recipe/7063127")
        sys.exit(1)
    
    url = sys.argv[1]
    scraper = RecipeScraper()
    
    # URL 유효성 검증
    if not scraper.validate_url(url):
        print(f"올바르지 않은 URL입니다: {url}")
        print(f"만개의레시피 URL이어야 합니다: {scraper.base_url}/recipe/[숫자]")
        sys.exit(1)
    
    # 레시피 ID 추출
    recipe_id = scraper.extract_recipe_id(url)
    if not recipe_id:
        print("URL에서 레시피 ID를 추출할 수 없습니다.")
        sys.exit(1)
    
    print(f"레시피 ID: {recipe_id}")
    print(f"대상 URL: {url}")
    print("\n크롤링 스크립트:")
    print(scraper.get_scraping_script())
    print("\n사용법 안내:")
    print(scraper.get_usage_instructions())


if __name__ == "__main__":
    main()
