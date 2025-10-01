"""
배치 승인 서비스 (Phase 2.6 / Phase 5.4)

ImportBatch를 승인하여 Pending 테이블 → Production 테이블로 이동
- PendingIngredient → Ingredient
- PendingRecipe → Recipe
- RecipeIngredient 관계 생성
- 중복 재료 병합 (duplicate_of_id 처리)
- 트랜잭션 보장 (원자성)
"""
import logging
from datetime import datetime
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.admin import ImportBatch, PendingIngredient, PendingRecipe
from app.models.recipe import Ingredient, Recipe, RecipeIngredient

logger = logging.getLogger(__name__)


class BatchApprovalService:
    """배치 승인 서비스"""

    @staticmethod
    async def approve_batch(
        db: AsyncSession,
        batch_id: str,
        admin_user: str = "system"
    ) -> Dict[str, int]:
        """
        배치 승인 실행

        Args:
            db: 데이터베이스 세션
            batch_id: 승인할 배치 ID
            admin_user: 승인자 (추후 인증 통합 시 사용)

        Returns:
            dict: 승인 결과 통계
                - ingredients_created: 새로 생성된 재료 개수
                - ingredients_merged: 중복 병합된 재료 개수
                - recipes_created: 새로 생성된 레시피 개수
                - relationships_created: RecipeIngredient 관계 개수

        Raises:
            ValueError: 배치가 존재하지 않거나 이미 승인됨
            Exception: 트랜잭션 실패 시
        """
        logger.info(f"🚀 배치 승인 시작: batch_id={batch_id}, admin_user={admin_user}")

        # 1. 배치 조회 및 검증
        batch = await BatchApprovalService._validate_batch(db, batch_id)

        # 2. 승인 대기 중인 PendingIngredient/Recipe 조회
        pending_ingredients = await BatchApprovalService._get_approved_pending_ingredients(
            db, batch_id
        )
        pending_recipes = await BatchApprovalService._get_approved_pending_recipes(
            db, batch_id
        )

        logger.info(f"📊 승인 대기: 재료 {len(pending_ingredients)}개, 레시피 {len(pending_recipes)}개")

        # 3. 트랜잭션 시작 (원자성 보장)
        stats = {
            "ingredients_created": 0,
            "ingredients_merged": 0,
            "recipes_created": 0,
            "relationships_created": 0,
        }

        try:
            # 3.1 재료 승인 (중복 처리 포함)
            ingredient_mapping = await BatchApprovalService._approve_ingredients(
                db, pending_ingredients
            )
            stats["ingredients_created"] = len([v for v in ingredient_mapping.values() if v["is_new"]])
            stats["ingredients_merged"] = len([v for v in ingredient_mapping.values() if not v["is_new"]])

            # 3.2 레시피 승인
            recipe_mapping = await BatchApprovalService._approve_recipes(
                db, pending_recipes, batch_id, admin_user
            )
            stats["recipes_created"] = len(recipe_mapping)

            # 3.3 RecipeIngredient 관계 생성
            relationships_count = await BatchApprovalService._create_recipe_ingredient_relationships(
                db, pending_recipes, recipe_mapping, ingredient_mapping
            )
            stats["relationships_created"] = relationships_count

            # 3.4 배치 상태 업데이트
            batch.status = "approved"
            batch.approved_at = datetime.utcnow()
            batch.approved_by = admin_user

            await db.commit()

            logger.info(f"✅ 배치 승인 완료: {stats}")
            return stats

        except Exception as e:
            logger.error(f"❌ 배치 승인 실패: {e}", exc_info=True)
            await db.rollback()
            raise

    @staticmethod
    async def _validate_batch(db: AsyncSession, batch_id: str) -> ImportBatch:
        """배치 검증"""
        result = await db.execute(
            select(ImportBatch).where(ImportBatch.id == batch_id)
        )
        batch = result.scalar_one_or_none()

        if not batch:
            raise ValueError(f"배치를 찾을 수 없습니다: {batch_id}")

        if batch.status == "approved":
            raise ValueError(f"이미 승인된 배치입니다: {batch_id}")

        return batch

    @staticmethod
    async def _get_approved_pending_ingredients(
        db: AsyncSession, batch_id: str
    ) -> List[PendingIngredient]:
        """승인 대기 중인 PendingIngredient 조회 (approval_status='approved'만)"""
        result = await db.execute(
            select(PendingIngredient)
            .where(
                and_(
                    PendingIngredient.import_batch_id == batch_id,
                    PendingIngredient.approval_status == "approved"
                )
            )
            .options(selectinload(PendingIngredient.suggested_category))
        )
        return list(result.scalars().all())

    @staticmethod
    async def _get_approved_pending_recipes(
        db: AsyncSession, batch_id: str
    ) -> List[PendingRecipe]:
        """승인 대기 중인 PendingRecipe 조회 (approval_status='approved'만)"""
        result = await db.execute(
            select(PendingRecipe)
            .where(
                and_(
                    PendingRecipe.import_batch_id == batch_id,
                    PendingRecipe.approval_status == "approved"
                )
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def _approve_ingredients(
        db: AsyncSession,
        pending_ingredients: List[PendingIngredient]
    ) -> Dict[int, Dict]:
        """
        재료 승인 및 중복 병합

        Returns:
            dict: {pending_ingredient.id: {"ingredient_id": int, "is_new": bool}}
        """
        ingredient_mapping = {}

        for pending in pending_ingredients:
            # 중복 재료가 지정된 경우 기존 재료 사용
            if pending.duplicate_of_id:
                logger.info(f"🔗 재료 병합: {pending.normalized_name} → Ingredient#{pending.duplicate_of_id}")
                ingredient_mapping[pending.id] = {
                    "ingredient_id": pending.duplicate_of_id,
                    "is_new": False
                }
                continue

            # 정규화된 이름으로 기존 재료 검색
            existing_result = await db.execute(
                select(Ingredient).where(Ingredient.name == pending.normalized_name)
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                # 기존 재료 재사용
                logger.info(f"✅ 기존 재료 재사용: {pending.normalized_name} (Ingredient#{existing.id})")
                ingredient_mapping[pending.id] = {
                    "ingredient_id": existing.id,
                    "is_new": False
                }
            else:
                # 새 재료 생성
                new_ingredient = Ingredient(
                    name=pending.normalized_name,
                    category_id=pending.suggested_category_id,
                    approval_status="approved",
                    normalized_at=datetime.utcnow()
                )
                db.add(new_ingredient)
                await db.flush()  # ID 생성

                logger.info(f"🆕 새 재료 생성: {pending.normalized_name} (Ingredient#{new_ingredient.id})")
                ingredient_mapping[pending.id] = {
                    "ingredient_id": new_ingredient.id,
                    "is_new": True
                }

        return ingredient_mapping

    @staticmethod
    async def _approve_recipes(
        db: AsyncSession,
        pending_recipes: List[PendingRecipe],
        batch_id: str,
        admin_user: str
    ) -> Dict[int, int]:
        """
        레시피 승인

        Returns:
            dict: {pending_recipe.id: recipe.id}
        """
        recipe_mapping = {}

        for pending in pending_recipes:
            # Recipe 생성 (모든 PendingRecipe 필드 포함)
            new_recipe = Recipe(
                rcp_sno=pending.rcp_sno,
                rcp_ttl=pending.rcp_ttl,
                ckg_nm=pending.ckg_nm,
                rgtr_id=pending.rgtr_id,
                rgtr_nm=pending.rgtr_nm,
                inq_cnt=pending.inq_cnt,
                rcmm_cnt=pending.rcmm_cnt,
                srap_cnt=pending.srap_cnt,
                ckg_mth_acto_nm=pending.ckg_mth_acto_nm,
                ckg_sta_acto_nm=pending.ckg_sta_acto_nm,
                ckg_mtrl_acto_nm=pending.ckg_mtrl_acto_nm,
                ckg_knd_acto_nm=pending.ckg_knd_acto_nm,
                ckg_ipdc=pending.ckg_ipdc,
                ckg_mtrl_cn=pending.ckg_mtrl_cn,
                ckg_inbun_nm=pending.ckg_inbun_nm,
                ckg_dodf_nm=pending.ckg_dodf_nm,
                ckg_time_nm=pending.ckg_time_nm,
                first_reg_dt=pending.first_reg_dt,
                rcp_img_url=pending.rcp_img_url,
                approval_status="approved",
                import_batch_id=batch_id,
                approved_by=admin_user,
                approved_at=datetime.utcnow()
            )
            db.add(new_recipe)
            await db.flush()  # ID 생성

            recipe_mapping[pending.rcp_sno] = new_recipe.rcp_sno
            logger.info(f"새 레시피 생성: {pending.rcp_ttl} (Recipe#{new_recipe.rcp_sno})")

        return recipe_mapping

    @staticmethod
    async def _create_recipe_ingredient_relationships(
        db: AsyncSession,
        pending_recipes: List[PendingRecipe],
        recipe_mapping: Dict[int, int],
        ingredient_mapping: Dict[int, Dict]
    ) -> int:
        """
        RecipeIngredient 관계 생성

        recipe_name을 기준으로 PendingIngredient와 매칭하여 RecipeIngredient 생성

        Returns:
            int: 생성된 관계 개수
        """
        relationships_count = 0

        # recipe_name을 key로 하는 pending_ingredients 그룹핑
        recipe_ingredients_map = {}
        for pending_ing_id, ing_info in ingredient_mapping.items():
            # PendingIngredient 조회
            result = await db.execute(
                select(PendingIngredient).where(PendingIngredient.id == pending_ing_id)
            )
            pending_ing = result.scalar_one_or_none()

            if pending_ing and pending_ing.recipe_name:
                if pending_ing.recipe_name not in recipe_ingredients_map:
                    recipe_ingredients_map[pending_ing.recipe_name] = []
                recipe_ingredients_map[pending_ing.recipe_name].append({
                    "ingredient_id": ing_info["ingredient_id"],
                    "pending_ing": pending_ing
                })

        # 각 PendingRecipe에 대해 RecipeIngredient 생성
        for pending_recipe in pending_recipes:
            if pending_recipe.rcp_sno not in recipe_mapping:
                continue

            recipe_sno = recipe_mapping[pending_recipe.rcp_sno]
            recipe_title = pending_recipe.rcp_ttl

            # recipe_name으로 매칭되는 PendingIngredient 찾기
            matched_ingredients = recipe_ingredients_map.get(recipe_title, [])

            for idx, ing_data in enumerate(matched_ingredients):
                # RecipeIngredient 생성
                recipe_ingredient = RecipeIngredient(
                    rcp_sno=recipe_sno,
                    ingredient_id=ing_data["ingredient_id"],
                    quantity_from=ing_data["pending_ing"].quantity_from,
                    quantity_to=ing_data["pending_ing"].quantity_to,
                    unit=ing_data["pending_ing"].quantity_unit,
                    is_vague=ing_data["pending_ing"].is_vague,
                    display_order=idx,
                    category_id=ing_data["pending_ing"].suggested_category_id,
                    raw_quantity_text=ing_data["pending_ing"].raw_name
                )
                db.add(recipe_ingredient)
                relationships_count += 1

            if matched_ingredients:
                logger.info(f"🔗 {recipe_title}: {len(matched_ingredients)}개 재료 연결")

        await db.flush()
        logger.info(f"✅ RecipeIngredient 관계 생성 완료: {relationships_count}개")
        return relationships_count

    @staticmethod
    async def rollback_batch_approval(
        db: AsyncSession,
        batch_id: str
    ) -> Dict[str, int]:
        """
        배치 승인 롤백 (선택사항)

        주의: 실제 운영에서는 데이터 무결성 이슈로 권장하지 않음
        대신 새 배치로 수정사항 반영 권장
        """
        logger.warning(f"⚠️ 배치 롤백은 권장하지 않습니다: {batch_id}")
        logger.info("💡 대안: 새 CSV로 수정사항 재업로드 후 재승인")

        # 구현 생략 (Phase 5 범위 외)
        raise NotImplementedError("배치 롤백은 구현되지 않았습니다. 새 배치를 사용하세요.")
