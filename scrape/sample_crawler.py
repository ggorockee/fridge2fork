#!/usr/bin/env python3
"""
만개의레시피 샘플 데이터 크롤링 스크립트

Phase 1.4: 100개의 샘플 데이터를 수집하여 데이터 정상 삽입을 확인합니다.
pandas를 이용하여 데이터를 검증하고 head(), tail() 메소드로 확인합니다.

사용법:
    python sample_crawler.py

특징:
- 100개의 레시피 데이터 수집
- pandas를 이용한 데이터 검증
- 안정성을 위한 1.5초 지연시간
- 오류 발생 시 재시도 로직
"""

import json
import time
import random
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
import re
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawling.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SampleRecipeCrawler:
    """만개의레시피 샘플 데이터 크롤러"""
    
    def __init__(self):
        self.base_url = "https://www.10000recipe.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.scraped_recipes = []
        self.failed_urls = []
        
    def get_recipe_list_urls(self, category: str = "한식", max_pages: int = 5) -> List[str]:
        """카테고리별 레시피 목록 URL 생성"""
        urls = []
        for page in range(1, max_pages + 1):
            # 테스트에서 확인된 URL 패턴 사용
            if page == 1:
                url = f"{self.base_url}/recipe/list.html"
            else:
                url = f"{self.base_url}/recipe/list.html?order=reco&page={page}"
            urls.append(url)
        return urls
    
    def extract_recipe_ids_from_list(self, list_url: str) -> List[str]:
        """레시피 목록 페이지에서 레시피 ID 추출"""
        try:
            response = self.session.get(list_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 다양한 패턴으로 레시피 링크 찾기
            recipe_ids = []
            
            # 패턴 1: 일반적인 레시피 링크
            recipe_links = soup.find_all('a', href=re.compile(r'/recipe/\d+'))
            for link in recipe_links:
                href = link.get('href', '')
                # 상대 경로와 절대 경로 모두 처리
                if href.startswith('/recipe/'):
                    match = re.search(r'/recipe/(\d+)', href)
                    if match:
                        recipe_ids.append(match.group(1))
                elif '10000recipe.com/recipe/' in href:
                    match = re.search(r'/recipe/(\d+)', href)
                    if match:
                        recipe_ids.append(match.group(1))
            
            # 패턴 2: data-recipe-id 속성
            elements_with_recipe_id = soup.find_all(attrs={'data-recipe-id': True})
            for element in elements_with_recipe_id:
                recipe_id = element.get('data-recipe-id')
                if recipe_id:
                    recipe_ids.append(recipe_id)
            
            # 패턴 3: onclick 속성에서 추출
            onclick_elements = soup.find_all(attrs={'onclick': re.compile(r'viewRecipe\(\d+\)')})
            for element in onclick_elements:
                onclick = element.get('onclick', '')
                match = re.search(r'viewRecipe\((\d+)\)', onclick)
                if match:
                    recipe_ids.append(match.group(1))
            
            # 중복 제거
            recipe_ids = list(set(recipe_ids))
            logger.info(f"페이지에서 {len(recipe_ids)}개의 레시피 ID 추출: {list_url}")
            
            # 디버깅을 위해 HTML 일부 출력
            if len(recipe_ids) == 0:
                logger.warning(f"레시피 ID를 찾을 수 없음. HTML 구조 확인 필요: {list_url}")
                # HTML의 일부를 로그로 출력
                page_title = soup.find('title')
                if page_title:
                    logger.warning(f"페이지 제목: {page_title.get_text()}")
            
            return recipe_ids
            
        except Exception as e:
            logger.error(f"레시피 목록 추출 실패 {list_url}: {e}")
            return []
    
    def scrape_recipe_detail(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """개별 레시피 상세 정보 스크래핑"""
        url = f"{self.base_url}/recipe/{recipe_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 기본 정보 추출
            recipe_data = {
                'recipeId': recipe_id,
                'url': url,
                'title': '',
                'description': '',
                'servings': '',
                'cookingTime': '',
                'difficulty': '',
                'ingredients': [],
                'cookingSteps': [],
                'author': '',
                'tags': [],
                'images': [],
                'scrapedAt': datetime.now().isoformat() + 'Z'
            }
            
            # 제목 추출
            title_element = soup.find('h3')
            if title_element:
                recipe_data['title'] = title_element.get_text(strip=True)
            
            # 설명 추출
            desc_container = title_element.parent.next_sibling if title_element and title_element.parent else None
            if desc_container:
                desc_divs = desc_container.find_all('div')
                if len(desc_divs) >= 2:
                    recipe_data['description'] = desc_divs[1].get_text(strip=True)
            
            # 메타 정보 추출 (인분, 시간, 난이도)
            meta_container = soup.find('div', class_='view2_summary_info')
            if meta_container:
                meta_items = meta_container.find_all('span')
                for i, item in enumerate(meta_items):
                    text = item.get_text(strip=True)
                    if i == 0:
                        recipe_data['servings'] = text
                    elif i == 1:
                        recipe_data['cookingTime'] = text
                    elif i == 2:
                        recipe_data['difficulty'] = text
            
            # 재료 추출
            ingredient_links = soup.find_all('a', href=re.compile(r'javascript:viewMaterial'))
            for link in ingredient_links:
                name = link.get_text(strip=True)
                amount_element = link.parent.next_sibling
                amount = amount_element.get_text(strip=True) if amount_element else ''
                
                if name and amount:
                    recipe_data['ingredients'].append({
                        'name': name,
                        'amount': amount,
                        'isEssential': True  # 기본값
                    })
            
            # 조리 단계 추출
            steps_container = soup.find('div', class_='view_step')
            if steps_container:
                step_divs = steps_container.find_all('div')
                step_number = 1
                
                for div in step_divs:
                    text = div.get_text(strip=True)
                    # 조리순서 관련 텍스트만 필터링
                    if (text and 
                        len(text) > 10 and
                        not any(keyword in text for keyword in [
                            '조리순서', '이미지크게보기', '텍스트만보기', 
                            '이미지작게보기', '더보기', '맛보장', '등록일',
                            '저작자', '레시피 작성자', '요리 후기', '댓글'
                        ])):
                        
                        recipe_data['cookingSteps'].append({
                            'stepNumber': step_number,
                            'description': text.replace('\n', ' ').strip(),
                            'imageUrl': ''
                        })
                        step_number += 1
            
            # 작성자 추출
            author_link = soup.find('a', href=re.compile(r'/profile/index.html'))
            if author_link:
                recipe_data['author'] = author_link.get_text(strip=True)
            
            # 태그 추출
            tag_links = soup.find_all('a', href=re.compile(r'/recipe/list.html\?q='))
            for link in tag_links:
                tag = link.get_text(strip=True).replace('#', '')
                if tag and len(tag) > 1 and '더보기' not in tag:
                    recipe_data['tags'].append(tag)
            
            # 이미지 추출
            images = soup.find_all('img', src=re.compile(r'cache/recipe'))
            for img in images:
                src = img.get('src', '')
                if src and 'icon' not in src and 'btn' not in src:
                    recipe_data['images'].append(src)
            
            # 중복 제거
            recipe_data['images'] = list(set(recipe_data['images']))
            recipe_data['tags'] = list(set(recipe_data['tags']))
            
            # 데이터 검증
            if recipe_data['title'] and recipe_data['ingredients']:
                logger.info(f"레시피 스크래핑 성공: {recipe_data['title']} (ID: {recipe_id})")
                return recipe_data
            else:
                logger.warning(f"레시피 데이터 불완전: {recipe_id}")
                return None
                
        except Exception as e:
            logger.error(f"레시피 스크래핑 실패 {recipe_id}: {e}")
            self.failed_urls.append(url)
            return None
    
    def crawl_sample_recipes(self, target_count: int = 100) -> List[Dict[str, Any]]:
        """샘플 레시피 데이터 크롤링"""
        logger.info(f"샘플 레시피 크롤링 시작 - 목표: {target_count}개")
        
        # 레시피 목록 URL 생성
        list_urls = self.get_recipe_list_urls(max_pages=10)
        
        # 모든 레시피 ID 수집
        all_recipe_ids = []
        for list_url in list_urls:
            recipe_ids = self.extract_recipe_ids_from_list(list_url)
            all_recipe_ids.extend(recipe_ids)
            
            # 1.5초 지연 (서버 부하 최소화)
            time.sleep(1.5)
            
            # 충분한 ID가 수집되면 중단
            if len(all_recipe_ids) >= target_count * 2:  # 여유분 확보
                break
        
        # 중복 제거
        all_recipe_ids = list(set(all_recipe_ids))
        logger.info(f"총 {len(all_recipe_ids)}개의 레시피 ID 수집 완료")
        
        # 샘플 레시피 상세 정보 수집
        scraped_count = 0
        for recipe_id in all_recipe_ids:
            if scraped_count >= target_count:
                break
                
            recipe_data = self.scrape_recipe_detail(recipe_id)
            if recipe_data:
                self.scraped_recipes.append(recipe_data)
                scraped_count += 1
                
                # 진행 상황 로깅
                if scraped_count % 10 == 0:
                    logger.info(f"진행 상황: {scraped_count}/{target_count} 완료")
            
            # 1.5초 지연 (안정성 우선)
            time.sleep(1.5)
        
        logger.info(f"샘플 크롤링 완료: {len(self.scraped_recipes)}개 수집")
        return self.scraped_recipes
    
    def save_to_json(self, filename: str = None) -> str:
        """크롤링 결과를 JSON 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"sample_recipes_{timestamp}.json"
        
        data = {
            'metadata': {
                'totalRecipes': len(self.scraped_recipes),
                'scrapedAt': datetime.now().isoformat() + 'Z',
                'source': '10000recipe.com',
                'method': 'BeautifulSoup HTML parsing',
                'failedUrls': len(self.failed_urls)
            },
            'recipes': self.scraped_recipes
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"크롤링 결과가 {filename}에 저장되었습니다.")
        return filename
    
    def validate_with_pandas(self, json_file: str) -> pd.DataFrame:
        """pandas를 이용한 데이터 검증"""
        logger.info("pandas를 이용한 데이터 검증 시작")
        
        # JSON 파일 로드
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        recipes = data['recipes']
        
        # DataFrame 생성
        df = pd.DataFrame(recipes)
        
        # 기본 정보 출력
        logger.info(f"총 레시피 수: {len(df)}")
        logger.info(f"컬럼: {list(df.columns)}")
        
        # 데이터 검증
        validation_results = {
            'total_recipes': len(df),
            'recipes_with_title': len(df[df['title'].notna() & (df['title'] != '')]),
            'recipes_with_ingredients': len(df[df['ingredients'].apply(lambda x: len(x) > 0)]),
            'recipes_with_steps': len(df[df['cookingSteps'].apply(lambda x: len(x) > 0)]),
            'recipes_with_images': len(df[df['images'].apply(lambda x: len(x) > 0)]),
            'avg_ingredients_per_recipe': df['ingredients'].apply(len).mean(),
            'avg_steps_per_recipe': df['cookingSteps'].apply(len).mean(),
            'avg_images_per_recipe': df['images'].apply(len).mean()
        }
        
        logger.info("=== 데이터 검증 결과 ===")
        for key, value in validation_results.items():
            logger.info(f"{key}: {value}")
        
        # head() 및 tail() 출력
        logger.info("\n=== 처음 5개 레시피 (head) ===")
        head_data = df[['recipeId', 'title', 'servings', 'cookingTime', 'difficulty']].head()
        logger.info(f"\n{head_data.to_string()}")
        
        logger.info("\n=== 마지막 5개 레시피 (tail) ===")
        tail_data = df[['recipeId', 'title', 'servings', 'cookingTime', 'difficulty']].tail()
        logger.info(f"\n{tail_data.to_string()}")
        
        # 재료 정보 샘플
        logger.info("\n=== 재료 정보 샘플 ===")
        sample_recipe = df.iloc[0]
        logger.info(f"레시피: {sample_recipe['title']}")
        logger.info(f"재료 수: {len(sample_recipe['ingredients'])}")
        for i, ingredient in enumerate(sample_recipe['ingredients'][:5]):  # 처음 5개만
            logger.info(f"  {i+1}. {ingredient['name']} - {ingredient['amount']}")
        
        return df


def main():
    """메인 함수"""
    logger.info("=== 만개의레시피 샘플 데이터 크롤링 시작 ===")
    
    # 크롤러 초기화
    crawler = SampleRecipeCrawler()
    
    try:
        # 100개 샘플 레시피 크롤링
        recipes = crawler.crawl_sample_recipes(target_count=100)
        
        if not recipes:
            logger.error("크롤링된 레시피가 없습니다.")
            return
        
        # JSON 파일로 저장
        json_file = crawler.save_to_json()
        
        # pandas를 이용한 데이터 검증
        df = crawler.validate_with_pandas(json_file)
        
        logger.info("=== 샘플 데이터 크롤링 완료 ===")
        logger.info(f"수집된 레시피 수: {len(recipes)}")
        logger.info(f"저장된 파일: {json_file}")
        
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
