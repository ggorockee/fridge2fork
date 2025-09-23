"""
만개의 레시피 크롤링 시스템 설정
Phase 1: 프로토타입용 설정
"""

import os
from pathlib import Path

# 프로젝트 기본 설정
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# 타겟 사이트 설정
TARGET_SITE = {
    'base_url': 'https://www.10000recipe.com',
    'recipe_list_url': '/recipe/list.html',
    'categories': [
        {'name': '전체', 'code': ''},
        {'name': '밥/죽/떡', 'code': '63'},
        {'name': '국/탕/찌개', 'code': '56'},
        {'name': '반찬/김치/장아찌', 'code': '54'},
        {'name': '면/파스타', 'code': '53'},
        {'name': '디저트', 'code': '60'}
    ]
}

# 크롤링 설정
CRAWLING_CONFIG = {
    'max_recipes': 5,  # 더 작은 목표로 테스트
    'delay_between_requests': 5,  # 더 긴 지연시간
    'timeout': 60000,  # 60초로 타임아웃 증가
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'headless': False,  # 디버깅을 위해 헤드리스 모드 해제
    'max_retries': 2  # 재시도 횟수 축소
}

# CSS 셀렉터 (실제 사이트 구조에 맞게 조정 필요)
SELECTORS = {
    'recipe_list': '.common_sp_list_ul li',
    'recipe_link': 'a',
    'recipe_title': '.common_sp_caption_tit',
    'recipe_image': '.common_sp_thumb img',
    'recipe_rating': '.common_sp_star_p',
    'recipe_detail': {
        'title': 'h1.recipe-title, .view_recipe h3',
        'ingredients': '.ready_ingre3 li, .recipe_ingredient li',
        'description': '.view_recipe_intro, .recipe_intro',
        'cooking_time': '.view_recipe_info li:contains("조리시간")',
        'servings': '.view_recipe_info li:contains("인분")',
        'difficulty': '.view_recipe_info li:contains("난이도")',
        'cooking_steps': '.view_step_cont, .recipe_step'
    }
}

# 한국어 재료 정규화 패턴
NORMALIZATION_PATTERNS = {
    'quantity_patterns': {
        'integer': r'(\d+)(개|스푼|큰술|작은술|컵|g|ml|kg|L|cc|T|t)',
        'decimal': r'(\d+\.?\d*)(개|스푼|큰술|작은술|컵|g|ml|kg|L|cc|T|t)',
        'fraction': r'(\d+/\d+)(개|스푼|큰술|작은술|컵|g|ml|kg|L|cc|T|t)',
        'range': r'(\d+)~(\d+)(개|스푼|큰술|작은술|컵|g|ml|kg|L|cc|T|t)'
    },
    'unit_mapping': {
        '스푼': '큰술',
        'T': '큰술',
        't': '작은술',
        '큰수저': '큰술',
        '작은수저': '작은술',
        'ml': 'ml',
        'L': 'ml',  # 1000ml로 변환
        'cc': 'ml',
        'kg': 'g'   # 1000g로 변환
    },
    'ingredient_mapping': {
        '양파(중간크기)': '양파',
        '양파(소)': '양파',
        '양파(대)': '양파',
        '당근(중간크기)': '당근',
        '대파': '파',
        '쪽파': '파',
        '청양고추': '고추',
        '홍고추': '고추'
    },
    'vague_quantities': {
        '적당히': 1,
        '조금': 0.5,
        '약간': 0.3,
        '많이': 2,
        '한줌': 1,
        '한꼬집': 0.1
    }
}

# 데이터 품질 검증 규칙
VALIDATION_RULES = {
    'recipe_title': {
        'required': True,
        'min_length': 2,
        'max_length': 200
    },
    'ingredients': {
        'required': True,
        'min_count': 2,
        'max_count': 50
    },
    'cooking_time': {
        'required': False,
        'min_value': 1,
        'max_value': 600  # 분
    }
}

# 로깅 설정
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': LOGS_DIR / 'crawler.log',
    'max_bytes': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# Export 설정
EXPORT_CONFIG = {
    'csv_file': DATA_DIR / 'recipes.csv',
    'json_file': DATA_DIR / 'recipes.json',
    'encoding': 'utf-8',
    'include_raw_data': True
}

def create_directories():
    """필요한 디렉토리들을 생성합니다."""
    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

if __name__ == "__main__":
    create_directories()
    print("Configuration loaded successfully!")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Logs directory: {LOGS_DIR}")