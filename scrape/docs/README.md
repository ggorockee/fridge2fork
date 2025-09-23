# 만개의레시피 스크래핑 프로젝트

20만개 레시피 데이터를 수집하고 정규화하는 프로젝트입니다.

## 📋 프로젝트 개요

### 목표
- 만개의레시피(10000recipe.com)에서 레시피 데이터 수집
- 재료 데이터 정규화 ("고추장2스푼" → 2, "스푼")
- PostgreSQL 데이터베이스에 구조화된 데이터 저장
- FastAPI를 통한 REST API 제공

### 아키텍처
```
Web Scraping → Data Processing → Database Storage → API Service
     ↓              ↓                ↓               ↓
  Beautiful      Normalization    PostgreSQL     FastAPI
    Soup         Processing         20만개        REST API
   Requests      ("고추장2스푼")     레시피         검색/필터
```

## 🗂️ 프로젝트 구조

```
fridge2fork/scrape/
├── docs/                    # 프로젝트 문서
├── helm-charts/            # Kubernetes 배포용 Helm Charts
│   ├── postgresql/         # 데이터베이스 차트
│   ├── recipe-scraper/     # 스크래핑 크론잡 차트
│   └── recipe-api/         # FastAPI 백엔드 차트
├── scraper/                # 스크래핑 Python 코드
├── analysis/               # 데이터 분석 코드
└── data/                   # 수집된 데이터
```

## 🔍 스크래핑 대상

### 기본 정보
- **대상 사이트**: https://www.10000recipe.com/
- **예상 레시피 수**: 200,000+
- **수집 데이터**: 레시피 제목, 재료, 조리법, 이미지, 카테고리

### 주요 엔드포인트
1. **레시피 목록**: `https://www.10000recipe.com/recipe/list.html`
2. **레시피 상세**: `https://www.10000recipe.com/recipe/{recipe_id}`
3. **댓글 API**: `https://www.10000recipe.com/recipe/ajax.html?q_mode=getListComment&seq={recipe_id}`

## 📊 데이터 구조

### 데이터베이스 스키마
- **recipes**: 기본 레시피 정보
- **ingredients**: 재료 마스터 데이터
- **recipe_ingredients**: 레시피-재료 관계 (정규화된 데이터)
- **categories**: 카테고리 분류
- **recipe_steps**: 조리 단계

### 정규화 예시
```
원본 데이터: "고추장2스푼, 양파1개, 설탕1큰술"
↓
정규화 결과:
- 고추장: 2, 스푼
- 양파: 1, 개  
- 설탕: 1, 큰술(스푼)
```

## 🚀 시작하기

### 1. 환경 설정
```bash
# 필수 패키지 설치
pip install -r requirements.txt

# 데이터베이스 설정 (Kubernetes)
kubectl apply -f helm-charts/postgresql/
```

### 2. 스크래핑 실행
```bash
# 샘플 데이터 수집
python scraper/sample_scraper.py

# 전체 데이터 수집 (크론잡)
kubectl apply -f helm-charts/recipe-scraper/
```

### 3. API 서버 실행
```bash
# 로컬 개발
python -m uvicorn api.main:app --reload

# Kubernetes 배포
kubectl apply -f helm-charts/recipe-api/
```

## 📈 분석 도구

- **데이터 탐색**: `analysis/data_exploration.ipynb`
- **시각화**: `analysis/recipe_visualization.py`
- **통계 분석**: `analysis/ingredient_analysis.py`

## 🛠️ 개발 도구

- **언어**: Python 3.9+
- **프레임워크**: FastAPI, SQLAlchemy
- **데이터베이스**: PostgreSQL 15
- **컨테이너**: Docker, Kubernetes
- **분석**: Pandas, Matplotlib, Seaborn
