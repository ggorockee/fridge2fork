#!/usr/bin/env python3
"""
중복 방지 시스템 테스트
"""
import asyncio
import sys
sys.path.append('.')

from scripts.crawling.database import recipe_storage

async def test_duplicate_prevention():
    """중복 방지 테스트"""
    print("🧪 중복 방지 시스템 테스트 시작")
    
    # 기존 레시피 제목 확인
    existing_recipe = "145.우무묵콩국수(ft.다이어트)"
    
    # 중복 확인 테스트
    is_duplicate = await recipe_storage._is_duplicate_recipe(existing_recipe)
    
    print(f"📊 테스트 결과:")
    print(f"  • 기존 레시피: '{existing_recipe}'")
    print(f"  • 중복 확인 결과: {'중복됨' if is_duplicate else '중복 아님'}")
    
    if is_duplicate:
        print("✅ 중복 방지 시스템 정상 작동!")
        print("  → 같은 제목의 레시피는 건너뛰게 됩니다.")
    else:
        print("❌ 중복 방지 시스템 오류")
    
    # 새 레시피 제목 테스트
    new_recipe = "테스트 레시피 12345"
    is_new_duplicate = await recipe_storage._is_duplicate_recipe(new_recipe)
    
    print(f"\n  • 새 레시피: '{new_recipe}'")
    print(f"  • 중복 확인 결과: {'중복됨' if is_new_duplicate else '중복 아님'}")
    
    if not is_new_duplicate:
        print("✅ 새 레시피는 중복이 아님 - 정상!")
    
    print("\n🎉 중복 방지 시스템 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_duplicate_prevention())

