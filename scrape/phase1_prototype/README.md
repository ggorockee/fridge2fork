# 만개의 레시피 크롤링 시스템 Phase 1

Phase 1 프로토타입: 100개 샘플 레시피 데이터 크롤링 및 정규화

## 🎯 목표

- 만개의 레시피 사이트에서 100개 샘플 레시피 데이터 수집
- 한국어 재료 정보 정규화 ("설탕 2스푼" → 2)
- CSV/JSON 형태로 데이터 export
- 데이터 품질 검증 및 통계 생성

## 📁 프로젝트 구조

```
phase1_prototype/
├── sample_crawler.py         # 메인 크롤링 스크립트
├── ingredient_normalizer.py  # 한국어 재료 정규화 함수
├── data_exporter.py         # Pandas 기반 CSV/JSON export
├── config.py                # 설정 관리
├── requirements.txt         # Python 종속성
├── README.md               # 실행 가이드
├── data/                   # 크롤링된 데이터 저장소
│   ├── recipes.csv         # 샘플 레시피 데이터 (CSV)
│   ├── recipes.json        # 샘플 레시피 데이터 (JSON)
│   └── statistics.json     # 데이터 통계
└── logs/                   # 로그 파일들
    └── crawler.log
```

## 🚀 설치 및 실행

### 1. 환경 설정

```bash
# Conda 환경 생성 및 활성화
conda create -n fridge2fork python=3.9
conda activate fridge2fork

# 종속성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 2. 크롤링 실행

```bash
# 메인 크롤링 스크립트 실행
python sample_crawler.py
```

### 3. 개별 모듈 테스트

```bash
# 한국어 재료 정규화 테스트
python ingredient_normalizer.py

# 데이터 export 테스트
python data_exporter.py

# 설정 확인
python config.py
```

## 📊 출력 데이터 형식

### CSV 파일 (recipes.csv)
| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| recipe_id | 레시피 ID | 1 |
| title | 레시피 제목 | 김치볶음밥 |
| description | 레시피 설명 | 간단하고 맛있는 김치볶음밥 |
| url | 원본 URL | https://www.10000recipe.com/recipe/... |
| cooking_time | 조리 시간 (분) | 15 |
| ingredients_count | 재료 개수 | 5 |
| ingredients_normalized | 정규화된 재료 | 김치 200g \| 밥 2공기 \| 대파 1대 |
| main_ingredients | 주요 재료 | 김치 \| 밥 \| 대파 |

### JSON 파일 (recipes.json)
```json
[
  {
    "title": "김치볶음밥",
    "description": "간단하고 맛있는 김치볶음밥",
    "url": "https://www.10000recipe.com/recipe/...",
    "cooking_time": "15분",
    "ingredients": [
      {
        "name": "김치",
        "quantity": 200.0,
        "unit": "g",
        "original_text": "김치 200g",
        "confidence": 0.95
      }
    ],
    "cooking_steps": ["김치를 잘게 썬다", "팬에 김치를 볶는다"],
    "crawled_at": "2024-01-15T10:30:00"
  }
]
```

## ⚙️ 설정 옵션

`config.py`에서 다음 설정들을 조정할 수 있습니다:

```python
# 크롤링 설정
CRAWLING_CONFIG = {
    'max_recipes': 100,           # 수집할 레시피 수
    'delay_between_requests': 2,   # 요청 간 지연 (초)
    'timeout': 30000,             # 페이지 로드 타임아웃 (ms)
    'headless': True,             # 브라우저 헤드리스 모드
    'max_retries': 3              # 재시도 횟수
}
```

## 🔍 데이터 품질 관리

### 검증 규칙
- 레시피 제목: 2자 이상 200자 이하
- 재료 개수: 최소 2개 이상
- 조리 시간: 1-600분 범위

### 정규화 품질 지표
- 재료 파싱 성공률: 95% 이상 목표
- 수량 추출 성공률: 90% 이상 목표
- 단위 표준화 성공률: 95% 이상 목표

## 📈 모니터링 및 로깅

### 로그 파일
- 위치: `logs/crawler.log`
- 레벨: INFO, WARNING, ERROR
- 로테이션: 10MB, 5개 파일

### 진행률 모니터링
크롤링 중 실시간으로 다음 정보가 출력됩니다:
- 현재 진행률 (X/100)
- 성공/실패 개수
- 예상 완료 시간

## 🚨 문제 해결

### 일반적인 문제들

1. **브라우저 설치 오류**
   ```bash
   playwright install chromium
   ```

2. **사이트 접근 차단**
   - `config.py`에서 `delay_between_requests` 증가
   - User-Agent 변경

3. **메모리 부족**
   - `max_recipes` 수를 줄여서 테스트
   - 브라우저 헤드리스 모드 사용

4. **SSL 인증서 오류**
   ```python
   # config.py에서 브라우저 옵션 추가
   'ignore_https_errors': True
   ```

## 📋 다음 단계 (Phase 2)

Phase 1 완료 후 다음 기능들이 추가될 예정입니다:
- PostgreSQL 데이터베이스 연동
- 병렬 처리 (멀티 브라우저)
- 실시간 모니터링 대시보드
- 고급 에러 핸들링
- 10,000개 대용량 데이터 처리

## 📞 지원

문제 발생 시 다음을 확인해주세요:
1. `logs/crawler.log` 파일의 에러 메시지
2. 네트워크 연결 상태
3. 사이트 접근 가능 여부
4. Python 및 종속성 버전