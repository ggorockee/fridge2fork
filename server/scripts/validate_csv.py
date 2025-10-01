#!/usr/bin/env python3
"""
CSV 데이터 검증 스크립트 (Phase 5.1)

TB_RECIPE_SEARCH_241226_cleaned.csv 파일을 검증:
- 인코딩 확인 (UTF-8)
- 필수 컬럼 존재 확인
- 행 개수 확인
- 데이터 샘플링 확인

사용법:
    python scripts/validate_csv.py
    python scripts/validate_csv.py --file datas/custom.csv
"""
import sys
import csv
import chardet
from pathlib import Path
from typing import Dict, List

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 필수 컬럼 정의
REQUIRED_COLUMNS = [
    "RCP_SNO",      # 레시피 일련번호
    "RCP_TTL",      # 레시피 제목
    "CKG_NM",       # 요리명
    "CKG_MTRL_CN",  # 재료 내용 (핵심!)
]

# 권장 컬럼
RECOMMENDED_COLUMNS = [
    "CKG_INBUN_NM",  # 인분명
    "CKG_DODF_NM",   # 난이도명
    "CKG_CPCTY_CN",  # 조리법 내용
    "RCP_IMG_URL",   # 이미지 URL
]


def detect_encoding(file_path: Path) -> str:
    """파일 인코딩 감지"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(100000)  # 100KB 샘플
        result = chardet.detect(raw_data)
        return result['encoding']


def validate_csv_file(file_path: Path) -> Dict:
    """
    CSV 파일 검증

    Returns:
        dict: 검증 결과
    """
    print(f"\n🔍 CSV 파일 검증: {file_path}")
    print("=" * 80)

    results = {
        "file_path": str(file_path),
        "exists": file_path.exists(),
        "encoding": None,
        "total_rows": 0,
        "columns": [],
        "required_columns_present": False,
        "recommended_columns_present": [],
        "missing_columns": [],
        "sample_rows": [],
        "errors": [],
        "warnings": [],
    }

    # 1. 파일 존재 확인
    if not file_path.exists():
        results["errors"].append(f"파일이 존재하지 않습니다: {file_path}")
        return results

    print(f"✅ 파일 존재 확인")

    # 2. 인코딩 확인
    try:
        detected_encoding = detect_encoding(file_path)
        results["encoding"] = detected_encoding
        print(f"📝 감지된 인코딩: {detected_encoding}")

        if detected_encoding.lower() not in ['utf-8', 'utf8', 'ascii']:
            results["warnings"].append(
                f"UTF-8이 아닌 인코딩 감지됨: {detected_encoding}. "
                "CSV 파일은 UTF-8 인코딩을 권장합니다."
            )
    except Exception as e:
        results["errors"].append(f"인코딩 감지 실패: {e}")
        return results

    # 3. CSV 파일 읽기
    try:
        # UTF-8로 시도, 실패 시 감지된 인코딩 사용
        encoding = 'utf-8'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                csv.reader(f).__next__()
        except UnicodeDecodeError:
            encoding = detected_encoding
            results["warnings"].append(f"UTF-8 읽기 실패. {encoding} 인코딩 사용")

        with open(file_path, 'r', encoding=encoding, newline='') as f:
            reader = csv.DictReader(f)
            results["columns"] = reader.fieldnames or []

            # 4. 필수 컬럼 확인
            missing_required = [col for col in REQUIRED_COLUMNS if col not in results["columns"]]
            results["missing_columns"] = missing_required
            results["required_columns_present"] = len(missing_required) == 0

            if results["required_columns_present"]:
                print(f"✅ 필수 컬럼 존재 확인: {REQUIRED_COLUMNS}")
            else:
                print(f"❌ 필수 컬럼 누락: {missing_required}")
                results["errors"].append(f"필수 컬럼 누락: {missing_required}")

            # 5. 권장 컬럼 확인
            present_recommended = [col for col in RECOMMENDED_COLUMNS if col in results["columns"]]
            results["recommended_columns_present"] = present_recommended

            if present_recommended:
                print(f"✅ 권장 컬럼 존재: {present_recommended}")

            missing_recommended = [col for col in RECOMMENDED_COLUMNS if col not in results["columns"]]
            if missing_recommended:
                print(f"⚠️  권장 컬럼 누락: {missing_recommended}")
                results["warnings"].append(f"권장 컬럼 누락: {missing_recommended}")

            # 6. 행 개수 세기 및 샘플링
            rows = list(reader)
            results["total_rows"] = len(rows)
            print(f"📊 총 행 개수: {results['total_rows']:,}개")

            # 7. 샘플 데이터 저장 (처음 5개)
            sample_size = min(5, len(rows))
            results["sample_rows"] = [
                {
                    "row_number": i + 2,  # 헤더가 1행이므로 +2
                    "RCP_TTL": row.get("RCP_TTL", ""),
                    "CKG_NM": row.get("CKG_NM", ""),
                    "CKG_MTRL_CN": row.get("CKG_MTRL_CN", "")[:100],  # 처음 100자만
                }
                for i, row in enumerate(rows[:sample_size])
            ]

            print(f"\n📋 샘플 데이터 (처음 {sample_size}개):")
            for sample in results["sample_rows"]:
                print(f"  행 {sample['row_number']}: {sample['RCP_TTL']}")
                print(f"    - 요리명: {sample['CKG_NM']}")
                print(f"    - 재료: {sample['CKG_MTRL_CN'][:50]}...")

    except Exception as e:
        results["errors"].append(f"CSV 파일 읽기 실패: {e}")
        return results

    return results


def print_validation_summary(results: Dict):
    """검증 결과 요약 출력"""
    print("\n" + "=" * 80)
    print("📊 검증 결과 요약")
    print("=" * 80)

    # 성공/실패 판정
    if results["errors"]:
        print("❌ 검증 실패")
        print("\n오류:")
        for error in results["errors"]:
            print(f"  - {error}")
    else:
        print("✅ 검증 성공")

    # 경고
    if results["warnings"]:
        print("\n⚠️  경고:")
        for warning in results["warnings"]:
            print(f"  - {warning}")

    # 통계
    print("\n📊 파일 정보:")
    print(f"  - 경로: {results['file_path']}")
    print(f"  - 인코딩: {results['encoding']}")
    print(f"  - 총 행 개수: {results['total_rows']:,}개")
    print(f"  - 컬럼 개수: {len(results['columns'])}개")
    print(f"  - 필수 컬럼 존재: {'✅' if results['required_columns_present'] else '❌'}")

    print("\n" + "=" * 80)


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="CSV 데이터 검증 스크립트")
    parser.add_argument(
        "--file",
        type=str,
        default="datas/TB_RECIPE_SEARCH_241226_cleaned.csv",
        help="검증할 CSV 파일 경로"
    )
    args = parser.parse_args()

    csv_file = Path(args.file)

    # 검증 실행
    results = validate_csv_file(csv_file)

    # 결과 요약 출력
    print_validation_summary(results)

    # Exit code 설정
    exit_code = 0 if not results["errors"] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
