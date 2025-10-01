#!/usr/bin/env python3
"""
Phase 1 마이그레이션 검증 스크립트
005_add_approval_workflow.py 마이그레이션 검증

이 스크립트는 마이그레이션을 실제로 실행하지 않고 Python 문법과 import만 검증합니다.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def verify_models():
    """모델 파일 import 검증"""
    print("🔍 모델 파일 검증 중...")

    try:
        # Admin models
        from app.models.admin import (
            IngredientCategory,
            SystemConfig,
            ImportBatch,
            PendingRecipe,
            PendingIngredient
        )
        print("✅ Admin 모델 import 성공")

        # Recipe models with new columns
        from app.models.recipe import (
            Recipe,
            Ingredient,
            RecipeIngredient,
            UserFridgeSession
        )
        print("✅ Recipe 모델 import 성공")

        # Check model attributes
        assert hasattr(Recipe, 'approval_status'), "Recipe.approval_status 컬럼 누락"
        assert hasattr(Recipe, 'import_batch_id'), "Recipe.import_batch_id 컬럼 누락"
        assert hasattr(Ingredient, 'category_id'), "Ingredient.category_id 컬럼 누락"
        assert hasattr(Ingredient, 'approval_status'), "Ingredient.approval_status 컬럼 누락"
        assert hasattr(RecipeIngredient, 'category_id'), "RecipeIngredient.category_id 컬럼 누락"
        assert hasattr(RecipeIngredient, 'raw_quantity_text'), "RecipeIngredient.raw_quantity_text 컬럼 누락"
        assert hasattr(UserFridgeSession, 'session_duration_hours'), "UserFridgeSession.session_duration_hours 컬럼 누락"
        assert hasattr(UserFridgeSession, 'session_type'), "UserFridgeSession.session_type 컬럼 누락"
        print("✅ 모델 컬럼 검증 성공")

        # Check PendingIngredient special columns
        assert hasattr(PendingIngredient, 'quantity_from'), "PendingIngredient.quantity_from 컬럼 누락"
        assert hasattr(PendingIngredient, 'quantity_to'), "PendingIngredient.quantity_to 컬럼 누락"
        assert hasattr(PendingIngredient, 'quantity_unit'), "PendingIngredient.quantity_unit 컬럼 누락"
        assert hasattr(PendingIngredient, 'is_vague'), "PendingIngredient.is_vague 컬럼 누락"
        assert hasattr(PendingIngredient, 'is_abstract'), "PendingIngredient.is_abstract 컬럼 누락"
        assert hasattr(PendingIngredient, 'suggested_specific'), "PendingIngredient.suggested_specific 컬럼 누락"
        assert hasattr(PendingIngredient, 'abstraction_notes'), "PendingIngredient.abstraction_notes 컬럼 누락"
        print("✅ PendingIngredient 수량/추상화 컬럼 검증 성공")

        return True

    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        return False
    except AssertionError as e:
        print(f"❌ 모델 검증 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 예기치 않은 오류: {e}")
        return False


def verify_migration_file():
    """마이그레이션 파일 문법 검증"""
    print("\n🔍 마이그레이션 파일 검증 중...")

    migration_file = "migrations/versions/005_add_approval_workflow.py"

    if not os.path.exists(migration_file):
        print(f"❌ 마이그레이션 파일이 없습니다: {migration_file}")
        return False

    print(f"✅ 마이그레이션 파일 발견: {migration_file}")

    # Python 문법 검증 (compile)
    try:
        with open(migration_file, 'r') as f:
            code = f.read()
            compile(code, migration_file, 'exec')
        print("✅ 마이그레이션 파일 문법 검증 성공")
        return True
    except SyntaxError as e:
        print(f"❌ 문법 오류: {e}")
        return False


def verify_schema_consistency():
    """스키마 일관성 검증"""
    print("\n🔍 스키마 일관성 검증 중...")

    try:
        from app.models.admin import IngredientCategory, PendingIngredient
        from app.models.recipe import Ingredient

        # PendingIngredient와 Ingredient의 관계 확인
        assert hasattr(PendingIngredient, 'suggested_category'), "PendingIngredient.suggested_category relationship 누락"
        assert hasattr(Ingredient, 'ingredient_category'), "Ingredient.ingredient_category relationship 누락"

        print("✅ 모델 관계 검증 성공")
        return True

    except AssertionError as e:
        print(f"❌ 스키마 일관성 검증 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 예기치 않은 오류: {e}")
        return False


def main():
    """검증 메인 함수"""
    print("=" * 70)
    print("📋 Phase 1 마이그레이션 검증 (005_add_approval_workflow)")
    print("=" * 70)

    results = []

    # 1. 모델 검증
    results.append(("모델 Import 및 컬럼", verify_models()))

    # 2. 마이그레이션 파일 검증
    results.append(("마이그레이션 파일 문법", verify_migration_file()))

    # 3. 스키마 일관성 검증
    results.append(("스키마 일관성", verify_schema_consistency()))

    # 결과 출력
    print("\n" + "=" * 70)
    print("📊 검증 결과 요약")
    print("=" * 70)

    all_passed = True
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{status} | {test_name}")
        if not result:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n🎉 모든 검증 통과!")
        print("\n📋 다음 단계:")
        print("1. Dry-run SQL 미리보기:")
        print("   alembic upgrade head --sql > migration_preview.sql")
        print("\n2. 실제 마이그레이션 실행:")
        print("   python scripts/migrate.py")
        print("\n3. 데이터베이스 확인:")
        print("   psql -d fridge2fork -c '\\dt' (테이블 목록)")
        return True
    else:
        print("\n❌ 일부 검증 실패")
        print("위 오류를 수정한 후 다시 시도하세요.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
