"""
SQLAdmin View 클래스들
관리자 UI를 통한 데이터 관리
"""
from typing import Any
from sqladmin import ModelView
from sqlalchemy import select, func
from wtforms import TextAreaField, BooleanField

from app.models.admin import (
    ImportBatch,
    PendingIngredient,
    PendingRecipe,
    IngredientCategory,
    SystemConfig,
)
from app.models.recipe import Recipe, Ingredient


class ImportBatchAdmin(ModelView, model=ImportBatch):
    """CSV 임포트 배치 관리"""

    name = "Import Batch"
    name_plural = "Import Batches"
    icon = "fa-solid fa-file-csv"

    # 컬럼 표시 설정
    column_list = [
        "id",
        "filename",
        "status",
        "total_rows",
        "processed_rows",
        "success_count",
        "error_count",
        "created_by",
        "created_at",
        "approved_at",
    ]

    column_searchable_list = ["filename", "created_by"]
    column_sortable_list = ["created_at", "status", "total_rows"]
    column_default_sort = ("created_at", True)  # 최신순

    # 필터
    column_filters = ["status", "created_at"]

    # 상세 페이지 표시 컬럼
    column_details_list = [
        "id",
        "filename",
        "status",
        "total_rows",
        "processed_rows",
        "success_count",
        "error_count",
        "created_by",
        "approved_by",
        "created_at",
        "approved_at",
        "error_log",
    ]

    # 포맷팅
    column_formatters = {
        "error_log": lambda m, a: str(m.error_log) if m.error_log else "None",
    }

    # 읽기 전용 필드
    can_create = False
    can_edit = False
    can_delete = True

    page_size = 20


class PendingIngredientAdmin(ModelView, model=PendingIngredient):
    """승인 대기 재료 관리 (핵심 기능)"""

    name = "Pending Ingredient"
    name_plural = "Pending Ingredients"
    icon = "fa-solid fa-carrot"

    # 컬럼 표시
    column_list = [
        "id",
        "batch_id",
        "raw_name",
        "normalized_name",
        "quantity_from",
        "quantity_to",
        "quantity_unit",
        "is_vague",
        "is_abstract",
        "suggested_specific",
        "suggested_category",
        "approval_status",
    ]

    column_searchable_list = ["raw_name", "normalized_name", "suggested_specific"]
    column_sortable_list = ["id", "normalized_name", "approval_status", "is_vague", "is_abstract"]
    column_default_sort = ("id", False)

    # 필터 (워크플로우 최적화)
    column_filters = [
        "approval_status",
        "batch_id",
        "suggested_category",
        "is_vague",
        "is_abstract",
    ]

    # 상세 페이지
    column_details_list = [
        "id",
        "batch_id",
        "raw_name",
        "normalized_name",
        "quantity_from",
        "quantity_to",
        "quantity_unit",
        "is_vague",
        "is_abstract",
        "suggested_specific",
        "abstraction_notes",
        "suggested_category",
        "approval_status",
        "admin_notes",
        "created_at",
    ]

    # 인라인 편집 활성화
    can_create = False
    can_edit = True
    can_delete = True

    # 편집 가능 필드 (관리자가 파싱 결과 수정)
    form_columns = [
        "normalized_name",
        "quantity_from",
        "quantity_to",
        "quantity_unit",
        "suggested_specific",
        "abstraction_notes",
        "suggested_category",
        "approval_status",
        "admin_notes",
    ]

    # 포맷팅
    column_formatters = {
        "suggested_category": lambda m, a: m.suggested_category.name_ko if m.suggested_category else "없음",
        "is_vague": lambda m, a: "✓" if m.is_vague else "",
        "is_abstract": lambda m, a: "✓" if m.is_abstract else "",
    }

    page_size = 50


class PendingRecipeAdmin(ModelView, model=PendingRecipe):
    """승인 대기 레시피 관리"""

    name = "Pending Recipe"
    name_plural = "Pending Recipes"
    icon = "fa-solid fa-book"

    # 컬럼 표시
    column_list = [
        "id",
        "batch_id",
        "rcp_ttl",
        "ckg_nm",
        "approval_status",
        "created_at",
    ]

    column_searchable_list = ["rcp_ttl", "ckg_nm"]
    column_sortable_list = ["id", "rcp_ttl", "approval_status", "created_at"]
    column_default_sort = ("id", False)

    # 필터
    column_filters = ["approval_status", "batch_id", "ckg_nm"]

    # 상세 페이지
    column_details_list = [
        "id",
        "batch_id",
        "rcp_ttl",
        "ckg_nm",
        "ckg_mtrl_cn",
        "ckg_inbun_nm",
        "ckg_dodf_nm",
        "rcp_img_url",
        "approval_status",
        "admin_notes",
        "created_at",
    ]

    # 인라인 편집
    can_create = False
    can_edit = True
    can_delete = True

    form_columns = [
        "rcp_ttl",
        "ckg_nm",
        "ckg_mtrl_cn",
        "approval_status",
        "admin_notes",
    ]

    # 포맷팅 (긴 텍스트 줄이기)
    column_formatters = {
        "ckg_mtrl_cn": lambda m, a: (m.ckg_mtrl_cn[:50] + "...") if m.ckg_mtrl_cn and len(m.ckg_mtrl_cn) > 50 else m.ckg_mtrl_cn,
    }

    page_size = 50


class IngredientCategoryAdmin(ModelView, model=IngredientCategory):
    """재료 카테고리 관리"""

    name = "Ingredient Category"
    name_plural = "Ingredient Categories"
    icon = "fa-solid fa-tags"

    # 컬럼 표시
    column_list = [
        "id",
        "code",
        "name_ko",
        "name_en",
        "description",
        "display_order",
        "is_active",
    ]

    column_searchable_list = ["code", "name_ko", "name_en"]
    column_sortable_list = ["display_order", "code", "name_ko"]
    column_default_sort = ("display_order", False)

    # 필터
    column_filters = ["is_active"]

    # 상세 페이지
    column_details_list = [
        "id",
        "code",
        "name_ko",
        "name_en",
        "description",
        "display_order",
        "is_active",
        "created_at",
        "updated_at",
    ]

    # CRUD 활성화
    can_create = True
    can_edit = True
    can_delete = False  # 데이터 무결성 보호

    form_columns = [
        "code",
        "name_ko",
        "name_en",
        "description",
        "display_order",
        "is_active",
    ]

    # 포맷팅
    column_formatters = {
        "is_active": lambda m, a: "✓" if m.is_active else "✗",
    }

    page_size = 20


class SystemConfigAdmin(ModelView, model=SystemConfig):
    """시스템 설정 관리"""

    name = "System Config"
    name_plural = "System Configs"
    icon = "fa-solid fa-cog"

    # 컬럼 표시
    column_list = [
        "id",
        "config_key",
        "config_value",
        "value_type",
        "category",
        "is_editable",
        "updated_at",
    ]

    column_searchable_list = ["config_key", "description"]
    column_sortable_list = ["config_key", "category", "updated_at"]
    column_default_sort = ("category", False)

    # 필터
    column_filters = ["category", "value_type", "is_editable"]

    # 상세 페이지
    column_details_list = [
        "id",
        "config_key",
        "config_value",
        "value_type",
        "category",
        "description",
        "is_editable",
        "created_at",
        "updated_at",
    ]

    # CRUD
    can_create = False  # 시스템 설정은 마이그레이션에서만 생성
    can_edit = True
    can_delete = False

    form_columns = [
        "config_value",
        "description",
    ]

    # 포맷팅
    column_formatters = {
        "is_editable": lambda m, a: "✓" if m.is_editable else "✗ (읽기 전용)",
    }

    page_size = 20


class RecipeAdmin(ModelView, model=Recipe):
    """레시피 관리 (기존 테이블 강화)"""

    name = "Recipe"
    name_plural = "Recipes"
    icon = "fa-solid fa-utensils"

    # 컬럼 표시
    column_list = [
        "rcp_sno",
        "rcp_ttl",
        "ckg_nm",
        "approval_status",
        "import_batch_id",
        "created_at",
    ]

    column_searchable_list = ["rcp_ttl", "ckg_nm"]
    column_sortable_list = ["rcp_sno", "rcp_ttl", "approval_status", "created_at"]
    column_default_sort = ("created_at", True)

    # 필터 (approval_status 추가)
    column_filters = ["approval_status", "import_batch_id", "ckg_nm"]

    # 상세 페이지
    column_details_list = [
        "rcp_sno",
        "rcp_ttl",
        "ckg_nm",
        "ckg_mtrl_cn",
        "ckg_inbun_nm",
        "ckg_dodf_nm",
        "rcp_img_url",
        "approval_status",
        "import_batch_id",
        "approved_by",
        "approved_at",
        "created_at",
        "updated_at",
    ]

    # 편집 제한 (승인된 레시피는 수정 주의)
    can_create = False
    can_edit = True
    can_delete = False

    form_columns = [
        "rcp_ttl",
        "ckg_nm",
        "ckg_mtrl_cn",
        "approval_status",
    ]

    # 포맷팅
    column_formatters = {
        "ckg_mtrl_cn": lambda m, a: (m.ckg_mtrl_cn[:50] + "...") if m.ckg_mtrl_cn and len(m.ckg_mtrl_cn) > 50 else m.ckg_mtrl_cn,
        "import_batch_id": lambda m, a: m.import_batch_id if m.import_batch_id else "-",
    }

    page_size = 50


class IngredientAdmin(ModelView, model=Ingredient):
    """재료 관리 (기존 테이블 강화)"""

    name = "Ingredient"
    name_plural = "Ingredients"
    icon = "fa-solid fa-seedling"

    # 컬럼 표시
    column_list = [
        "id",
        "name",
        "category",
        "approval_status",
        "created_at",
    ]

    column_searchable_list = ["name"]
    column_sortable_list = ["id", "name", "approval_status", "created_at"]
    column_default_sort = ("created_at", True)

    # 필터
    column_filters = ["approval_status"]

    # 상세 페이지
    column_details_list = [
        "id",
        "name",
        "category",
        "approval_status",
        "normalized_at",
        "created_at",
        "updated_at",
    ]

    # 편집 제한
    can_create = False
    can_edit = True
    can_delete = False

    form_columns = [
        "name",
        "category",
        "approval_status",
    ]

    # 포맷팅
    column_formatters = {
        "category": lambda m, a: m.category.name_ko if m.category else "없음",
    }

    page_size = 50
