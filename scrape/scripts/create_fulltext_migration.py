#!/usr/bin/env python3
"""
전문검색 인덱스 마이그레이션 생성 스크립트

Usage:
    python scripts/create_fulltext_migration.py

Prerequisites:
    - DATABASE_URL이 .env 파일에 설정되어 있어야 함
    - 초기 마이그레이션이 실행되어 있어야 함
"""
import subprocess
import sys
import os
from pathlib import Path

def create_fulltext_migration():
    """전문검색 마이그레이션 생성"""
    # 프로젝트 루트로 이동
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("🔄 전문검색 마이그레이션 생성 중...")

    try:
        # 빈 마이그레이션 생성
        result = subprocess.run([
            sys.executable, "-m", "alembic", "revision",
            "-m", "Add fulltext search indexes"
        ], capture_output=True, text=True, check=True)

        print("✅ 마이그레이션 파일 생성 완료")
        print(f"출력: {result.stdout}")

        # 생성된 마이그레이션 파일 찾기
        versions_dir = project_root / "migrations" / "versions"
        migration_files = list(versions_dir.glob("*_add_fulltext_search_indexes.py"))

        if migration_files:
            migration_file = migration_files[0]
            print(f"📄 생성된 마이그레이션 파일: {migration_file.name}")

            # 마이그레이션 파일에 전문검색 코드 추가
            add_fulltext_code_to_migration(migration_file)
        else:
            # 가장 최근 마이그레이션 파일 찾기
            all_migration_files = list(versions_dir.glob("*.py"))
            if all_migration_files:
                latest_migration = max(all_migration_files, key=lambda p: p.stat().st_mtime)
                print(f"📄 최신 마이그레이션 파일: {latest_migration.name}")
                add_fulltext_code_to_migration(latest_migration)

    except subprocess.CalledProcessError as e:
        print(f"❌ 마이그레이션 생성 실패: {e}")
        print(f"에러 출력: {e.stderr}")
        return 1
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return 1

    return 0

def add_fulltext_code_to_migration(migration_file_path):
    """마이그레이션 파일에 전문검색 코드 추가"""
    print(f"📝 마이그레이션 파일에 전문검색 코드 추가: {migration_file_path.name}")

    # 전문검색 마이그레이션 코드
    fulltext_migration_code = '''"""Add fulltext search indexes

Revision ID: {revision}
Revises: {down_revision}
Create Date: {create_date}

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '{revision}'
down_revision = '{down_revision}'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """전문검색 인덱스 추가"""

    # PostgreSQL pg_trgm 확장 설치
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # 레시피 제목/요리명에 한국어 전문검색 GIN 인덱스 생성
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_recipes_title_fulltext
        ON recipes USING gin(to_tsvector('korean', title));
    """)

    # 재료명에 전문검색 인덱스 생성
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_ingredients_name_fulltext
        ON ingredients USING gin(to_tsvector('korean', name));
    """)

    # 재료명에 트라이그램 인덱스 생성 (유사도 검색용)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_ingredients_name_trgm
        ON ingredients USING gin(name gin_trgm_ops);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_ingredients_normalized_name_trgm
        ON ingredients USING gin(normalized_name gin_trgm_ops);
    """)

    # 성능 최적화를 위한 복합 인덱스
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_recipe_ingredients_recipe_ingredient
        ON recipe_ingredients(recipe_id, ingredient_id);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_recipe_ingredients_importance_recipe
        ON recipe_ingredients(importance, recipe_id) WHERE importance = 'essential';
    """)

def downgrade() -> None:
    """전문검색 인덱스 제거"""

    # 인덱스 제거
    op.execute("DROP INDEX IF EXISTS ix_recipes_title_fulltext;")
    op.execute("DROP INDEX IF EXISTS ix_ingredients_name_fulltext;")
    op.execute("DROP INDEX IF EXISTS ix_ingredients_name_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_ingredients_normalized_name_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_recipe_ingredients_recipe_ingredient;")
    op.execute("DROP INDEX IF EXISTS ix_recipe_ingredients_importance_recipe;")

    # pg_trgm 확장은 제거하지 않음 (다른 곳에서 사용될 수 있음)
'''

    try:
        # 기존 파일 읽기
        with open(migration_file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # 파일에서 revision, down_revision, create_date 추출
        import re

        revision_match = re.search(r"revision = ['\"]([^'\"]+)['\"]", original_content)
        down_revision_match = re.search(r"down_revision = ['\"]?([^'\"]+)['\"]?", original_content)
        create_date_match = re.search(r"Create Date: (.+)", original_content)

        if revision_match and down_revision_match and create_date_match:
            revision = revision_match.group(1)
            down_revision = down_revision_match.group(1)
            create_date = create_date_match.group(1)

            # 코드에 값 대입
            final_code = fulltext_migration_code.format(
                revision=revision,
                down_revision=down_revision,
                create_date=create_date
            )

            # 파일 덮어쓰기
            with open(migration_file_path, 'w', encoding='utf-8') as f:
                f.write(final_code)

            print("✅ 전문검색 코드가 마이그레이션 파일에 추가되었습니다.")
        else:
            print("⚠️  마이그레이션 파일에서 필요한 정보를 찾을 수 없습니다.")
            print("📄 수동으로 전문검색 코드를 추가해야 합니다.")

    except Exception as e:
        print(f"❌ 마이그레이션 파일 수정 실패: {e}")

def main():
    """메인 함수"""
    return create_fulltext_migration()

if __name__ == "__main__":
    sys.exit(main())