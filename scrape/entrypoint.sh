#!/bin/bash
set -e

# 환경변수 디버깅
echo "🔍 환경변수 확인:"
echo "POSTGRES_DB: ${POSTGRES_DB:-'NOT SET'}"
echo "POSTGRES_USER: ${POSTGRES_USER:-'NOT SET'}"
echo "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:+SET}"
echo "POSTGRES_SERVER: ${POSTGRES_SERVER:-'NOT SET'}"
echo "POSTGRES_PORT: ${POSTGRES_PORT:-'NOT SET'}"
if [ -n "$DATABASE_URL" ]; then
    echo "DATABASE_URL: SET (안전하게 마스킹됨)"
else
    echo "DATABASE_URL: NOT SET"
fi

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

    # DATABASE_URL에서 안전하게 호스트 정보만 추출하여 표시
    DB_HOST_SAFE=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT_SAFE=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME_SAFE=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
    log_info "DATABASE_URL 확인: postgresql://***:***@${DB_HOST_SAFE}:${DB_PORT_SAFE}/${DB_NAME_SAFE}"
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

    # 최대 5분 대기 (Kubernetes 환경에서 초기화 시간 고려)
    MAX_WAIT=${DB_MAX_WAIT:-300}  # 환경변수로 조정 가능, 기본 300초 (5분)
    WAIT_COUNT=0

    while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
        if pg_isready -h $DB_HOST -p $DB_PORT -t 1 >/dev/null 2>&1; then
            log_info "PostgreSQL 서버 연결 성공!"
            return 0
        fi
        echo -n "."
        sleep 1
        WAIT_COUNT=$((WAIT_COUNT + 1))
    done

    log_error "PostgreSQL 서버 연결 실패 (${MAX_WAIT}초 타임아웃)"
    exit 1
}

# Alembic 마이그레이션 실행
run_alembic_migrations() {
    log_info "==================== Alembic 마이그레이션 시작 ===================="

    # migrations/versions 디렉토리 확인 및 생성
    log_info "migrations 디렉토리 구조 확인 중..."
    if [ ! -d "migrations/versions" ]; then
        log_warning "⚠️ migrations/versions 디렉토리가 없습니다. 생성 중..."
        mkdir -p migrations/versions

        # __init__.py 파일 생성
        touch migrations/versions/__init__.py
        log_info "✅ migrations/versions 디렉토리 생성 완료"
    fi

    # 마이그레이션 파일이 있는지 확인
    if [ ! -f "migrations/versions/001_create_recipes_tables.py" ]; then
        log_info "📋 초기 마이그레이션 파일 생성 중..."

        # 초기 마이그레이션 파일을 환경에 맞게 생성
        cat > migrations/versions/001_create_recipes_tables.py << 'EOF'
"""Create recipes, ingredients, recipe_ingredients tables

Revision ID: 001_initial
Revises:
Create Date: 2025-09-28 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create recipes table
    op.create_table('recipes',
        sa.Column('rcp_sno', sa.BigInteger(), nullable=False),
        sa.Column('rcp_ttl', sa.String(length=200), nullable=False),
        sa.Column('ckg_nm', sa.String(length=40), nullable=True),
        sa.Column('rgtr_id', sa.String(length=32), nullable=True),
        sa.Column('rgtr_nm', sa.String(length=64), nullable=True),
        sa.Column('inq_cnt', sa.Integer(), nullable=True, default=0),
        sa.Column('rcmm_cnt', sa.Integer(), nullable=True, default=0),
        sa.Column('srap_cnt', sa.Integer(), nullable=True, default=0),
        sa.Column('ckg_mth_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_sta_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_mtrl_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_knd_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_ipdc', sa.Text(), nullable=True),
        sa.Column('ckg_mtrl_cn', sa.Text(), nullable=True),
        sa.Column('ckg_inbun_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_dodf_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_time_nm', sa.String(length=200), nullable=True),
        sa.Column('first_reg_dt', sa.CHAR(length=14), nullable=True),
        sa.Column('rcp_img_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('rcp_sno')
    )

    # Create indexes for recipes table
    op.create_index('ix_recipes_title', 'recipes', ['rcp_ttl'])
    op.create_index('ix_recipes_method', 'recipes', ['ckg_mth_acto_nm'])
    op.create_index('ix_recipes_difficulty', 'recipes', ['ckg_dodf_nm'])
    op.create_index('ix_recipes_time', 'recipes', ['ckg_time_nm'])
    op.create_index('ix_recipes_category', 'recipes', ['ckg_knd_acto_nm'])
    op.create_index('ix_recipes_popularity', 'recipes', ['inq_cnt', 'rcmm_cnt'], postgresql_using='btree')
    op.create_index('ix_recipes_reg_date', 'recipes', ['first_reg_dt'])
    op.create_index('ix_recipes_created_at', 'recipes', ['created_at'])
    op.create_index('ix_recipes_updated_at', 'recipes', ['updated_at'])

    # Create ingredients table
    op.create_table('ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('original_name', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('is_common', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create indexes for ingredients table
    op.create_index('ix_ingredients_name', 'ingredients', ['name'])
    op.create_index('ix_ingredients_category', 'ingredients', ['category'])
    op.create_index('ix_ingredients_common', 'ingredients', ['is_common'])
    op.create_index('ix_ingredients_created_at', 'ingredients', ['created_at'])
    op.create_index('ix_ingredients_category_common', 'ingredients', ['category', 'is_common'])

    # Create recipe_ingredients table
    op.create_table('recipe_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rcp_sno', sa.BigInteger(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity_text', sa.Text(), nullable=True),
        sa.Column('quantity_from', sa.Float(), nullable=True),
        sa.Column('quantity_to', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('is_vague', sa.Boolean(), nullable=True, default=False),
        sa.Column('display_order', sa.Integer(), nullable=True, default=0),
        sa.Column('importance', sa.String(length=20), nullable=True, default='normal'),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ),
        sa.ForeignKeyConstraint(['rcp_sno'], ['recipes.rcp_sno'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for recipe_ingredients table
    op.create_index('ix_recipe_ingredients_rcp_sno', 'recipe_ingredients', ['rcp_sno'])
    op.create_index('ix_recipe_ingredients_ingredient_id', 'recipe_ingredients', ['ingredient_id'])
    op.create_index('ix_recipe_ingredients_importance', 'recipe_ingredients', ['importance'])
    op.create_index('ix_recipe_ingredients_compound', 'recipe_ingredients', ['ingredient_id', 'rcp_sno', 'importance'])
    op.create_index('ix_recipe_ingredients_display_order', 'recipe_ingredients', ['rcp_sno', 'display_order'])
    op.create_index('uk_recipe_ingredient', 'recipe_ingredients', ['rcp_sno', 'ingredient_id'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('recipe_ingredients')
    op.drop_table('ingredients')
    op.drop_table('recipes')
EOF
        log_info "✅ 초기 마이그레이션 파일 생성 완료"
    fi

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
                # CSV 마이그레이션 실행
                if [ -f "main.py" ]; then
                    log_info "main.py를 통한 CSV 마이그레이션 실행"
                    export MODE=migrate
                    python main.py
                else
                    log_warning "⚠️ main.py가 없습니다. scripts/migrate_csv_data.py 직접 실행"
                    run_csv_migration
                fi
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