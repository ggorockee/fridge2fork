"""
Pydantic 스키마 정의 - Phase 2 데이터베이스 설정
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class RecipeBase(BaseModel):
    """레시피 기본 스키마"""
    rcp_ttl: str = Field(..., max_length=200, description="레시피 제목")
    ckg_nm: Optional[str] = Field(None, max_length=40, description="요리명")
    rgtr_id: Optional[str] = Field(None, max_length=32, description="등록자 ID")
    rgtr_nm: Optional[str] = Field(None, max_length=64, description="등록자명")
    inq_cnt: int = Field(default=0, ge=0, description="조회수")
    rcmm_cnt: int = Field(default=0, ge=0, description="추천수")
    srap_cnt: int = Field(default=0, ge=0, description="스크랩수")
    ckg_mth_acto_nm: Optional[str] = Field(None, max_length=200, description="요리방법별명")
    ckg_sta_acto_nm: Optional[str] = Field(None, max_length=200, description="요리상황별명")
    ckg_mtrl_acto_nm: Optional[str] = Field(None, max_length=200, description="요리재료별명")
    ckg_knd_acto_nm: Optional[str] = Field(None, max_length=200, description="요리종류별명")
    ckg_ipdc: Optional[str] = Field(None, description="요리소개")
    ckg_mtrl_cn: Optional[str] = Field(None, description="원본 재료 내용")
    ckg_inbun_nm: Optional[str] = Field(None, max_length=200, description="인분")
    ckg_dodf_nm: Optional[str] = Field(None, max_length=200, description="난이도")
    ckg_time_nm: Optional[str] = Field(None, max_length=200, description="조리시간")
    first_reg_dt: Optional[str] = Field(None, max_length=14, description="최초등록일시")
    rcp_img_url: Optional[str] = Field(None, description="레시피 이미지 URL")

    @validator('inq_cnt', 'rcmm_cnt', 'srap_cnt')
    def validate_positive_counts(cls, v):
        if v < 0:
            raise ValueError('카운트는 0 이상이어야 합니다')
        return v

    @validator('first_reg_dt')
    def validate_first_reg_dt(cls, v):
        if v and len(v) != 14:
            raise ValueError('날짜 형식은 YYYYMMDDHHMMSS (14자리)여야 합니다')
        return v


class RecipeCreate(RecipeBase):
    """레시피 생성 스키마"""
    rcp_sno: int = Field(..., description="레시피 일련번호")


class RecipeUpdate(BaseModel):
    """레시피 업데이트 스키마"""
    rcp_ttl: Optional[str] = Field(None, max_length=200, description="레시피 제목")
    ckg_nm: Optional[str] = Field(None, max_length=40, description="요리명")
    inq_cnt: Optional[int] = Field(None, ge=0, description="조회수")
    rcmm_cnt: Optional[int] = Field(None, ge=0, description="추천수")
    srap_cnt: Optional[int] = Field(None, ge=0, description="스크랩수")
    ckg_ipdc: Optional[str] = Field(None, description="요리소개")


class Recipe(RecipeBase):
    """레시피 응답 스키마"""
    rcp_sno: int = Field(..., description="레시피 일련번호")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    class Config:
        from_attributes = True


class IngredientBase(BaseModel):
    """재료 기본 스키마"""
    name: str = Field(..., max_length=100, description="정규화된 재료명")
    original_name: Optional[str] = Field(None, max_length=100, description="원본 재료명")
    category: Optional[str] = Field(None, max_length=50, description="재료 카테고리")
    is_common: bool = Field(default=False, description="공통 재료 여부")

    @validator('name')
    def validate_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('재료명은 비어있을 수 없습니다')
        return v.strip()


class IngredientCreate(IngredientBase):
    """재료 생성 스키마"""
    pass


class IngredientUpdate(BaseModel):
    """재료 업데이트 스키마"""
    name: Optional[str] = Field(None, max_length=100, description="정규화된 재료명")
    original_name: Optional[str] = Field(None, max_length=100, description="원본 재료명")
    category: Optional[str] = Field(None, max_length=50, description="재료 카테고리")
    is_common: Optional[bool] = Field(None, description="공통 재료 여부")


class Ingredient(IngredientBase):
    """재료 응답 스키마"""
    id: int = Field(..., description="재료 ID")
    created_at: datetime = Field(..., description="생성일시")

    class Config:
        from_attributes = True


class RecipeIngredientBase(BaseModel):
    """레시피-재료 연결 기본 스키마"""
    quantity_text: Optional[str] = Field(None, description="원본 수량 표현")
    quantity_from: Optional[float] = Field(None, ge=0, description="파싱된 수량 시작값")
    quantity_to: Optional[float] = Field(None, ge=0, description="파싱된 수량 끝값")
    unit: Optional[str] = Field(None, max_length=20, description="단위")
    is_vague: bool = Field(default=False, description="모호한 수량 여부")
    display_order: int = Field(default=0, ge=0, description="표시 순서")
    importance: Literal['essential', 'normal', 'optional', 'garnish'] = Field(
        default='normal',
        description="중요도"
    )

    @validator('quantity_to')
    def validate_quantity_range(cls, v, values):
        if v is not None and 'quantity_from' in values and values['quantity_from'] is not None:
            if v < values['quantity_from']:
                raise ValueError('끝값은 시작값보다 크거나 같아야 합니다')
        return v

    @validator('quantity_from', 'quantity_to')
    def validate_positive_quantity(cls, v):
        if v is not None and v < 0:
            raise ValueError('수량은 0 이상이어야 합니다')
        return v


class RecipeIngredientCreate(RecipeIngredientBase):
    """레시피-재료 연결 생성 스키마"""
    rcp_sno: int = Field(..., description="레시피 일련번호")
    ingredient_id: int = Field(..., description="재료 ID")


class RecipeIngredientUpdate(BaseModel):
    """레시피-재료 연결 업데이트 스키마"""
    quantity_text: Optional[str] = Field(None, description="원본 수량 표현")
    quantity_from: Optional[float] = Field(None, ge=0, description="파싱된 수량 시작값")
    quantity_to: Optional[float] = Field(None, ge=0, description="파싱된 수량 끝값")
    unit: Optional[str] = Field(None, max_length=20, description="단위")
    is_vague: Optional[bool] = Field(None, description="모호한 수량 여부")
    display_order: Optional[int] = Field(None, ge=0, description="표시 순서")
    importance: Optional[Literal['essential', 'normal', 'optional', 'garnish']] = Field(
        None,
        description="중요도"
    )


class RecipeIngredient(RecipeIngredientBase):
    """레시피-재료 연결 응답 스키마"""
    id: int = Field(..., description="연결 ID")
    rcp_sno: int = Field(..., description="레시피 일련번호")
    ingredient_id: int = Field(..., description="재료 ID")

    # 연관 객체 (선택적)
    ingredient: Optional[Ingredient] = None

    class Config:
        from_attributes = True


class RecipeWithIngredients(Recipe):
    """재료 정보를 포함한 레시피 스키마"""
    recipe_ingredients: List[RecipeIngredient] = Field(default=[], description="레시피 재료들")

    class Config:
        from_attributes = True


# 검색 및 필터링을 위한 스키마
class RecipeSearchFilter(BaseModel):
    """레시피 검색 필터"""
    title: Optional[str] = Field(None, description="제목 검색")
    category: Optional[str] = Field(None, description="카테고리")
    difficulty: Optional[str] = Field(None, description="난이도")
    cooking_time: Optional[str] = Field(None, description="조리시간")
    cooking_method: Optional[str] = Field(None, description="조리방법")
    ingredients: Optional[List[str]] = Field(None, description="재료 목록")
    min_views: Optional[int] = Field(None, ge=0, description="최소 조회수")


class IngredientSearchFilter(BaseModel):
    """재료 검색 필터"""
    name: Optional[str] = Field(None, description="재료명 검색")
    category: Optional[str] = Field(None, description="카테고리")
    is_common: Optional[bool] = Field(None, description="공통 재료 여부")


# 통계를 위한 스키마
class DatabaseStats(BaseModel):
    """데이터베이스 통계"""
    total_recipes: int = Field(..., description="총 레시피 수")
    total_ingredients: int = Field(..., description="총 재료 수")
    total_relations: int = Field(..., description="총 연결 수")
    avg_ingredients_per_recipe: float = Field(..., description="레시피당 평균 재료 수")


class CategoryStats(BaseModel):
    """카테고리별 통계"""
    category: str = Field(..., description="카테고리명")
    ingredient_count: int = Field(..., description="재료 수")
    recipe_count: int = Field(..., description="사용 레시피 수")


class PopularIngredient(BaseModel):
    """인기 재료"""
    name: str = Field(..., description="재료명")
    category: Optional[str] = Field(None, description="카테고리")
    usage_count: int = Field(..., description="사용 횟수")
    essential_count: int = Field(..., description="필수 재료로 사용된 횟수")