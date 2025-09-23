# 만개의 레시피 크롤링 시스템 구현 계획

## 프로젝트 개요

### 목표
- **타겟 사이트**: https://www.10000recipe.com/
- **데이터 규모**: 최종 200,000개 레시피, 현재 단계 100개 샘플
- **목적**: 레시피 추천 시스템용 정규화된 데이터 수집
- **핵심 기능**: 한국어 재료 정보 정규화 ("설탕 2스푼" → 2)

### 기술 스택
- **크롤링**: Playwright (TypeScript/Python)
- **데이터베이스**: PostgreSQL (메인), Redis (캐시/세션)
- **컨테이너화**: Docker
- **모니터링**: Grafana + Prometheus

## 시스템 아키텍처

### 1. 크롤러 엔진 (Playwright 기반)
```
브라우저 자동화
├── 세션 관리 (쿠키/헤더 처리)
├── Rate Limiting (서버 부하 방지)
├── 동적 콘텐츠 처리
└── 멀티 브라우저 인스턴스 (병렬 처리)
```

### 2. 데이터 파이프라인
```
원시 HTML → 구조화된 데이터
├── 레시피 메타데이터 추출
├── 재료 정보 파싱
├── 한국어 재료 정규화 엔진
└── 데이터 검증 및 품질 관리
```

### 3. 큐 시스템
```
작업 분산 처리
├── 크롤링 작업 큐
├── 실패 작업 재시도 메커니즘
├── 진행률 추적
└── 상태 관리 (Redis)
```

### 4. 데이터 스토리지
```
다계층 저장소
├── PostgreSQL (정규화된 레시피 데이터)
├── Redis (크롤링 상태 및 캐시)
└── 파일 시스템 (이미지 및 로그)
```

## 데이터베이스 스키마

### 핵심 테이블 구조

```sql
-- 레시피 메인 정보
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    cooking_time INTEGER, -- 분 단위
    difficulty_level INTEGER, -- 1-5 난이도
    servings INTEGER, -- 몇 인분
    category_id INTEGER,
    image_url VARCHAR(500),
    source_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 재료 마스터 테이블
CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL, -- 정규화된 재료명
    category VARCHAR(50), -- 채소, 육류, 조미료 등
    unit VARCHAR(20) -- 기본 단위
);

-- 레시피-재료 관계 (정규화된 수량 포함)
CREATE TABLE recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id),
    ingredient_id INTEGER REFERENCES ingredients(id),
    quantity DECIMAL(10,2), -- 정규화된 수량
    unit VARCHAR(20), -- 단위
    original_text VARCHAR(100) -- 원본 텍스트 보존
);

-- 카테고리 테이블
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL, -- 밥/죽/떡, 국/탕/찌개 등
    parent_id INTEGER REFERENCES categories(id)
);
```

### 인덱스 전략
```sql
-- 성능 최적화용 인덱스
CREATE INDEX idx_recipes_title ON recipes(title);
CREATE INDEX idx_recipes_category ON recipes(category_id);
CREATE INDEX idx_recipes_cooking_time ON recipes(cooking_time);
CREATE INDEX idx_recipe_ingredients_recipe ON recipe_ingredients(recipe_id);
CREATE INDEX idx_recipe_ingredients_ingredient ON recipe_ingredients(ingredient_id);
CREATE INDEX idx_ingredient_quantity ON recipe_ingredients(ingredient_id, quantity);
```

## 한국어 재료 정규화 로직

### 정규화 패턴

#### 1. 수량 추출 패턴
```python
# 정규표현식 패턴들
patterns = {
    'integer': r'(\d+)(개|스푼|큰술|작은술|컵|g|ml)',
    'decimal': r'(\d+\.?\d*)(개|스푼|큰술|작은술|컵|g|ml)',
    'fraction': r'(\d+/\d+)(개|스푼|큰술|작은술|컵|g|ml)',
    'range': r'(\d+)~(\d+)(개|스푼|큰술|작은술|컵|g|ml)'
}
```

#### 2. 단위 표준화 매핑
```python
unit_mapping = {
    '스푼': '큰술',
    'T': '큰술',
    't': '작은술',
    '큰수저': '큰술',
    '작은수저': '작은술',
    'ml': 'ml',
    'L': 'ml',  # 1000ml로 변환
    'cc': 'ml'
}
```

#### 3. 재료명 정규화
```python
ingredient_mapping = {
    '양파(중간크기)': '양파',
    '양파(소)': '양파',
    '당근(중간크기)': '당근',
    '대파': '파',
    '쪽파': '파'
}
```

#### 4. 모호한 표현 처리
```python
vague_quantities = {
    '적당히': 1,
    '조금': 0.5,
    '약간': 0.3,
    '많이': 2,
    '한줌': 1
}
```

## 크롤링 전략

### 1. 사이트 구조 분석
```
https://www.10000recipe.com/
├── 메인 페이지
├── 카테고리 페이지 (/recipe/list.html?cat=)
│   ├── 밥/죽/떡
│   ├── 국/탕/찌개
│   ├── 반찬/김치/장아찌
│   ├── 면/파스타
│   └── 디저트
└── 개별 레시피 페이지
    ├── 제목, 설명
    ├── 재료 목록
    ├── 조리 순서
    └── 이미지
```

### 2. 크롤링 시퀀스
```python
1. 카테고리 페이지 접근
2. 레시피 목록 수집 (페이지네이션 처리)
3. 개별 레시피 상세페이지 접근
4. 데이터 추출 및 파싱
5. 정규화 처리
6. 데이터베이스 저장
```

### 3. CSS 셀렉터 매핑
```python
selectors = {
    'recipe_list': '.recipe-list .item',
    'recipe_title': '.recipe-title h1',
    'ingredients': '.recipe-ingredients li',
    'cooking_steps': '.recipe-steps .step',
    'cooking_time': '.recipe-info .time',
    'difficulty': '.recipe-info .difficulty',
    'servings': '.recipe-info .servings'
}
```

## 에러 핸들링 및 복구 메커니즘

### 1. 네트워크 레벨 에러 처리
```python
# Exponential Backoff 재시도 전략
retry_strategy = {
    'max_retries': 5,
    'base_delay': 1,  # 초
    'max_delay': 60,  # 초
    'backoff_multiplier': 2
}
```

### 2. Circuit Breaker 패턴
```python
circuit_breaker = {
    'failure_threshold': 10,  # 연속 실패 횟수
    'timeout': 300,  # 5분 대기
    'success_threshold': 3   # 복구 판단 기준
}
```

### 3. 데이터 품질 검증
```python
quality_checks = {
    'required_fields': ['title', 'ingredients'],
    'min_ingredients': 2,
    'max_cooking_time': 600,  # 분
    'image_validation': True
}
```

## 성능 최적화 전략

### 1. 병렬 처리 아키텍처
```python
# 동시 처리 설정
concurrent_settings = {
    'browser_instances': 4,    # 병렬 브라우저
    'worker_processes': 8,     # 데이터 처리 워커
    'batch_size': 50,          # 배치 크기
    'db_connection_pool': 20   # DB 커넥션 풀
}
```

### 2. 메모리 관리
```python
# 리소스 관리 전략
resource_management = {
    'browser_restart_interval': 100,  # 100개 처리 후 재시작
    'memory_limit_mb': 2048,          # 메모리 제한
    'gc_frequency': 50,               # 가비지 컬렉션 주기
    'streaming_processing': True      # 스트리밍 방식 처리
}
```

### 3. 데이터베이스 최적화
```python
# DB 최적화 설정
db_optimization = {
    'batch_insert_size': 1000,        # 배치 INSERT 크기
    'commit_frequency': 100,          # 커밋 주기
    'index_creation': 'post_load',    # 데이터 로드 후 인덱스 생성
    'vacuum_schedule': 'daily'        # 정리 작업 스케줄
}
```

## 모니터링 및 알림 시스템

### 1. 성능 지표
```python
monitoring_metrics = {
    'crawling_speed': 'recipes/minute',
    'success_rate': 'percentage',
    'memory_usage': 'MB',
    'error_rate': 'errors/hour',
    'data_quality_score': '0-100'
}
```

### 2. 알림 임계값
```python
alert_thresholds = {
    'error_rate_warning': 5,    # 5% 에러율
    'error_rate_critical': 15,  # 15% 에러율
    'memory_usage_warning': 80,  # 80% 메모리 사용
    'crawling_speed_low': 10    # 분당 10개 미만
}
```

## 구현 로드맵

### Phase 1: 프로토타입 (1-2주)
## 언어 python
#### execuete: conda
#### execute name: fridge2fork
**목표**: 100개 샘플 데이터 크롤링

#### 주요 작업
- [ ] Playwright 기본 크롤링 스크립트 개발
- [ ] 사이트 구조 분석 및 CSS 셀렉터 매핑
- [ ] 한국어 재료 정규화 로직 구현
- [ ] Python Pandas를 이용해 CSV/JSON 파일로 데이터 export
- [ ] 100개 샘플 데이터 크롤링 테스트

#### 예상 결과물
```
phase1_prototype/
├── sample_crawler.py         # 메인 크롤링 스크립트
├── ingredient_normalizer.py  # 한국어 재료 정규화 함수
├── data_exporter.py         # Pandas 기반 CSV/JSON export
├── config.py                # 설정 관리
├── data/                    # 크롤링된 데이터 저장소
│   ├── recipes.csv          # 샘플 레시피 데이터 (CSV)
│   └── recipes.json         # 샘플 레시피 데이터 (JSON)
└── logs/                    # 로그 파일들
```

### Phase 2: 확장 및 최적화 (2-3주)
**목표**: 10,000개 데이터 크롤링

#### 주요 작업
- [ ] Phase 1 결과 검증 및 피드백 반영
- [ ] 기본 데이터베이스 스키마 구현 (PostgreSQL)
- [ ] 병렬 처리 아키텍처 구현 (멀티 브라우저)
- [ ] 큐 시스템 및 작업 분산 (Redis 기반)
- [ ] 고급 에러 핸들링 및 재시도 로직
- [ ] 실시간 모니터링 및 로깅 시스템
- [ ] 성능 튜닝 및 메모리 최적화
- [ ] 대용량 데이터 처리를 위한 배치 시스템

#### 예상 결과물
```
phase2_scalable/
├── database/            # 데이터베이스 관련
│   ├── schema.sql       # PostgreSQL 테이블 스키마
│   ├── migrations/      # 스키마 마이그레이션
│   └── connection.py    # DB 연결 풀 관리
├── crawler/              # 크롤링 엔진
│   ├── engine.py         # 멀티 브라우저 크롤링 엔진
│   ├── worker.py         # 워커 프로세스
│   └── scheduler.py      # 작업 스케줄러
├── pipeline/            # 데이터 처리 파이프라인
│   ├── processor.py     # 배치 데이터 처리
│   ├── validator.py     # 데이터 품질 검증
│   └── normalizer.py    # 재료 정규화 (개선)
├── queue/               # 큐 시스템
│   ├── manager.py       # Redis 기반 큐 관리
│   └── retry_handler.py # 실패 작업 재시도
├── monitoring/          # 모니터링 시스템
│   ├── metrics.py       # 성능 지표 수집
│   ├── logger.py        # 구조화된 로깅
│   └── dashboard.py     # 실시간 대시보드
├── config/              # 설정 관리
│   └── settings.py      # 애플리케이션 설정
└── data/                # 데이터 저장소
    ├── processed/       # 처리된 데이터
    └── exports/         # CSV/JSON 내보내기
```

### Phase 3: 프로덕션 배포 (3-4주)
**목표**: 200,000개 전체 데이터 크롤링

#### 주요 작업
- [ ] 전체 데이터 크롤링 실행
- [ ] 데이터 품질 검증 및 정제
- [ ] 백업 및 복구 시스템
- [ ] API 연동 준비
- [ ] 문서화 및 운영 가이드 작성

#### 예상 결과물
```
fridge2fork_crawler/
├── production/           # 프로덕션 코드
├── data/                # 크롤링된 데이터
├── backups/             # 백업 파일들
├── logs/                # 로그 파일들
├── monitoring/          # 모니터링 대시보드
└── docs/                # 운영 문서
```

## 예상 처리 시간 및 리소스

### 처리 시간 추정
- **100개 샘플**: 10-15분
- **10,000개**: 8-10시간
- **200,000개**: 7-10일 (24시간 연속 처리)

### 필요 리소스
```yaml
# 최소 시스템 요구사항
minimum_requirements:
  cpu: "4 cores"
  memory: "8GB RAM"
  storage: "100GB SSD"
  network: "100Mbps"

# 권장 시스템 요구사항
recommended_requirements:
  cpu: "8 cores"
  memory: "16GB RAM"
  storage: "500GB SSD"
  network: "1Gbps"
```

## 데이터 품질 관리

### 1. 검증 규칙
```python
validation_rules = {
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
        'max_value': 600
    }
}
```

### 2. 정규화 품질 점수
```python
quality_score = {
    'ingredient_parsing_success': '95%+',
    'quantity_extraction_success': '90%+',
    'unit_standardization_success': '95%+',
    'duplicate_detection_accuracy': '99%+'
}
```

## 위험 요소 및 대응 방안

### 1. 기술적 위험
| 위험 요소 | 영향도 | 확률 | 대응 방안 |
|----------|--------|------|----------|
| 사이트 구조 변경 | 높음 | 중간 | CSS 셀렉터 자동 감지, 백업 전략 |
| IP 차단 | 높음 | 낮음 | 프록시 로테이션, User-Agent 변경 |
| 서버 과부하 | 중간 | 중간 | Rate Limiting, 분산 처리 |
| 데이터 품질 저하 | 중간 | 높음 | 실시간 품질 모니터링 |

### 2. 운영적 위험
| 위험 요소 | 영향도 | 확률 | 대응 방안 |
|----------|--------|------|----------|
| 메모리 부족 | 높음 | 중간 | 메모리 모니터링, 자동 재시작 |
| 디스크 공간 부족 | 높음 | 낮음 | 용량 모니터링, 자동 정리 |
| 네트워크 불안정 | 중간 | 높음 | 재시도 로직, 오프라인 모드 |

## 확장 계획

### 1. 추가 사이트 지원
```
향후 확장 가능한 레시피 사이트들:
├── 쿡패드 (cookpad.com/kr)
├── 네이버 요리 (recipe.naver.com)
├── 다음 요리 (recipe.daum.net)
└── 유튜브 요리 채널들
```

### 2. 기능 확장
```
추가 기능 개발 계획:
├── 실시간 크롤링 (새 레시피 자동 수집)
├── 이미지 분석 (재료 자동 인식)
├── 영양 정보 계산
└── 레시피 난이도 자동 평가
```

## 결론

본 구현 계획은 만개의 레시피 사이트에서 200,000개 레시피 데이터를 효율적으로 수집하고 정규화하기 위한 체계적인 접근 방법을 제시합니다.

**핵심 성공 요소:**
1. **점진적 개발**: 100개 → 10,000개 → 200,000개 단계적 확장
2. **robust 아키텍처**: 에러 핸들링, 모니터링, 복구 메커니즘
3. **데이터 품질**: 한국어 재료 정규화 및 검증 시스템
4. **확장성**: 다른 사이트로의 확장 가능한 설계

이 계획에 따라 구현하면 레시피 추천 시스템에 필요한 고품질 데이터를 안정적으로 확보할 수 있을 것입니다.