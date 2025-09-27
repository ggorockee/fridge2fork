#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 실행 스크립트
"""
import os
import sys
import asyncio
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# 환경변수 로드
load_dotenv()

async def run_migration():
    """데이터베이스 마이그레이션 실행"""
    
    # DATABASE_URL 설정
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        db = os.getenv('POSTGRES_DB')
        user = os.getenv('POSTGRES_USER')
        password = os.getenv('POSTGRES_PASSWORD')
        server = os.getenv('POSTGRES_SERVER')
        port = os.getenv('POSTGRES_PORT')
        
        if all([db, user, password, server, port]):
            database_url = f"postgresql://{user}:{password}@{server}:{port}/{db}"
            os.environ['DATABASE_URL'] = database_url
        else:
            print("❌ DATABASE_URL을 설정할 수 없습니다.")
            return
    
    # PostgreSQL URL을 asyncpg용으로 변환
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    print(f"🔗 데이터베이스 연결: {database_url.split('@')[0]}@***")
    
    try:
        # 엔진 생성
        engine = create_async_engine(database_url, echo=True)
        
        async with engine.begin() as conn:
            # Alembic 마이그레이션 실행
            print("📚 Alembic 마이그레이션 실행 중...")
            
            # Alembic 명령어 실행을 위해 subprocess 사용
            import subprocess
            
            # 환경변수 설정
            env = os.environ.copy()
            env['DATABASE_URL'] = database_url.replace('postgresql+asyncpg://', 'postgresql://')
            
            # 마이그레이션 실행
            result = subprocess.run([
                'python', '-m', 'alembic', 'upgrade', 'head'
            ], env=env, cwd=project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 마이그레이션 성공!")
                print(result.stdout)
            else:
                print("❌ 마이그레이션 실패!")
                print(result.stderr)
                
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(run_migration())
