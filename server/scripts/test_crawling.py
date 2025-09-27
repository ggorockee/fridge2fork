#!/usr/bin/env python3
"""
간단한 크롤링 테스트 스크립트
"""
import asyncio
import json
from datetime import datetime

# 이미 크롤링된 레시피 데이터를 사용해서 Supabase에 저장 테스트
def test_save_to_supabase():
    """기존 recipe_data.json을 Supabase에 저장"""
    print("🧪 Supabase 저장 테스트 시작...")
    
    try:
        # 기존 크롤링된 데이터 로드
        with open('recipe_data.json', 'r', encoding='utf-8') as f:
            recipe_data = json.load(f)
        
        print(f"📄 로드된 레시피: {recipe_data.get('title', 'Unknown')}")
        
        # 레시피 기본 정보 저장 쿼리
        recipe_insert_query = f"""
        INSERT INTO recipes (name, description, author, category, difficulty, 
                           cooking_time_minutes, servings, tags, tips, source_url)
        VALUES (
            '{recipe_data.get('title', '').replace("'", "''")}',
            '{recipe_data.get('description', '').replace("'", "''")}',
            '{recipe_data.get('author', '').replace("'", "''")}',
            'other',
            'easy',
            20,
            2,
            ARRAY{recipe_data.get('tags', [])},
            ARRAY{recipe_data.get('tips', [])},
            '{recipe_data.get('url', '')}'
        )
        RETURNING id;
        """
        
        print("💾 레시피 저장 중...")
        print(f"쿼리: {recipe_insert_query[:200]}...")
        
        # 여기서 실제로는 MCP Supabase 함수를 호출해야 하지만
        # 테스트를 위해 쿼리만 출력
        print("✅ 레시피 저장 쿼리 준비 완료")
        
        # 재료 저장
        ingredients = recipe_data.get('ingredients', [])
        print(f"🥬 재료 {len(ingredients)}개 저장 준비...")
        
        for i, ingredient in enumerate(ingredients):
            ingredient_name = ingredient.get('name', '').replace("'", "''")
            ingredient_amount = ingredient.get('amount', '').replace("'", "''")
            
            print(f"  - {ingredient_name}: {ingredient_amount}")
            
            if i >= 5:  # 처음 5개만 출력
                print(f"  ... 및 {len(ingredients) - 5}개 더")
                break
        
        # 조리과정 저장
        cooking_steps = recipe_data.get('cookingSteps', [])
        print(f"👩‍🍳 조리과정 {len(cooking_steps)}개 저장 준비...")
        
        for i, step in enumerate(cooking_steps):
            step_instruction = step.get('instruction', '')[:50]
            print(f"  {i+1}. {step_instruction}...")
            
        print("🎉 테스트 완료! 실제 저장을 위해서는 MCP Supabase 연동 필요")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        return False

def test_simple_crawling():
    """간단한 크롤링 테스트"""
    print("🚀 간단한 크롤링 테스트...")
    
    # 10개의 샘플 레시피 URL (실제로는 크롤링해서 수집)
    sample_urls = [
        "https://www.10000recipe.com/recipe/6842069",
        "https://www.10000recipe.com/recipe/6842070", 
        "https://www.10000recipe.com/recipe/6842071",
        "https://www.10000recipe.com/recipe/6842072",
        "https://www.10000recipe.com/recipe/6842073"
    ]
    
    print(f"📋 테스트 URL {len(sample_urls)}개:")
    for i, url in enumerate(sample_urls, 1):
        print(f"  {i}. {url}")
    
    print("✅ URL 수집 시뮬레이션 완료")
    
    # 각 URL에 대해 데이터 추출 시뮬레이션
    extracted_recipes = []
    
    for i, url in enumerate(sample_urls, 1):
        print(f"🔍 레시피 {i} 추출 중...")
        
        # 실제로는 여기서 MCP Playwright로 페이지 접속 및 데이터 추출
        sample_recipe = {
            "title": f"테스트 레시피 {i}",
            "description": f"테스트용 레시피 {i} 설명",
            "author": "테스트 작성자",
            "difficulty": "easy",
            "cookingTime": "20분",
            "servings": "2인분",
            "ingredients": [
                {"name": "양파", "amount": "1개"},
                {"name": "마늘", "amount": "2쪽"},
                {"name": "간장", "amount": "2큰술"}
            ],
            "cookingSteps": [
                {"stepNumber": 1, "instruction": "양파를 썰어줍니다."},
                {"stepNumber": 2, "instruction": "마늘을 다져줍니다."},
                {"stepNumber": 3, "instruction": "간장과 함께 볶아줍니다."}
            ],
            "tags": ["#간단요리", "#집밥"],
            "url": url
        }
        
        extracted_recipes.append(sample_recipe)
        print(f"  ✅ '{sample_recipe['title']}' 추출 완료")
    
    print(f"🎉 총 {len(extracted_recipes)}개 레시피 추출 완료!")
    
    return extracted_recipes

async def main():
    """메인 테스트 함수"""
    print("🍳 Fridge2Fork 크롤링 테스트")
    print("=" * 50)
    
    # 1. 기존 데이터 저장 테스트
    print("\n1️⃣ 기존 레시피 데이터 저장 테스트")
    test_save_to_supabase()
    
    print("\n" + "="*50)
    
    # 2. 크롤링 시뮬레이션 테스트
    print("\n2️⃣ 크롤링 시뮬레이션 테스트")
    recipes = test_simple_crawling()
    
    print("\n" + "="*50)
    print("✅ 모든 테스트 완료!")
    print(f"📊 처리된 레시피: {len(recipes)}개")
    
    print("\n🚀 다음 단계:")
    print("1. MCP Playwright 브라우저 연동")
    print("2. 실제 레시피 페이지 크롤링")
    print("3. Supabase 데이터 저장")
    print("4. 10,000개 레시피 대량 크롤링")

if __name__ == "__main__":
    asyncio.run(main())

