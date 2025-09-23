# Fridge2Fork 크롤링 및 데이터 설계 계획서

## 📋 프로젝트 개요

### 목표
만개의레시피 사이트에서 한식 레시피 데이터를 체계적으로 수집하여 Fridge2Fork 모바일 앱에 통합할 수 있는 형태로 가공하는 시스템 구축

### 핵심 요구사항
- **데이터 소스**: 만개의레시피 (HTML 스크래핑 기반)
- **타겟 앱**: Fridge2Fork (Flutter 멀티플랫폼)
- **데이터 규모**: 10,000-50,000개 레시피
- **데이터 품질**: 높은 정확도와 일관성 보장

## 🏗️ Phase별 실행 계획

---

## Phase 1: 인프라 구축 및 데이터 수집 전략 (2-3주)

### 1.1 기술 스택 선정 및 환경 구축

#### 크롤링 도구
```python
# 핵심 라이브러리
- Selenium WebDriver (JavaScript 렌더링)
- BeautifulSoup4 (HTML 파싱)
- Requests (HTTP 요청)
- Scrapy (대규모 크롤링 프레임워크)
```

#### 데이터 저장소
```yaml
Primary Database: PostgreSQL
  - 관계형 데이터 구조
  - ACID 트랜잭션 보장
  - 복잡한 쿼리 지원

Cache Layer: Redis
  - 세션 관리
  - 요청 캐싱
  - 실시간 모니터링

File Storage: AWS S3 / GCS
  - 이미지 저장
  - 백업 관리
```

#### 개발 환경
```dockerfile
# Docker 컨테이너화
- Python 3.11 환경
- Chrome/Chromium 헤드리스 브라우저
- PostgreSQL 15
- Redis 7
```

### 1.2 데이터베이스 스키마 설계

#### Core Tables
```sql
-- 레시피 기본 정보
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(20) UNIQUE NOT NULL,  -- 만개레시피 ID
    title VARCHAR(255) NOT NULL,
    description TEXT,
    image_url TEXT,
    category VARCHAR(100),
    difficulty VARCHAR(20),
    cooking_time_minutes INTEGER,
    servings INTEGER,
    rating DECIMAL(3,2),
    review_count INTEGER,
    is_popular BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 재료 정보
CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id),
    name VARCHAR(100) NOT NULL,
    amount VARCHAR(50),
    is_essential BOOLEAN DEFAULT TRUE,
    normalized_name VARCHAR(100),  -- 정규화된 재료명
    created_at TIMESTAMP DEFAULT NOW()
);

-- 조리 단계
CREATE TABLE cooking_steps (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id),
    step_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 이미지 정보
CREATE TABLE recipe_images (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id),
    image_url TEXT NOT NULL,
    local_path TEXT,
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 1.3 크롤링 규칙 및 에티켓 정의

#### 크롤링 정책
```python
CRAWLING_CONFIG = {
    "request_delay": 1.5,  # 요청 간 지연시간 (초)
    "max_concurrent": 3,   # 동시 요청 수
    "retry_attempts": 3,   # 재시도 횟수
    "timeout": 30,         # 요청 타임아웃
    "user_agents": [       # User-Agent 로테이션
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ]
}
```

#### 법적 준수사항
- robots.txt 준수
- 이용약관 확인 및 준수
- 데이터 사용 목적 명시
- 개인정보 보호 규정 준수

---

## Phase 2: 핵심 데이터 수집 (4-6주)

### 2.1 레시피 목록 수집

#### 목록 페이지 스크래핑
```python
class RecipeListScraper:
    def __init__(self):
        self.base_url = "https://www.10000recipe.com/recipe/list.html"
        self.categories = [
            "한식", "중식", "일식", "양식", "분식", 
            "간식", "음료", "베이킹", "반찬", "국/탕"
        ]
    
    def scrape_category_pages(self, category: str):
        """카테고리별 레시피 목록 수집"""
        # 페이지네이션 처리
        # 레시피 ID 추출
        # 메타데이터 수집
        pass
    
    def extract_recipe_ids(self, page_html: str) -> List[str]:
        """HTML에서 레시피 ID 추출"""
        # 정규식 또는 CSS 셀렉터 사용
        pass
```

#### 예상 수집 규모
- **총 레시피 수**: 50,000개
- **카테고리별 분포**: 한식 40%, 기타 60%
- **일일 수집량**: 2,000-3,000개

### 2.2 레시피 상세 정보 수집

#### 상세 페이지 스크래핑
```python
class RecipeDetailScraper:
    def scrape_recipe_detail(self, recipe_id: str) -> Dict:
        """레시피 상세 정보 수집"""
        url = f"https://www.10000recipe.com/recipe/{recipe_id}"
        
        # 페이지 로딩 및 데이터 추출
        soup = self.get_page_content(url)
        
        return {
            "basic_info": self.extract_basic_info(soup),
            "ingredients": self.extract_ingredients(soup),
            "cooking_steps": self.extract_cooking_steps(soup),
            "images": self.extract_images(soup),
            "metadata": self.extract_metadata(soup)
        }
    
    def extract_ingredients(self, soup) -> List[Dict]:
        """재료 정보 추출"""
        # CSS 셀렉터: a[href*="javascript:viewMaterial"]
        # 재료명과 양 추출
        pass
    
    def extract_cooking_steps(self, soup) -> List[Dict]:
        """조리 단계 추출"""
        # CSS 셀렉터: .view_step > div
        # 단계별 설명 추출
        pass
```

### 2.3 이미지 수집 및 처리

#### 이미지 다운로드 시스템
```python
class ImageDownloader:
    def download_recipe_images(self, recipe_id: str, image_urls: List[str]):
        """레시피 이미지 다운로드"""
        for url in image_urls:
            # 이미지 다운로드
            # 리사이징 (최적화)
            # S3/GCS 업로드
            # 로컬 경로 저장
            pass
    
    def optimize_image(self, image_path: str) -> str:
        """이미지 최적화"""
        # 크기 조정 (최대 800x600)
        # 품질 최적화 (JPEG 85%)
        # 메타데이터 제거
        pass
```

---

## Phase 3: 데이터 정제 및 정규화 (3-4주)

### 3.1 재료명 표준화

#### 재료 정규화 시스템
```python
class IngredientNormalizer:
    def __init__(self):
        self.ingredient_mapping = {
            "감자": ["감자", "포테이토", "potato"],
            "양파": ["양파", "onion"],
            "마늘": ["마늘", "garlic"],
            # ... 더 많은 매핑
        }
    
    def normalize_ingredient(self, raw_name: str) -> str:
        """재료명 정규화"""
        # 불필요한 문자 제거
        # 단위 정보 분리
        # 표준명으로 변환
        pass
    
    def extract_amount(self, raw_text: str) -> Dict[str, str]:
        """양과 단위 분리"""
        # "감자 4개" -> {"ingredient": "감자", "amount": "4", "unit": "개"}
        pass
```

#### 재료 분류 시스템
```python
INGREDIENT_CATEGORIES = {
    "정육/계란": ["돼지고기", "소고기", "닭고기", "계란"],
    "수산물": ["생선", "새우", "게", "오징어"],
    "채소": ["양파", "마늘", "감자", "당근"],
    "장/양념/오일": ["된장", "고추장", "간장", "식용유"]
}
```

### 3.2 조리 단계 정리

#### 단계 표준화
```python
class CookingStepProcessor:
    def standardize_steps(self, raw_steps: List[str]) -> List[Dict]:
        """조리 단계 표준화"""
        processed_steps = []
        
        for i, step in enumerate(raw_steps):
            # 불필요한 텍스트 제거
            # 단계별 설명 정리
            # 이미지 정보 연결
            processed_steps.append({
                "step": i + 1,
                "description": self.clean_description(step),
                "image_url": self.extract_step_image(step)
            })
        
        return processed_steps
```

### 3.3 데이터 품질 관리

#### 검증 시스템
```python
class DataValidator:
    def validate_recipe(self, recipe_data: Dict) -> Dict[str, List[str]]:
        """레시피 데이터 검증"""
        errors = []
        warnings = []
        
        # 필수 필드 검증
        if not recipe_data.get("title"):
            errors.append("제목이 없습니다")
        
        if not recipe_data.get("ingredients"):
            errors.append("재료 정보가 없습니다")
        
        # 데이터 품질 검증
        if len(recipe_data.get("ingredients", [])) < 2:
            warnings.append("재료가 너무 적습니다")
        
        return {"errors": errors, "warnings": warnings}
```

---

## Phase 4: Fridge2Fork 앱 통합 (2-3주)

### 4.1 앱 데이터 모델 매핑

#### Flutter 앱 모델 변환
```dart
// Fridge2Fork 앱의 Recipe 모델
class Recipe {
  final String id;
  final String name;
  final String description;
  final String imageUrl;
  final int cookingTimeMinutes;
  final int servings;
  final String difficulty;
  final String category;
  final double rating;
  final int reviewCount;
  final bool isPopular;
  final List<Ingredient> ingredients;
  final List<CookingStep> cookingSteps;
}

// 데이터베이스 → 앱 모델 변환
class RecipeMapper {
  static Recipe fromDatabase(RecipeEntity entity) {
    return Recipe(
      id: entity.sourceId,
      name: entity.title,
      description: entity.description ?? '',
      imageUrl: entity.imageUrl ?? '',
      cookingTimeMinutes: entity.cookingTimeMinutes ?? 0,
      servings: entity.servings ?? 1,
      difficulty: entity.difficulty ?? '보통',
      category: entity.category ?? '기타',
      rating: entity.rating?.toDouble() ?? 0.0,
      reviewCount: entity.reviewCount ?? 0,
      isPopular: entity.isPopular,
      ingredients: entity.ingredients.map((i) => IngredientMapper.fromEntity(i)).toList(),
      cookingSteps: entity.cookingSteps.map((s) => CookingStepMapper.fromEntity(s)).toList(),
    );
  }
}
```

### 4.2 JSON 변환 시스템

#### 앱용 JSON 생성
```python
class AppDataGenerator:
    def generate_recipes_json(self) -> str:
        """앱용 레시피 JSON 생성"""
        recipes = self.get_all_recipes()
        
        app_data = {
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "total_recipes": len(recipes),
            "recipes": []
        }
        
        for recipe in recipes:
            app_recipe = self.convert_to_app_format(recipe)
            app_data["recipes"].append(app_recipe)
        
        return json.dumps(app_data, ensure_ascii=False, indent=2)
    
    def convert_to_app_format(self, recipe: RecipeEntity) -> Dict:
        """데이터베이스 모델을 앱 형식으로 변환"""
        return {
            "id": recipe.source_id,
            "name": recipe.title,
            "description": recipe.description or "",
            "imageUrl": recipe.image_url or "",
            "cookingTimeMinutes": recipe.cooking_time_minutes or 0,
            "servings": recipe.servings or 1,
            "difficulty": recipe.difficulty or "보통",
            "category": recipe.category or "기타",
            "rating": float(recipe.rating or 0),
            "reviewCount": recipe.review_count or 0,
            "isPopular": recipe.is_popular,
            "ingredients": [
                {
                    "name": ing.name,
                    "amount": ing.amount,
                    "isEssential": ing.is_essential
                }
                for ing in recipe.ingredients
            ],
            "cookingSteps": [
                {
                    "step": step.step_number,
                    "description": step.description,
                    "imageUrl": step.image_url or ""
                }
                for step in recipe.cooking_steps
            ]
        }
```

### 4.3 성능 최적화

#### 앱 성능 고려사항
```python
class PerformanceOptimizer:
    def optimize_for_mobile(self, recipes_data: List[Dict]) -> Dict:
        """모바일 앱 성능 최적화"""
        # 이미지 URL 최적화
        # 데이터 크기 최적화
        # 페이지네이션 지원
        pass
    
    def create_paginated_data(self, recipes: List[Dict], page_size: int = 20) -> List[Dict]:
        """페이지네이션 데이터 생성"""
        paginated_data = []
        
        for i in range(0, len(recipes), page_size):
            page = recipes[i:i + page_size]
            paginated_data.append({
                "page": i // page_size + 1,
                "recipes": page,
                "has_more": i + page_size < len(recipes)
            })
        
        return paginated_data
```

---

## Phase 5: 운영 및 유지보수 (지속적)

### 5.1 자동화 시스템 구축

#### 스케줄링 시스템
```python
# Celery 기반 작업 스케줄링
from celery import Celery

app = Celery('recipe_crawler')

@app.task
def daily_crawl_new_recipes():
    """일일 신규 레시피 크롤링"""
    scraper = RecipeListScraper()
    new_recipes = scraper.find_new_recipes()
    
    for recipe_id in new_recipes:
        scrape_recipe_detail.delay(recipe_id)

@app.task
def weekly_data_validation():
    """주간 데이터 검증 및 정리"""
    validator = DataValidator()
    validator.validate_all_recipes()
```

#### 모니터링 시스템
```python
class CrawlingMonitor:
    def __init__(self):
        self.prometheus_client = PrometheusClient()
    
    def track_crawling_metrics(self):
        """크롤링 지표 모니터링"""
        metrics = {
            "recipes_crawled_total": self.count_crawled_recipes(),
            "crawling_errors_total": self.count_crawling_errors(),
            "data_quality_score": self.calculate_quality_score(),
            "images_downloaded_total": self.count_downloaded_images()
        }
        
        self.prometheus_client.record_metrics(metrics)
```

### 5.2 데이터 품질 관리

#### 품질 모니터링 대시보드
```python
class QualityDashboard:
    def generate_quality_report(self) -> Dict:
        """데이터 품질 보고서 생성"""
        return {
            "total_recipes": self.get_total_recipes_count(),
            "complete_recipes": self.get_complete_recipes_count(),
            "recipes_with_images": self.get_recipes_with_images_count(),
            "average_ingredients_per_recipe": self.get_avg_ingredients_count(),
            "data_freshness": self.get_last_update_time(),
            "quality_issues": self.get_quality_issues()
        }
    
    def get_quality_issues(self) -> List[Dict]:
        """품질 문제 목록"""
        issues = []
        
        # 이미지 없는 레시피
        issues.append({
            "type": "missing_images",
            "count": self.count_recipes_without_images(),
            "severity": "medium"
        })
        
        # 재료 정보 부족
        issues.append({
            "type": "insufficient_ingredients",
            "count": self.count_recipes_with_few_ingredients(),
            "severity": "high"
        })
        
        return issues
```

### 5.3 확장성 고려사항

#### 대규모 처리 지원
```python
class ScalableCrawler:
    def __init__(self):
        self.worker_nodes = 5  # 작업자 노드 수
        self.redis_cluster = RedisCluster()
    
    def distribute_crawling_tasks(self, recipe_ids: List[str]):
        """크롤링 작업 분산 처리"""
        chunk_size = len(recipe_ids) // self.worker_nodes
        
        for i in range(self.worker_nodes):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < self.worker_nodes - 1 else len(recipe_ids)
            
            chunk = recipe_ids[start_idx:end_idx]
            self.redis_cluster.enqueue_task("crawl_recipes", chunk)
```

---

## 📊 예상 일정 및 리소스

### 타임라인
```
Phase 1: 인프라 구축 (2-3주)
├─ 주 1: 기술 스택 선정 및 환경 구축
├─ 주 2: 데이터베이스 설계 및 구현
└─ 주 3: 크롤링 시스템 기본 구조

Phase 2: 데이터 수집 (4-6주)
├─ 주 1-2: 레시피 목록 수집
├─ 주 3-4: 상세 정보 수집
└─ 주 5-6: 이미지 수집 및 처리

Phase 3: 데이터 정제 (3-4주)
├─ 주 1-2: 재료명 정규화
├─ 주 3: 조리 단계 정리
└─ 주 4: 품질 검증

Phase 4: 앱 통합 (2-3주)
├─ 주 1-2: 데이터 모델 매핑
└─ 주 3: JSON 생성 및 최적화

Phase 5: 운영 (지속적)
├─ 자동화 시스템 구축
├─ 모니터링 대시보드
└─ 지속적 개선
```

### 필요 리소스
- **개발자**: 2-3명 (백엔드 1명, 데이터 엔지니어 1명, 품질 관리 1명)
- **인프라**: 클라우드 서버 (AWS/GCP)
- **저장소**: 데이터베이스, 파일 저장소
- **모니터링**: 로깅 및 메트릭 수집 시스템

### 예상 비용
- **개발 비용**: 3-4개월 개발 기간
- **인프라 비용**: 월 $200-500 (서버, 저장소)
- **유지보수**: 월 $100-200 (모니터링, 백업)

---

## ⚠️ 위험 요소 및 대응 방안

### 기술적 위험
1. **웹사이트 구조 변경**
   - 대응: 유연한 셀렉터 시스템, 정기적 구조 분석
2. **크롤링 차단**
   - 대응: IP 로테이션, User-Agent 변경, 요청 패턴 변경
3. **데이터 품질 저하**
   - 대응: 자동 검증 시스템, 수동 검토 프로세스

### 법적 위험
1. **저작권 문제**
   - 대응: 이용약관 준수, 데이터 사용 목적 명시
2. **개인정보 보호**
   - 대응: 개인정보 제외, 익명화 처리

### 운영 위험
1. **서버 부하**
   - 대응: 점진적 확장, 로드 밸런싱
2. **데이터 손실**
   - 대응: 정기 백업, 복제본 관리

---

## 🎯 성공 지표

### 데이터 품질 지표
- **완전성**: 95% 이상의 레시피가 필수 정보 포함
- **정확성**: 90% 이상의 재료명 정규화 성공
- **일관성**: 95% 이상의 데이터 형식 통일

### 시스템 성능 지표
- **처리 속도**: 일일 3,000개 레시피 처리
- **가용성**: 99.5% 이상 시스템 가동률
- **응답 시간**: 평균 2초 이내 API 응답

### 앱 통합 지표
- **호환성**: Fridge2Fork 앱과 100% 호환
- **성능**: 앱 로딩 시간 3초 이내
- **사용성**: 사용자 만족도 4.5/5.0 이상

---

## 📝 결론

이 계획서는 만개의레시피에서 Fridge2Fork 앱으로의 체계적인 데이터 수집 및 통합 프로세스를 제시합니다. 

각 Phase는 명확한 목표와 산출물을 가지고 있으며, 단계별로 검증과 개선이 가능한 구조로 설계되었습니다. 특히 데이터 품질 관리와 법적 준수사항을 중점적으로 고려하여 안정적이고 확장 가능한 시스템 구축을 목표로 합니다.

성공적인 구현을 통해 Fridge2Fork 앱의 레시피 데이터베이스를 크게 확장하고, 사용자에게 더욱 풍부한 요리 경험을 제공할 수 있을 것입니다.
