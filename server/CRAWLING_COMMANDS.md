# 🚀 Fridge2Fork 크롤링 명령어 완전 가이드

## 📋 목차
1. [기본 크롤링 명령어](#기본-크롤링-명령어)
2. [성능 최적화 크롤링](#성능-최적화-크롤링)
3. [전체 크롤링 명령어](#전체-크롤링-명령어)
4. [모니터링 및 관리](#모니터링-및-관리)
5. [문제 해결](#문제-해결)

---

## 🎯 기본 크롤링 명령어

### 환경 설정 및 준비
```bash
# Conda 환경 활성화
conda activate fridge2fork

# 프로젝트 디렉토리 이동
cd /Users/woohyeon/woohalabs/fridge2fork/server

# 의존성 확인
pip list | grep -E "(asyncio|aiohttp|beautifulsoup4)"
```

### 기본 실행 명령어
```bash
# 🧪 기본 테스트 (100개 레시피)
python scripts/run_crawling.py --target 100

# 📊 중간 규모 (1,000개 레시피)
python scripts/run_crawling.py --target 1000

# 🎯 목표 달성 (10,000개 레시피)
python scripts/run_crawling.py --target 10000

# ⚙️ 커스텀 설정
python scripts/run_crawling.py --target 5000 --batch-size 75 --delay 1.2
```

---

## ⚡ 성능 최적화 크롤링

### 단계별 최적화 크롤링
```bash
# 🧪 1단계: 안전 테스트 (100개, 1.5초 딜레이)
python scripts/optimized_crawling.py --test

# ⚡ 2단계: 빠른 크롤링 (1,000개, 0.5초 딜레이)
python scripts/optimized_crawling.py --fast --target 1000

# 🚀 3단계: 터보 크롤링 (5,000개, 0.2초 딜레이)
python scripts/optimized_crawling.py --turbo --target 5000

# 🔥 4단계: 최대 성능 (10,000개, 0.2초 딜레이, 200개 배치)
python scripts/optimized_crawling.py --turbo --batch-large --target 10000
```

### 모드별 최적화 명령어
```bash
# 🛡️ 안전 모드 (서버 부하 최소)
python scripts/optimized_crawling.py --safe --target 10000

# ⚖️ 균형 모드 (성능과 안정성 균형)
python scripts/optimized_crawling.py --normal --target 5000

# 🚀 고성능 모드 (빠른 크롤링)
python scripts/optimized_crawling.py --fast --target 8000

# 🔥 극한 모드 (최대 성능, 주의 필요)
python scripts/optimized_crawling.py --extreme --target 20000
```

---

## 🎯 전체 크롤링 명령어 (10,000개+ 레시피)

### 🏆 추천 전체 크롤링 명령어

#### 방법 1: 안전한 대량 크롤링 (권장)
```bash
# 3-4시간 소요, 서버 부하 최소, IP 차단 위험 낮음
python scripts/optimized_crawling.py --safe --target 10000
```

#### 방법 2: 균형잡힌 대량 크롤링
```bash
# 1.5-2시간 소요, 적당한 성능과 안정성
python scripts/optimized_crawling.py --normal --target 10000
```

#### 방법 3: 고속 대량 크롤링
```bash
# 1-1.5시간 소요, 높은 성능, 모니터링 필요
python scripts/optimized_crawling.py --turbo --batch-large --target 10000
```

#### 방법 4: 단계적 대량 크롤링 (최고 안정성)
```bash
# 1단계: 2,000개
python scripts/optimized_crawling.py --fast --target 2000

# 2단계: 추가 3,000개 (총 5,000개)
python scripts/optimized_crawling.py --fast --target 3000

# 3단계: 추가 5,000개 (총 10,000개)
python scripts/optimized_crawling.py --turbo --target 5000
```

### 🔥 극한 성능 크롤링 (고급 사용자용)
```bash
# ⚠️ 주의: 높은 서버 부하, IP 차단 위험
python scripts/optimized_crawling.py --extreme --target 15000

# 🚨 최대 성능: 20,000개 레시피 (매우 위험)
python scripts/optimized_crawling.py --custom \
  --target 20000 \
  --delay 0.1 \
  --batch-size 250
```

### 📊 대용량 크롤링 전략

#### 전략 A: 시간 우선 (빠른 완료)
```bash
# 예상 시간: 45분-1시간
python scripts/optimized_crawling.py --turbo --batch-large --target 10000
```

#### 전략 B: 안정성 우선 (안전한 완료)
```bash
# 예상 시간: 3-4시간
python scripts/optimized_crawling.py --safe --target 10000
```

#### 전략 C: 분할 크롤링 (최고 안정성)
```bash
# 카테고리별 분할 크롤링 (각각 1,500-2,000개씩)
python scripts/run_crawling.py --target 2000 --delay 1.0  # 1차
sleep 1800  # 30분 휴식
python scripts/run_crawling.py --target 2000 --delay 1.0  # 2차
sleep 1800  # 30분 휴식
python scripts/run_crawling.py --target 2000 --delay 1.0  # 3차
sleep 1800  # 30분 휴식
python scripts/run_crawling.py --target 2000 --delay 1.0  # 4차
sleep 1800  # 30분 휴식
python scripts/run_crawling.py --target 2000 --delay 1.0  # 5차 (총 10,000개)
```

---

## 📊 모니터링 및 관리

### 실시간 모니터링
```bash
# 로그 실시간 확인
tail -f crawling.log

# 진행상황 모니터링 (별도 터미널)
watch -n 30 'echo "=== $(date) ===" && python -c "
import asyncio
import sys
sys.path.append(\".\")
from scripts.crawling.database import recipe_storage
stats = asyncio.run(recipe_storage.get_crawling_stats())
print(f\"총 레시피: {stats.get(\"total_recipes\", 0):,}개\")
print(f\"총 재료: {stats.get(\"total_ingredients\", 0):,}개\")
for cat, count in stats.get(\"category_breakdown\", {}).items():
    print(f\"  - {cat}: {count:,}개\")
"'
```

### 데이터베이스 상태 확인
```bash
# 현재 저장된 레시피 수 확인
python -c "
import asyncio
from scripts.crawling.database import recipe_storage
stats = asyncio.run(recipe_storage.get_crawling_stats())
print('📊 현재 데이터베이스 상태:')
print(f'  • 총 레시피: {stats.get(\"total_recipes\", 0):,}개')
print(f'  • 총 재료: {stats.get(\"total_ingredients\", 0):,}개')
print('  • 카테고리별 분포:')
for category, count in stats.get('category_breakdown', {}).items():
    print(f'    - {category}: {count:,}개')
"

# Supabase 직접 확인
python -c "
import sys
sys.path.append('.')
# MCP Supabase 함수 호출 시뮬레이션
print('Supabase 연결 테스트 필요')
"
```

### 성능 측정
```bash
# 크롤링 속도 측정 (1분간)
echo "크롤링 속도 측정 시작..."
BEFORE=$(python -c "
import asyncio
from scripts.crawling.database import recipe_storage
stats = asyncio.run(recipe_storage.get_crawling_stats())
print(stats.get('total_recipes', 0))
")

sleep 60

AFTER=$(python -c "
import asyncio
from scripts.crawling.database import recipe_storage
stats = asyncio.run(recipe_storage.get_crawling_stats())
print(stats.get('total_recipes', 0))
")

echo "1분간 크롤링된 레시피: $((AFTER - BEFORE))개"
echo "시간당 예상 크롤링: $(($(($AFTER - $BEFORE)) * 60))개"
```

---

## 🛠️ 문제 해결

### 크롤링 중단 시 재시작
```bash
# 현재 상태 확인 후 부족한 만큼 추가 크롤링
CURRENT=$(python -c "
import asyncio
from scripts.crawling.database import recipe_storage
stats = asyncio.run(recipe_storage.get_crawling_stats())
print(stats.get('total_recipes', 0))
")

TARGET=10000
REMAINING=$((TARGET - CURRENT))

if [ $REMAINING -gt 0 ]; then
    echo "추가로 $REMAINING 개 레시피 크롤링 필요"
    python scripts/optimized_crawling.py --fast --target $REMAINING
else
    echo "목표 달성! 현재 $CURRENT 개 레시피 저장됨"
fi
```

### 오류 발생 시 복구
```bash
# 크롤링 로그 확인
grep -i error crawling.log | tail -10

# 실패한 레시피 재시도
python scripts/run_crawling.py --target 100 --delay 2.0

# 데이터베이스 정합성 확인
python -c "
import asyncio
from scripts.crawling.database import recipe_storage

async def check_integrity():
    # 레시피 수 확인
    recipes = await recipe_storage.supabase_client.execute_sql('SELECT COUNT(*) FROM recipes')
    
    # 재료 없는 레시피 확인
    orphan_recipes = await recipe_storage.supabase_client.execute_sql('''
        SELECT r.name FROM recipes r 
        LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id 
        WHERE ri.recipe_id IS NULL
    ''')
    
    print(f'총 레시피: {recipes[0][\"count\"] if recipes else 0}개')
    print(f'재료 없는 레시피: {len(orphan_recipes)}개')

asyncio.run(check_integrity())
"
```

### 성능 튜닝
```bash
# 시스템 리소스 모니터링
top -p $(pgrep -f "python.*crawling")

# 메모리 사용량 확인
ps aux | grep python | grep crawling

# 네트워크 연결 상태
netstat -an | grep 443 | wc -l
```

---

## 🎯 최종 추천 명령어

### 🥇 초보자용 (안전하고 확실함)
```bash
# 단계적 접근
python scripts/optimized_crawling.py --test        # 100개 테스트
python scripts/optimized_crawling.py --safe --target 1000   # 1,000개
python scripts/optimized_crawling.py --safe --target 5000   # 추가 4,000개
python scripts/optimized_crawling.py --safe --target 5000   # 추가 5,000개 (총 10,000개)
```

### 🥈 중급자용 (균형잡힌 성능)
```bash
# 효율적인 대량 크롤링
python scripts/optimized_crawling.py --normal --target 10000
```

### 🥉 고급자용 (최고 성능)
```bash
# 고속 대량 크롤링 (모니터링 필수)
python scripts/optimized_crawling.py --turbo --batch-large --target 10000
```

### 🏆 전문가용 (극한 성능)
```bash
# 최대 성능 크롤링 (위험 수준 높음)
python scripts/optimized_crawling.py --extreme --target 15000
```

---

## ⚠️ 주의사항

1. **서버 부하**: 딜레이가 0.5초 미만일 때는 서버 부하 주의
2. **IP 차단**: 너무 빠른 크롤링 시 IP 차단 위험
3. **메모리 사용**: 배치 크기가 클수록 메모리 사용량 증가
4. **데이터 품질**: 빠른 크롤링일수록 데이터 검증 강화 필요
5. **백업**: 크롤링 전 데이터베이스 백업 권장

---

## 🎉 성공 기준

- ✅ **10,000개 이상** 레시피 수집
- ✅ **95% 이상** 데이터 완성도
- ✅ **중복 제거** 완료
- ✅ **재료 표준화** 완료
- ✅ **카테고리 분류** 정확도 90% 이상

---

*마지막 업데이트: 2025년 9월 22일*

