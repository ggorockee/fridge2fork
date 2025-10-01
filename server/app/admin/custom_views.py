"""
SQLAdmin 커스텀 뷰 - CSV 업로드 페이지
"""
import io
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from sqladmin import BaseView, expose
import httpx


class CSVUploadView(BaseView):
    """CSV 파일 업로드 커스텀 뷰"""

    name = "CSV Upload"
    icon = "fa-solid fa-upload"

    @expose("/csv-upload", methods=["GET", "POST"])
    async def upload_page(self, request: Request) -> HTMLResponse:
        """CSV 업로드 페이지"""
        upload_result = None
        error_message = None

        if request.method == "POST":
            try:
                # multipart/form-data를 max_files 제한으로 처리
                # 임시 디렉토리 문제 회피: 파일을 메모리에서 직접 읽음
                form = await request.form()
                file = form.get("csv_file")

                if not file or not hasattr(file, 'filename'):
                    error_message = "파일을 선택해주세요"
                elif not file.filename.endswith('.csv'):
                    error_message = "CSV 파일만 업로드 가능합니다"
                else:
                    # 파일 내용을 메모리에서 직접 읽기 (임시 파일 회피)
                    file_content = await file.read()

                    # 파일 크기 검증 (10MB 제한)
                    if len(file_content) > 10 * 1024 * 1024:
                        error_message = "파일 크기가 10MB를 초과합니다"
                    else:
                        # FastAPI 엔드포인트로 파일 전송
                        async with httpx.AsyncClient() as client:
                            # BytesIO로 파일 객체 생성하여 전송
                            import io
                            files = {
                                'file': (
                                    file.filename,
                                    io.BytesIO(file_content),
                                    'text/csv'
                                )
                            }

                            # 같은 앱 내부 API 호출
                            response = await client.post(
                                "http://localhost:8000/fridge2fork/v1/admin/batches/upload",
                                files=files,
                                timeout=60.0
                            )

                            if response.status_code == 200:
                                upload_result = response.json()
                            else:
                                error_message = f"업로드 실패: {response.text}"

            except Exception as e:
                error_message = f"오류 발생: {str(e)}"

        # HTML 템플릿 렌더링 (SQLAdmin TemplateResponse 형식)
        return await self.templates.TemplateResponse(
            request,
            "csv_upload.html",
            {
                "upload_result": upload_result,
                "error_message": error_message,
            }
        )
