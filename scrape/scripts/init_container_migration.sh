#!/bin/bash
set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 환경변수 설정 (주의: 비밀번호 포함, 로그 출력 금지)
export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

log_info "🔄 데이터베이스 연결 대기 중..."
timeout=60
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  echo "Waiting for database..."
  sleep 2
  timeout=$((timeout - 2))
  if [ $timeout -le 0 ]; then
    log_error "❌ 데이터베이스 연결 타임아웃"
    exit 1
  fi
done
log_info "✅ 데이터베이스 연결 성공"

log_info "🔄 Alembic 마이그레이션 시작..."
cd /app

# 현재 마이그레이션 상태 확인
log_debug "현재 마이그레이션 상태 확인..."
alembic current || log_warning "마이그레이션 히스토리가 비어있음"

# 마이그레이션 파일 존재 확인
if [ ! "$(ls -A migrations/versions/ 2>/dev/null)" ]; then
  log_warning "마이그레이션 파일이 없습니다. 자동 생성을 시도합니다."

  # 마이그레이션 파일 자동 생성 시도
  log_info "🔧 마이그레이션 파일 자동 생성 중..."
  if alembic revision --autogenerate -m "Initial schema with recipes tables" 2>/dev/null; then
    log_info "✅ 마이그레이션 파일 자동 생성 성공"
  else
    log_warning "⚠️ 자동 생성 실패, 수동 생성된 마이그레이션 파일 사용"
  fi
fi

# 마이그레이션 실행
log_info "⚡ 마이그레이션 실행 중..."
alembic upgrade head

if [ $? -eq 0 ]; then
  log_info "✅ Alembic 마이그레이션 성공!"
else
  log_error "❌ Alembic 마이그레이션 실패!"
  exit 1
fi

# 테이블 생성 확인
log_info "🔍 생성된 테이블 확인..."
python3 -c "
import os
import asyncio
import asyncpg

async def check_tables():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        result = await conn.fetch(\"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name != 'alembic_version'\")
        tables = [row['table_name'] for row in result]
        print(f'✅ 생성된 테이블: {tables}')

        expected = ['recipes', 'ingredients', 'recipe_ingredients']
        missing = [t for t in expected if t not in tables]
        if missing:
            print(f'❌ 누락된 테이블: {missing}')
            exit(1)
        else:
            print(f'🎉 모든 필수 테이블 생성 완료: {len(tables)}개')
        await conn.close()
    except Exception as e:
        print(f'❌ 테이블 확인 실패: {e}')
        exit(1)

asyncio.run(check_tables())
"

if [ $? -eq 0 ]; then
  log_info "✅ 모든 테이블이 정상적으로 생성되었습니다!"
else
  log_error "❌ 테이블 생성 검증 실패!"
  exit 1
fi

log_info "🎉 init container 마이그레이션 완료!"