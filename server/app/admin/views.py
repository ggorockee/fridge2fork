"""
SQLAdmin View 클래스들
관리자 UI를 통한 데이터 관리
"""
from typing import Any
from sqladmin import ModelView, action
from sqlalchemy import select, func
from wtforms import TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired
from starlette.requests import Request
from starlette.responses import RedirectResponse

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

    name = "요리책 업로드"
    name_plural = "요리책 배치 목록"
    icon = "upload_file"

    # 한글 컬럼 레이블
    column_labels = {
        "id": "배치 ID",
        "filename": "파일 이름",
        "status": "상태",
        "total_rows": "전체 건수",
        "processed_rows": "처리 건수",
        "success_count": "성공",
        "error_count": "오류",
        "created_by": "등록자",
        "approved_by": "승인자",
        "created_at": "등록일",
        "approved_at": "승인일",
        "error_log": "오류 로그",
    }

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

    # 필터 비활성화 (SQLAdmin 호환성 문제)
    # column_filters = []

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
        "status": lambda m, a: {
            "pending": "대기중",
            "approved": "승인됨",
            "rejected": "거부됨",
        }.get(m.status, m.status),
    }

    # 읽기 전용 필드
    can_create = False
    can_edit = False
    can_delete = True  # 삭제 기능 활성화

    # 삭제 확인 메시지
    delete_modal = True
    delete_modal_template = "sqladmin/modals/delete.html"

    # 삭제 액션
    @action(
        name="delete_selected",
        label="선택 항목 삭제",
        confirmation_message="",
        add_in_detail=False,
        add_in_list=True,
    )
    async def delete_selected_action(self, request: Request) -> RedirectResponse:
        """선택된 배치 삭제 (CASCADE 분석 포함)"""
        from app.services.deletion_service import DeletionService
        from app.core.database import get_db
        import logging

        logger = logging.getLogger(__name__)

        pks = request.query_params.get("pks", "").split(",")
        if not pks or pks == [""]:
            return RedirectResponse(
                url=request.url_for("admin:list", identity=self.identity),
                status_code=302
            )

        async for session in get_db():
            cascade_impact = await DeletionService.analyze_cascade_impact(
                db=session,
                table_name="import_batches",
                record_ids=pks
            )

            logger.info(f"배치 삭제 CASCADE 분석: {cascade_impact}")

            result = await DeletionService.safe_delete(
                db=session,
                table_name="import_batches",
                record_ids=pks
            )

            if result["success"]:
                logger.info(f"✅ 배치 {result['deleted_count']}개 삭제 완료")
            else:
                logger.error(f"❌ 배치 삭제 실패: {result.get('error')}")

            break

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    # 배치 승인 액션
    @action(
        name="approve_batch",
        label="배치 승인 (개발 DB로 이동)",
        confirmation_message="이 배치를 승인하여 개발 테이블로 이동하시겠습니까? (approval_status='approved'인 항목만 이동됩니다)",
        add_in_detail=True,
        add_in_list=True,
    )
    async def approve_batch_action(self, request: Request) -> RedirectResponse:
        """배치 승인 실행 - PendingIngredient/Recipe → 개발 테이블로 이동"""
        from app.services.batch_approval import BatchApprovalService
        from app.core.database import get_db
        import logging

        logger = logging.getLogger(__name__)

        # URL에서 batch_id 추출
        pks = request.query_params.get("pks", "").split(",")

        # 단일 배치 승인 (상세 페이지에서 호출 시)
        if not pks or pks == [""]:
            # Detail 페이지에서는 URL path에서 ID 추출
            batch_id = request.path_params.get("pk")
            if batch_id:
                pks = [batch_id]

        if not pks or pks == [""]:
            logger.warning("배치 ID를 찾을 수 없습니다")
            return RedirectResponse(
                url=request.url_for("admin:list", identity=self.identity),
                status_code=302
            )

        # get_db 제너레이터를 사용하여 세션 획득
        async for session in get_db():
            for batch_id in pks:
                try:
                    logger.info(f"배치 승인 시작: {batch_id}")

                    # 배치 승인 서비스 호출
                    stats = await BatchApprovalService.approve_batch(
                        db=session,
                        batch_id=batch_id,
                        admin_user="admin"  # TODO: 실제 인증 사용자
                    )

                    logger.info(f"배치 {batch_id} 승인 완료: {stats}")

                except ValueError as e:
                    # 이미 승인됨 또는 존재하지 않는 배치
                    logger.warning(f"배치 {batch_id} 승인 실패: {e}")
                except Exception as e:
                    # 기타 오류
                    logger.error(f"배치 {batch_id} 승인 오류: {e}", exc_info=True)

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    page_size = 20


class PendingIngredientAdmin(ModelView, model=PendingIngredient):
    """승인 대기 재료 관리 (핵심 기능)"""

    name = "재료 검토함"
    name_plural = "재료 검토함"
    icon = "inventory_2"

    # 한글 컬럼 레이블 및 설명
    column_labels = {
        "id": "ID",
        "import_batch_id": "배치 ID",
        "recipe_name": "레시피 이름",  # 해당 재료가 속한 레시피 이름
        "raw_name": "원본 이름",  # CSV에서 추출한 원본 재료 표현 (예: "떡국떡400g")
        "normalized_name": "정규화 이름",  # 정제된 재료 이름 (예: "떡국떡")
        "quantity_from": "수량 시작",  # 수량 범위의 최소값 (예: "200-300g"의 200)
        "quantity_to": "수량 끝",  # 수량 범위의 최대값 (예: "200-300g"의 300)
        "quantity_unit": "단위",  # 수량 단위 (g, ml, 개, 컵, 큰술 등)
        "is_vague": "모호함",  # 수량 표현이 모호한 경우 (예: "적당량", "약간")
        "is_abstract": "추상적",  # 재료명이 추상적인 경우 (예: "고기", "채소")
        "suggested_specific": "구체적 제안",  # 추상적 재료를 구체적으로 변환한 제안 (예: "고기" → "소고기")
        "abstraction_notes": "추상화 메모",  # 추상적 표현에 대한 관리자 메모
        "suggested_category": "제안 카테고리",  # AI가 자동 분류한 재료 카테고리
        "approval_status": "승인 상태",  # pending/approved/rejected (읽기 전용)
        "merge_notes": "병합 메모",  # 중복 재료 병합 시 관리자 메모
        "created_at": "생성일",
    }

    # 컬럼 표시
    column_list = [
        "id",
        "recipe_name",  # 레시피 이름 추가
        "normalized_name",
        "quantity_from",
        "quantity_to",
        "quantity_unit",
        "suggested_category",
        "is_vague",
        "is_abstract",
        "approval_status",
    ]

    column_searchable_list = ["recipe_name", "raw_name", "normalized_name", "suggested_specific"]
    column_sortable_list = ["id", "recipe_name", "normalized_name", "approval_status", "is_vague", "is_abstract"]
    column_default_sort = ("id", False)

    # 필터 비활성화 (SQLAdmin 호환성 문제)
    # column_filters = []

    # 상세 페이지
    column_details_list = [
        "id",
        "import_batch_id",
        "recipe_name",
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
        "merge_notes",
        "created_at",
    ]

    # 인라인 편집 활성화
    can_create = True  # 재료 추가 기능 활성화
    can_edit = True
    can_delete = True

    # 삭제 확인 메시지
    delete_modal = True
    delete_modal_template = "sqladmin/modals/delete.html"

    # 편집 가능 필드 (부분 승인을 위해 approval_status 포함)
    form_columns = [
        "import_batch_id",  # 재료 추가 시 배치 ID 필요
        "recipe_name",      # 레시피 이름
        "raw_name",         # 원본 이름
        "normalized_name",
        "quantity_from",
        "quantity_to",
        "quantity_unit",
        "suggested_specific",
        "abstraction_notes",
        "suggested_category",
        "approval_status",  # 개별 재료 승인/거부 상태 변경 가능
        "merge_notes",
    ]

    # 폼 필드 커스터마이징
    form_overrides = {
        "approval_status": SelectField,
    }

    form_args = {
        "approval_status": {
            "label": "승인 상태",
            "choices": [
                ("pending", "대기중"),
                ("approved", "승인"),
                ("rejected", "거부"),
            ],
            "validators": [DataRequired()],
            "description": "재료 승인 상태를 선택하세요",
        }
    }

    # 포맷팅 (목록 및 상세 페이지)
    column_formatters = {
        "suggested_category": lambda m, a: m.suggested_category.name_ko if m.suggested_category else "없음",
        "is_vague": lambda m, a: "Y" if m.is_vague else "",
        "is_abstract": lambda m, a: "Y" if m.is_abstract else "",
        "approval_status": lambda m, a: {
            "pending": "대기중",
            "approved": "승인",
            "rejected": "거부",
        }.get(m.approval_status, m.approval_status),
    }

    # 삭제 액션
    @action(
        name="delete_selected",
        label="선택 항목 삭제",
        confirmation_message="선택한 재료들을 삭제하시겠습니까?",
        add_in_detail=False,
        add_in_list=True,
    )
    async def delete_selected_action(self, request: Request) -> RedirectResponse:
        """선택된 대기 재료 삭제"""
        from app.services.deletion_service import DeletionService
        from app.core.database import get_db
        import logging

        logger = logging.getLogger(__name__)

        pks = request.query_params.get("pks", "").split(",")
        if not pks or pks == [""]:
            return RedirectResponse(
                url=request.url_for("admin:list", identity=self.identity),
                status_code=302
            )

        async for session in get_db():
            result = await DeletionService.safe_delete(
                db=session,
                table_name="pending_ingredients",
                record_ids=[int(pk) for pk in pks]
            )

            if result["success"]:
                logger.info(f"✅ 대기 재료 {result['deleted_count']}개 삭제 완료")
            else:
                logger.error(f"❌ 대기 재료 삭제 실패: {result.get('error')}")

            break

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    # 일괄 작업 액션
    @action(
        name="approve_selected",
        label="선택 항목 승인",
        confirmation_message="선택한 재료들을 승인하시겠습니까?",
        add_in_detail=False,
        add_in_list=True,
    )
    async def approve_selected(self, request: Request) -> RedirectResponse:
        """선택된 재료들을 일괄 승인"""
        pks = request.query_params.get("pks", "").split(",")
        if not pks or pks == [""]:
            return RedirectResponse(
                url=request.url_for("admin:list", identity=self.identity),
                status_code=302
            )

        async with self.session_maker() as session:
            for pk in pks:
                result = await session.execute(
                    select(PendingIngredient).where(PendingIngredient.id == int(pk))
                )
                ingredient = result.scalar_one_or_none()
                if ingredient:
                    ingredient.approval_status = "approved"
            await session.commit()

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    @action(
        name="reject_selected",
        label="선택 항목 거부",
        confirmation_message="선택한 재료들을 거부하시겠습니까?",
        add_in_detail=False,
        add_in_list=True,
    )
    async def reject_selected(self, request: Request) -> RedirectResponse:
        """선택된 재료들을 일괄 거부"""
        pks = request.query_params.get("pks", "").split(",")
        if not pks or pks == [""]:
            return RedirectResponse(
                url=request.url_for("admin:list", identity=self.identity),
                status_code=302
            )

        async with self.session_maker() as session:
            for pk in pks:
                result = await session.execute(
                    select(PendingIngredient).where(PendingIngredient.id == int(pk))
                )
                ingredient = result.scalar_one_or_none()
                if ingredient:
                    ingredient.approval_status = "rejected"
            await session.commit()

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    @action(
        name="approve_all_pending",
        label="대기중 항목 전체 승인",
        confirmation_message="현재 대기중인 모든 재료를 승인하시겠습니까?",
        add_in_detail=False,
        add_in_list=True,
    )
    async def approve_all_pending(self, request: Request) -> RedirectResponse:
        """대기중인 모든 재료를 일괄 승인"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(PendingIngredient).where(PendingIngredient.approval_status == "pending")
            )
            ingredients = result.scalars().all()

            for ingredient in ingredients:
                ingredient.approval_status = "approved"

            await session.commit()

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    @action(
        name="view_ingredient_warehouse",
        label="식재료 창고 (고유 재료 목록)",
        add_in_detail=False,
        add_in_list=True,
    )
    async def view_ingredient_warehouse(self, request: Request):
        """고유 재료 목록을 쉼표로 구분하여 표시"""
        from starlette.responses import HTMLResponse

        async with self.session_maker() as session:
            # 고유 재료 이름 조회 (중복 제거)
            result = await session.execute(
                select(PendingIngredient.normalized_name).distinct().order_by(PendingIngredient.normalized_name)
            )
            unique_ingredients = [row[0] for row in result.fetchall() if row[0]]

        # 쉼표로 구분된 문자열 생성
        ingredients_text = ", ".join(unique_ingredients)

        # 간단한 HTML 페이지
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>식재료 창고 - 고유 재료 목록</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                h1 {{ color: #333; }}
                .stats {{ background: #f0f0f0; padding: 10px; margin: 20px 0; border-radius: 5px; }}
                .content {{ background: white; border: 1px solid #ddd; padding: 20px; border-radius: 5px; }}
                textarea {{ width: 100%; height: 400px; font-family: monospace; padding: 10px; }}
                button {{ background: #007bff; color: white; border: none; padding: 10px 20px;
                         cursor: pointer; border-radius: 5px; font-size: 16px; margin: 10px 5px; }}
                button:hover {{ background: #0056b3; }}
                .back-btn {{ background: #6c757d; }}
                .back-btn:hover {{ background: #545b62; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏪 식재료 창고 - 고유 재료 목록</h1>
                <div class="stats">
                    <strong>총 고유 재료 개수:</strong> {len(unique_ingredients)}개
                </div>
                <div class="content">
                    <h3>쉼표로 구분된 목록 (복사 가능)</h3>
                    <textarea id="ingredientsText" readonly>{ingredients_text}</textarea>
                    <button onclick="copyToClipboard()">📋 클립보드에 복사</button>
                    <button class="back-btn" onclick="window.history.back()">← 돌아가기</button>
                </div>
            </div>
            <script>
                function copyToClipboard() {{
                    const text = document.getElementById('ingredientsText');
                    text.select();
                    document.execCommand('copy');
                    alert('클립보드에 복사되었습니다!');
                }}
            </script>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    @action(
        name="bulk_rename_ingredient",
        label="재료 이름 일괄 수정",
        add_in_detail=False,
        add_in_list=True,
    )
    async def bulk_rename_ingredient(self, request: Request):
        """재료 이름을 일괄 수정하는 폼 제공"""
        from starlette.responses import HTMLResponse

        # POST 요청 처리 (실제 수정)
        if request.method == "POST":
            form = await request.form()
            old_name = form.get("old_name", "").strip()
            new_name = form.get("new_name", "").strip()

            if old_name and new_name:
                async with self.session_maker() as session:
                    # 재료 조회 및 업데이트
                    result = await session.execute(
                        select(PendingIngredient).where(PendingIngredient.normalized_name == old_name)
                    )
                    ingredients = result.scalars().all()

                    updated_count = len(ingredients)
                    for ingredient in ingredients:
                        ingredient.normalized_name = new_name

                    await session.commit()

                # 성공 메시지와 함께 리다이렉트
                return RedirectResponse(
                    url=request.url_for("admin:list", identity=self.identity) + f"?msg=Updated {updated_count} ingredients",
                    status_code=302
                )

        # GET 요청 처리 (폼 표시)
        async with self.session_maker() as session:
            # 고유 재료 이름 조회
            result = await session.execute(
                select(PendingIngredient.normalized_name).distinct().order_by(PendingIngredient.normalized_name)
            )
            unique_ingredients = [row[0] for row in result.fetchall() if row[0]]

        # 드롭다운 옵션 생성
        options_html = "".join([f'<option value="{ing}">{ing}</option>' for ing in unique_ingredients])

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>재료 이름 일괄 수정</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; margin-bottom: 30px; }}
                .form-group {{ margin-bottom: 20px; }}
                label {{ display: block; font-weight: bold; margin-bottom: 8px; color: #555; }}
                select, input {{ width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ddd; border-radius: 5px; }}
                select {{ background: white; }}
                .button-group {{ margin-top: 30px; display: flex; gap: 10px; }}
                button {{ flex: 1; padding: 12px; font-size: 16px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }}
                .submit-btn {{ background: #28a745; color: white; }}
                .submit-btn:hover {{ background: #218838; }}
                .back-btn {{ background: #6c757d; color: white; }}
                .back-btn:hover {{ background: #545b62; }}
                .info {{ background: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; margin-bottom: 20px; }}
                .warning {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✏️ 재료 이름 일괄 수정</h1>

                <div class="info">
                    <strong>💡 사용 방법:</strong> 변경할 재료 이름을 선택하고, 새로운 이름을 입력한 후 수정 버튼을 누르세요.
                </div>

                <div class="warning">
                    <strong>⚠️ 주의:</strong> 이 작업은 되돌릴 수 없습니다. 신중하게 진행하세요.
                </div>

                <form method="POST">
                    <div class="form-group">
                        <label for="old_name">변경할 재료 이름 선택:</label>
                        <select id="old_name" name="old_name" required>
                            <option value="">-- 재료를 선택하세요 --</option>
                            {options_html}
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="new_name">새로운 재료 이름:</label>
                        <input type="text" id="new_name" name="new_name" placeholder="예: 후추" required>
                    </div>

                    <div class="button-group">
                        <button type="submit" class="submit-btn">✅ 일괄 수정 실행</button>
                        <button type="button" class="back-btn" onclick="window.history.back()">← 취소</button>
                    </div>
                </form>

                <div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                    <strong>현재 고유 재료 개수:</strong> {len(unique_ingredients)}개
                </div>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    page_size = 50


class PendingRecipeAdmin(ModelView, model=PendingRecipe):
    """승인 대기 레시피 관리"""

    name = "레시피 검토함"
    name_plural = "레시피 검토함"
    icon = "menu_book"

    # 한글 컬럼 레이블
    column_labels = {
        "rcp_sno": "레시피 일련번호",
        "rcp_ttl": "레시피 제목",
        "ckg_nm": "요리명",
        "ckg_mtrl_cn": "재료 목록",
        "ckg_inbun_nm": "인분",
        "ckg_dodf_nm": "난이도",
        "ckg_time_nm": "조리 시간",
        "rcp_img_url": "레시피 이미지 URL",
        "approval_status": "승인 상태",
        "rejection_reason": "거부 사유",
        "import_batch_id": "배치 ID",
        "approved_by": "승인자",
        "approved_at": "승인일",
        "created_at": "등록일",
    }

    # 컬럼 표시
    column_list = [
        "rcp_sno",
        "import_batch_id",
        "rcp_ttl",
        "ckg_nm",
        "approval_status",
        "created_at",
    ]

    column_searchable_list = ["rcp_ttl", "ckg_nm"]
    column_sortable_list = ["rcp_sno", "rcp_ttl", "approval_status", "created_at"]
    column_default_sort = ("rcp_sno", False)

    # 필터 비활성화 (SQLAdmin 호환성 문제)
    # column_filters = []

    # 상세 페이지
    column_details_list = [
        "rcp_sno",
        "import_batch_id",
        "rcp_ttl",
        "ckg_nm",
        "ckg_mtrl_cn",
        "ckg_inbun_nm",
        "ckg_dodf_nm",
        "rcp_img_url",
        "approval_status",
        "rejection_reason",
        "approved_by",
        "approved_at",
        "created_at",
    ]

    # 인라인 편집
    can_create = False
    can_edit = True
    can_delete = True

    # 삭제 확인 메시지 커스터마이징
    delete_modal = True  # 삭제 모달 활성화
    delete_modal_template = "sqladmin/modals/delete.html"  # 기본 삭제 모달 템플릿

    form_columns = [
        "rcp_ttl",
        "ckg_nm",
        "ckg_mtrl_cn",
        "ckg_inbun_nm",  # 인분
        "ckg_dodf_nm",   # 난이도
        "ckg_time_nm",   # 조리 시간
        "rcp_img_url",   # 이미지 URL
        "approval_status",
        "rejection_reason",
    ]

    # 폼 필드 커스터마이징
    form_overrides = {
        "approval_status": SelectField,
    }

    form_args = {
        "approval_status": {
            "label": "승인 상태",
            "choices": [
                ("pending", "대기중"),
                ("approved", "승인"),
                ("rejected", "거부"),
            ],
            "validators": [DataRequired()],
            "description": "레시피 승인 상태를 선택하세요",
        }
    }

    # 포맷팅 (긴 텍스트 줄이기, 이모지 제거)
    column_formatters = {
        "ckg_mtrl_cn": lambda m, a: (m.ckg_mtrl_cn[:50] + "...") if m.ckg_mtrl_cn and len(m.ckg_mtrl_cn) > 50 else m.ckg_mtrl_cn,
        "approval_status": lambda m, a: {
            "pending": "대기중",
            "approved": "승인",
            "rejected": "거부",
        }.get(m.approval_status, m.approval_status),
    }

    # 삭제 액션
    @action(
        name="delete_selected",
        label="선택 항목 삭제",
        confirmation_message="선택한 레시피들을 삭제하시겠습니까?",
        add_in_detail=False,
        add_in_list=True,
    )
    async def delete_selected_action(self, request: Request) -> RedirectResponse:
        """선택된 대기 레시피 삭제"""
        from app.services.deletion_service import DeletionService
        from app.core.database import get_db
        import logging

        logger = logging.getLogger(__name__)

        pks = request.query_params.get("pks", "").split(",")
        if not pks or pks == [""]:
            return RedirectResponse(
                url=request.url_for("admin:list", identity=self.identity),
                status_code=302
            )

        async for session in get_db():
            result = await DeletionService.safe_delete(
                db=session,
                table_name="pending_recipes",
                record_ids=[int(pk) for pk in pks]
            )

            if result["success"]:
                logger.info(f"✅ 대기 레시피 {result['deleted_count']}개 삭제 완료")
            else:
                logger.error(f"❌ 대기 레시피 삭제 실패: {result.get('error')}")

            break

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    # 일괄 작업 액션
    @action(
        name="approve_selected",
        label="선택 항목 승인",
        confirmation_message="선택한 레시피들을 승인하시겠습니까?",
        add_in_detail=False,
        add_in_list=True,
    )
    async def approve_selected(self, request: Request) -> RedirectResponse:
        """선택된 레시피들을 일괄 승인"""
        pks = request.query_params.get("pks", "").split(",")
        if not pks or pks == [""]:
            return RedirectResponse(
                url=request.url_for("admin:list", identity=self.identity),
                status_code=302
            )

        async with self.session_maker() as session:
            for pk in pks:
                result = await session.execute(
                    select(PendingRecipe).where(PendingRecipe.rcp_sno == int(pk))
                )
                recipe = result.scalar_one_or_none()
                if recipe:
                    recipe.approval_status = "approved"
            await session.commit()

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    @action(
        name="reject_selected",
        label="선택 항목 거부",
        confirmation_message="선택한 레시피들을 거부하시겠습니까?",
        add_in_detail=False,
        add_in_list=True,
    )
    async def reject_selected(self, request: Request) -> RedirectResponse:
        """선택된 레시피들을 일괄 거부"""
        pks = request.query_params.get("pks", "").split(",")
        if not pks or pks == [""]:
            return RedirectResponse(
                url=request.url_for("admin:list", identity=self.identity),
                status_code=302
            )

        async with self.session_maker() as session:
            for pk in pks:
                result = await session.execute(
                    select(PendingRecipe).where(PendingRecipe.rcp_sno == int(pk))
                )
                recipe = result.scalar_one_or_none()
                if recipe:
                    recipe.approval_status = "rejected"
            await session.commit()

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    @action(
        name="approve_all_pending",
        label="대기중 항목 전체 승인",
        confirmation_message="현재 대기중인 모든 레시피를 승인하시겠습니까?",
        add_in_detail=False,
        add_in_list=True,
    )
    async def approve_all_pending(self, request: Request) -> RedirectResponse:
        """대기중인 모든 레시피를 일괄 승인"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(PendingRecipe).where(PendingRecipe.approval_status == "pending")
            )
            recipes = result.scalars().all()

            for recipe in recipes:
                recipe.approval_status = "approved"

            await session.commit()

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    page_size = 50


class IngredientCategoryAdmin(ModelView, model=IngredientCategory):
    """재료 카테고리 관리"""

    name = "재료 분류"
    name_plural = "재료 분류 관리"
    icon = "category"

    # 한글 컬럼 레이블
    column_labels = {
        "id": "ID",
        "code": "분류 코드",
        "name_ko": "한글명",
        "name_en": "영문명",
        "description": "설명",
        "display_order": "정렬 순서",
        "is_active": "활성화",
        "created_at": "등록일",
        "updated_at": "수정일",
    }

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

    # 필터 비활성화 (SQLAdmin 호환성 문제)
    # column_filters = []

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

    name = "시스템 설정"
    name_plural = "시스템 설정 관리"
    icon = "settings"

    # 한글 컬럼 레이블
    column_labels = {
        "id": "ID",
        "config_key": "설정 키",
        "config_value": "설정 값",
        "value_type": "데이터 타입",
        "category": "카테고리",
        "description": "설명",
        "is_editable": "수정 가능",
        "created_at": "등록일",
        "updated_at": "수정일",
    }

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

    # 필터 비활성화 (SQLAdmin 호환성 문제)
    # column_filters = []

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

    name = "오늘 뭐 먹지?"
    name_plural = "레시피 도서관"
    icon = "restaurant"

    # 한글 컬럼 레이블
    column_labels = {
        "rcp_sno": "레시피 일련번호",
        "rcp_ttl": "레시피 제목",
        "ckg_nm": "요리명",
        "ckg_mtrl_cn": "재료 목록",
        "ckg_inbun_nm": "재료 분량",
        "ckg_dodf_nm": "난이도",
        "ckg_time_nm": "조리 시간",
        "rcp_img_url": "레시피 이미지",
        "approval_status": "승인 상태",
        "import_batch_id": "배치 ID",
        "approved_by": "승인자",
        "approved_at": "승인일",
        "created_at": "등록일",
        "updated_at": "수정일",
    }

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

    # 필터 비활성화 (SQLAdmin 호환성 문제)
    # column_filters = []

    # 상세 페이지
    column_details_list = [
        "rcp_sno",
        "rcp_ttl",
        "ckg_nm",
        "ckg_mtrl_cn",
        "ckg_inbun_nm",
        "ckg_dodf_nm",
        "ckg_time_nm",
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
    can_delete = True  # 삭제 기능 활성화

    # 삭제 확인 메시지
    delete_modal = True
    delete_modal_template = "sqladmin/modals/delete.html"

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

    # 삭제 액션
    @action(
        name="delete_selected",
        label="선택 항목 삭제",
        confirmation_message="",  # 동적으로 생성
        add_in_detail=False,
        add_in_list=True,
    )
    async def delete_selected_action(self, request: Request) -> RedirectResponse:
        """선택된 레시피 삭제 (CASCADE 분석 포함)"""
        from app.services.deletion_service import DeletionService
        from app.core.database import get_db
        import logging

        logger = logging.getLogger(__name__)

        pks = request.query_params.get("pks", "").split(",")
        if not pks or pks == [""]:
            return RedirectResponse(
                url=request.url_for("admin:list", identity=self.identity),
                status_code=302
            )

        # 삭제 실행
        async for session in get_db():
            # CASCADE 영향 분석
            cascade_impact = await DeletionService.analyze_cascade_impact(
                db=session,
                table_name="recipes",
                record_ids=[int(pk) for pk in pks]
            )

            logger.info(f"레시피 삭제 CASCADE 분석: {cascade_impact}")

            # 삭제 실행
            result = await DeletionService.safe_delete(
                db=session,
                table_name="recipes",
                record_ids=[int(pk) for pk in pks]
            )

            if result["success"]:
                logger.info(f"✅ 레시피 {result['deleted_count']}개 삭제 완료")
            else:
                logger.error(f"❌ 레시피 삭제 실패: {result.get('error')}")

            break

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    page_size = 50


class IngredientAdmin(ModelView, model=Ingredient):
    """재료 관리 (기존 테이블 강화)"""

    name = "냉장고 식재료"
    name_plural = "식재료 창고"
    icon = "grass"

    # 한글 컬럼 레이블
    column_labels = {
        "id": "ID",
        "name": "재료명",
        "category": "분류",
        "approval_status": "승인 상태",
        "normalized_at": "정규화 일시",
        "created_at": "등록일",
        "updated_at": "수정일",
    }

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

    # 필터 비활성화 (SQLAdmin 호환성 문제)
    # column_filters = []

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
    can_delete = True  # 삭제 기능 활성화

    # 삭제 확인 메시지
    delete_modal = True
    delete_modal_template = "sqladmin/modals/delete.html"

    form_columns = [
        "name",
        "category",
        "approval_status",
    ]

    # 포맷팅
    column_formatters = {
        "category": lambda m, a: m.category.name_ko if m.category else "없음",
    }

    # 삭제 액션
    @action(
        name="delete_selected",
        label="선택 항목 삭제",
        confirmation_message="",
        add_in_detail=False,
        add_in_list=True,
    )
    async def delete_selected_action(self, request: Request) -> RedirectResponse:
        """선택된 재료 삭제 (CASCADE 분석 포함)"""
        from app.services.deletion_service import DeletionService
        from app.core.database import get_db
        import logging

        logger = logging.getLogger(__name__)

        pks = request.query_params.get("pks", "").split(",")
        if not pks or pks == [""]:
            return RedirectResponse(
                url=request.url_for("admin:list", identity=self.identity),
                status_code=302
            )

        async for session in get_db():
            cascade_impact = await DeletionService.analyze_cascade_impact(
                db=session,
                table_name="ingredients",
                record_ids=[int(pk) for pk in pks]
            )

            logger.info(f"재료 삭제 CASCADE 분석: {cascade_impact}")

            result = await DeletionService.safe_delete(
                db=session,
                table_name="ingredients",
                record_ids=[int(pk) for pk in pks]
            )

            if result["success"]:
                logger.info(f"✅ 재료 {result['deleted_count']}개 삭제 완료")
            else:
                logger.error(f"❌ 재료 삭제 실패: {result.get('error')}")

            break

        return RedirectResponse(
            url=request.url_for("admin:list", identity=self.identity),
            status_code=302
        )

    page_size = 50
