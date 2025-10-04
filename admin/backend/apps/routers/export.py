"""
📤📥 데이터 내보내기/가져오기 API 라우터
CSV/JSON/Excel 형식의 데이터 내보내기/가져오기, 백업/복원 기능 제공
"""
import csv
import json
import tempfile
import os
import gzip
import base64
from datetime import datetime
from io import StringIO, BytesIO
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, File, UploadFile
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect

from ..database import get_db
from ..schemas import (
    ExportRequest, ExportResponse, ImportRequest, ImportResponse,
    BackupRequest, BackupResponse, RestoreRequest, RestoreResponse,
    ImportValidationError
)
from ..models import Ingredient, Recipe, RecipeIngredient
from ..logging_config import get_logger

router = APIRouter(tags=["📤📥 데이터 내보내기/가져오기"])
logger = get_logger(__name__)

# 지원되는 테이블 매핑
TABLE_MODELS = {
    "ingredients": Ingredient,
    "recipes": Recipe,
    "recipe_ingredients": RecipeIngredient
}

# 지원되는 형식
SUPPORTED_FORMATS = ["csv", "json", "excel"]


# ===== 데이터 내보내기 =====

@router.get("/export/{table}/{format}")
async def export_data(
    table: str,
    format: str,
    columns: Optional[str] = Query(None, description="내보낼 컬럼 (쉼표로 구분)"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="제한 개수"),
    include_headers: bool = Query(True, description="헤더 포함 여부"),
    date_format: str = Query("ISO", description="날짜 형식"),
    db: Session = Depends(get_db)
):
    """📤 데이터 내보내기"""
    logger.info(f"📤 데이터 내보내기: {table}.{format}")

    # 유효성 검사
    if table not in TABLE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원되지 않는 테이블: {table}. 지원 테이블: {list(TABLE_MODELS.keys())}"
        )

    if format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원되지 않는 형식: {format}. 지원 형식: {SUPPORTED_FORMATS}"
        )

    try:
        model = TABLE_MODELS[table]

        # 데이터 조회
        query = db.query(model)
        if limit:
            query = query.limit(limit)

        records = query.all()

        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="내보낼 데이터가 없습니다"
            )

        # 컬럼 선택
        if columns:
            selected_columns = [col.strip() for col in columns.split(",")]
        else:
            # 모든 컬럼 포함
            inspector = inspect(model)
            selected_columns = [column.name for column in inspector.columns]

        # 데이터 변환
        data = []
        for record in records:
            row = {}
            for column in selected_columns:
                if hasattr(record, column):
                    value = getattr(record, column)
                    # 날짜 형식 처리
                    if isinstance(value, datetime):
                        if date_format == "ISO":
                            value = value.isoformat()
                        else:
                            value = value.strftime("%Y-%m-%d %H:%M:%S")
                    row[column] = value
            data.append(row)

        # 형식별 내보내기
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{table}_{timestamp}.{format}"

        if format == "csv":
            return export_csv(data, filename, include_headers)
        elif format == "json":
            return export_json(data, filename)
        elif format == "excel":
            return export_excel(data, filename, include_headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 데이터 내보내기 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터 내보내기 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/export/custom", response_model=ExportResponse)
async def export_custom_data(
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """📤 사용자 정의 데이터 내보내기"""
    logger.info(f"📤 사용자 정의 내보내기: {request.table}.{request.format}")

    try:
        if request.table not in TABLE_MODELS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원되지 않는 테이블: {request.table}"
            )

        if request.format not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원되지 않는 형식: {request.format}"
            )

        model = TABLE_MODELS[request.table]
        query = db.query(model)

        # 필터 적용
        if request.filters:
            for field, value in request.filters.items():
                if hasattr(model, field):
                    if isinstance(value, list):
                        query = query.filter(getattr(model, field).in_(value))
                    else:
                        query = query.filter(getattr(model, field) == value)

        records = query.all()
        record_count = len(records)

        # 컬럼 선택
        if request.columns:
            selected_columns = request.columns
        else:
            inspector = inspect(model)
            selected_columns = [column.name for column in inspector.columns]

        # 데이터 변환
        data = []
        for record in records:
            row = {}
            for column in selected_columns:
                if hasattr(record, column):
                    value = getattr(record, column)
                    if isinstance(value, datetime):
                        if request.date_format == "ISO":
                            value = value.isoformat()
                        else:
                            value = value.strftime("%Y-%m-%d %H:%M:%S")
                    row[column] = value
            data.append(row)

        # 임시 파일 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{request.table}_{timestamp}.{request.format}"

        with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix=f".{request.format}") as temp_file:
            file_path = temp_file.name

            if request.format == "csv":
                write_csv_to_file(data, file_path, request.include_headers)
            elif request.format == "json":
                write_json_to_file(data, file_path)
            elif request.format == "excel":
                write_excel_to_file(data, file_path, request.include_headers)

        file_size = os.path.getsize(file_path)

        # 파일을 base64로 인코딩하여 다운로드 URL 생성 (실제로는 별도 저장소 사용 권장)
        download_url = f"/download/{os.path.basename(file_path)}"

        return ExportResponse(
            success=True,
            message=f"데이터 내보내기가 완료되었습니다",
            download_url=download_url,
            file_name=filename,
            file_size_bytes=file_size,
            record_count=record_count,
            exported_at=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 사용자 정의 내보내기 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 정의 내보내기 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 데이터 가져오기 =====

@router.post("/import/{table}/{format}", response_model=ImportResponse)
async def import_data(
    table: str,
    format: str,
    file: UploadFile = File(...),
    skip_duplicates: bool = Form(True),
    validate_only: bool = Form(False),
    auto_map_columns: bool = Form(True),
    db: Session = Depends(get_db)
):
    """📥 데이터 가져오기"""
    logger.info(f"📥 데이터 가져오기: {table}.{format}")

    try:
        if table not in TABLE_MODELS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원되지 않는 테이블: {table}"
            )

        if format not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원되지 않는 형식: {format}"
            )

        # 파일 읽기
        content = await file.read()

        # 형식별 파싱
        if format == "csv":
            data = parse_csv_data(content)
        elif format == "json":
            data = parse_json_data(content)
        elif format == "excel":
            data = parse_excel_data(content)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원되지 않는 형식: {format}"
            )

        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="가져올 데이터가 없습니다"
            )

        # 데이터 검증
        validation_errors = validate_import_data(table, data, auto_map_columns)

        if validation_errors and not validate_only:
            # 심각한 오류가 있으면 가져오기 중단
            critical_errors = [err for err in validation_errors if err.severity == "error"]
            if critical_errors:
                return ImportResponse(
                    success=False,
                    message=f"데이터 검증 실패: {len(critical_errors)}개의 오류가 있습니다",
                    total_rows=len(data),
                    imported_rows=0,
                    skipped_rows=0,
                    error_rows=len(critical_errors),
                    validation_errors=validation_errors,
                    imported_ids=[],
                    import_time_ms=0,
                    imported_at=datetime.now()
                )

        if validate_only:
            return ImportResponse(
                success=len(validation_errors) == 0,
                message=f"데이터 검증 완료: {len(validation_errors)}개의 문제 발견",
                total_rows=len(data),
                imported_rows=0,
                skipped_rows=0,
                error_rows=len(validation_errors),
                validation_errors=validation_errors,
                imported_ids=[],
                import_time_ms=0,
                imported_at=datetime.now()
            )

        # 실제 가져오기
        import_result = import_data_to_db(table, data, skip_duplicates, db)

        return import_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 데이터 가져오기 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터 가져오기 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 백업 및 복원 =====

@router.post("/export/backup", response_model=BackupResponse)
async def create_backup(
    request: BackupRequest,
    db: Session = Depends(get_db)
):
    """💾 데이터베이스 백업"""
    logger.info(f"💾 데이터베이스 백업 시작")

    try:
        backup_data = {}
        tables_included = []

        # 백업할 테이블 결정
        if request.tables:
            tables_to_backup = [t for t in request.tables if t in TABLE_MODELS]
        else:
            tables_to_backup = list(TABLE_MODELS.keys())

        # 각 테이블 데이터 수집
        for table_name in tables_to_backup:
            model = TABLE_MODELS[table_name]
            records = db.query(model).all()

            table_data = []
            for record in records:
                # 모델을 딕셔너리로 변환
                record_dict = {}
                for column in inspect(model).columns:
                    value = getattr(record, column.name)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    record_dict[column.name] = value
                table_data.append(record_dict)

            backup_data[table_name] = table_data
            tables_included.append(table_name)

        # 스키마 정보 포함
        if request.include_schema:
            backup_data["_schema"] = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "tables": tables_included,
                "record_counts": {table: len(backup_data[table]) for table in tables_included}
            }

        # JSON으로 직렬화
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)

        # 압축
        if request.compress:
            backup_bytes = backup_json.encode('utf-8')
            compressed = gzip.compress(backup_bytes)
            final_data = base64.b64encode(compressed).decode('ascii')
            file_extension = "json.gz.b64"
        else:
            final_data = backup_json
            file_extension = "json"

        # 암호화 (간단한 base64 인코딩으로 대체)
        if request.encryption_key:
            # 실제로는 적절한 암호화 알고리즘 사용
            final_data = base64.b64encode(final_data.encode('utf-8')).decode('ascii')
            file_extension += ".enc"

        # 백업 파일 저장
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_name = f"{backup_id}.{file_extension}"

        # 임시 파일에 저장 (실제로는 별도 저장소 사용)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=f".{file_extension}") as temp_file:
            temp_file.write(final_data)
            file_path = temp_file.name

        file_size = os.path.getsize(file_path)

        return BackupResponse(
            success=True,
            message=f"데이터베이스 백업이 완료되었습니다",
            backup_id=backup_id,
            file_name=file_name,
            file_size_bytes=file_size,
            tables_included=tables_included,
            backup_time_ms=1000,  # 실제 시간 측정 필요
            created_at=datetime.now()
        )

    except Exception as e:
        logger.error(f"❌ 데이터베이스 백업 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터베이스 백업 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/import/restore", response_model=RestoreResponse)
async def restore_backup(
    request: RestoreRequest,
    db: Session = Depends(get_db)
):
    """🔄 데이터베이스 복원"""
    logger.info("🔄 데이터베이스 복원 시작")

    try:
        # 백업 데이터 복호화 및 압축 해제
        backup_data_str = request.backup_data

        # 암호화된 경우 복호화
        if request.decryption_key:
            try:
                backup_data_str = base64.b64decode(backup_data_str).decode('utf-8')
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="백업 데이터 복호화에 실패했습니다"
                )

        # 압축된 경우 압축 해제
        try:
            # base64 디코딩 시도
            compressed_data = base64.b64decode(backup_data_str)
            # gzip 압축 해제 시도
            backup_data_str = gzip.decompress(compressed_data).decode('utf-8')
        except Exception:
            # 압축되지 않은 데이터로 간주
            pass

        # JSON 파싱
        try:
            backup_data = json.loads(backup_data_str)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"백업 데이터 파싱 실패: {str(e)}"
            )

        # 복원 전 검증
        if request.validate_before_restore:
            validation_errors = validate_backup_data(backup_data)
            if validation_errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"백업 데이터 검증 실패: {validation_errors}"
                )

        # 복원할 테이블 결정
        available_tables = [t for t in backup_data.keys() if t != "_schema" and t in TABLE_MODELS]
        if request.tables:
            tables_to_restore = [t for t in request.tables if t in available_tables]
        else:
            tables_to_restore = available_tables

        restored_tables = []
        total_records = 0

        # 각 테이블 복원
        for table_name in tables_to_restore:
            if table_name not in backup_data:
                continue

            model = TABLE_MODELS[table_name]
            table_data = backup_data[table_name]

            # 기존 데이터 삭제 (덮어쓰기 모드)
            if request.overwrite_existing:
                db.query(model).delete()

            # 데이터 삽입
            for record_data in table_data:
                # datetime 문자열을 다시 datetime 객체로 변환
                for key, value in record_data.items():
                    if isinstance(value, str) and "T" in value:
                        try:
                            record_data[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        except ValueError:
                            pass

                # 중복 확인
                if not request.overwrite_existing:
                    primary_key = inspect(model).primary_key[0].name
                    existing = db.query(model).filter(
                        getattr(model, primary_key) == record_data[primary_key]
                    ).first()
                    if existing:
                        continue

                # 새 레코드 생성
                new_record = model(**record_data)
                db.add(new_record)

            restored_tables.append(table_name)
            total_records += len(table_data)

        # 커밋
        db.commit()

        return RestoreResponse(
            success=True,
            message=f"데이터베이스 복원이 완료되었습니다",
            restored_tables=restored_tables,
            total_records=total_records,
            restore_time_ms=1000,  # 실제 시간 측정 필요
            restored_at=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 데이터베이스 복원 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터베이스 복원 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 유틸리티 함수 =====

def export_csv(data: List[Dict], filename: str, include_headers: bool) -> StreamingResponse:
    """CSV 내보내기"""
    output = StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        if include_headers:
            writer.writeheader()
        writer.writerows(data)

    output.seek(0)
    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    return response


def export_json(data: List[Dict], filename: str) -> StreamingResponse:
    """JSON 내보내기"""
    json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    response = StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    return response


def export_excel(data: List[Dict], filename: str, include_headers: bool) -> StreamingResponse:
    """Excel 내보내기"""
    try:
        import pandas as pd
        df = pd.DataFrame(data)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, header=include_headers)

        output.seek(0)
        response = StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        return response
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Excel 내보내기를 위해 pandas와 openpyxl이 필요합니다"
        )


def write_csv_to_file(data: List[Dict], file_path: str, include_headers: bool):
    """CSV 파일 작성"""
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            if include_headers:
                writer.writeheader()
            writer.writerows(data)


def write_json_to_file(data: List[Dict], file_path: str):
    """JSON 파일 작성"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def write_excel_to_file(data: List[Dict], file_path: str, include_headers: bool):
    """Excel 파일 작성"""
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False, header=include_headers)
    except ImportError:
        raise Exception("Excel 파일 작성을 위해 pandas와 openpyxl이 필요합니다")


def parse_csv_data(content: bytes) -> List[Dict]:
    """CSV 데이터 파싱"""
    content_str = content.decode('utf-8')
    reader = csv.DictReader(StringIO(content_str))
    return list(reader)


def parse_json_data(content: bytes) -> List[Dict]:
    """JSON 데이터 파싱"""
    content_str = content.decode('utf-8')
    data = json.loads(content_str)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]
    else:
        raise ValueError("JSON 데이터는 리스트 또는 딕셔너리여야 합니다")


def parse_excel_data(content: bytes) -> List[Dict]:
    """Excel 데이터 파싱"""
    try:
        import pandas as pd
        df = pd.read_excel(BytesIO(content))
        return df.to_dict('records')
    except ImportError:
        raise Exception("Excel 파일 파싱을 위해 pandas와 openpyxl이 필요합니다")


def validate_import_data(table: str, data: List[Dict], auto_map_columns: bool) -> List[ImportValidationError]:
    """데이터 검증"""
    errors = []
    model = TABLE_MODELS[table]
    inspector = inspect(model)

    required_columns = [col.name for col in inspector.columns if not col.nullable and not col.default]
    available_columns = [col.name for col in inspector.columns]

    for row_idx, row in enumerate(data):
        # 필수 컬럼 검사
        for required_col in required_columns:
            if required_col not in row or row[required_col] is None:
                errors.append(ImportValidationError(
                    row=row_idx + 1,
                    column=required_col,
                    value=str(row.get(required_col, "")),
                    error=f"필수 컬럼이 누락되었습니다",
                    severity="error"
                ))

        # 존재하지 않는 컬럼 검사
        for col in row.keys():
            if col not in available_columns:
                errors.append(ImportValidationError(
                    row=row_idx + 1,
                    column=col,
                    value=str(row[col]),
                    error=f"존재하지 않는 컬럼입니다",
                    severity="warning"
                ))

    return errors


def import_data_to_db(table: str, data: List[Dict], skip_duplicates: bool, db: Session) -> ImportResponse:
    """데이터베이스에 데이터 가져오기"""
    start_time = datetime.now()
    model = TABLE_MODELS[table]

    imported_rows = 0
    skipped_rows = 0
    error_rows = 0
    imported_ids = []
    validation_errors = []

    try:
        for row_idx, row_data in enumerate(data):
            try:
                # 중복 검사 (이름 기준으로 간단히)
                if skip_duplicates and hasattr(model, 'name'):
                    existing = db.query(model).filter(
                        getattr(model, 'name') == row_data.get('name')
                    ).first()
                    if existing:
                        skipped_rows += 1
                        continue

                # 새 레코드 생성
                # ID 필드 제거 (자동 생성)
                clean_data = {k: v for k, v in row_data.items()
                             if k not in ['ingredient_id', 'recipe_id'] and v is not None}

                new_record = model(**clean_data)
                db.add(new_record)
                db.flush()  # ID 얻기

                imported_rows += 1

                # ID 수집
                if hasattr(new_record, 'ingredient_id'):
                    imported_ids.append(new_record.ingredient_id)
                elif hasattr(new_record, 'recipe_id'):
                    imported_ids.append(new_record.recipe_id)

            except Exception as e:
                error_rows += 1
                validation_errors.append(ImportValidationError(
                    row=row_idx + 1,
                    column="전체",
                    value=str(row_data),
                    error=str(e),
                    severity="error"
                ))

        db.commit()

        end_time = datetime.now()
        import_time_ms = int((end_time - start_time).total_seconds() * 1000)

        return ImportResponse(
            success=error_rows == 0,
            message=f"데이터 가져오기 완료: {imported_rows}개 성공, {error_rows}개 실패, {skipped_rows}개 건너뛰기",
            total_rows=len(data),
            imported_rows=imported_rows,
            skipped_rows=skipped_rows,
            error_rows=error_rows,
            validation_errors=validation_errors,
            imported_ids=imported_ids,
            import_time_ms=import_time_ms,
            imported_at=end_time
        )

    except Exception as e:
        db.rollback()
        raise e


def validate_backup_data(backup_data: Dict) -> List[str]:
    """백업 데이터 검증"""
    errors = []

    if "_schema" not in backup_data:
        errors.append("스키마 정보가 없습니다")

    for table_name in backup_data.keys():
        if table_name.startswith("_"):
            continue
        if table_name not in TABLE_MODELS:
            errors.append(f"지원되지 않는 테이블: {table_name}")

    return errors