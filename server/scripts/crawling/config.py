"""
크롤링 설정 파일
"""
import os
from typing import List, Dict

class CrawlingConfig:
    """크롤링 설정"""
    
    # 기본 설정
    BASE_URL = "https://www.10000recipe.com"
    RECIPE_LIST_URL = "/recipe/list.html"
    
    # 크롤링 속도 제어
    DELAY_BETWEEN_REQUESTS = 1.0  # 초
    DELAY_BETWEEN_PAGES = 2.0     # 초
    MAX_RETRIES = 3
    
    # 배치 처리 설정
    BATCH_SIZE = 50               # 한 번에 처리할 레시피 수
    MAX_RECIPES_PER_CATEGORY = 2000  # 카테고리당 최대 레시피 수
    TOTAL_TARGET_RECIPES = 10000  # 전체 목표 레시피 수
    
    # 카테고리 설정
    CATEGORIES = {
        "": "전체",
        "1": "밑반찬", 
        "2": "메인반찬",
        "3": "국/탕",
        "4": "찌개",
        "5": "디저트",
        "6": "면/만두",
        "7": "밥/죽/떡",
        "8": "퓨전",
        "9": "김치/젓갈/장류",
        "10": "양념/소스/잼",
        "11": "양식",
        "12": "샐러드",
        "13": "스프",
        "14": "빵",
        "15": "과자",
        "16": "차/음료/술",
        "17": "기타"
    }
    
    # 데이터 검증 설정
    MIN_INGREDIENTS = 1           # 최소 재료 수
    MIN_COOKING_STEPS = 1         # 최소 조리 단계 수
    MAX_TITLE_LENGTH = 255        # 최대 제목 길이
    
    # 로깅 설정
    LOG_LEVEL = "INFO"
    LOG_FILE = "crawling.log"
    
    # Supabase 설정
    SUPABASE_BATCH_SIZE = 100     # Supabase 배치 삽입 크기


