#!/usr/bin/env python3
"""
CSV 파일 분할 스크립트

TB_RECIPE_SEARCH-2.csv 파일을 헤더는 유지하면서
데이터를 2개 파일로 분할합니다.

Usage:
    python scripts/split_csv.py
"""
import os
import csv
from pathlib import Path


def detect_encoding(file_path: str):
    """파일의 인코딩을 감지"""
    encodings = [
        ('utf-8', 'strict'),
        ('euc-kr', 'replace'),  # 에러 문자 치환
        ('cp949', 'replace'),
        ('utf-8', 'replace'),
        ('latin-1', 'replace')
    ]

    for encoding, error_handling in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors=error_handling) as f:
                # 여러 줄 읽어서 안전성 확인
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
            print(f"🔍 감지된 인코딩: {encoding} (오류처리: {error_handling})")
            return encoding, error_handling
        except Exception:
            continue

    raise ValueError("지원되는 인코딩을 찾을 수 없습니다")


def split_csv_file(input_file: str, output_prefix: str, num_files: int = 2):
    """CSV 파일을 지정된 개수로 분할"""

    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_file}")

    print(f"📁 입력 파일: {input_file}")
    print(f"📊 파일 크기: {input_path.stat().st_size / (1024*1024):.1f} MB")

    # 인코딩 감지
    encoding, error_handling = detect_encoding(input_file)

    # 전체 행 수 계산 (헤더 제외)
    with open(input_file, 'r', encoding=encoding, errors=error_handling) as f:
        total_lines = sum(1 for _ in f) - 1  # 헤더 제외

    print(f"📈 총 데이터 행 수: {total_lines:,}")

    # 파일당 행 수 계산
    lines_per_file = total_lines // num_files
    remainder = total_lines % num_files

    print(f"🔄 {num_files}개 파일로 분할:")
    print(f"   - 파일당 기본 행 수: {lines_per_file:,}")
    if remainder > 0:
        print(f"   - 나머지 {remainder}행은 첫 번째 파일에 추가")

    # 헤더 읽기
    with open(input_file, 'r', encoding=encoding, errors=error_handling) as f:
        reader = csv.reader(f)
        header = next(reader)

        # 각 파일별로 분할
        for file_idx in range(num_files):
            output_file = f"{output_prefix}-{file_idx + 1}.csv"

            # 첫 번째 파일은 나머지 행도 포함
            current_lines = lines_per_file + (remainder if file_idx == 0 else 0)

            print(f"\n📝 생성 중: {output_file} ({current_lines:,} 행)")

            with open(output_file, 'w', encoding='utf-8', newline='') as out_f:
                writer = csv.writer(out_f)

                # 헤더 쓰기
                writer.writerow(header)

                # 데이터 쓰기
                for i in range(current_lines):
                    try:
                        row = next(reader)
                        writer.writerow(row)
                    except StopIteration:
                        print(f"⚠️  파일 끝에 도달: {i} 행 처리됨")
                        break

            # 생성된 파일 정보
            output_path = Path(output_file)
            file_size = output_path.stat().st_size / (1024*1024)
            print(f"   ✅ 완료: {file_size:.1f} MB")


def main():
    """메인 함수"""
    # 프로젝트 루트로 이동
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    input_file = "datas/TB_RECIPE_SEARCH-2.csv"
    output_prefix = "datas/TB_RECIPE_SEARCH-2"

    try:
        print("🔄 CSV 파일 분할 시작")
        print("=" * 50)

        split_csv_file(input_file, output_prefix, num_files=2)

        print("\n" + "=" * 50)
        print("✅ CSV 파일 분할 완료!")

        # 분할된 파일들 목록
        print("\n📂 생성된 파일들:")
        for i in range(1, 3):
            split_file = f"datas/TB_RECIPE_SEARCH-2-{i}.csv"
            if Path(split_file).exists():
                size = Path(split_file).stat().st_size / (1024*1024)
                lines = sum(1 for _ in open(split_file, 'r', encoding='utf-8'))
                print(f"   - {split_file}: {size:.1f} MB, {lines:,} 행 (헤더 포함)")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())