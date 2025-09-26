# 🚀 Fridge2Fork Admin API

냉장고에서 포크까지 - 오늘의냉장고 관리자용 백엔드 API

## 📋 주요 기능

- **FastAPI** 기반 REST API (`/v1` prefix)
- **PostgreSQL** 데이터베이스 연동
- **이모지 로깅** 시스템으로 가독성 향상
- **환경별 requirements** 파일 분리
- **Docker 컨테이너화** 지원

## 🏗️ 프로젝트 구조

```
admin/backend/
├── main.py                 # 애플리케이션 진입점
├── apps/                   # 애플리케이션 모듈
│   ├── config.py          # 설정 관리
│   ├── database.py        # DB 연결 및 세션 관리
│   ├── models.py          # SQLAlchemy 모델
│   ├── schemas.py         # Pydantic 스키마
│   ├── logging_config.py  # 로깅 설정
│   └── routers/           # API 라우터
│       ├── ingredients.py # 식재료 API
│       └── recipes.py     # 레시피 API
├── requirements.common.txt # 공통 패키지
├── requirements.dev.txt    # 개발 환경 패키지
├── requirements.prod.txt   # 운영 환경 패키지
└── Dockerfile             # Docker 설정
```

## 🚀 실행 방법

### 개발 환경 (로컬)

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 개발 패키지 설치
pip install -r requirements.dev.txt

# 애플리케이션 실행
python main.py
```

### Docker 실행

```bash
# 개발 모드 (uvicorn)
docker build -t fridge2fork-admin .
docker run -p 8000:8000 -e ENVIRONMENT=development fridge2fork-admin

# 운영 모드 (gunicorn)
docker run -p 8000:8000 -e ENVIRONMENT=production fridge2fork-admin
```

## 🌐 API 엔드포인트

- **헬스체크**: `GET /health`
- **API 문서**: `GET /v1/docs` (Swagger UI)
- **식재료 API**: `GET/POST/PUT/DELETE /v1/ingredients/*`
- **레시피 API**: `GET/POST/PUT/DELETE /v1/recipes/*`

## 🔄 CI/CD (GitHub Actions)

브랜치별 자동 배포:

- **`develop`** 브랜치 → 개발 환경 (uvicorn, --reload)
- **`main`** 또는 **`prod`** 브랜치 → 운영 환경 (gunicorn, 워커 4개)

## 🗄️ 데이터베이스 모델

### Ingredients (식재료)
- `ingredient_id`: 고유 ID
- `name`: 식재료 이름 (고유값)
- `is_vague`: 모호한 식재료 여부
- `vague_description`: 모호한 식재료 설명

### Recipes (레시피)
- `recipe_id`: 고유 ID
- `url`: 레시피 원본 URL (고유값)
- `title`: 레시피 제목
- `description`: 레시피 설명
- `image_url`: 레시피 이미지 URL
- `created_at`: 생성 시간

### Recipe Ingredients (레시피-식재료 연결)
- `recipe_id`: 레시피 ID (외래키)
- `ingredient_id`: 식재료 ID (외래키)
- `quantity_from`: 수량 (시작 범위)
- `quantity_to`: 수량 (종료 범위)
- `unit`: 수량 단위
- `importance`: 재료 중요도 (essential, optional 등)

## 📝 로깅

이모지가 포함된 로그 시스템:

- 🐛 **DEBUG**: 디버그 정보
- ℹ️ **INFO**: 일반 정보
- ⚠️ **WARNING**: 경고
- ❌ **ERROR**: 오류
- 🚨 **CRITICAL**: 심각한 오류

## 🔧 환경 변수

`.env` 파일에서 설정:

```env
# 데이터베이스 설정
DATABASE_URL=postgresql://user:password@host:port/dbname
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fridge2fork
DB_USER=fridge2fork
DB_PASSWORD=your_password

# 애플리케이션 설정
APP_NAME=Fridge2Fork Admin API
APP_VERSION=1.0.0
DEBUG=True
LOG_LEVEL=INFO
API_PREFIX=/v1
```

## 🧪 테스트

```bash
# 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=apps

# 특정 파일 테스트
pytest tests/test_ingredients.py
```

## 📦 의존성 관리

- **requirements.common.txt**: 공통 패키지 (FastAPI, SQLAlchemy 등)
- **requirements.dev.txt**: 개발용 패키지 (pytest, black, flake8 등)
- **requirements.prod.txt**: 운영용 패키지 (gunicorn, prometheus 등)

## 🐳 Docker 최적화

- Python 3.11 슬림 이미지 사용
- 멀티스테이지 빌드로 이미지 크기 최적화
- 헬스체크 포함
- 환경 변수에 따른 실행 명령 분기

## 📚 추가 문서

- [API 문서](http://localhost:8000/v1/docs) - Swagger UI
- [데이터베이스 스키마](docs/database_schema_row.md)


# 사용자 서비스
개발: api-dev.woohalabs.com/fridge2fork/v1
운영: api.woohalabs.com/fridge2fork/v1
개발웹: dev.woohalabs.com/fridge2fork  
운영웹: woohalabs.com/fridge2fork

# 관리자 서비스  
개발: admin-api-dev.woohalabs.com/fridge2fork/v1
개발웹: admin-dev.woohalabs.com/fridge2fork

운영: admin-api.woohalabs.com/fridge2fork/v1
운영웹: admin.woohalabs.com/fridge2fork