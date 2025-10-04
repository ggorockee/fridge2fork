#!/usr/bin/env python3
"""
CSV 파일 분석 스크립트


Usage:
    python scripts/analyze_csv.py

CSV 파일의 구조, 인코딩, 샘플 데이터를 분석합니다.
"""
import pandas as pd
import chardet
from pathlib import Path
import sys


def detect_encoding(file_path):
    """파일의 인코딩 감지"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(100000)  # 처음 100KB만 읽어서 인코딩 감지
        result = chardet.detect(raw_data)
        return result['encoding']


def analyze_csv_file(file_path):
    """CSV 파일 분석"""
    print(f"\n{'='*60}")
    print(f"📄 파일: {file_path.name}")
    print(f"📊 크기: {file_path.stat().st_size / 1024 / 1024:.2f} MB")

    # 인코딩 감지
    encoding = detect_encoding(file_path)
    print(f"🔤 인코딩: {encoding}")

    # 인코딩 시도 순서
    encodings_to_try = [encoding] if encoding else []
    encodings_to_try.extend(['EUC-KR', 'UTF-8', 'CP949', 'UTF-16'])

    df = None
    used_encoding = None

    for enc in encodings_to_try:
        try:
            df = pd.read_csv(file_path, encoding=enc, nrows=5)
            used_encoding = enc
            print(f"✅ {enc} 인코딩으로 읽기 성공")
            break
        except:
            continue

    if df is None:
        print(f"❌ 파일을 읽을 수 없습니다.")
        return

    # 전체 데이터 로드 (행 수 확인용)
    try:
        df_full = pd.read_csv(file_path, encoding=used_encoding)
        print(f"📝 총 행 수: {len(df_full):,}")
        print(f"📋 총 컬럼 수: {len(df_full.columns)}")

        # 컬럼 정보
        print(f"\n📊 컬럼 목록:")
        for i, col in enumerate(df_full.columns, 1):
            # 각 컬럼의 null이 아닌 값 개수
            non_null_count = df_full[col].notna().sum()
            null_pct = (1 - non_null_count / len(df_full)) * 100
            print(f"  {i:2d}. {col} ({df_full[col].dtype}) - NULL: {null_pct:.1f}%")

        # 샘플 데이터
        print(f"\n📄 샘플 데이터 (처음 3개 행):")
        print(df_full.head(3).to_string(index=False, max_colwidth=30))

        # 재료 관련 컬럼 분석
        ingredient_cols = [col for col in df_full.columns if '재료' in col or 'RCP_PARTS_DTLS' in col]
        if ingredient_cols:
            print(f"\n🥘 재료 관련 컬럼 분석:")
            for col in ingredient_cols:
                print(f"\n  {col}:")
                # 재료 샘플 출력
                sample_ingredients = df_full[col].dropna().head(3)
                for i, ing in enumerate(sample_ingredients, 1):
                    print(f"    예시 {i}: {ing[:100]}...")

        # 메모리 정리
        del df_full

    except Exception as e:
        print(f"❌ 전체 데이터 로드 실패: {e}")


def main():
    """메인 함수"""
    # 프로젝트 루트로 이동
    project_root = Path(__file__).parent.parent
    datas_dir = project_root / "datas"

    print("🔍 CSV 파일 분석 시작")
    print(f"📁 디렉토리: {datas_dir}")

    # CSV 파일 찾기
    csv_files = list(datas_dir.glob("TB_RECIPE_SEARCH*.csv"))

    if not csv_files:
        print("❌ CSV 파일을 찾을 수 없습니다.")
        return 1

    print(f"📊 찾은 CSV 파일: {len(csv_files)}개")

    # 각 파일 분석
    for csv_file in sorted(csv_files):
        try:
            analyze_csv_file(csv_file)
        except Exception as e:
            print(f"❌ {csv_file.name} 분석 실패: {e}")

    print(f"\n{'='*60}")
    print("✅ CSV 파일 분석 완료")

    return 0


if __name__ == "__main__":
    sys.exit(main())