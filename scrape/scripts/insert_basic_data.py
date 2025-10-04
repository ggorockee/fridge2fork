#!/usr/bin/env python3
"""
기본 카테고리 데이터 삽입 스크립트

Usage:
    python scripts/insert_basic_data.py

Prerequisites:
    - DATABASE_URL이 .env 파일에 설정되어 있어야 함
    - PostgreSQL 서버가 실행 중이어야 함
    - 마이그레이션이 실행되어 테이블이 생성되어 있어야 함
"""
import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# 새 스키마에서는 cooking_categories 테이블을 사용하므로
# 이 스크립트는 더 이상 필요하지 않습니다.
# docs/sql/02_insert_categories.sql 이 동일한 역할을 수행합니다.
import sys
print("ℹ️ 새 스키마에서는 docs/sql/02_insert_categories.sql을 사용하세요.")
sys.exit(0)

# 환경변수 로드
load_dotenv()

# 모든 기능이 SQL 스크립트로 대체되었으므로 더 이상 함수 정의가 필요하지 않습니다.