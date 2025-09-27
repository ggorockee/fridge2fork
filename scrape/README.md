# Fridge2Fork 데이터 파이프라인

레시피 데이터 수집 및 PostgreSQL 마이그레이션 시스템

## 📋 프로젝트 개요

한국 레시피 데이터를 수집하고 PostgreSQL 데이터베이스로 마이그레이션하는 통합 시스템입니다.

- **크롤링**: 만개의 레시피에서 레시피 데이터 수집
- **마이그레이션**: CSV 데이터를 정규화하여 PostgreSQL로 이관
- **재료 파싱**: 한국어 재료 텍스트를 구조화된 데이터로 변환

## 🚀 Quick Start

### 1. 환경 설정
```bash
# Conda 환경 생성 (권장)
conda create -n fridge2fork python=3.12
conda activate fridge2fork

# 패키지 설치
pip install -r requirements.txt
pip install -r requirements-api.txt

# 환경변수 설정
cp env.example .env
# .env 파일 편집 (DATABASE_URL 필수)
```

### 2. 데이터베이스 설정
```bash
# 전체 DB 설정 (Alembic + 기본 데이터)
python scripts/setup_database.py

# 또는 개별 실행
alembic upgrade head
python scripts/insert_basic_data.py
```

### 3. 데이터 마이그레이션
```bash
# CSV 분석
python scripts/analyze_csv.py

# 전체 마이그레이션
python scripts/migrate_csv_data.py

# 검증
python scripts/verify_migration.py
```

## 🐳 Docker 사용

통합 Dockerfile은 크롤링과 마이그레이션 모두 지원합니다:

```bash
# 이미지 빌드
docker build -t fridge2fork .

# 크롤링 실행 (기본값)
docker run --rm fridge2fork

# 마이그레이션 실행
docker run --rm \
  -e MODE=migration \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  fridge2fork
```

## 📁 프로젝트 구조

```
scrape/
├── app/                    # 애플리케이션 코드
│   ├── models/            # SQLAlchemy 모델
│   └── utils/             # 재료 파싱 등 유틸리티
├── scripts/               # 실행 스크립트
│   ├── migrate_csv_data.py    # 메인 마이그레이션
│   ├── verify_migration.py    # 검증
│   └── setup_database.py      # DB 설정
├── migrations/            # Alembic 마이그레이션
├── datas/                # CSV 파일
├── docs/                 # 상세 문서
│   ├── 05_implementation_roadmap.md  # 전체 로드맵
│   └── phases/           # 단계별 가이드
└── Dockerfile           # 통합 Docker 이미지
```

## 📚 상세 문서

- [구현 로드맵](docs/05_implementation_roadmap.md)
- [Phase 2: 데이터베이스 설정](docs/phases/phase2_database_setup.md)
- [Phase 3: 데이터 마이그레이션](docs/phases/phase3_data_migration.md)
- [Phase 4: 배포 가이드](docs/phases/phase4_kubernetes_deployment.md)

## ⚙️ 환경변수

`.env` 파일 필수 설정:
```bash
# PostgreSQL 연결
DATABASE_URL=postgresql://user:pass@localhost:5432/fridge2fork

# 마이그레이션 옵션
CHUNK_SIZE=100
MAX_RECORDS=0  # 0=전체
```

## 🔧 주요 기능

- **비동기 처리**: asyncio/aiohttp를 통한 효율적 데이터 수집
- **배치 처리**: 메모리 효율적인 청크 단위 처리
- **재료 파싱**: 한국어 재료 텍스트 정규화
- **전문검색**: PostgreSQL GIN 인덱스 기반 한국어 검색
- **Docker 지원**: 환경 독립적 실행

## 📊 데이터 스키마

### 주요 테이블
- `recipes`: 레시피 기본 정보
- `ingredients`: 재료 마스터
- `ingredient_categories`: 재료 카테고리 (8개)
- `recipe_ingredients`: 레시피-재료 관계

### 인덱스
- 한국어 전문검색 (GIN)
- 트라이그램 유사도 검색
- 성능 최적화 복합 인덱스

## 🛠 개발 가이드

### 테스트 실행
```bash
# 작은 데이터셋으로 테스트
python scripts/migrate_csv_data.py --max-records 100
```

### 디버깅
```bash
# Docker 컨테이너 쉘 접속
docker run -it --rm fridge2fork /bin/bash
```

## 📝 라이선스

MIT License