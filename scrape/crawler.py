"""
만개의 레시피 (10000recipe.com) 웹사이트에서 레시피 정보를 비동기적으로 크롤링하고,
수집된 데이터를 PostgreSQL 데이터베이스에 저장하는 스크립트입니다.

이 스크립트는 목표한 수량의 레시피를 수집할 때까지 페이지를 탐색하며,
각 레시피의 상세 정보를 동시에 요청하여 효율성을 극대화합니다.
결과는 데이터베이스에 저장되며, 동시에 recipes.jsonl 파일에도 기록됩니다.

주요 라이브러리:
- requests: 초기 페이지 목록을 가져오기 위해 사용
- beautifulsoup4: HTML을 파싱하여 데이터를 추출하기 위해 사용
- aiohttp: 비동기 HTTP 요청을 위해 사용
- psycopg2-binary: PostgreSQL 데이터베이스와 통신하기 위해 사용
- python-dotenv: 환경 변수를 관리하기 위해 사용

사용법:
    1. .env 파일을 생성하고 데이터베이스 연결 정보를 설정합니다. (.env.example 참고)
    2. pip install -r requirements.txt
    3. python crawler.py

CI 테스트를 위한 업데이트
"""

import asyncio
import json
import re
import time
import os
import logging
import aiohttp
import requests
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from dotenv import load_dotenv
from datetime import datetime

# --- 환경 변수 및 설정 (Configuration) ---
load_dotenv()

# --- 로깅 설정 ---
def setup_logging():
    """로깅 설정을 초기화합니다."""
    # 로그 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 루트 로거 설정
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 콘솔 핸들러만 사용 (Pod 로그로 확인)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(console_handler)
    
    return logger

# 로깅 초기화
logger = setup_logging()

TARGET_RECIPE_COUNT = 100
BASE_URL = "https://www.10000recipe.com"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
HEADERS = {'User-Agent': USER_AGENT}
OUTPUT_FILENAME = "recipes.jsonl"
CONCURRENT_REQUESTS = 3  # 동시 요청 수 제어

# --- 데이터베이스 설정 ---
DB_POOL = None
try:
    DATABASE_URL = (
        f"dbname={os.getenv('POSTGRES_DB')} "
        f"user={os.getenv('POSTGRES_USER')} "
        f"password={os.getenv('POSTGRES_PASSWORD')} "
        f"host={os.getenv('POSTGRES_SERVER')} "
        f"port={os.getenv('POSTGRES_PORT')}"
    )
    DB_POOL = SimpleConnectionPool(minconn=1, maxconn=5, dsn=DATABASE_URL)
    logger.info("✅ 데이터베이스 커넥션 풀 생성 성공")
    logger.info(f"데이터베이스 연결 정보: {os.getenv('POSTGRES_SERVER')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}")
except Exception as e:
    logger.error(f"🚨 데이터베이스 커넥션 풀 생성 실패: {e}")
    DB_POOL = None


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

# --- Database Functions ---
async def insert_recipe_data(pool, recipe_data):
    """
    단일 레시피 데이터를 데이터베이스에 Upsert합니다.
    """
    conn = None
    try:
        conn = pool.getconn()
        cursor = conn.cursor()

        # 1. recipes 테이블에 Upsert
        cursor.execute(
            """INSERT INTO recipes (url, title, description, image_url)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (url) DO UPDATE SET
                 title = EXCLUDED.title,
                 description = EXCLUDED.description,
                 image_url = EXCLUDED.image_url
               RETURNING recipe_id;""",
            (recipe_data['url'], recipe_data['title'], recipe_data['description'], recipe_data['image_url'])
        )
        recipe_id = cursor.fetchone()[0]

        # 2. ingredients 및 recipe_ingredients 테이블 처리
        for ing in recipe_data['ingredients']:
            # 2a. ingredients 테이블에 Upsert (DO NOTHING)
            cursor.execute(
                """INSERT INTO ingredients (name)
                   VALUES (%s)
                   ON CONFLICT (name) DO NOTHING
                   RETURNING ingredient_id;""",
                (ing['name'],)
            )
            result = cursor.fetchone()
            if result:
                ingredient_id = result[0]
            else:
                # 이미 존재하여 id가 반환되지 않은 경우, id를 조회
                cursor.execute("SELECT ingredient_id FROM ingredients WHERE name = %s;", (ing['name'],))
                ingredient_id = cursor.fetchone()[0]

            # 2b. recipe_ingredients 테이블에 Upsert
            cursor.execute(
                """INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity_from, quantity_to, unit)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (recipe_id, ingredient_id) DO UPDATE SET
                     quantity_from = EXCLUDED.quantity_from,
                     quantity_to = EXCLUDED.quantity_to,
                     unit = EXCLUDED.unit;""",
                (recipe_id, ingredient_id, ing['quantity_from'], ing['quantity_to'], ing['unit'])
            )
        
        conn.commit()
        logger.info(f"✅ DB 저장 성공: {recipe_data['title']} (재료 {len(recipe_data['ingredients'])}개)")

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"❌ DB 저장 실패: {recipe_data.get('title', 'N/A')} - {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            pool.putconn(conn)

# --- Synchronous Functions ---
def get_all_recipe_urls(target_count):
    """
    목표 수량에 도달할 때까지 페이지를 넘기며 모든 레시피의 URL을 수집합니다.
    """
    logger.info(f"🚀 레시피 URL 수집 시작 - 목표: {target_count}개")
    start_time = time.time()
    recipe_urls = set()
    page = 1
    while len(recipe_urls) < target_count:
        list_url = f"{BASE_URL}/recipe/list.html?page={page}"
        if not rp.can_fetch(USER_AGENT, list_url):
            logger.warning(f"⚠️ robots.txt에 의해 페이지 {page} 접근이 차단됨")
            break

        logger.info(f"📄 페이지 {page} 처리 중... (현재 수집: {len(recipe_urls)}/{target_count})")
        try:
            response = requests.get(list_url, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            links_on_page = soup.select(SELECTORS["recipe_links_primary"]) or soup.select(SELECTORS["recipe_links_fallback"])
            
            if not links_on_page:
                logger.warning(f"⚠️ 페이지 {page}에서 레시피를 찾을 수 없음 - 수집 중단")
                break
            
            new_links_count = 0
            for link in links_on_page:
                href = link['href']
                full_url = BASE_URL + href if not href.startswith('http') else href
                if rp.can_fetch(USER_AGENT, full_url):
                    recipe_urls.add(full_url)
                    new_links_count += 1
                if len(recipe_urls) >= target_count:
                    break
            
            logger.info(f"✅ 페이지 {page} 완료 - 새로 수집된 링크: {new_links_count}개")
            page += 1
            time.sleep(2) # 서버 부하를 줄이기 위한 지연

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 페이지 {page} 요청 실패: {e} - 5초 후 재시도")
            time.sleep(5)

    elapsed_time = time.time() - start_time
    logger.info(f"🎯 URL 수집 완료 - 총 {len(recipe_urls)}개 수집 (소요시간: {elapsed_time:.2f}초)")
    return list(recipe_urls)[:target_count]

# --- Asynchronous Functions ---
async def scrape_recipe_details(session, url, semaphore):
    """
    비동기적으로 개별 레시피 페이지의 상세 정보를 스크랩합니다.
    """
    async with semaphore:
        try:
            await asyncio.sleep(1) # 추가적인 요청 간 지연
            logger.debug(f"🔍 스크래핑 시작: {url}")
            
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

                logger.debug(f"✅ 스크래핑 완료: {title} (재료 {len(ingredients)}개)")
                return {
                    "url": url,
                    "title": title,
                    "image_url": image_url,
                    "description": description,
                    "ingredients": ingredients,
                }
        except Exception as e:
            logger.error(f"❌ 스크래핑 실패: {url} - {e}")
            return None

async def main():
    """
    비동기 크롤링 프로세스를 총괄하는 메인 함수.
    """
    logger.info("=" * 60)
    logger.info("🚀 만개의 레시피 크롤러 시작")
    logger.info(f"📊 설정: 목표 {TARGET_RECIPE_COUNT}개, 동시 요청 {CONCURRENT_REQUESTS}개")
    logger.info("=" * 60)
    
    if not DB_POOL:
        logger.error("🚨 데이터베이스 연결이 설정되지 않았습니다. 스크립트를 종료합니다.")
        return

    start_time = time.time()
    recipe_urls = get_all_recipe_urls(TARGET_RECIPE_COUNT)
    logger.info(f"\n📋 총 {len(recipe_urls)}개의 URL에 대한 상세 정보 크롤링을 시작합니다.")
    
    scraped_count = 0
    failed_count = 0
    db_tasks = []

    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession() as session:
        logger.info("🔄 비동기 스크래핑 시작...")
        tasks = [scrape_recipe_details(session, url, semaphore) for url in recipe_urls]
        results = await asyncio.gather(*tasks)
        
        logger.info("💾 크롤링 결과 처리 및 데이터베이스 저장을 시작합니다.")
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            for i, result in enumerate(results, 1):
                if result:
                    # 1. 파일에 기록 (기존 기능 유지)
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    scraped_count += 1
                    
                    # 2. 데이터베이스에 저장
                    db_tasks.append(insert_recipe_data(DB_POOL, result))
                    
                    # 진행률 표시 (10개마다)
                    if i % 10 == 0:
                        logger.info(f"📈 진행률: {i}/{len(results)} ({i/len(results)*100:.1f}%)")
                else:
                    failed_count += 1

            if db_tasks:
                logger.info("💾 데이터베이스 저장 시작...")
                await asyncio.gather(*db_tasks)
    
    total_time = time.time() - start_time
    logger.info("=" * 60)
    logger.info("🎉 크롤링 및 저장 완료!")
    logger.info(f"📊 최종 통계:")
    logger.info(f"   ✅ 성공: {scraped_count}개")
    logger.info(f"   ❌ 실패: {failed_count}개")
    logger.info(f"   ⏱️ 총 소요시간: {total_time:.2f}초")
    logger.info(f"   📁 출력파일: {OUTPUT_FILENAME}")
    logger.info("=" * 60)

if __name__ == "__main__":
    try:
        logger.info(f"🕐 크롤러 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("⚠️ 사용자에 의해 크롤링이 중단되었습니다.")
    except Exception as e:
        logger.error(f"🚨 예상치 못한 오류 발생: {e}")
    finally:
        if DB_POOL:
            DB_POOL.closeall()
            logger.info("✅ 데이터베이스 커넥션 풀을 모두 닫았습니다.")
        logger.info(f"🕐 크롤러 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")