#!/bin/bash

# 🚀 Fridge2Fork Admin API Entrypoint Script
# 환경 변수에 따른 실행 명령 분기

set -e  # 오류 발생 시 스크립트 종료

echo "🐳 Fridge2Fork Admin API 컨테이너 시작 중..."

# 환경 변수 기본값 설정
ENVIRONMENT=${ENVIRONMENT:-production}

# 환경에 따른 실행 명령 분기
if [ "$ENVIRONMENT" = "development" ]; then
    echo "🛠️ 개발 모드로 시작합니다 (uvicorn)"
    echo "📍 호스트: 0.0.0.0, 포트: 8000, 리로드: 활성화"
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "🏭 운영 모드로 시작합니다 (gunicorn)"
    echo "📍 워커: 2개, 호스트: 0.0.0.0, 포트: 8000"
    exec gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
fi
