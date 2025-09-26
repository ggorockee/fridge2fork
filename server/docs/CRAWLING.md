# Fridge2Fork 레시피 크롤링 전략 및 계획서

## 📋 프로젝트 개요
Fridge2Fork 앱을 위한 만개의레시피(10000recipe.com) 크롤링 시스템 구축 계획서입니다.
냉장고 재료 기반 맞춤형 한식 레시피 추천 서비스를 위한 데이터 수집 및 저장 전략을 다룹니다.

## 🎯 목표
- **주요 목표**: 사용자 보유 재료를 기반으로 최적의 레시피 추천
- **핵심 기능**: 재료 매칭율 계산, 부족한 재료 식별, 개인화 추천
- **데이터 품질**: 정확하고 표준화된 레시피 및 재료 정보 구축

## 🔍 크롤링 대상 분석

### 대상 사이트
- **URL**: https://www.10000recipe.com/
- **특징**: 한국 최대 레시피 커뮤니티, 다양한 한식 레시피 보유
- **구조**: 카테고리별 분류, 페이지네이션, 상세 레시피 페이지

### 수집 데이터 범위
1. **레시피 기본 정보**
   - 제목, 설명, 작성자
   - 카테고리 (찌개, 볶음, 반찬, 밥, 김치, 국, 면)
   - 난이도 (쉬움, 보통, 어려움)
   - 조리시간, 인분수

2. **재료 정보**
   - 재료명 (표준화 필요)
   - 필요량 (예: 200g, 1개, 적당량)
   - 필수/선택 재료 구분

3. **조리 과정**
   - 단계별 조리 방법
   - 조리 팁 및 주의사항

4. **추가 정보**
   - 태그 (#다이어트, #간단요리 등)
   - 관련 상품 정보
   - 평점 및 리뷰 수

## 🏗️ 데이터베이스 설계

### 테이블 구조

#### 1. recipes (레시피)
```sql
CREATE TABLE recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    author VARCHAR(100),
    category VARCHAR(50),
    difficulty VARCHAR(20),
    cooking_time_minutes INTEGER,
    servings INTEGER,
    rating DECIMAL(3,2),
    review_count INTEGER DEFAULT 0,
    is_popular BOOLEAN DEFAULT false,
    image_url TEXT,
    source_url TEXT,
    tags TEXT[],
    tips TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. ingredients (재료 마스터)
```sql
CREATE TABLE ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),
    aliases TEXT[], -- 동일 재료의 다른 표기법
    unit VARCHAR(20), -- 기본 단위
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. recipe_ingredients (레시피-재료 관계)
```sql
CREATE TABLE recipe_ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_id UUID REFERENCES ingredients(id),
    amount VARCHAR(50),
    is_essential BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. cooking_steps (조리 단계)
```sql
CREATE TABLE cooking_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    instruction TEXT NOT NULL,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. categories (카테고리)
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🤖 크롤링 시스템 설계

### 크롤링 프로세스

#### 1단계: 카테고리별 레시피 목록 수집
```
1. 메인 페이지 접속
2. "레시피 분류" 버튼 클릭
3. 각 카테고리별 레시피 목록 페이지 순회
4. 페이지네이션 처리하여 모든 페이지 크롤링
5. 레시피 URL 목록 수집
```

#### 2단계: 레시피 상세 정보 크롤링
```
1. 수집된 레시피 URL 순차 접속
2. 레시피 상세 정보 파싱
   - 기본 정보 추출
   - 재료 목록 파싱
   - 조리 과정 추출
   - 추가 정보 수집
3. 데이터 정규화 및 검증
4. 데이터베이스 저장
```

### 크롤링 스크립트 구조

#### 파일 구조
```
scripts/
├── crawling/
│   ├── __init__.py
│   ├── crawler.py          # 메인 크롤러
│   ├── parser.py           # 데이터 파싱
│   ├── normalizer.py       # 데이터 정규화
│   ├── database.py         # DB 저장 로직
│   └── config.py           # 크롤링 설정
└── run_crawling.py         # 실행 스크립트
```

#### 주요 클래스 설계
```python
class RecipeCrawler:
    """메인 크롤링 클래스"""
    def crawl_categories(self)
    def crawl_recipe_list(self, category)
    def crawl_recipe_detail(self, recipe_url)
    
class RecipeParser:
    """레시피 데이터 파싱"""
    def parse_basic_info(self, html)
    def parse_ingredients(self, html)
    def parse_cooking_steps(self, html)
    
class DataNormalizer:
    """데이터 정규화"""
    def normalize_ingredient_name(self, name)
    def normalize_amount(self, amount)
    def categorize_recipe(self, title, ingredients)
```

## 🧮 매칭 알고리즘 설계

### 재료 매칭율 계산

#### 기본 매칭율 공식
```python
def calculate_matching_rate(user_ingredients, recipe_ingredients):
    """
    매칭율 = (보유 재료 수 / 전체 필요 재료 수) * 100
    """
    total_ingredients = len(recipe_ingredients)
    matched_ingredients = 0
    
    for ingredient in recipe_ingredients:
        if ingredient.name in user_ingredients:
            matched_ingredients += 1
            
    return (matched_ingredients / total_ingredients) * 100
```

#### 고급 매칭율 계산 (가중치 적용)
```python
def calculate_weighted_matching_rate(user_ingredients, recipe_ingredients):
    """
    필수 재료와 선택 재료에 다른 가중치 적용
    필수 재료: 가중치 1.5
    선택 재료: 가중치 1.0
    """
    total_weight = 0
    matched_weight = 0
    
    for ingredient in recipe_ingredients:
        weight = 1.5 if ingredient.is_essential else 1.0
        total_weight += weight
        
        if ingredient.name in user_ingredients:
            matched_weight += weight
            
    return (matched_weight / total_weight) * 100
```

### 추천 알고리즘

#### 1. 매칭율 기반 추천
- 높은 매칭율 우선 정렬
- 필수 재료 부족 시 하위 순위

#### 2. 개인화 추천
- 사용자 요리 히스토리 분석
- 선호 카테고리 가중치 적용
- 난이도 선호도 반영

#### 3. 상황별 추천
- 조리시간 기반 필터링
- 계절별 재료 고려
- 인분수 맞춤 추천

## 📊 데이터 품질 관리

### 재료명 표준화

#### 표준화 규칙
```python
INGREDIENT_ALIASES = {
    "돼지고기": ["돼지고기", "돼지 고기", "포크"],
    "양파": ["양파", "양파1개", "중간양파"],
    "마늘": ["마늘", "다진마늘", "마늘쫑"],
    "간장": ["간장", "진간장", "조선간장"],
}

def normalize_ingredient_name(raw_name):
    """재료명을 표준명으로 변환"""
    for standard_name, aliases in INGREDIENT_ALIASES.items():
        if raw_name in aliases:
            return standard_name
    return raw_name
```

### 데이터 검증

#### 필수 검증 항목
1. **레시피 기본 정보**
   - 제목 존재 여부
   - 최소 1개 이상의 재료
   - 최소 1개 이상의 조리 단계

2. **재료 정보**
   - 재료명 유효성
   - 양 정보 형식 검증
   - 중복 재료 제거

3. **데이터 일관성**
   - 카테고리 표준화
   - 난이도 표준화
   - 조리시간 범위 검증

## 🚀 구현 단계별 계획

### Phase 1: 크롤링 시스템 구축 (1-2주)
- [ ] MCP Playwright 크롤링 스크립트 개발
- [ ] 데이터 파싱 로직 구현
- [ ] 기본 데이터 정규화 시스템
- [ ] 예외 처리 및 로깅 시스템

### Phase 2: 데이터베이스 설계 및 구축 (1주)
- [ ] PostgreSQL 스키마 설계
- [ ] Alembic 마이그레이션 파일 생성
- [ ] 데이터 저장 로직 구현
- [ ] 인덱스 및 성능 최적화

### Phase 3: API 개발 (2주)
- [ ] FastAPI 레시피 엔드포인트 구현
- [ ] 매칭 알고리즘 API 구현
- [ ] 검색 및 필터링 기능
- [ ] 추천 시스템 구현

### Phase 4: 데이터 품질 관리 (1주)
- [ ] 재료명 표준화 시스템 구축
- [ ] 중복 데이터 제거 로직
- [ ] 데이터 검증 및 정제
- [ ] 품질 모니터링 시스템

### Phase 5: 테스트 및 최적화 (1주)
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 수행
- [ ] 성능 최적화
- [ ] 문서화 완성

## 🔧 기술적 고려사항

### 크롤링 최적화
- **속도 제어**: 서버 부하 방지를 위한 딜레이 설정
- **재시도 로직**: 네트워크 오류 시 자동 재시도
- **세션 관리**: 로그인 상태 유지 (필요시)
- **캐싱**: 중복 요청 방지

### 데이터 저장 최적화
- **배치 처리**: 대량 데이터 일괄 저장
- **트랜잭션 관리**: 데이터 일관성 보장
- **중복 처리**: UPSERT 패턴 활용

### 성능 고려사항
- **인덱싱**: 검색 성능 최적화
- **캐싱**: Redis를 통한 응답 속도 향상
- **페이지네이션**: 대량 데이터 조회 최적화

## 📈 성과 지표

### 데이터 품질 지표
- **수집 레시피 수**: 목표 10,000개 이상
- **재료 표준화율**: 95% 이상
- **데이터 완성도**: 필수 필드 100% 채움률

### 시스템 성능 지표
- **크롤링 속도**: 시간당 500개 레시피
- **API 응답시간**: 평균 200ms 이하
- **매칭 정확도**: 사용자 만족도 90% 이상

## 🔒 법적 고려사항
- **저작권**: 레시피 데이터 사용 권한 확인
- **이용약관**: 크롤링 허용 범위 검토
- **개인정보**: 작성자 정보 처리 방침 수립

## 📝 결론
이 계획서는 Fridge2Fork 앱의 핵심 기능인 재료 기반 레시피 추천 시스템을 위한 종합적인 데이터 수집 및 처리 전략을 제시합니다. 체계적인 크롤링과 데이터 품질 관리를 통해 사용자에게 최적의 레시피 추천 서비스를 제공할 수 있는 기반을 마련할 것입니다.
