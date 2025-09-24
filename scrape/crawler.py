"""
만개의 레시피 (10000recipe.com) 웹사이트에서 레시피 정보를 비동기적으로 크롤링하는 스크립트입니다.

이 스크립트는 목표한 수량의 레시피를 수집할 때까지 페이지를 탐색하며,
각 레시피의 상세 정보를 동시에 요청하여 효율성을 극대화합니다.
결과는 recipes.jsonl 파일에 한 줄씩 JSON 형태로 저장됩니다.

주요 라이브러리:
- requests: 초기 페이지 목록을 가져오기 위해 사용
- beautifulsoup4: HTML을 파싱하여 데이터를 추출하기 위해 사용
- aiohttp: 비동기 HTTP 요청을 위해 사용
- lxml: BeautifulSoup가 사용하는 빠른 HTML 파서

사용법:
    conda run -n fridge2fork python crawler.py
"""

import asyncio
import json
import re
import time
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

# --- 설정 (Configuration) ---
TARGET_RECIPE_COUNT = 100
BASE_URL = "https://www.10000recipe.com"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
HEADERS = {'User-Agent': USER_AGENT}
OUTPUT_FILENAME = "recipes.jsonl"
CONCURRENT_REQUESTS = 3  # 동시 요청 수 제어

# --- CSS 선택자 (Selectors) ---
SELECTORS = {
    "recipe_links_primary": "li.common_sp_list_li a.common_sp_link",
    "recipe_links_fallback": "div.common_sp_thumb a",
    "title": "div.view2_summary h3",
    "image": "#main_thumbs",
    "description": "#recipeIntro",
    "ingredients_container": "#divConfirmedMaterialArea ul",
    "ingredient_item": "li",
}

# --- robots.txt 파서 설정 ---
rp = RobotFileParser()
rp.set_url(f"{BASE_URL}/robots.txt")
rp.read()

# --- Helper Functions ---
def parse_ingredient(text):
    """
    단일 재료 텍스트를 파싱하여 이름, 수량, 단위로 구조화합니다.
    예: "다진 마늘 1/2큰술" -> {'name': '다진 마늘', 'quantity_from': 0.5, 'quantity_to': None, 'unit': '큰술'}
    """
    original_text = text.replace("구매", "").strip()
    text = original_text

    # 수량/단위 패턴 매칭 (문자열 끝에서부터)
    pattern = r"(.+?)\s*([\d./~-]+)\s*([\w가-힣]*)$"
    match = re.match(pattern, text)
    
    name, quant_from, quant_to, unit = None, None, None, None

    if match:
        name = match.group(1).strip()
        quantity_str = match.group(2)
        unit = match.group(3).strip() if match.group(3) else None

        try:
            if '~' in quantity_str or '-' in quantity_str:
                parts = re.split(r'[~-]', quantity_str)
                quant_from = float(parts[0])
                quant_to = float(parts[1])
            elif '/' in quantity_str:
                parts = quantity_str.split('/')
                quant_from = float(parts[0]) / float(parts[1])
            else:
                quant_from = float(quantity_str)
        except (ValueError, IndexError, ZeroDivisionError):
            # 파싱 실패 시 원본 텍스트를 이름으로 사용
            name = original_text
            quant_from, quant_to, unit = None, None, None
    else:
        name = text

    return {"name": name, "quantity_from": quant_from, "quantity_to": quant_to, "unit": unit}

# --- Synchronous Functions ---
def get_all_recipe_urls(target_count):
    """
    목표 수량에 도달할 때까지 페이지를 넘기며 모든 레시피의 URL을 수집합니다.
    """
    print(f"목표 수량 {target_count}개를 채우기 위해 레시피 URL 수집을 시작합니다.")
    recipe_urls = set()
    page = 1
    while len(recipe_urls) < target_count:
        list_url = f"{BASE_URL}/recipe/list.html?page={page}"
        if not rp.can_fetch(USER_AGENT, list_url):
            print(f"[Stopped] robots.txt에 의해 페이지 {page} 접근이 차단되었습니다.")
            break

        print(f"페이지 {page}에서 URL 수집 중... (현재 {len(recipe_urls)}개)")
        try:
            response = requests.get(list_url, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            links_on_page = soup.select(SELECTORS["recipe_links_primary"]) or soup.select(SELECTORS["recipe_links_fallback"])
            
            if not links_on_page:
                print(f"페이지 {page}에서 더 이상 레시피를 찾을 수 없습니다. 수집을 중단합니다.")
                break
                
            for link in links_on_page:
                href = link['href']
                full_url = BASE_URL + href if not href.startswith('http') else href
                if rp.can_fetch(USER_AGENT, full_url):
                    recipe_urls.add(full_url)
                if len(recipe_urls) >= target_count:
                    break
            
            page += 1
            time.sleep(2) # 서버 부하를 줄이기 위한 지연

        except requests.exceptions.RequestException as e:
            print(f"페이지 {page} 요청 중 오류 발생: {e}. 5초 후 재시도합니다.")
            time.sleep(5)

    return list(recipe_urls)[:target_count]

# --- Asynchronous Functions ---
async def scrape_recipe_details(session, url, semaphore):
    """
    비동기적으로 개별 레시피 페이지의 상세 정보를 스크랩합니다.
    """
    async with semaphore:
        try:
            await asyncio.sleep(1) # 추가적인 요청 간 지연
            async with session.get(url, headers=HEADERS) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "lxml")

                title = soup.select_one(SELECTORS["title"]).get_text(strip=True) if soup.select_one(SELECTORS["title"]) else "제목 없음"
                image_url = soup.select_one(SELECTORS["image"])['src'] if soup.select_one(SELECTORS["image"]) else "이미지 없음"
                description = soup.select_one(SELECTORS["description"]).get_text(strip=True) if soup.select_one(SELECTORS["description"]) else "설명 없음"

                ingredients = []
                container = soup.select_one(SELECTORS["ingredients_container"])
                if container:
                    items = container.select(SELECTORS["ingredient_item"])
                    for item in items:
                        full_text = re.sub(r'\s+', ' ', item.get_text(separator=" ").replace('\n', '')).strip()
                        if full_text:
                            ingredients.append(parse_ingredient(full_text))

                return {
                    "url": url,
                    "title": title,
                    "image_url": image_url,
                    "description": description,
                    "ingredients": ingredients,
                }
        except Exception as e:
            print(f"  [Error] {url} 처리 중 오류: {e}")
            return None

async def main():
    """
    비동기 크롤링 프로세스를 총괄하는 메인 함수.
    """
    recipe_urls = get_all_recipe_urls(TARGET_RECIPE_COUNT)
    print(f"\n총 {len(recipe_urls)}개의 허용된 URL에 대한 상세 정보 크롤링을 시작합니다.")
    
    scraped_count = 0
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession() as session:
        tasks = [scrape_recipe_details(session, url, semaphore) for url in recipe_urls]
        results = await asyncio.gather(*tasks)
        
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            for result in results:
                if result:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    scraped_count += 1
    
    print(f"\n크롤링 완료! 총 {scraped_count}개의 레시피를 '{OUTPUT_FILENAME}' 파일에 저장했습니다.")

if __name__ == "__main__":
    asyncio.run(main())