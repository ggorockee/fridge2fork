# 통합 Dockerfile - 크롤링과 마이그레이션 모두 지원
FROM python:3.12-slim

# 필수 시스템 패키지 설치 (PostgreSQL 클라이언트 포함)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사
COPY requirements*.txt ./

# 모든 의존성 설치
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-api.txt

# 애플리케이션 코드 복사
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY migrations/ ./migrations/
COPY datas/ ./datas/
COPY alembic.ini ./alembic.ini
COPY crawler.py ./crawler.py
COPY entrypoint.sh ./entrypoint.sh

# 스크립트 실행 권한 부여
RUN chmod +x scripts/*.py && \
    chmod +x entrypoint.sh

# 환경변수 설정
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    MODE=crawler

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# MODE 환경변수에 따라 실행 모드 결정
# MODE=crawler: 크롤링 실행 (기본값)
# MODE=migration: DB 마이그레이션 실행
ENTRYPOINT ["/bin/sh", "-c", "if [ \"$MODE\" = 'migration' ]; then exec /entrypoint.sh \"$@\"; else exec python crawler.py \"$@\"; fi", "--"]
