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
        name="ingredient_warehouse",
        label="🏪 식재료 창고",
        add_in_detail=False,
        add_in_list=True,
    )
    async def ingredient_warehouse(self, request: Request):
        """식재료 창고 - 탭 기반 통합 페이지 (재료 목록 + 일괄 수정)"""
        from starlette.responses import HTMLResponse

        # GET 요청 처리 (탭 페이지 표시)
        active_tab = request.query_params.get("tab", "list")

        async with self.session_maker() as session:
            result = await session.execute(
                select(PendingIngredient.normalized_name).distinct().order_by(PendingIngredient.normalized_name)
            )
            unique_ingredients = [row[0] for row in result.fetchall() if row[0]]

        ingredients_text = ", ".join(unique_ingredients)
        options_html = "".join([f'<option value="{ing}">{ing}</option>' for ing in unique_ingredients])

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>🏪 식재료 창고</title>
            <style>
                * {{ box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background: #f5f7fa; margin: 0; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px;
                            box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }}

                /* Header */
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 32px; font-weight: 600; }}
                .header .stats {{ margin-top: 10px; opacity: 0.9; font-size: 16px; }}

                /* Tabs */
                .tabs {{ display: flex; border-bottom: 2px solid #e2e8f0; background: #f8fafc; }}
                .tab {{ flex: 1; padding: 18px 24px; cursor: pointer; border: none; background: transparent;
                       font-size: 16px; font-weight: 600; color: #64748b; transition: all 0.3s;
                       border-bottom: 3px solid transparent; }}
                .tab:hover {{ background: #f1f5f9; color: #475569; }}
                .tab.active {{ color: #667eea; border-bottom-color: #667eea; background: white; }}

                /* Tab Content */
                .tab-content {{ display: none; padding: 40px; }}
                .tab-content.active {{ display: block; }}

                /* List Tab */
                .copy-area {{ background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 8px; padding: 20px; }}
                .copy-area textarea {{ width: 100%; height: 400px; font-family: 'Courier New', monospace;
                                      padding: 16px; border: none; background: white; border-radius: 6px;
                                      font-size: 14px; line-height: 1.6; resize: vertical; }}
                .button-group {{ margin-top: 20px; display: flex; gap: 12px; }}
                button {{ padding: 14px 28px; font-size: 16px; border: none; border-radius: 8px;
                         cursor: pointer; font-weight: 600; transition: all 0.3s; }}
                .copy-btn {{ background: #667eea; color: white; flex: 1; }}
                .copy-btn:hover {{ background: #5568d3; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }}
                .back-btn {{ background: #6c757d; color: white; }}
                .back-btn:hover {{ background: #5a6268; }}

                /* Edit Tab */
                .edit-form {{ max-width: 700px; margin: 0 auto; }}
                .info-box {{ background: #e0e7ff; padding: 16px; border-left: 4px solid #667eea;
                           border-radius: 6px; margin-bottom: 24px; }}
                .warning-box {{ background: #fef3c7; padding: 16px; border-left: 4px solid #f59e0b;
                              border-radius: 6px; margin-bottom: 24px; }}
                .form-group {{ margin-bottom: 24px; }}
                .form-group label {{ display: block; font-weight: 600; margin-bottom: 10px;
                                    color: #1e293b; font-size: 15px; }}
                .form-group select,
                .form-group input {{ width: 100%; padding: 14px; font-size: 16px; border: 2px solid #e2e8f0;
                                    border-radius: 8px; transition: all 0.3s; }}
                .form-group select:focus,
                .form-group input:focus {{ outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }}
                .submit-btn {{ background: #10b981; color: white; width: 100%; }}
                .submit-btn:hover {{ background: #059669; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(16,185,129,0.4); }}

                /* Success Animation */
                @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
                .fade-in {{ animation: fadeIn 0.4s ease-out; }}
            </style>
        </head>
        <body>
            <div class="container fade-in">
                <div class="header">
                    <h1>🏪 식재료 창고</h1>
                    <div class="stats">총 고유 재료 개수: <strong>{len(unique_ingredients)}개</strong></div>
                </div>

                <div class="tabs">
                    <button class="tab {'active' if active_tab == 'list' else ''}" onclick="switchTab('list')">
                        📋 재료 목록 보기
                    </button>
                    <button class="tab {'active' if active_tab == 'edit' else ''}" onclick="switchTab('edit')">
                        ✏️ 재료 이름 수정
                    </button>
                </div>

                <!-- Tab 1: 재료 목록 -->
                <div id="listTab" class="tab-content {'active' if active_tab == 'list' else ''}">
                    <h2 style="margin-top: 0; color: #1e293b;">📋 쉼표로 구분된 재료 목록</h2>
                    <p style="color: #64748b; margin-bottom: 20px;">
                        아래 텍스트 영역의 내용을 복사하여 다른 곳에 붙여넣을 수 있습니다.
                    </p>
                    <div class="copy-area">
                        <textarea id="ingredientsText" readonly>{ingredients_text}</textarea>
                    </div>
                    <div class="button-group">
                        <button class="copy-btn" onclick="copyToClipboard()">
                            📋 클립보드에 복사
                        </button>
                        <button class="back-btn" onclick="window.history.back()">
                            ← 돌아가기
                        </button>
                    </div>
                </div>

                <!-- Tab 2: 일괄 수정 -->
                <div id="editTab" class="tab-content {'active' if active_tab == 'edit' else ''}">
                    <div class="edit-form">
                        <h2 style="margin-top: 0; color: #1e293b;">✏️ 재료 이름 일괄 수정</h2>

                        <div class="info-box">
                            <strong>💡 사용 방법</strong><br>
                            변경할 재료 이름을 선택하고, 새로운 이름을 입력한 후 수정 버튼을 누르세요.
                        </div>

                        <div class="warning-box">
                            <strong>⚠️ 주의사항</strong><br>
                            이 작업은 되돌릴 수 없습니다. 신중하게 진행하세요.
                        </div>

                        <form id="bulkEditForm">
                            <div class="form-group">
                                <label for="old_name">변경할 재료 이름 선택:</label>
                                <select id="old_name" name="old_name" required>
                                    <option value="">-- 재료를 선택하세요 --</option>
                                    {options_html}
                                </select>
                            </div>

                            <div class="form-group">
                                <label for="new_name">새로운 재료 이름:</label>
                                <input type="text" id="new_name" name="new_name"
                                       placeholder="예: 후추" required>
                            </div>

                            <div class="button-group">
                                <button type="submit" class="submit-btn">
                                    ✅ 일괄 수정 실행
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>

            <script>
                function switchTab(tabName) {{
                    // Hide all tabs
                    document.querySelectorAll('.tab-content').forEach(tab => {{
                        tab.classList.remove('active');
                    }});
                    document.querySelectorAll('.tab').forEach(tab => {{
                        tab.classList.remove('active');
                    }});

                    // Show selected tab
                    if (tabName === 'list') {{
                        document.getElementById('listTab').classList.add('active');
                        document.querySelector('.tab:nth-child(1)').classList.add('active');
                        window.history.replaceState(null, null, '?tab=list');
                    }} else {{
                        document.getElementById('editTab').classList.add('active');
                        document.querySelector('.tab:nth-child(2)').classList.add('active');
                        window.history.replaceState(null, null, '?tab=edit');
                    }}
                }}

                function copyToClipboard() {{
                    const text = document.getElementById('ingredientsText');
                    text.select();
                    text.setSelectionRange(0, 99999); // For mobile devices

                    try {{
                        document.execCommand('copy');
                        alert('✅ 클립보드에 복사되었습니다!');
                    }} catch (err) {{
                        alert('❌ 복사 실패: ' + err);
                    }}
                }}

                // 일괄 수정 폼 제출 처리
                document.getElementById('bulkEditForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();

                    const oldName = document.getElementById('old_name').value;
                    const newName = document.getElementById('new_name').value;

                    if (!oldName || !newName) {{
                        alert('⚠️ 모든 필드를 입력해주세요.');
                        return;
                    }}

                    const submitBtn = this.querySelector('.submit-btn');
                    submitBtn.disabled = true;
                    submitBtn.textContent = '⏳ 처리 중...';

                    try {{
                        const response = await fetch(
                            `/fridge2fork/v1/admin/ingredients/bulk-rename?old_name=${{encodeURIComponent(oldName)}}&new_name=${{encodeURIComponent(newName)}}`,
                            {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json'
                                }}
                            }}
                        );

                        const data = await response.json();

                        if (response.ok) {{
                            alert(`✅ ${{data.updated_count}}개 재료를 "${{oldName}}" → "${{newName}}"로 수정했습니다!`);
                            window.location.reload();
                        }} else {{
                            alert(`❌ 오류: ${{data.detail || '알 수 없는 오류'}}`);
                        }}
                    }} catch (error) {{
                        alert(`❌ 네트워크 오류: ${{error.message}}`);
                    }} finally {{
                        submitBtn.disabled = false;
                        submitBtn.textContent = '✅ 일괄 수정 실행';
                    }}
                }});
            </script>
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
