"""
레시피 데이터 파싱 모듈
"""
import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class RecipeData:
    """레시피 데이터 구조"""
    title: str
    description: str = ""
    author: str = ""
    category: str = ""
    difficulty: str = ""
    cooking_time: Optional[int] = None
    servings: Optional[int] = None
    rating: Optional[float] = None
    review_count: int = 0
    ingredients: List[Dict[str, str]] = None
    cooking_steps: List[Dict[str, str]] = None
    tips: List[str] = None
    tags: List[str] = None
    image_url: str = ""
    source_url: str = ""
    
    def __post_init__(self):
        if self.ingredients is None:
            self.ingredients = []
        if self.cooking_steps is None:
            self.cooking_steps = []
        if self.tips is None:
            self.tips = []
        if self.tags is None:
            self.tags = []

class RecipeParser:
    """레시피 데이터 파싱 클래스"""
    
    def __init__(self):
        self.ingredient_aliases = {
            "돼지고기": ["돼지고기", "돼지 고기", "포크", "돼지목살", "돼지등심"],
            "소고기": ["소고기", "소 고기", "비프", "우육", "소등심", "소목살"],
            "닭고기": ["닭고기", "닭 고기", "치킨", "계육", "닭다리", "닭가슴살"],
            "양파": ["양파", "양파1개", "중간양파", "대파", "파"],
            "마늘": ["마늘", "다진마늘", "마늘쫑", "마늘종"],
            "간장": ["간장", "진간장", "조선간장", "왜간장"],
            "고춧가루": ["고춧가루", "고추가루", "굵은고춧가루", "고운고춧가루"],
            "참기름": ["참기름", "깨기름"],
            "식용유": ["식용유", "기름", "올리브오일", "카놀라유"],
            "소금": ["소금", "천일염", "굵은소금"],
            "설탕": ["설탕", "백설탕", "황설탕", "흑설탕"],
            "대파": ["대파", "파", "쪽파", "실파"],
            "생강": ["생강", "다진생강", "생강즙"],
            "후추": ["후추", "흰후추", "검은후추", "후춧가루"]
        }
        
        self.difficulty_map = {
            "아무나": "easy",
            "초급": "easy", 
            "중급": "medium",
            "고급": "hard",
            "쉬움": "easy",
            "보통": "medium", 
            "어려움": "hard"
        }
    
    def parse_recipe_from_json(self, recipe_json: Dict) -> RecipeData:
        """JSON 데이터에서 레시피 정보 파싱"""
        try:
            recipe = RecipeData(
                title=self._clean_text(recipe_json.get("title", "")),
                description=self._clean_text(recipe_json.get("description", "")),
                author=self._clean_text(recipe_json.get("author", "")),
                source_url=recipe_json.get("url", ""),
                image_url=recipe_json.get("image_url", "")
            )
            
            # 카테고리 파싱
            recipe.category = self._parse_category(recipe.title, recipe.description)
            
            # 난이도 파싱
            recipe.difficulty = self._parse_difficulty(recipe_json)
            
            # 조리시간 파싱
            recipe.cooking_time = self._parse_cooking_time(recipe_json)
            
            # 인분 파싱
            recipe.servings = self._parse_servings(recipe_json)
            
            # 재료 파싱
            recipe.ingredients = self._parse_ingredients(recipe_json.get("ingredients", []))
            
            # 조리과정 파싱
            recipe.cooking_steps = self._parse_cooking_steps(recipe_json.get("cookingSteps", []))
            
            # 팁 파싱
            recipe.tips = self._parse_tips(recipe_json.get("tips", []))
            
            # 태그 파싱
            recipe.tags = self._parse_tags(recipe_json.get("tags", []))
            
            return recipe
            
        except Exception as e:
            print(f"레시피 파싱 오류: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        if not text:
            return ""
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # 특수문자 정리
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _parse_category(self, title: str, description: str) -> str:
        """카테고리 자동 분류"""
        title_desc = (title + " " + description).lower()
        
        if any(keyword in title_desc for keyword in ["찌개", "김치찌개", "된장찌개", "부대찌개"]):
            return "stew"
        elif any(keyword in title_desc for keyword in ["볶음", "볶은", "제육볶음", "오징어볶음"]):
            return "stirFry"
        elif any(keyword in title_desc for keyword in ["국", "미역국", "콩나물국", "북어국"]):
            return "soup"
        elif any(keyword in title_desc for keyword in ["밥", "비빔밥", "볶음밥", "덮밥"]):
            return "rice"
        elif any(keyword in title_desc for keyword in ["면", "국수", "냉면", "라면"]):
            return "noodles"
        elif any(keyword in title_desc for keyword in ["김치", "깍두기", "무김치"]):
            return "kimchi"
        elif any(keyword in title_desc for keyword in ["반찬", "나물", "무침", "조림"]):
            return "sideDish"
        else:
            return "other"
    
    def _parse_difficulty(self, recipe_json: Dict) -> str:
        """난이도 파싱"""
        difficulty = recipe_json.get("difficulty", "").strip()
        return self.difficulty_map.get(difficulty, "easy")
    
    def _parse_cooking_time(self, recipe_json: Dict) -> Optional[int]:
        """조리시간 파싱 (분 단위)"""
        cooking_time = recipe_json.get("cookingTime", "")
        if not cooking_time:
            return None
        
        # "20분 이내", "1시간" 등의 형태에서 숫자 추출
        time_match = re.search(r'(\d+)', cooking_time)
        if time_match:
            time_value = int(time_match.group(1))
            if "시간" in cooking_time:
                return time_value * 60
            else:
                return time_value
        
        return None
    
    def _parse_servings(self, recipe_json: Dict) -> Optional[int]:
        """인분 파싱"""
        servings = recipe_json.get("servings", "")
        if not servings:
            return None
        
        # "2인분", "4~6인분" 등에서 숫자 추출
        servings_match = re.search(r'(\d+)', servings)
        if servings_match:
            return int(servings_match.group(1))
        
        return None
    
    def _parse_ingredients(self, ingredients_list: List[Dict]) -> List[Dict[str, str]]:
        """재료 파싱 및 표준화"""
        parsed_ingredients = []
        
        for ingredient in ingredients_list:
            name = ingredient.get("name", "").strip()
            amount = ingredient.get("amount", "").strip()
            
            if not name:
                continue
            
            # 재료명 표준화
            normalized_name = self._normalize_ingredient_name(name)
            
            parsed_ingredients.append({
                "name": normalized_name,
                "amount": amount,
                "original_name": name
            })
        
        return parsed_ingredients
    
    def _normalize_ingredient_name(self, name: str) -> str:
        """재료명 표준화"""
        name = name.lower().strip()
        
        for standard_name, aliases in self.ingredient_aliases.items():
            for alias in aliases:
                if alias.lower() in name.lower():
                    return standard_name
        
        return name
    
    def _parse_cooking_steps(self, steps_list: List[Dict]) -> List[Dict[str, str]]:
        """조리과정 파싱"""
        parsed_steps = []
        
        for i, step in enumerate(steps_list, 1):
            instruction = step.get("instruction", "").strip()
            if instruction:
                parsed_steps.append({
                    "step_number": i,
                    "instruction": self._clean_text(instruction),
                    "image_url": step.get("image_url", "")
                })
        
        return parsed_steps
    
    def _parse_tips(self, tips_list: List[str]) -> List[str]:
        """팁 파싱"""
        return [self._clean_text(tip) for tip in tips_list if tip.strip()]
    
    def _parse_tags(self, tags_list: List[str]) -> List[str]:
        """태그 파싱"""
        parsed_tags = []
        for tag in tags_list:
            if tag.strip():
                # #으로 시작하지 않으면 추가
                clean_tag = tag.strip()
                if not clean_tag.startswith('#'):
                    clean_tag = '#' + clean_tag
                parsed_tags.append(clean_tag)
        
        return parsed_tags
    
    def validate_recipe(self, recipe: RecipeData) -> bool:
        """레시피 데이터 검증"""
        if not recipe:
            return False
        
        # 필수 필드 검증
        if not recipe.title or len(recipe.title.strip()) == 0:
            return False
        
        # 제목 길이 검증
        if len(recipe.title) > 255:
            return False
        
        # 최소 재료 수 검증
        if len(recipe.ingredients) < 1:
            return False
        
        # 최소 조리과정 검증
        if len(recipe.cooking_steps) < 1:
            return False
        
        return True


