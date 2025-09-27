# 데이터 마이그레이션 가이드

## 개요

Alembic을 사용한 데이터베이스 스키마 마이그레이션과 CSV 데이터를 PostgreSQL로 배치 입력하는 프로세스를 설명합니다.

## 1. Alembic 초기 설정

### Alembic 초기화
```bash
# 프로젝트 루트에서 실행
alembic init migrations

# alembic.ini 파일이 생성되고, migrations/ 디렉토리가 생성됩니다
```

### alembic.ini 설정
```ini
# alembic.ini
[alembic]
# 마이그레이션 스크립트 위치
script_location = migrations

# 데이터베이스 URL (환경변수 사용)
sqlalchemy.url =

# 기타 설정
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url =

[post_write_hooks]
# 코드 포맷팅 후크 (선택적)
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 88 REVISION_SCRIPT_FILENAME

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### migrations/env.py 설정
```python
"""Alembic 환경 설정"""

import asyncio
import os
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# Alembic Config 객체
config = context.config

# 환경변수에서 데이터베이스 URL 설정
config.set_main_option(
    "sqlalchemy.url",
    os.getenv("DATABASE_URL", "postgresql://localhost/fridge2fork_db")
)

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 모델 메타데이터 import
# 실제 모델들을 import 해야 auto-generate가 작동합니다
from app.db.base import Base  # 모든 모델이 포함된 Base import

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """오프라인 모드에서 마이그레이션 실행"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """마이그레이션 실행"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """비동기 마이그레이션 실행"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """온라인 모드에서 마이그레이션 실행"""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## 2. 데이터베이스 모델 정의

### app/models/recipe.py
```python
"""레시피 관련 데이터베이스 모델"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, DECIMAL, func
)
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Recipe(Base):
    """레시피 모델"""
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    rcp_sno = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    cooking_name = Column(String(200))
    registrant_id = Column(String(100))
    registrant_name = Column(String(100))
    inquiry_count = Column(Integer, default=0)
    recommendation_count = Column(Integer, default=0)
    scrap_count = Column(Integer, default=0)
    cooking_method = Column(String(100), index=True)
    cooking_situation = Column(String(100), index=True)
    cooking_material_category = Column(String(100))
    cooking_kind = Column(String(100))
    introduction = Column(Text)
    raw_ingredients = Column(Text)
    serving_size = Column(String(50))
    difficulty = Column(String(50), index=True)
    cooking_time = Column(String(50), index=True)
    registered_at = Column(DateTime)
    image_url = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 관계 설정
    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe")

class Ingredient(Base):
    """재료 모델"""
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    normalized_name = Column(String(200), nullable=False, index=True)
    category = Column(String(100), index=True)
    is_vague = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=func.now())

    # 관계 설정
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient")

class RecipeIngredient(Base):
    """레시피-재료 관계 모델"""
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False, index=True)
    quantity_text = Column(String(100))
    quantity_from = Column(DECIMAL(10, 2))
    quantity_to = Column(DECIMAL(10, 2))
    unit = Column(String(50), index=True)
    is_essential = Column(Boolean, default=True, index=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    # 관계 설정
    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")

class IngredientCategory(Base):
    """재료 카테고리 모델"""
    __tablename__ = "ingredient_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("ingredient_categories.id"))
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())

    # 자기 참조 관계
    parent = relationship("IngredientCategory", remote_side=[id])
```

### app/db/base_class.py
```python
"""SQLAlchemy Base 클래스"""

from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr

@as_declarative()
class Base:
    id: Any
    __name__: str

    # 테이블명 자동 생성
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
```

### app/db/base.py
```python
"""모든 모델을 import하는 파일 (Alembic auto-generate용)"""

from app.db.base_class import Base
from app.models.recipe import Recipe, Ingredient, RecipeIngredient, IngredientCategory

# Alembic이 모든 모델을 인식할 수 있도록 __all__에 추가
__all__ = ["Base", "Recipe", "Ingredient", "RecipeIngredient", "IngredientCategory"]
```

## 3. 마이그레이션 생성 및 실행

### 첫 번째 마이그레이션 생성
```bash
# 환경 활성화
conda activate fridge2fork

# 첫 번째 마이그레이션 생성
alembic revision --autogenerate -m "Initial migration: create recipes, ingredients, recipe_ingredients, ingredient_categories tables"

# 생성된 마이그레이션 파일 확인
ls migrations/versions/
```

### 마이그레이션 검토 및 수정
생성된 마이그레이션 파일을 검토하고 필요시 수정:

```python
"""Initial migration: create recipes, ingredients tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 재료 카테고리 테이블
    op.create_table('ingredient_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['ingredient_categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_ingredient_categories_id'), 'ingredient_categories', ['id'], unique=False)

    # 재료 테이블
    op.create_table('ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('normalized_name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_vague', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_ingredients_category'), 'ingredients', ['category'], unique=False)
    op.create_index(op.f('ix_ingredients_id'), 'ingredients', ['id'], unique=False)
    op.create_index(op.f('ix_ingredients_is_vague'), 'ingredients', ['is_vague'], unique=False)
    op.create_index(op.f('ix_ingredients_name'), 'ingredients', ['name'], unique=False)
    op.create_index(op.f('ix_ingredients_normalized_name'), 'ingredients', ['normalized_name'], unique=False)

    # 레시피 테이블
    op.create_table('recipes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rcp_sno', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('cooking_name', sa.String(length=200), nullable=True),
        sa.Column('registrant_id', sa.String(length=100), nullable=True),
        sa.Column('registrant_name', sa.String(length=100), nullable=True),
        sa.Column('inquiry_count', sa.Integer(), nullable=True),
        sa.Column('recommendation_count', sa.Integer(), nullable=True),
        sa.Column('scrap_count', sa.Integer(), nullable=True),
        sa.Column('cooking_method', sa.String(length=100), nullable=True),
        sa.Column('cooking_situation', sa.String(length=100), nullable=True),
        sa.Column('cooking_material_category', sa.String(length=100), nullable=True),
        sa.Column('cooking_kind', sa.String(length=100), nullable=True),
        sa.Column('introduction', sa.Text(), nullable=True),
        sa.Column('raw_ingredients', sa.Text(), nullable=True),
        sa.Column('serving_size', sa.String(length=50), nullable=True),
        sa.Column('difficulty', sa.String(length=50), nullable=True),
        sa.Column('cooking_time', sa.String(length=50), nullable=True),
        sa.Column('registered_at', sa.DateTime(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rcp_sno')
    )

    # 레시피-재료 관계 테이블
    op.create_table('recipe_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity_text', sa.String(length=100), nullable=True),
        sa.Column('quantity_from', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('quantity_to', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('is_essential', sa.Boolean(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 인덱스 생성
    op.create_index(op.f('ix_recipes_cooking_method'), 'recipes', ['cooking_method'], unique=False)
    op.create_index(op.f('ix_recipes_cooking_situation'), 'recipes', ['cooking_situation'], unique=False)
    op.create_index(op.f('ix_recipes_difficulty'), 'recipes', ['difficulty'], unique=False)
    op.create_index(op.f('ix_recipes_cooking_time'), 'recipes', ['cooking_time'], unique=False)
    op.create_index(op.f('ix_recipes_rcp_sno'), 'recipes', ['rcp_sno'], unique=False)
    op.create_index(op.f('ix_recipes_title'), 'recipes', ['title'], unique=False)

    op.create_index(op.f('ix_recipe_ingredients_ingredient_id'), 'recipe_ingredients', ['ingredient_id'], unique=False)
    op.create_index(op.f('ix_recipe_ingredients_is_essential'), 'recipe_ingredients', ['is_essential'], unique=False)
    op.create_index(op.f('ix_recipe_ingredients_recipe_id'), 'recipe_ingredients', ['recipe_id'], unique=False)
    op.create_index(op.f('ix_recipe_ingredients_unit'), 'recipe_ingredients', ['unit'], unique=False)

    # 복합 인덱스 (성능 최적화)
    op.create_index('ix_recipe_ingredients_ingredient_essential', 'recipe_ingredients', ['ingredient_id', 'is_essential'], unique=False)

    # 기본 카테고리 데이터 삽입
    op.execute("""
        INSERT INTO ingredient_categories (name, description) VALUES
        ('육류', '소고기, 돼지고기, 닭고기 등'),
        ('해산물', '생선, 새우, 조개 등'),
        ('채소류', '양파, 당근, 배추 등'),
        ('양념류', '간장, 소금, 설탕 등'),
        ('곡류', '쌀, 면류, 밀가루 등'),
        ('유제품', '우유, 치즈, 버터 등'),
        ('가공식품', '햄, 소시지, 통조림 등'),
        ('조미료', '다시다, 후추, 마늘 등'),
        ('기타', '분류되지 않은 재료');
    """)

def downgrade() -> None:
    op.drop_index('ix_recipe_ingredients_ingredient_essential', table_name='recipe_ingredients')
    op.drop_index(op.f('ix_recipe_ingredients_unit'), table_name='recipe_ingredients')
    op.drop_index(op.f('ix_recipe_ingredients_recipe_id'), table_name='recipe_ingredients')
    op.drop_index(op.f('ix_recipe_ingredients_is_essential'), table_name='recipe_ingredients')
    op.drop_index(op.f('ix_recipe_ingredients_ingredient_id'), table_name='recipe_ingredients')
    op.drop_table('recipe_ingredients')

    op.drop_index(op.f('ix_recipes_title'), table_name='recipes')
    op.drop_index(op.f('ix_recipes_rcp_sno'), table_name='recipes')
    op.drop_index(op.f('ix_recipes_cooking_time'), table_name='recipes')
    op.drop_index(op.f('ix_recipes_difficulty'), table_name='recipes')
    op.drop_index(op.f('ix_recipes_cooking_situation'), table_name='recipes')
    op.drop_index(op.f('ix_recipes_cooking_method'), table_name='recipes')
    op.drop_table('recipes')

    op.drop_index(op.f('ix_ingredients_normalized_name'), table_name='ingredients')
    op.drop_index(op.f('ix_ingredients_name'), table_name='ingredients')
    op.drop_index(op.f('ix_ingredients_is_vague'), table_name='ingredients')
    op.drop_index(op.f('ix_ingredients_id'), table_name='ingredients')
    op.drop_index(op.f('ix_ingredients_category'), table_name='ingredients')
    op.drop_table('ingredients')

    op.drop_index(op.f('ix_ingredient_categories_id'), table_name='ingredient_categories')
    op.drop_table('ingredient_categories')
```

### 마이그레이션 실행
```bash
# 현재 마이그레이션 상태 확인
alembic current

# 최신 마이그레이션으로 업그레이드
alembic upgrade head

# 마이그레이션 히스토리 확인
alembic history

# 특정 리비전으로 업그레이드/다운그레이드
alembic upgrade 001_initial
alembic downgrade base
```

## 4. 전문 검색 인덱스 추가

한국어 전문 검색을 위한 GIN 인덱스를 별도 마이그레이션으로 생성:

```bash
# 전문 검색 인덱스 마이그레이션 생성
alembic revision -m "Add full-text search indexes"
```

```python
"""Add full-text search indexes

Revision ID: 002_fulltext_search
Revises: 001_initial
Create Date: 2024-01-01 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002_fulltext_search'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 한국어 전문 검색을 위한 GIN 인덱스 생성
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
    """)

    # 레시피 제목 전문 검색 인덱스
    op.execute("""
        CREATE INDEX CONCURRENTLY ix_recipes_title_gin
        ON recipes USING GIN (to_tsvector('korean', title));
    """)

    # 요리명 전문 검색 인덱스
    op.execute("""
        CREATE INDEX CONCURRENTLY ix_recipes_cooking_name_gin
        ON recipes USING GIN (to_tsvector('korean', cooking_name));
    """)

    # 재료명 전문 검색 인덱스
    op.execute("""
        CREATE INDEX CONCURRENTLY ix_ingredients_name_gin
        ON ingredients USING GIN (to_tsvector('korean', name));
    """)

    # 정규화된 재료명 전문 검색 인덱스
    op.execute("""
        CREATE INDEX CONCURRENTLY ix_ingredients_normalized_gin
        ON ingredients USING GIN (to_tsvector('korean', normalized_name));
    """)

    # 트라이그램 인덱스 (유사 검색용)
    op.execute("""
        CREATE INDEX CONCURRENTLY ix_ingredients_name_trigram
        ON ingredients USING GIN (name gin_trgm_ops);
    """)

def downgrade() -> None:
    op.execute("DROP INDEX CONCURRENTLY ix_ingredients_name_trigram;")
    op.execute("DROP INDEX CONCURRENTLY ix_ingredients_normalized_gin;")
    op.execute("DROP INDEX CONCURRENTLY ix_ingredients_name_gin;")
    op.execute("DROP INDEX CONCURRENTLY ix_recipes_cooking_name_gin;")
    op.execute("DROP INDEX CONCURRENTLY ix_recipes_title_gin;")
```

## 5. 데이터베이스 설정 스크립트

### scripts/setup_database.py
```python
#!/usr/bin/env python3
"""데이터베이스 초기 설정 스크립트"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
from app.core.config import settings
from app.db.base import Base

async def create_database_if_not_exists():
    """데이터베이스가 존재하지 않으면 생성"""
    # 데이터베이스명 제외한 URL로 연결
    base_url = settings.DATABASE_URL.replace(f"/{settings.DATABASE_NAME}", "/postgres")
    engine = create_async_engine(base_url)

    async with engine.connect() as conn:
        # 데이터베이스 존재 확인
        result = await conn.execute(
            f"SELECT 1 FROM pg_database WHERE datname = '{settings.DATABASE_NAME}'"
        )

        if not result.fetchone():
            # 데이터베이스 생성
            await conn.execute(f"CREATE DATABASE {settings.DATABASE_NAME}")
            print(f"✅ 데이터베이스 '{settings.DATABASE_NAME}' 생성 완료")
        else:
            print(f"✅ 데이터베이스 '{settings.DATABASE_NAME}' 이미 존재")

    await engine.dispose()

async def create_tables():
    """테이블 생성 (개발/테스트용 - 운영에서는 Alembic 사용)"""
    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ 테이블 생성 완료")

    await engine.dispose()

async def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.connect() as conn:
            result = await conn.execute("SELECT version()")
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL 연결 성공: {version}")
        await engine.dispose()
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False

async def main():
    """메인 함수"""
    load_dotenv()

    print("🔧 데이터베이스 설정 시작...\n")

    # 1. 데이터베이스 생성
    try:
        await create_database_if_not_exists()
    except Exception as e:
        print(f"❌ 데이터베이스 생성 실패: {e}")
        return 1

    # 2. 연결 테스트
    if not await test_connection():
        return 1

    print("\n🎉 데이터베이스 설정 완료!")
    print("\n다음 단계:")
    print("1. alembic upgrade head  # 스키마 생성")
    print("2. python scripts/load_csv_data.py  # 데이터 로드")

    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))
```

## 6. 마이그레이션 실행 절차

### 전체 설정 및 마이그레이션 실행
```bash
# 1. 환경 활성화
conda activate fridge2fork

# 2. 환경변수 설정 확인
cat .env

# 3. 데이터베이스 설정
python scripts/setup_database.py

# 4. Alembic 현재 상태 확인
alembic current

# 5. 마이그레이션 실행
alembic upgrade head

# 6. 마이그레이션 히스토리 확인
alembic history --verbose

# 7. 테이블 생성 확인
psql fridge2fork_db -c "\dt"
```

### 마이그레이션 검증
```sql
-- PostgreSQL 콘솔에서 실행
\c fridge2fork_db

-- 테이블 목록 확인
\dt

-- 각 테이블 구조 확인
\d recipes
\d ingredients
\d recipe_ingredients
\d ingredient_categories

-- 인덱스 확인
\di

-- 외래키 제약조건 확인
SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public';

-- 기본 카테고리 데이터 확인
SELECT * FROM ingredient_categories;
```

## 7. 트러블슈팅

### 일반적인 문제들

1. **Alembic 자동 감지 실패**:
   ```bash
   # 모델 import 확인
   python -c "from app.db.base import Base; print(Base.metadata.tables.keys())"

   # 수동으로 마이그레이션 생성
   alembic revision -m "manual migration"
   ```

2. **데이터베이스 연결 실패**:
   ```bash
   # PostgreSQL 서비스 상태 확인
   brew services list | grep postgresql  # macOS
   sudo systemctl status postgresql      # Ubuntu

   # 연결 테스트
   psql -h localhost -U username -d fridge2fork_db
   ```

3. **인코딩 문제**:
   ```sql
   -- 데이터베이스 인코딩 확인
   SHOW client_encoding;
   SHOW server_encoding;

   -- UTF-8 설정
   SET client_encoding = 'UTF8';
   ```

4. **마이그레이션 충돌**:
   ```bash
   # 마이그레이션 상태 확인
   alembic current
   alembic history

   # 강제 리셋 (개발환경에서만!)
   alembic downgrade base
   alembic upgrade head
   ```

5. **GIN 인덱스 생성 실패**:
   ```sql
   -- PostgreSQL 확장 확인
   SELECT * FROM pg_extension WHERE extname IN ('pg_trgm', 'btree_gin');

   -- 확장 설치
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   CREATE EXTENSION IF NOT EXISTS btree_gin;
   ```

다음 단계에서는 CSV 데이터를 실제로 데이터베이스에 로드하는 배치 스크립트를 작성하겠습니다.