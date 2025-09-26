# 🐳 Fridge2Fork Admin API Dockerfile
# Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 캐시 최적화를 위한 환경 변수
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# requirements 파일들 복사
COPY requirements.common.txt requirements.dev.txt requirements.prod.txt ./

# 환경별 requirements 파일 설치
# ENVIRONMENT=development: requirements.dev.txt (개발용)
# ENVIRONMENT=production: requirements.prod.txt (운영용)
RUN if [ "$ENVIRONMENT" = "development" ]; then \
        echo "🛠️ 개발 환경 패키지 설치 중..."; \
        pip install --no-cache-dir -r requirements.dev.txt; \
    else \
        echo "🏭 운영 환경 패키지 설치 중..."; \
        pip install --no-cache-dir -r requirements.prod.txt; \
    fi

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# entrypoint.sh 스크립트를 실행 파일로 복사
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 환경 변수에 따른 실행 명령 분기
# ENVIRONMENT=development: uvicorn (개발용)
# ENVIRONMENT=production: gunicorn (운영용)
ENTRYPOINT ["/entrypoint.sh"]
