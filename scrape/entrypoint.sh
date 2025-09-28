#!/bin/bash
set -e

# 환경변수 디버깅
echo "🔍 환경변수 확인:"
echo "POSTGRES_DB: ${POSTGRES_DB:-'NOT SET'}"
echo "POSTGRES_USER: ${POSTGRES_USER:-'NOT SET'}"
echo "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:+SET}"
echo "POSTGRES_SERVER: ${POSTGRES_SERVER:-'NOT SET'}"
echo "POSTGRES_PORT: ${POSTGRES_PORT:-'NOT SET'}"
echo "DATABASE_URL: ${DATABASE_URL:-'NOT SET'}"

# Kubernetes Secret에서 주입된 환경변수로 DATABASE_URL 구성
if [ -n "$POSTGRES_DB" ] && [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_PASSWORD" ] && [ -n "$POSTGRES_SERVER" ] && [ -n "$POSTGRES_PORT" ]; then
    # DATABASE_URL 구성
    export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}:${POSTGRES_PORT}/${POSTGRES_DB}"
    echo "✅ DATABASE_URL 구성 완료: postgresql://${POSTGRES_USER}:***@${POSTGRES_SERVER}:${POSTGRES_PORT}/${POSTGRES_DB}"
else
    echo "⚠️ 일부 PostgreSQL 환경변수가 설정되지 않았습니다."
    echo "필요한 환경변수: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_PORT"
fi

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 환경변수 확인
check_environment() {
    log_info "환경변수 확인 중..."

    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL이 설정되지 않았습니다."
        exit 1
    fi

    log_info "DATABASE_URL 확인: ${DATABASE_URL%%@*}@***"
    log_info "MIGRATION_MODE: ${MIGRATION_MODE:-full}"
    log_info "CHUNK_SIZE: ${CHUNK_SIZE:-100}"
    log_info "MAX_RECORDS: ${MAX_RECORDS:-0}"
}

# PostgreSQL 연결 대기
wait_for_postgres() {
    log_info "PostgreSQL 서버 연결 대기 중..."

    # DATABASE_URL에서 호스트와 포트 추출
    # postgresql://user:pass@host:port/dbname 형식
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

    if [ -z "$DB_HOST" ]; then
        DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^/]*\)\/.*/\1/p')
        DB_PORT=5432
    fi

    log_info "PostgreSQL 서버: $DB_HOST:$DB_PORT"

    # 최대 30초 대기
    for i in {1..30}; do
        if pg_isready -h $DB_HOST -p $DB_PORT -t 1 >/dev/null 2>&1; then
            log_info "PostgreSQL 서버 연결 성공!"
            return 0
        fi
        echo -n "."
        sleep 1
    done

    log_error "PostgreSQL 서버 연결 실패 (30초 타임아웃)"
    exit 1
}

# Alembic 마이그레이션 실행
run_alembic_migrations() {
    log_info "==================== Alembic 마이그레이션 시작 ===================="

    # 현재 마이그레이션 상태 확인
    log_info "현재 마이그레이션 상태 확인..."
    python -m alembic current || true

    # 마이그레이션 실행
    log_info "마이그레이션 실행 중..."
    python -m alembic upgrade head

    if [ $? -eq 0 ]; then
        log_info "✅ Alembic 마이그레이션 성공!"

        # 마이그레이션 히스토리 출력
        log_info "마이그레이션 히스토리:"
        python -m alembic history --verbose
    else
        log_error "❌ Alembic 마이그레이션 실패!"
        exit 1
    fi
}

# CSV 데이터 마이그레이션
run_csv_migration() {
    log_info "==================== CSV 데이터 마이그레이션 시작 ===================="

    # 마이그레이션 옵션 설정
    MIGRATION_ARGS=""

    if [ "$CHUNK_SIZE" != "0" ]; then
        MIGRATION_ARGS="$MIGRATION_ARGS --chunk-size $CHUNK_SIZE"
    fi

    if [ "$MAX_RECORDS" != "0" ]; then
        MIGRATION_ARGS="$MIGRATION_ARGS --max-records $MAX_RECORDS"
    fi

    log_info "마이그레이션 옵션: $MIGRATION_ARGS"

    # CSV 파일 확인
    log_info "CSV 파일 확인 중..."
    if ls datas/*.csv >/dev/null 2>&1; then
        log_info "발견된 CSV 파일들:"
        ls -lh datas/*.csv
    else
        log_warning "⚠️ CSV 파일이 없습니다. 볼륨이 마운트되었는지 확인하세요."
        log_info "현재 datas 디렉토리 내용:"
        ls -la datas/ || log_warning "datas 디렉토리가 존재하지 않습니다."
    fi

    # 마이그레이션 실행
    python scripts/migrate_csv_data.py $MIGRATION_ARGS

    if [ $? -eq 0 ]; then
        log_info "✅ CSV 데이터 마이그레이션 성공!"
    else
        log_error "❌ CSV 데이터 마이그레이션 실패!"
        exit 1
    fi
}

# 마이그레이션 검증
verify_migration() {
    log_info "==================== 마이그레이션 검증 시작 ===================="

    python scripts/verify_migration.py

    if [ $? -eq 0 ]; then
        log_info "✅ 마이그레이션 검증 성공!"
    else
        log_error "❌ 마이그레이션 검증 실패!"
        exit 1
    fi
}

# 메인 함수
main() {
    log_info "🚀 Fridge2Fork 애플리케이션 시작"
    log_info "시작 시간: $(date)"

    # 환경 확인
    check_environment

    # PostgreSQL 연결 대기
    wait_for_postgres

    # 명령어에 따른 처리
    case "${1:-migrate}" in
        migrate)
            # 전체 마이그레이션 프로세스
            log_info "전체 마이그레이션 모드"
            run_alembic_migrations

            if [ "$MIGRATION_MODE" != "schema-only" ]; then
                # main.py를 사용한 CSV 마이그레이션
                log_info "main.py를 통한 CSV 마이그레이션 실행"
                export MODE=migrate
                python main.py
                verify_migration
            fi
            ;;

        app)
            # 유지보수 모드 (main.py 실행)
            log_info "유지보수 모드 실행"
            run_alembic_migrations  # 스키마 확인
            export MODE=maintenance
            python main.py
            ;;

        verify)
            # 데이터 검증 모드
            log_info "데이터 무결성 검증 모드"
            export MODE=verify
            python main.py
            ;;

        stats)
            # 통계 모드
            log_info "데이터베이스 통계 모드"
            export MODE=stats
            python main.py
            ;;

        health)
            # 헬스 체크 모드
            log_info "헬스 체크 모드"
            export MODE=health
            python main.py
            ;;

        alembic)
            # Alembic 마이그레이션만
            log_info "Alembic 마이그레이션만 실행"
            run_alembic_migrations
            ;;

        data)
            # 데이터 마이그레이션만
            log_info "데이터 마이그레이션만 실행"
            export MODE=migrate
            python main.py
            ;;

        verify)
            # 검증만
            log_info "마이그레이션 검증만 실행"
            verify_migration
            ;;

        shell)
            # 디버깅용 쉘
            log_info "디버그 쉘 모드"
            exec /bin/bash
            ;;

        db-migration)
            # 데이터베이스 스키마 마이그레이션만
            log_info "데이터베이스 스키마 마이그레이션 실행"
            python run_migration.py
            ;;

        *)
            # 직접 명령어 실행
            log_info "직접 명령어 실행: $@"
            exec "$@"
            ;;
    esac

    log_info "🎉 작업 완료!"
    log_info "종료 시간: $(date)"
}

# 스크립트 실행
main "$@"