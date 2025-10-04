#!/usr/bin/env python3
"""
Phase 1 구현 테스트 스크립트 (DB 연결 없이 실행 가능)

사용법:
    python scripts/test_phase1.py

테스트 항목:
- SQLAlchemy 모델 로딩
- 재료 파싱 시스템 테스트
- CSV 파일 구조 분석
- 환경변수 설정 확인
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_models_import():
    """SQLAlchemy 모델 import 테스트"""
    print("🧪 SQLAlchemy 모델 import 테스트")
    try:
        from app.models.recipe import Recipe, Ingredient, RecipeIngredient
        print("  ✅ Recipe 모델 로딩 성공")
        print("  ✅ Ingredient 모델 로딩 성공")
        print("  ✅ RecipeIngredient 모델 로딩 성공")

        # 모델 필드 확인
        recipe_fields = len([attr for attr in dir(Recipe) if not attr.startswith('_')])
        ingredient_fields = len([attr for attr in dir(Ingredient) if not attr.startswith('_')])
        relation_fields = len([attr for attr in dir(RecipeIngredient) if not attr.startswith('_')])

        print(f"  📊 Recipe 필드/메서드: {recipe_fields}개")
        print(f"  📊 Ingredient 필드/메서드: {ingredient_fields}개")
        print(f"  📊 RecipeIngredient 필드/메서드: {relation_fields}개")
        return True
    except Exception as e:
        print(f"  ❌ 모델 import 실패: {e}")
        return False

def test_ingredient_parser():
    """재료 파싱 시스템 테스트"""
    print("\n🧪 재료 파싱 시스템 테스트")
    try:
        from app.utils.ingredient_parser import IngredientParser, parse_ingredients_list

        parser = IngredientParser()
        print("  ✅ IngredientParser 클래스 로딩 성공")

        # 테스트 재료들
        test_ingredients = [
            "어묵 2개",
            "양파 1/2개",
            "간장 1T",
            "올리브유 적당량",
            "물 1~2컵"
        ]

        print("  🧪 개별 재료 파싱 테스트:")
        for ingredient_text in test_ingredients:
            parsed = parser.parse(ingredient_text)
            if parsed:
                print(f"    '{ingredient_text}' → {parsed.normalized_name}")
                if parsed.quantity_from:
                    quantity_str = f"{parsed.quantity_from}"
                    if parsed.quantity_to:
                        quantity_str += f"~{parsed.quantity_to}"
                    if parsed.unit:
                        quantity_str += f" {parsed.unit}"
                    print(f"      수량: {quantity_str}")
                if parsed.is_vague:
                    print(f"      모호한 표현: {parsed.vague_description}")

        # 재료 목록 파싱 테스트
        ingredients_text = "[재료] 어묵 2개| 김밥용김 3장| 당면 1움큼| 양파 1/2개| 올리브유 적당량"
        parsed_list = parse_ingredients_list(ingredients_text)
        print(f"  🧪 재료 목록 파싱: {len(parsed_list)}개 재료 인식")

        return True
    except Exception as e:
        print(f"  ❌ 재료 파싱 테스트 실패: {e}")
        return False

def test_csv_files():
    """CSV 파일 존재 확인"""
    print("\n🧪 CSV 파일 존재 확인")

    datas_dir = project_root / "datas"
    print(f"  📁 데이터 디렉토리: {datas_dir}")

    if not datas_dir.exists():
        print("  ❌ datas 디렉토리가 존재하지 않습니다")
        return False

    csv_files = list(datas_dir.glob("*.csv"))
    print(f"  📊 발견된 CSV 파일: {len(csv_files)}개")

    for csv_file in csv_files[:3]:  # 최대 3개만 표시
        size_mb = csv_file.stat().st_size / 1024 / 1024
        print(f"    - {csv_file.name} ({size_mb:.1f}MB)")

    if len(csv_files) > 3:
        print(f"    ... 및 {len(csv_files) - 3}개 더")

    return len(csv_files) > 0

def test_environment():
    """환경설정 확인"""
    print("\n🧪 환경설정 확인")

    import os

    # 중요한 환경변수들 확인
    env_vars = [
        'POSTGRES_SERVER', 'POSTGRES_PORT', 'POSTGRES_DB',
        'POSTGRES_USER', 'POSTGRES_PASSWORD', 'DATABASE_URL'
    ]

    set_vars = []
    unset_vars = []

    for var in env_vars:
        if os.getenv(var):
            set_vars.append(var)
        else:
            unset_vars.append(var)

    print(f"  ✅ 설정된 환경변수: {len(set_vars)}개")
    for var in set_vars:
        if 'PASSWORD' in var:
            print(f"    - {var}=***")
        else:
            print(f"    - {var}={os.getenv(var)}")

    if unset_vars:
        print(f"  ⚠️  미설정 환경변수: {len(unset_vars)}개")
        for var in unset_vars:
            print(f"    - {var}")

    # DATABASE_URL 자동 구성 테스트
    try:
        from migrations.env import get_database_url
        db_url = get_database_url()
        if db_url:
            # 패스워드 마스킹
            masked_url = db_url
            if '@' in masked_url:
                parts = masked_url.split('@')
                if ':' in parts[0]:
                    user_pass = parts[0].split(':')
                    if len(user_pass) >= 3:  # postgresql://user:pass
                        user_pass[-1] = '***'
                        parts[0] = ':'.join(user_pass)
                masked_url = '@'.join(parts)
            print(f"  ✅ DATABASE_URL 구성 가능: {masked_url}")
        else:
            print(f"  ❌ DATABASE_URL 구성 불가")
    except Exception as e:
        print(f"  ❌ DATABASE_URL 테스트 실패: {e}")

    return len(set_vars) > 0

def test_main_cli():
    """main.py CLI 테스트"""
    print("\n🧪 main.py CLI 테스트")

    try:
        # 환경변수를 help로 설정하고 main import
        import os
        original_mode = os.getenv('MODE')
        os.environ['MODE'] = 'help'

        from main import print_usage
        print("  ✅ main.py import 성공")
        print("  ✅ print_usage 함수 로딩 성공")

        # 원래 MODE 복구
        if original_mode:
            os.environ['MODE'] = original_mode
        elif 'MODE' in os.environ:
            del os.environ['MODE']

        return True
    except Exception as e:
        print(f"  ❌ main.py 테스트 실패: {e}")
        return False

def main():
    """Phase 1 테스트 실행"""
    print("🚀 Phase 1 구현 테스트 시작")
    print("=" * 60)

    tests = [
        ("모델 import", test_models_import),
        ("재료 파싱", test_ingredient_parser),
        ("CSV 파일", test_csv_files),
        ("환경설정", test_environment),
        ("Main CLI", test_main_cli)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 예상치 못한 오류: {e}")
            results.append((test_name, False))

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 Phase 1 테스트 결과")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "✅ 통과" if success else "❌ 실패"
        print(f"{test_name:15s}: {status}")
        if success:
            passed += 1

    print(f"\n총 테스트: {total}개 / 통과: {passed}개 / 실패: {total - passed}개")

    if passed == total:
        print("🎉 모든 Phase 1 구성요소가 정상 동작합니다!")
        print("\n📋 다음 단계:")
        print("1. PostgreSQL 데이터베이스 구성")
        print("2. alembic upgrade head 실행")
        print("3. MODE=migrate python main.py 실행")
        return 0
    else:
        print("⚠️  일부 구성요소에 문제가 있습니다. 위 오류를 확인하세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main())