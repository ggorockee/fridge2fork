# 개발 환경 설정 가이드

## 개요

Fridge2Fork 프로젝트를 위한 conda 환경 설정과 필요한 패키지 설치 가이드입니다.

## 1. Conda 환경 설정

### 환경 생성
- conda 환경 생성 (Python 3.11 권장): `conda create -n fridge2fork python=3.11 -y`
- 환경 활성화: `conda activate fridge2fork`

### 환경 검증
- Python 버전 확인: `python --version`
- conda 환경 확인: `conda env list`

## 2. 필수 패키지 설치

### 주요 패키지 목록
- **Web Framework**: fastapi, uvicorn
- **Database**: sqlalchemy, alembic, asyncpg, psycopg2-binary
- **Data Processing**: pandas, numpy
- **Validation**: pydantic, pydantic-settings
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Development Tools**: black, isort, flake8, mypy
- **Utilities**: python-dotenv, click, rich, tqdm
- **Korean Text Processing**: konlpy, hanja

### 패키지 설치
- requirements.txt 파일 사용: `pip install -r requirements-api.txt`
- 개별 설치: `pip install fastapi uvicorn sqlalchemy alembic asyncpg pandas pydantic python-dotenv`

## 3. PostgreSQL 설정

### PostgreSQL 설치
**macOS (Homebrew)**:
- 설치: `brew install postgresql@15`
- 서비스 시작: `brew services start postgresql@15`
- 데이터베이스 생성: `createdb fridge2fork_db`

**Ubuntu/Debian**:
- 설치: `sudo apt update && sudo apt install postgresql postgresql-contrib`
- 서비스 시작: `sudo systemctl start postgresql && sudo systemctl enable postgresql`
- 사용자 생성: `sudo -u postgres psql` 후 SQL 명령어 실행

### 환경변수 설정 (.env)

필수 환경변수:
```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/fridge2fork_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=fridge2fork_db
DATABASE_USER=fridge2fork_user
DATABASE_PASSWORD=your_password

# Application Configuration
APP_NAME=Fridge2Fork API
APP_VERSION=1.0.0
APP_DESCRIPTION=냉장고 재료 기반 레시피 추천 API
DEBUG=True

# API Configuration
API_V1_PREFIX=/v1
SECRET_KEY=your-secret-key-here

# Data Configuration
CSV_DATA_DIR=./datas
BATCH_SIZE=1000
MAX_WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 4. 프로젝트 구조 설정

### 디렉토리 구조 생성
필요한 디렉토리 및 파일 생성:
- `mkdir -p {app,app/api,app/api/v1,app/core,app/crud,app/db,app/models,app/schemas,app/services,app/utils,migrations,scripts,tests,docs}`
- `__init__.py` 파일들 생성

### 최종 프로젝트 구조
```
fridge2fork/
├── app/                        # 메인 애플리케이션
│   ├── main.py                 # FastAPI 엔트리포인트
│   ├── api/v1/                 # API v1 엔드포인트
│   ├── core/                   # 설정, 데이터베이스, 보안
│   ├── crud/                   # 데이터 액세스 레이어
│   ├── models/                 # SQLAlchemy 모델
│   ├── schemas/                # Pydantic 스키마
│   ├── services/               # 비즈니스 로직
│   └── utils/                  # 유틸리티 함수
├── migrations/                 # Alembic 마이그레이션
├── scripts/                    # 배치 스크립트
├── tests/                      # 테스트 코드
├── docs/                       # 문서
├── datas/                      # CSV 데이터 파일
├── .env                        # 환경변수
├── requirements-api.txt        # 패키지 목록
└── alembic.ini                # Alembic 설정
```

## 5. 개발 도구 설정

### Git 설정 (.gitignore)
주요 제외 항목:
- Python 캐시 파일 (`__pycache__/`, `*.pyc`)
- 환경변수 파일 (`.env`, `venv/`)
- 데이터베이스 파일 (`*.db`, `*.sqlite3`)
- IDE 설정 (`.vscode/`, `.idea/`)
- 로그 파일 (`*.log`)
- 테스트 커버리지 (`htmlcov/`, `.coverage`)
- 데이터 파일 (`datas/*.csv` 단, 샘플 제외)

### Code Formatting 설정
- **pylintrc**: 최대 라인 길이 88자
- **pyproject.toml**: black, isort, mypy 설정
- **개발 스크립트**: 포맷팅, 린팅, 테스트, 개발서버 실행

## 6. 환경 검증

### 검증 항목
1. **Python 버전**: 3.11 이상
2. **필수 패키지**: fastapi, uvicorn, sqlalchemy, alembic, asyncpg, pandas, pydantic
3. **데이터베이스 연결**: PostgreSQL 연결 테스트

### 검증 실행
환경 검증 스크립트로 설정 상태 확인

## 7. 다음 단계

환경 설정이 완료되면 다음 단계를 진행합니다:

1. **데이터베이스 마이그레이션**: Alembic을 사용한 스키마 생성
2. **CSV 데이터 로드**: 배치 스크립트로 데이터 입력
3. **API 개발**: FastAPI 애플리케이션 개발
4. **테스트**: API 테스트 및 검증

참고 문서: `docs/02_database_schema.md`, `docs/03_data_migration.md`, `docs/04_api_development.md`

## 트러블슈팅

### 일반적인 문제들

1. **conda 환경 활성화 문제**:
   - `conda init` 실행 후 터미널 재시작
   - `conda activate fridge2fork`

2. **PostgreSQL 연결 실패**:
   - 서비스 상태 확인: `brew services list | grep postgresql` (macOS)
   - 포트 확인: `lsof -i :5432`

3. **패키지 설치 실패**:
   - pip 업그레이드: `python -m pip install --upgrade pip`
   - conda-forge 사용: `conda install -c conda-forge package_name`

4. **한국어 처리 문제**:
   - 로케일 확인: `locale`
   - UTF-8 설정: `export LANG=en_US.UTF-8`