"""
Supabase 데이터베이스 저장 모듈
"""
import asyncio
import uuid
from typing import List, Dict, Optional
from datetime import datetime

from .parser import RecipeData
from .config import CrawlingConfig

class SupabaseRecipeStorage:
    """Supabase 레시피 저장 클래스"""
    
    def __init__(self):
        self.config = CrawlingConfig()
        self.ingredient_cache = {}  # 재료 ID 캐시
        
    async def save_recipe_batch(self, recipes: List[RecipeData]) -> Dict[str, int]:
        """레시피 배치 저장"""
        results = {
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        for recipe in recipes:
            try:
                if not recipe or not self._validate_recipe(recipe):
                    results["skipped"] += 1
                    continue
                
                # 중복 체크
                if await self._is_duplicate_recipe(recipe.title):
                    results["skipped"] += 1
                    continue
                
                # 레시피 저장
                recipe_id = await self._save_recipe(recipe)
                if recipe_id:
                    # 재료 저장
                    await self._save_recipe_ingredients(recipe_id, recipe.ingredients)
                    
                    # 조리과정 저장
                    await self._save_cooking_steps(recipe_id, recipe.cooking_steps)
                    
                    results["success"] += 1
                    print(f"✅ 저장 완료: {recipe.title}")
                else:
                    results["failed"] += 1
                    print(f"❌ 저장 실패: {recipe.title}")
                    
            except Exception as e:
                results["failed"] += 1
                print(f"❌ 저장 오류: {recipe.title if recipe else 'Unknown'} - {e}")
        
        return results
    
    async def _save_recipe(self, recipe: RecipeData) -> Optional[str]:
        """레시피 기본 정보 저장"""
        try:
            recipe_data = {
                "name": recipe.title,
                "description": recipe.description,
                "author": recipe.author,
                "category": recipe.category,
                "difficulty": recipe.difficulty,
                "cooking_time_minutes": recipe.cooking_time,
                "servings": recipe.servings,
                "rating": recipe.rating,
                "review_count": recipe.review_count,
                "is_popular": recipe.review_count > 100 if recipe.review_count else False,
                "image_url": recipe.image_url,
                "source_url": recipe.source_url,
                "tags": recipe.tags,
                "tips": recipe.tips,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Supabase MCP 클라이언트 사용
            from .supabase_client import supabase_client
            
            query = f"""
            INSERT INTO recipes (name, description, author, category, difficulty, 
                               cooking_time_minutes, servings, rating, review_count, 
                               is_popular, image_url, source_url, tags, tips)
            VALUES ('{recipe.title.replace("'", "''")}', 
                    '{recipe.description.replace("'", "''")}',
                    '{recipe.author.replace("'", "''")}',
                    '{recipe.category}',
                    '{recipe.difficulty}',
                    {recipe.cooking_time if recipe.cooking_time else 'NULL'},
                    {recipe.servings if recipe.servings else 'NULL'},
                    {recipe.rating if recipe.rating else 'NULL'},
                    {recipe.review_count},
                    {str(recipe.review_count > 100).lower()},
                    '{recipe.image_url}',
                    '{recipe.source_url}',
                    ARRAY{recipe.tags},
                    ARRAY{recipe.tips})
            RETURNING id;
            """
            
            result = supabase_client.execute_sql(query)
            
            if result and len(result) > 0:
                return result[0].get('id')
            
            return None
            
        except Exception as e:
            print(f"레시피 저장 오류: {e}")
            return None
    
    async def _save_recipe_ingredients(self, recipe_id: str, ingredients: List[Dict]) -> bool:
        """레시피 재료 저장"""
        try:
            for ingredient_data in ingredients:
                ingredient_name = ingredient_data.get("name", "").strip()
                if not ingredient_name:
                    continue
                
                # 재료 ID 가져오기 또는 생성
                ingredient_id = await self._get_or_create_ingredient(ingredient_name)
                if not ingredient_id:
                    continue
                
                # 레시피-재료 관계 저장
                amount = ingredient_data.get("amount", "").replace("'", "''")
                
                from .supabase_client import supabase_client
                supabase_client.execute_sql(
                    f"""
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_id, amount, is_essential)
                    VALUES ('{recipe_id}', '{ingredient_id}', '{amount}', true);
                    """
                )
            
            return True
            
        except Exception as e:
            print(f"재료 저장 오류: {e}")
            return False
    
    async def _get_or_create_ingredient(self, ingredient_name: str) -> Optional[str]:
        """재료 ID 가져오기 또는 생성"""
        try:
            # 캐시에서 확인
            if ingredient_name in self.ingredient_cache:
                return self.ingredient_cache[ingredient_name]
            
            # 기존 재료 확인
            from .supabase_client import supabase_client
            
            clean_name = ingredient_name.replace("'", "''")
            result = supabase_client.execute_sql(
                f"SELECT id FROM ingredients WHERE name = '{clean_name}' LIMIT 1;"
            )
            
            if result and len(result) > 0:
                ingredient_id = result[0].get('id')
                self.ingredient_cache[ingredient_name] = ingredient_id
                return ingredient_id
            
            # 새 재료 생성
            category = self._categorize_ingredient(ingredient_name)
            result = supabase_client.execute_sql(
                f"""
                INSERT INTO ingredients (name, category)
                VALUES ('{clean_name}', '{category}')
                RETURNING id;
                """
            )
            
            if result and len(result) > 0:
                ingredient_id = result[0].get('id')
                self.ingredient_cache[ingredient_name] = ingredient_id
                return ingredient_id
            
            return None
            
        except Exception as e:
            print(f"재료 처리 오류: {e}")
            return None
    
    def _categorize_ingredient(self, ingredient_name: str) -> str:
        """재료 카테고리 자동 분류"""
        name_lower = ingredient_name.lower()
        
        # 육류
        if any(meat in name_lower for meat in ["고기", "소고기", "돼지고기", "닭고기", "오리", "양고기"]):
            return "meat"
        
        # 해산물
        elif any(seafood in name_lower for seafood in ["생선", "새우", "오징어", "조개", "게", "멸치", "북어", "명태"]):
            return "seafood"
        
        # 채소
        elif any(vegetable in name_lower for vegetable in ["배추", "무", "당근", "양파", "마늘", "생강", "파", "고추", "버섯", "콩나물", "시금치"]):
            return "vegetable"
        
        # 양념/소스
        elif any(seasoning in name_lower for seasoning in ["간장", "된장", "고추장", "소금", "설탕", "식초", "기름", "참기름", "깨소금", "후추"]):
            return "seasoning"
        
        # 곡물/면류
        elif any(grain in name_lower for grain in ["쌀", "밥", "면", "국수", "라면", "떡", "밀가루"]):
            return "grain"
        
        # 유제품
        elif any(dairy in name_lower for dairy in ["우유", "치즈", "버터", "요거트", "크림"]):
            return "dairy"
        
        else:
            return "other"
    
    async def _save_cooking_steps(self, recipe_id: str, cooking_steps: List[Dict]) -> bool:
        """조리과정 저장"""
        try:
            for step_data in cooking_steps:
                step_number = step_data.get("step_number", 1)
                instruction = step_data.get("instruction", "").replace("'", "''")
                image_url = step_data.get("image_url", "")
                
                if not instruction.strip():
                    continue
                
                from .supabase_client import supabase_client
                supabase_client.execute_sql(
                    f"""
                    INSERT INTO cooking_steps (recipe_id, step_number, instruction, image_url)
                    VALUES ('{recipe_id}', {step_number}, '{instruction}', '{image_url}');
                    """
                )
            
            return True
            
        except Exception as e:
            print(f"조리과정 저장 오류: {e}")
            return False
    
    async def _is_duplicate_recipe(self, title: str) -> bool:
        """중복 레시피 확인"""
        try:
            from .supabase_client import supabase_client
            clean_title = title.replace("'", "''")
            result = supabase_client.execute_sql(
                f"SELECT id FROM recipes WHERE name = '{clean_title}' LIMIT 1;"
            )
            return result and len(result) > 0
        except:
            return False
    
    def _validate_recipe(self, recipe: RecipeData) -> bool:
        """레시피 데이터 검증"""
        if not recipe or not recipe.title:
            return False
        
        if len(recipe.title) > 255:
            return False
        
        if len(recipe.ingredients) < 1:
            return False
        
        if len(recipe.cooking_steps) < 1:
            return False
        
        return True
    
    async def get_crawling_stats(self) -> Dict[str, int]:
        """크롤링 통계 조회"""
        try:
            from .supabase_client import supabase_client
            
            # 총 레시피 수
            total_result = supabase_client.execute_sql("SELECT COUNT(*) as count FROM recipes;")
            total_recipes = total_result[0].get('count', 0) if total_result else 0
            
            # 총 재료 수
            ingredients_result = supabase_client.execute_sql("SELECT COUNT(*) as count FROM ingredients;")
            total_ingredients = ingredients_result[0].get('count', 0) if ingredients_result else 0
            
            # 카테고리별 레시피 수
            category_result = supabase_client.execute_sql(
                "SELECT category, COUNT(*) as count FROM recipes GROUP BY category;"
            )
            
            category_stats = {}
            if category_result:
                for row in category_result:
                    category_stats[row.get('category', 'unknown')] = row.get('count', 0)
            
            return {
                "total_recipes": total_recipes,
                "total_ingredients": total_ingredients,
                "category_breakdown": category_stats
            }
            
        except Exception as e:
            print(f"통계 조회 오류: {e}")
            return {}

# 전역 인스턴스
recipe_storage = SupabaseRecipeStorage()
