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
import psutil

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

# 환경변수로 설정 제어 (ConfigMap으로 주입)
TARGET_RECIPE_COUNT = int(os.getenv('TARGET_RECIPE_COUNT', '100'))
BASE_URL = "https://www.10000recipe.com"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
HEADERS = {'User-Agent': USER_AGENT}
OUTPUT_FILENAME = "recipes.jsonl"
CONCURRENT_REQUESTS = int(os.getenv('CONCURRENT_REQUESTS', '2'))  # 매우 보수적
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '5'))  # 작은 배치 크기
REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '3.0'))  # 요청 간 지연
BATCH_DELAY = float(os.getenv('BATCH_DELAY', '5.0'))  # 배치 간 지연
PROGRESS_INTERVAL = int(os.getenv('PROGRESS_INTERVAL', '10'))  # 진행률 표시 간격
MEMORY_CHECK_INTERVAL = int(os.getenv('MEMORY_CHECK_INTERVAL', '50'))  # 메모리 체크 간격

# 메모리 효율성을 위한 청크 설정
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '100'))  # 한 번에 처리할 URL 청크 크기
CHUNK_DELAY = float(os.getenv('CHUNK_DELAY', '10.0'))  # 청크 간 지연 (메모리 정리 시간)

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
def log_memory_usage():
    """메모리 사용량을 로깅합니다."""
    try:
        memory = psutil.virtual_memory()
        logger.info(f"💾 메모리 사용량: {memory.percent}% ({memory.used / 1024**3:.2f}GB / {memory.total / 1024**3:.2f}GB)")
        
        # 메모리 사용량이 80% 이상이면 경고
        if memory.percent > 80:
            logger.warning(f"⚠️ 메모리 사용량이 높습니다: {memory.percent}%")
    except Exception as e:
        logger.debug(f"메모리 정보 조회 실패: {e}")

def parse_ingredient(text):
    """
    단일 재료 텍스트를 파싱하여 이름, 수량, 단위로 구조화합니다.
    예: "다진 마늘 1/2큰술" -> {'name': '다진 마늘', 'quantity_from': 0.5, 'quantity_to': None, 'unit': '큰술'}
    예: "청양고추 약간" -> {'name': '청양고추', 'is_vague': True, 'vague_description': '약간', 'importance': 'optional'}
    """
    original_text = text.replace("구매", "").strip()
    text = original_text

    # 모호한 수량 표현 체크
    vague_indicators = ["약간", "적당히", "조금", "많이", "적당량"]
    
    for indicator in vague_indicators:
        if indicator in text:
            # 모호한 표현을 제거하고 앞뒤 공백도 정리
            clean_name = text.replace(indicator, "").strip()
            # 추가 공백 제거
            clean_name = re.sub(r'\s+', ' ', clean_name)
            
            return {
                "name": clean_name,
                "quantity_from": None,
                "quantity_to": None,
                "unit": None,
                "is_vague": True,
                "vague_description": indicator,
                "importance": "optional"
            }

    # 정확한 수량이 있는 경우 기존 로직
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

    return {
        "name": name, 
        "quantity_from": quant_from, 
        "quantity_to": quant_to, 
        "unit": unit,
        "is_vague": False,
        "importance": "essential"
    }

# --- Database Functions ---
async def insert_recipe_batch(pool, recipe_batch):
    """
    여러 레시피 데이터를 배치로 데이터베이스에 저장합니다.
    모든 레시피를 하나의 트랜잭션으로 처리하여 성능을 최적화합니다.
    """
    conn = None
    try:
        conn = pool.getconn()
        cursor = conn.cursor()
        
        success_count = 0
        
        # 배치 내 모든 레시피를 하나의 트랜잭션으로 처리
        for recipe_data in recipe_batch:
            try:
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
                    # 2a. ingredients 테이블에 Upsert (is_vague, vague_description 포함)
                    cursor.execute(
                        """INSERT INTO ingredients (name, is_vague, vague_description)
                           VALUES (%s, %s, %s)
                           ON CONFLICT (name) DO UPDATE SET
                             is_vague = EXCLUDED.is_vague,
                             vague_description = EXCLUDED.vague_description
                           RETURNING ingredient_id;""",
                        (ing['name'], ing.get('is_vague', False), ing.get('vague_description'))
                    )
                    result = cursor.fetchone()
                    if result:
                        ingredient_id = result[0]
                    else:
                        # 이미 존재하여 id가 반환되지 않은 경우, id를 조회
                        cursor.execute("SELECT ingredient_id FROM ingredients WHERE name = %s;", (ing['name'],))
                        ingredient_id = cursor.fetchone()[0]

                    # 2b. recipe_ingredients 테이블에 Upsert (importance 포함)
                    cursor.execute(
                        """INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity_from, quantity_to, unit, importance)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           ON CONFLICT (recipe_id, ingredient_id) DO UPDATE SET
                             quantity_from = EXCLUDED.quantity_from,
                             quantity_to = EXCLUDED.quantity_to,
                             unit = EXCLUDED.unit,
                             importance = EXCLUDED.importance;""",
                        (recipe_id, ingredient_id, ing['quantity_from'], ing['quantity_to'], 
                         ing['unit'], ing.get('importance', 'essential'))
                    )
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"❌ 배치 내 레시피 저장 실패: {recipe_data.get('title', 'N/A')} - {e}")
                # 개별 레시피 실패는 전체 배치를 중단시키지 않음
                continue
        
        # 배치 전체를 하나의 트랜잭션으로 커밋
        conn.commit()
        logger.info(f"✅ 배치 저장 완료: {success_count}/{len(recipe_batch)}개 성공 (트랜잭션 커밋)")
        
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"❌ 배치 저장 실패: {error}")
        if conn:
            conn.rollback()
            logger.error("🔄 배치 트랜잭션 롤백 완료")
    finally:
        if conn:
            pool.putconn(conn)

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
def get_recipe_urls_generator(target_count):
    """
    목표 수량에 도달할 때까지 페이지를 넘기며 레시피 URL을 생성기로 반환합니다.
    메모리 효율성을 위해 URL을 한 번에 모두 수집하지 않고 스트리밍 방식으로 제공합니다.
    """
    logger.info(f"🚀 레시피 URL 수집 시작 - 목표: {target_count}개 (스트리밍 모드)")
    start_time = time.time()
    collected_count = 0
    page = 1
    
    while collected_count < target_count:
        list_url = f"{BASE_URL}/recipe/list.html?page={page}"
        if not rp.can_fetch(USER_AGENT, list_url):
            logger.warning(f"⚠️ robots.txt에 의해 페이지 {page} 접근이 차단됨")
            break

        logger.info(f"📄 페이지 {page} 처리 중... (현재 수집: {collected_count}/{target_count})")
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
                if collected_count >= target_count:
                    break
                    
                href = link['href']
                full_url = BASE_URL + href if not href.startswith('http') else href
                if rp.can_fetch(USER_AGENT, full_url):
                    yield full_url
                    collected_count += 1
                    new_links_count += 1
            
            logger.info(f"✅ 페이지 {page} 완료 - 새로 수집된 링크: {new_links_count}개")
            page += 1
            time.sleep(REQUEST_DELAY) # 서버 부하를 줄이기 위한 지연

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 페이지 {page} 요청 실패: {e} - {REQUEST_DELAY * 2}초 후 재시도")
            time.sleep(REQUEST_DELAY * 2)

    elapsed_time = time.time() - start_time
    logger.info(f"🎯 URL 수집 완료 - 총 {collected_count}개 수집 (소요시간: {elapsed_time:.2f}초)")

# --- Asynchronous Functions ---
async def scrape_recipe_details(session, url, semaphore):
    """
    비동기적으로 개별 레시피 페이지의 상세 정보를 스크랩합니다.
    """
    async with semaphore:
        try:
            await asyncio.sleep(REQUEST_DELAY) # 추가적인 요청 간 지연
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

async def process_chunk(session, urls_chunk, semaphore):
    """
    URL 청크를 처리하는 함수. 메모리 효율성을 위해 청크 단위로 처리합니다.
    """
    logger.info(f"🔄 청크 처리 시작: {len(urls_chunk)}개 URL")
    
    # 청크 내에서만 비동기 처리
    tasks = [scrape_recipe_details(session, url, semaphore) for url in urls_chunk]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 결과 처리 및 즉시 DB 저장
    valid_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"❌ 청크 처리 중 예외 발생: {result}")
            continue
        if result:
            valid_results.append(result)
    
    # 청크 결과를 즉시 DB에 저장
    if valid_results:
        logger.info(f"💾 청크 결과 저장: {len(valid_results)}개")
        await insert_recipe_batch(DB_POOL, valid_results)
    
    # 메모리 정리를 위한 가비지 컬렉션
    import gc
    gc.collect()
    
    logger.info(f"✅ 청크 처리 완료: {len(valid_results)}개 성공")
    return len(valid_results)

async def main():
    """
    메모리 효율적인 스트리밍 크롤링 프로세스를 총괄하는 메인 함수.
    URL을 한 번에 모두 수집하지 않고 스트리밍 방식으로 처리하여 OOM을 방지합니다.
    """
    logger.info("=" * 60)
    logger.info("🚀 만개의 레시피 크롤러 시작 (스트리밍 모드)")
    logger.info(f"📊 설정: 목표 {TARGET_RECIPE_COUNT}개, 동시 요청 {CONCURRENT_REQUESTS}개")
    logger.info(f"📊 청크 크기: {CHUNK_SIZE}개, 배치 크기: {BATCH_SIZE}개")
    logger.info(f"📊 요청 지연: {REQUEST_DELAY}초, 청크 지연: {CHUNK_DELAY}초")
    logger.info("=" * 60)
    
    # 초기 메모리 상태 로깅
    log_memory_usage()
    
    if not DB_POOL:
        logger.error("🚨 데이터베이스 연결이 설정되지 않았습니다. 스크립트를 종료합니다.")
        return

    start_time = time.time()
    total_scraped = 0
    total_failed = 0
    chunk_idx = 0
    
    # URL 생성기로부터 스트리밍 처리
    url_generator = get_recipe_urls_generator(TARGET_RECIPE_COUNT)
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    
    async with aiohttp.ClientSession() as session:
        current_chunk = []
        
        for url in url_generator:
            current_chunk.append(url)
            
            # 청크가 가득 차면 처리
            if len(current_chunk) >= CHUNK_SIZE:
                chunk_idx += 1
                logger.info(f"🔄 청크 {chunk_idx} 처리 시작 ({len(current_chunk)}개 URL)")
                
                # 청크 처리
                scraped_count = await process_chunk(session, current_chunk, semaphore)
                total_scraped += scraped_count
                total_failed += len(current_chunk) - scraped_count
                
                # 진행률 표시
                progress = min(chunk_idx * CHUNK_SIZE, TARGET_RECIPE_COUNT)
                logger.info(f"📈 전체 진행률: {progress}/{TARGET_RECIPE_COUNT} ({progress/TARGET_RECIPE_COUNT*100:.1f}%)")
                
                # 메모리 사용량 체크
                log_memory_usage()
                
                # 청크 간 지연
                logger.info(f"⏳ 다음 청크까지 {CHUNK_DELAY}초 대기 (메모리 정리 시간)")
                await asyncio.sleep(CHUNK_DELAY)
                
                # 청크 초기화
                current_chunk = []
        
        # 마지막 청크 처리 (남은 URL들)
        if current_chunk:
            chunk_idx += 1
            logger.info(f"🔄 마지막 청크 {chunk_idx} 처리 시작 ({len(current_chunk)}개 URL)")
            
            scraped_count = await process_chunk(session, current_chunk, semaphore)
            total_scraped += scraped_count
            total_failed += len(current_chunk) - scraped_count
            
            # 최종 진행률 표시
            logger.info(f"📈 전체 진행률: {TARGET_RECIPE_COUNT}/{TARGET_RECIPE_COUNT} (100.0%)")
            log_memory_usage()
    
    total_time = time.time() - start_time
    logger.info("=" * 60)
    logger.info("🎉 크롤링 및 저장 완료!")
    logger.info(f"📊 최종 통계:")
    logger.info(f"   ✅ 성공: {total_scraped}개")
    logger.info(f"   ❌ 실패: {total_failed}개")
    logger.info(f"   ⏱️ 총 소요시간: {total_time:.2f}초")
    logger.info(f"   💾 데이터베이스에 저장 완료")
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