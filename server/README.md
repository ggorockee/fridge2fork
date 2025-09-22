# Fridge2Fork API Server

냉장고 재료 기반 한식 레시피 추천 API 서버입니다.

## 🛠️ 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **Session Store**: Redis
- **Authentication**: JWT
- **Migration**: Alembic
- **Python Environment**: Conda

## 📋 사전 요구사항

1. **Conda 환경 설정**
   ```bash
   # conda 환경 생성
   conda create -n fridge2fork python=3.11
   conda activate fridge2fork
   ```

2. **데이터베이스 서버**
   - PostgreSQL 서버 실행 중
   - Redis 서버 실행 중

## 🚀 설치 및 실행

### 1. 환경 설정

```bash
# conda 환경 활성화
conda activate fridge2fork

# 의존성 설치 (개발 환경)
pip install -r requirements.dev.txt

# 또는 운영 환경
pip install -r requirements.prod.txt
```

### 2. 환경 변수 설정

`.env.dev` (개발 환경) 또는 `.env.prod` (운영 환경) 파일에 실제 데이터베이스 정보를 설정하세요:

```env
# 개발 환경 (.env.dev)
DEBUG=True
ENVIRONMENT=development

# 데이터베이스 설정
DATABASE_URL=postgresql://username:password@localhost:5432/fridge2fork_dev
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fridge2fork_dev
DB_USER=username
DB_PASSWORD=password

# JWT 시크릿 키
JWT_SECRET_KEY=your_development_secret_key

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 3. 데이터베이스 마이그레이션

```bash
# conda 환경에서 실행
conda activate fridge2fork

# 마이그레이션 실행
python scripts/migrate.py
```

### 4. 서버 실행

#### 개발 환경
```bash
# 개발 서버 실행 (자동 리로드)
python scripts/run_dev.py

# 또는 직접 실행
ENVIRONMENT=development python main.py
```

#### 운영 환경
```bash
# 운영 서버 실행
python scripts/run_prod.py

# 또는 직접 실행
ENVIRONMENT=production python main.py
```

## 📚 API 문서

서버 실행 후 다음 주소에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🗂️ 프로젝트 구조

```
server/
├── app/
│   ├── api/v1/           # API 엔드포인트
│   ├── core/             # 핵심 설정
│   ├── models/           # 데이터베이스 모델
│   └── schemas/          # Pydantic 스키마
├── alembic/              # 데이터베이스 마이그레이션
├── scripts/              # 실행 스크립트
├── .env.common           # 공통 환경 변수
├── .env.dev              # 개발 환경 변수
├── .env.prod             # 운영 환경 변수
└── main.py               # 메인 애플리케이션
```

## 🔧 주요 스크립트

### 설정 스크립트
```bash
python scripts/setup.py      # 초기 설정
```

### 마이그레이션
```bash
python scripts/migrate.py    # 데이터베이스 마이그레이션
```

### 서버 실행
```bash
python scripts/run_dev.py    # 개발 서버
python scripts/run_prod.py   # 운영 서버
```

## 🌐 API 엔드포인트

### 인증 (Authentication) - `/v1/auth`
- `POST /v1/auth/register` - 회원가입
- `POST /v1/auth/login` - 로그인
- `POST /v1/auth/logout` - 로그아웃
- `POST /v1/auth/refresh` - 토큰 갱신
- `GET /v1/auth/profile` - 프로필 조회
- `PUT /v1/auth/profile` - 프로필 수정

### 레시피 (Recipes) - `/v1/recipes`
- `GET /v1/recipes` - 레시피 목록 조회
- `GET /v1/recipes/{id}` - 레시피 상세 조회
- `GET /v1/recipes/categories` - 카테고리 목록
- `GET /v1/recipes/popular` - 인기 레시피

### 냉장고 (Fridge) - `/v1/fridge`
- `GET /v1/fridge/ingredients` - 보유 재료 조회
- `POST /v1/fridge/ingredients` - 재료 추가
- `DELETE /v1/fridge/ingredients/{name}` - 재료 제거
- `POST /v1/fridge/cooking-complete` - 요리 완료

### 사용자 (User) - `/v1/user`
- `GET /v1/user/favorites` - 즐겨찾기 목록
- `POST /v1/user/favorites/{recipe_id}` - 즐겨찾기 추가
- `GET /v1/user/cooking-history` - 요리 히스토리
- `GET /v1/user/recommendations` - 맞춤 추천
- `POST /v1/user/feedback` - 피드백 제출

### 시스템 (System) - `/v1/system`
- `GET /v1/version` - 버전 정보
- `GET /v1/system/platforms` - 플랫폼 정보
- `GET /v1/system/health` - 헬스체크

## 🔒 인증 방식

- **JWT Bearer Token**: 회원 전용 기능
- **Session ID**: 냉장고 관리 (비회원 포함)

## 🐛 문제 해결

### conda 환경 관련
```bash
# conda 환경이 활성화되지 않은 경우
conda activate fridge2fork

# 의존성 설치 문제
pip install --upgrade pip
pip install -r requirements.dev.txt
```

### 데이터베이스 연결 문제
1. PostgreSQL 서버가 실행 중인지 확인
2. `.env.dev` 또는 `.env.prod`의 데이터베이스 정보 확인
3. 데이터베이스가 생성되어 있는지 확인

### Redis 연결 문제
1. Redis 서버가 실행 중인지 확인
2. Redis URL 설정 확인

## 📝 개발 가이드

### 새로운 마이그레이션 생성
```bash
alembic revision --autogenerate -m "설명"
```

### 마이그레이션 적용
```bash
alembic upgrade head
```

### 마이그레이션 롤백
```bash
alembic downgrade -1
```

## 📞 지원

문제가 발생하면 다음을 확인해주세요:

1. conda 환경 `fridge2fork`가 활성화되어 있는지
2. 필요한 환경 파일들이 올바르게 설정되어 있는지
3. PostgreSQL과 Redis 서버가 실행 중인지
4. 로그 메시지에서 구체적인 오류 내용 확인
