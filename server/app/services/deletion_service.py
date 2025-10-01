"""
데이터 삭제 서비스 (Deletion Service)

CASCADE 관계 분석 및 안전한 데이터 삭제 기능 제공
"""
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, inspect
from sqlalchemy.orm import class_mapper

from app.models.recipe import Recipe, Ingredient, RecipeIngredient
from app.models.admin import ImportBatch, PendingRecipe, PendingIngredient, IngredientCategory, SystemConfig

logger = logging.getLogger(__name__)


class DeletionService:
    """CASCADE 관계 분석 및 안전한 삭제 서비스"""

    # 테이블별 관계 정의 (CASCADE 영향 분석용)
    TABLE_RELATIONSHIPS = {
        "recipes": {
            "model": Recipe,
            "cascades": [
                {"table": "recipe_ingredients", "field": "rcp_sno", "description": "레시피-재료 관계"}
            ]
        },
        "ingredients": {
            "model": Ingredient,
            "cascades": [
                {"table": "recipe_ingredients", "field": "ingredient_id", "description": "재료-레시피 관계"}
            ]
        },
        "import_batches": {
            "model": ImportBatch,
            "cascades": [
                {"table": "pending_recipes", "field": "import_batch_id", "description": "대기 레시피 (SET NULL)"},
                {"table": "pending_ingredients", "field": "import_batch_id", "description": "대기 재료 (SET NULL)"}
            ]
        },
        "ingredient_categories": {
            "model": IngredientCategory,
            "cascades": [
                {"table": "pending_ingredients", "field": "suggested_category_id", "description": "대기 재료 카테고리 (SET NULL)"}
            ]
        },
        "pending_recipes": {
            "model": PendingRecipe,
            "cascades": []
        },
        "pending_ingredients": {
            "model": PendingIngredient,
            "cascades": []
        },
        "recipe_ingredients": {
            "model": RecipeIngredient,
            "cascades": []
        }
    }

    @staticmethod
    async def analyze_cascade_impact(
        db: AsyncSession,
        table_name: str,
        record_ids: List[Any]
    ) -> Dict[str, Any]:
        """
        CASCADE 삭제 영향 분석

        Args:
            db: 데이터베이스 세션
            table_name: 테이블 이름
            record_ids: 삭제할 레코드 ID 리스트

        Returns:
            dict: CASCADE 영향 정보
                - will_delete: CASCADE로 삭제될 레코드 정보
                - will_set_null: SET NULL로 영향받을 레코드 정보
                - total_affected: 총 영향받는 레코드 수
        """
        if table_name not in DeletionService.TABLE_RELATIONSHIPS:
            return {
                "will_delete": [],
                "will_set_null": [],
                "total_affected": 0,
                "error": f"알 수 없는 테이블: {table_name}"
            }

        table_info = DeletionService.TABLE_RELATIONSHIPS[table_name]
        model = table_info["model"]
        cascades = table_info["cascades"]

        will_delete = []
        will_set_null = []

        # 각 CASCADE 관계 분석
        for cascade_info in cascades:
            cascade_table = cascade_info["table"]
            cascade_field = cascade_info["field"]
            description = cascade_info["description"]

            # CASCADE 영향받는 레코드 카운트
            if cascade_table == "recipe_ingredients":
                # RecipeIngredient 관계 분석
                if table_name == "recipes":
                    # Recipe 삭제 시 RecipeIngredient도 삭제됨
                    result = await db.execute(
                        select(func.count(RecipeIngredient.id))
                        .where(RecipeIngredient.rcp_sno.in_(record_ids))
                    )
                    count = result.scalar()
                    if count > 0:
                        will_delete.append({
                            "table": cascade_table,
                            "description": description,
                            "count": count,
                            "action": "DELETE (CASCADE)"
                        })

                elif table_name == "ingredients":
                    # Ingredient 삭제 시 RecipeIngredient도 삭제됨
                    result = await db.execute(
                        select(func.count(RecipeIngredient.id))
                        .where(RecipeIngredient.ingredient_id.in_(record_ids))
                    )
                    count = result.scalar()
                    if count > 0:
                        will_delete.append({
                            "table": cascade_table,
                            "description": description,
                            "count": count,
                            "action": "DELETE (CASCADE)"
                        })

            elif cascade_table == "pending_recipes":
                # ImportBatch 삭제 시 PendingRecipe는 SET NULL
                result = await db.execute(
                    select(func.count(PendingRecipe.rcp_sno))
                    .where(PendingRecipe.import_batch_id.in_(record_ids))
                )
                count = result.scalar()
                if count > 0:
                    will_set_null.append({
                        "table": cascade_table,
                        "description": description,
                        "count": count,
                        "action": "SET NULL"
                    })

            elif cascade_table == "pending_ingredients":
                # ImportBatch 또는 IngredientCategory 삭제 시 SET NULL
                if table_name == "import_batches":
                    result = await db.execute(
                        select(func.count(PendingIngredient.id))
                        .where(PendingIngredient.import_batch_id.in_(record_ids))
                    )
                    count = result.scalar()
                    if count > 0:
                        will_set_null.append({
                            "table": cascade_table,
                            "description": description,
                            "count": count,
                            "action": "SET NULL (import_batch_id)"
                        })

                elif table_name == "ingredient_categories":
                    result = await db.execute(
                        select(func.count(PendingIngredient.id))
                        .where(PendingIngredient.suggested_category_id.in_(record_ids))
                    )
                    count = result.scalar()
                    if count > 0:
                        will_set_null.append({
                            "table": cascade_table,
                            "description": description,
                            "count": count,
                            "action": "SET NULL (suggested_category_id)"
                        })

        total_affected = sum(item["count"] for item in will_delete + will_set_null)

        return {
            "will_delete": will_delete,
            "will_set_null": will_set_null,
            "total_affected": total_affected
        }

    @staticmethod
    def generate_confirmation_message(
        table_name: str,
        record_count: int,
        cascade_impact: Dict[str, Any]
    ) -> str:
        """
        삭제 확인 메시지 생성

        Args:
            table_name: 테이블 이름
            record_count: 삭제할 레코드 수
            cascade_impact: CASCADE 영향 분석 결과

        Returns:
            str: 확인 메시지
        """
        table_kr_names = {
            "recipes": "레시피",
            "ingredients": "재료",
            "import_batches": "업로드 배치",
            "pending_recipes": "대기 레시피",
            "pending_ingredients": "대기 재료",
            "ingredient_categories": "재료 카테고리",
            "recipe_ingredients": "레시피-재료 관계"
        }

        table_kr = table_kr_names.get(table_name, table_name)
        message = f"{table_kr} {record_count}개를 삭제하시겠습니까?"

        # CASCADE 삭제 정보 추가
        if cascade_impact.get("will_delete"):
            message += "\n\n⚠️ CASCADE 삭제:"
            for item in cascade_impact["will_delete"]:
                item_table_kr = table_kr_names.get(item["table"], item["table"])
                message += f"\n- {item['description']}: {item_table_kr} {item['count']}개"

        # SET NULL 정보 추가
        if cascade_impact.get("will_set_null"):
            message += "\n\n📝 영향받는 데이터 (SET NULL):"
            for item in cascade_impact["will_set_null"]:
                item_table_kr = table_kr_names.get(item["table"], item["table"])
                message += f"\n- {item['description']}: {item_table_kr} {item['count']}개"

        total = cascade_impact.get("total_affected", 0)
        if total > 0:
            message += f"\n\n총 {total}개의 관련 데이터가 영향을 받습니다."

        return message

    @staticmethod
    async def safe_delete(
        db: AsyncSession,
        table_name: str,
        record_ids: List[Any]
    ) -> Dict[str, Any]:
        """
        안전한 삭제 실행

        Args:
            db: 데이터베이스 세션
            table_name: 테이블 이름
            record_ids: 삭제할 레코드 ID 리스트

        Returns:
            dict: 삭제 결과
                - success: 성공 여부
                - deleted_count: 삭제된 레코드 수
                - error: 에러 메시지 (실패 시)
        """
        if table_name not in DeletionService.TABLE_RELATIONSHIPS:
            return {
                "success": False,
                "deleted_count": 0,
                "error": f"알 수 없는 테이블: {table_name}"
            }

        try:
            model = DeletionService.TABLE_RELATIONSHIPS[table_name]["model"]
            mapper = class_mapper(model)
            primary_key = mapper.primary_key[0].name

            # 레코드 조회 및 삭제
            deleted_count = 0
            for record_id in record_ids:
                result = await db.execute(
                    select(model).where(getattr(model, primary_key) == record_id)
                )
                record = result.scalar_one_or_none()

                if record:
                    await db.delete(record)
                    deleted_count += 1
                    logger.info(f"✅ {table_name} 삭제: {primary_key}={record_id}")

            await db.commit()

            return {
                "success": True,
                "deleted_count": deleted_count
            }

        except Exception as e:
            logger.error(f"❌ {table_name} 삭제 실패: {e}", exc_info=True)
            await db.rollback()
            return {
                "success": False,
                "deleted_count": 0,
                "error": str(e)
            }
