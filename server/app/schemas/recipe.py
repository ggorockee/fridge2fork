"""
레시피 관련 Pydantic 스키마 (scrape 마이그레이션 스키마 기반)
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class IngredientInfo(BaseModel):
    """레시피에 포함된 재료 정보"""
    name: str
    category: Optional[str] = None
    quantity_text: Optional[str] = None
    quantity_from: Optional[float] = None
    quantity_to: Optional[float] = None
    unit: Optional[str] = None
    importance: str = "normal"
    is_vague: bool = False
    display_order: int = 0


class Ingredient(BaseModel):
    """재료 마스터 모델"""
    id: int
    name: str
    original_name: Optional[str] = None
    category: Optional[str] = None
    is_common: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class RecipeBase(BaseModel):
    """레시피 기본 정보"""
    rcp_ttl: str  # 레시피 제목
    ckg_nm: Optional[str] = None  # 요리명
    ckg_ipdc: Optional[str] = None  # 요리소개
    ckg_mtrl_cn: Optional[str] = None  # 요리재료내용
    ckg_knd_acto_nm: Optional[str] = None  # 요리종류
    ckg_time_nm: Optional[str] = None  # 요리시간
    ckg_dodf_nm: Optional[str] = None  # 요리난이도
    ckg_mth_acto_nm: Optional[str] = None  # 조리방법
    ckg_inbun_nm: Optional[str] = None  # 요리인분
    rcp_img_url: Optional[str] = None  # 레시피 이미지
    ingredients: List[IngredientInfo] = []


class Recipe(RecipeBase):
    """레시피 상세 정보"""
    rcp_sno: int  # 레시피 일련번호
    rgtr_id: Optional[str] = None  # 등록자 ID
    rgtr_nm: Optional[str] = None  # 등록자 이름
    inq_cnt: int = 0  # 조회수
    rcmm_cnt: int = 0  # 추천수
    srap_cnt: int = 0  # 스크랩수
    first_reg_dt: Optional[str] = None  # 최초등록일시
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecipeList(BaseModel):
    """레시피 목록 아이템"""
    rcp_sno: int
    rcp_ttl: str
    ckg_nm: Optional[str] = None
    ckg_ipdc: Optional[str] = None
    ckg_knd_acto_nm: Optional[str] = None
    ckg_time_nm: Optional[str] = None
    ckg_dodf_nm: Optional[str] = None
    rcp_img_url: Optional[str] = None
    inq_cnt: int = 0
    rcmm_cnt: int = 0
    ingredients_count: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecipeListResponse(BaseModel):
    """레시피 목록 응답"""
    recipes: List[RecipeList]
    pagination: Dict[str, Any]
    matching_rates: Optional[Dict[str, float]] = None


class CategoryInfo(BaseModel):
    """카테고리 정보"""
    name: str
    count: int


class CategoriesResponse(BaseModel):
    """카테고리 목록 응답"""
    categories: Dict[str, int]


class RecipeStatsResponse(BaseModel):
    """레시피 통계 응답"""
    total_recipes: int
    total_ingredients: int
    average_ingredients_per_recipe: float
    categories: Dict[str, int]
    last_updated: Optional[str] = None


class PopularRecipesResponse(BaseModel):
    """인기 레시피 응답"""
    recipes: List[RecipeList]


class RelatedRecipesResponse(BaseModel):
    """관련 레시피 응답"""
    recipes: List[RecipeList]
