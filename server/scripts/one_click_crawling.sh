#!/bin/bash

# 🚀 Fridge2Fork 원클릭 전체 크롤링 스크립트
# 사용법: ./scripts/one_click_crawling.sh [모드]
# 모드: safe, normal, fast, turbo, extreme

set -e  # 오류 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 로고 출력
echo -e "${CYAN}"
cat << "EOF"
 ______     _     _            ___   ______           _    
|  ____|   (_)   | |          |__ \ |  ____|         | |   
| |__ _ __  _  __| | __ _  ___    ) || |__ ___  _ __ | | __
|  __| '__|(_)/ _` |/ _` |/ _ \  / / |  __/ _ \| '__|| |/ /
| |  | |   | | (_| | (_| |  __/ / /_ | | | (_) | |   |   < 
|_|  |_|   |_|\__,_|\__, |\___||____||_|  \___/|_|   |_|\_\
                     __/ |                                 
                    |___/                                  
EOF
echo -e "${NC}"

echo -e "${PURPLE}🍳 Fridge2Fork 전체 레시피 크롤링 시스템${NC}"
echo -e "${PURPLE}============================================${NC}"

# 모드 설정
MODE=${1:-"normal"}

# Conda 환경 활성화 확인
if [[ "$CONDA_DEFAULT_ENV" != "fridge2fork" ]]; then
    echo -e "${YELLOW}⚠️  Conda 환경 활성화 중...${NC}"
    source ~/.bashrc
    conda activate fridge2fork
fi

echo -e "${GREEN}✅ Conda 환경: $CONDA_DEFAULT_ENV${NC}"
echo -e "${GREEN}✅ Python 버전: $(python --version)${NC}"
echo -e "${GREEN}✅ 작업 디렉토리: $(pwd)${NC}"
echo

# 현재 데이터베이스 상태 확인
echo -e "${CYAN}📊 현재 데이터베이스 상태 확인 중...${NC}"
python -c "
import asyncio
import sys
sys.path.append('.')
from scripts.crawling.database import recipe_storage

async def check_current_status():
    try:
        stats = await recipe_storage.get_crawling_stats()
        current_recipes = stats.get('total_recipes', 0)
        print(f'현재 저장된 레시피: {current_recipes:,}개')
        return current_recipes
    except Exception as e:
        print(f'상태 확인 오류: {e}')
        return 0

current = asyncio.run(check_current_status())
" 2>/dev/null || echo "데이터베이스 연결 확인 필요"

echo

# 모드별 설정
case $MODE in
    "safe")
        TARGET=10000
        DESCRIPTION="🛡️  안전 모드 (10,000개, 3-4시간 소요)"
        RISK="낮음"
        ;;
    "normal")
        TARGET=10000
        DESCRIPTION="⚖️  균형 모드 (10,000개, 1.5-2시간 소요)"
        RISK="낮음"
        ;;
    "fast")
        TARGET=10000
        DESCRIPTION="⚡ 빠른 모드 (10,000개, 1-1.5시간 소요)"
        RISK="보통"
        ;;
    "turbo")
        TARGET=10000
        DESCRIPTION="🚀 터보 모드 (10,000개, 45분-1시간 소요)"
        RISK="높음"
        ;;
    "extreme")
        TARGET=15000
        DESCRIPTION="🔥 극한 모드 (15,000개, 45분-1시간 소요)"
        RISK="매우 높음"
        ;;
    *)
        echo -e "${RED}❌ 알 수 없는 모드: $MODE${NC}"
        echo -e "${YELLOW}사용 가능한 모드: safe, normal, fast, turbo, extreme${NC}"
        exit 1
        ;;
esac

# 크롤링 정보 출력
echo -e "${BLUE}🎯 크롤링 모드: $DESCRIPTION${NC}"
echo -e "${BLUE}📊 목표 레시피: $TARGET 개${NC}"
echo -e "${BLUE}⚠️  위험 수준: $RISK${NC}"
echo

# 사용자 확인
echo -e "${YELLOW}계속 진행하시겠습니까? (y/N): ${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ 크롤링이 취소되었습니다.${NC}"
    exit 0
fi

# 크롤링 시작 시간 기록
START_TIME=$(date +%s)
echo -e "${GREEN}🎬 크롤링 시작! ($(date))${NC}"
echo -e "${PURPLE}============================================${NC}"

# 로그 파일 설정
LOG_FILE="crawling_$(date +%Y%m%d_%H%M%S).log"
echo -e "${CYAN}📝 로그 파일: $LOG_FILE${NC}"

# 크롤링 실행
if python scripts/optimized_crawling.py --$MODE --target $TARGET 2>&1 | tee "$LOG_FILE"; then
    # 성공 시
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    HOURS=$((DURATION / 3600))
    MINUTES=$(((DURATION % 3600) / 60))
    SECONDS=$((DURATION % 60))
    
    echo
    echo -e "${GREEN}🎉 크롤링 완료!${NC}"
    echo -e "${GREEN}⏱️  총 소요 시간: ${HOURS}시간 ${MINUTES}분 ${SECONDS}초${NC}"
    
    # 최종 통계
    echo -e "${CYAN}📊 최종 결과:${NC}"
    python -c "
import asyncio
import sys
sys.path.append('.')
from scripts.crawling.database import recipe_storage

async def final_stats():
    try:
        stats = await recipe_storage.get_crawling_stats())
        print(f'  • 총 레시피: {stats.get(\"total_recipes\", 0):,}개')
        print(f'  • 총 재료: {stats.get(\"total_ingredients\", 0):,}개')
        print('  • 카테고리별 분포:')
        for category, count in stats.get('category_breakdown', {}).items():
            print(f'    - {category}: {count:,}개')
    except Exception as e:
        print(f'  통계 조회 오류: {e}')

asyncio.run(final_stats())
" 2>/dev/null || echo "  통계 확인 필요"
    
    echo -e "${GREEN}✅ 로그 파일: $LOG_FILE${NC}"
    
else
    # 실패 시
    echo
    echo -e "${RED}❌ 크롤링 중 오류가 발생했습니다.${NC}"
    echo -e "${YELLOW}📝 로그 파일을 확인하세요: $LOG_FILE${NC}"
    echo -e "${YELLOW}🔧 문제 해결을 위해 다음 명령어를 실행하세요:${NC}"
    echo -e "${CYAN}   grep -i error $LOG_FILE${NC}"
    exit 1
fi

echo -e "${PURPLE}============================================${NC}"
echo -e "${GREEN}🎊 Fridge2Fork 크롤링 완료! 🎊${NC}"
