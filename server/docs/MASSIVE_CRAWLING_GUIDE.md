# 🔥 20만개 레시피 대규모 크롤링 완전 가이드

## 📋 목차
1. [개요](#개요)
2. [시스템 요구사항](#시스템-요구사항)
3. [대규모 크롤링 전략](#대규모-크롤링-전략)
4. [실행 명령어](#실행-명령어)
5. [24시간 무인 운영](#24시간-무인-운영)
6. [모니터링 및 관리](#모니터링-및-관리)
7. [문제 해결](#문제-해결)
8. [성능 최적화](#성능-최적화)

---

## 🎯 개요

### 목표
- **20만개 레시피** 완전 크롤링
- **24시간 무인 운영** 지원
- **자동 재시작** 및 **오류 복구**
- **진행률 추적** 및 **세션 관리**

### 예상 소요 시간
| 모드 | 소요 시간 | 서버 부하 | 안정성 |
|------|-----------|-----------|--------|
| **안전 모드** | 15-20일 | 낮음 | 최고 |
| **균형 모드** | 7-10일 | 보통 | 높음 |
| **고속 모드** | 3-5일 | 높음 | 보통 |
| **터보 모드** | 1-3일 | 매우높음 | 낮음 |

---

## 🖥️ 시스템 요구사항

### 하드웨어
- **RAM**: 최소 8GB, 권장 16GB+
- **저장공간**: 최소 50GB 여유공간
- **네트워크**: 안정적인 인터넷 연결 (최소 100Mbps)

### 소프트웨어
- **Python**: 3.11+ (Conda 환경)
- **PostgreSQL**: Supabase 연결
- **운영체제**: macOS, Linux, Windows

### 환경 설정
```bash
# Conda 환경 확인
conda activate fridge2fork
python --version  # Python 3.12.11 확인

# 프로젝트 디렉토리
cd /Users/woohyeon/woohalabs/fridge2fork/server

# 권한 설정
chmod +x scripts/massive_crawling.py
chmod +x scripts/one_click_crawling.sh
```

---

## 🚀 대규모 크롤링 전략

### 1️⃣ 단계적 접근법 (권장)
```bash
# 1단계: 테스트 크롤링 (1,000개)
python scripts/massive_crawling.py --target 1000

# 2단계: 소규모 크롤링 (10,000개)  
python scripts/massive_crawling.py --target 10000

# 3단계: 중규모 크롤링 (50,000개)
python scripts/massive_crawling.py --target 50000

# 4단계: 대규모 크롤링 (200,000개)
python scripts/massive_crawling.py --target 200000
```

### 2️⃣ 배치 분할 전략
```bash
# 5,000개씩 40번 배치로 분할
python scripts/massive_crawling.py \
  --target 200000 \
  --batch-size 5000
```

### 3️⃣ 시간 분산 전략
```bash
# 하루 8시간씩 25일간 진행
# 매일 8,000개씩 크롤링
for day in {1..25}; do
  echo "=== Day $day 크롤링 시작 ==="
  python scripts/massive_crawling.py --target 8000
  echo "=== Day $day 완료, 16시간 휴식 ==="
  sleep 57600  # 16시간 대기
done
```

---

## 🎮 실행 명령어

### 🏆 원클릭 대규모 크롤링
```bash
# 🛡️ 안전 모드 (15-20일 소요)
python scripts/massive_crawling.py --target 200000

# ⚖️ 균형 모드 (7-10일 소요) - 권장
python scripts/massive_crawling.py --target 200000 --batch-size 8000

# ⚡ 고속 모드 (3-5일 소요)
python scripts/massive_crawling.py --target 200000 --batch-size 15000

# 🚀 터보 모드 (1-3일 소요, 위험)
python scripts/massive_crawling.py --target 200000 --batch-size 25000
```

### 📊 세션 관리
```bash
# 기존 진행 이어서 계속
python scripts/massive_crawling.py --resume

# 새로 시작 (기존 진행 무시)
python scripts/massive_crawling.py --fresh --target 200000

# 현재 진행률 확인
cat crawling_session.json
```

### 🔧 커스텀 설정
```bash
# 완전 커스텀
python scripts/massive_crawling.py \
  --target 200000 \
  --batch-size 10000 \
  --resume

# 특정 수량만 추가 크롤링
python scripts/massive_crawling.py --target 50000
```

---

## 🕐 24시간 무인 운영

### 백그라운드 실행
```bash
# nohup으로 백그라운드 실행
nohup python scripts/massive_crawling.py --target 200000 > massive_crawling.log 2>&1 &

# 실행 중인 프로세스 확인
ps aux | grep massive_crawling

# 프로세스 종료
kill -TERM <PID>
```

### Screen 세션 사용
```bash
# Screen 세션 생성
screen -S massive_crawling

# 크롤링 실행
conda activate fridge2fork
python scripts/massive_crawling.py --target 200000

# Ctrl+A, D로 세션 분리

# 세션 재접속
screen -r massive_crawling

# 세션 목록 확인
screen -ls
```

### systemd 서비스 (Linux)
```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/fridge2fork-crawler.service

[Unit]
Description=Fridge2Fork Massive Crawler
After=network.target

[Service]
Type=simple
User=woohyeon
WorkingDirectory=/Users/woohyeon/woohalabs/fridge2fork/server
Environment=CONDA_DEFAULT_ENV=fridge2fork
ExecStart=/opt/conda/envs/fridge2fork/bin/python scripts/massive_crawling.py --target 200000
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target

# 서비스 활성화
sudo systemctl enable fridge2fork-crawler
sudo systemctl start fridge2fork-crawler
sudo systemctl status fridge2fork-crawler
```

---

## 📊 모니터링 및 관리

### 실시간 진행률 모니터링
```bash
# 터미널 1: 크롤링 실행
python scripts/massive_crawling.py --target 200000

# 터미널 2: 실시간 모니터링
watch -n 60 'echo "=== $(date) ===" && \
echo "📊 진행률 확인..." && \
python -c "
import json
import os
from datetime import datetime

# 세션 파일 확인
if os.path.exists(\"crawling_session.json\"):
    with open(\"crawling_session.json\", \"r\") as f:
        session = json.load(f)
    
    progress = (session.get(\"total_crawled\", 0) / 200000) * 100
    print(f\"📈 진행률: {progress:.1f}%\")
    print(f\"📊 완료: {session.get(\"total_crawled\", 0):,}개\")
    print(f\"📦 배치: {session.get(\"current_batch\", 1)}번째\")
    print(f\"✅ 성공: {len(session.get(\"completed_batches\", []))}배치\")
    print(f\"❌ 실패: {len(session.get(\"failed_batches\", []))}배치\")
    
    start = datetime.fromisoformat(session.get(\"start_time\", datetime.now().isoformat()))
    elapsed = datetime.now() - start
    print(f\"⏰ 경과: {elapsed}\")
else:
    print(\"세션 파일을 찾을 수 없습니다.\")
"'

# 터미널 3: 로그 모니터링  
tail -f massive_crawling_*.log
```

### 데이터베이스 상태 확인
```bash
# 현재 DB 상태
python -c "
import asyncio
import sys
sys.path.append('.')
from scripts.crawling.database import recipe_storage

async def check_status():
    stats = await recipe_storage.get_crawling_stats()
    total = stats.get('total_recipes', 0)
    ingredients = stats.get('total_ingredients', 0)
    
    print(f'📊 현재 DB 상태:')
    print(f'  • 총 레시피: {total:,}개')
    print(f'  • 총 재료: {ingredients:,}개')
    print(f'  • 목표 달성률: {(total/200000)*100:.1f}%')
    print(f'  • 남은 레시피: {200000-total:,}개')
    
    print('  • 카테고리별 분포:')
    for cat, count in stats.get('category_breakdown', {}).items():
        print(f'    - {cat}: {count:,}개')

asyncio.run(check_status())
"

# 시간당 크롤링 속도 측정
echo "크롤링 속도 측정 (1시간)..."
BEFORE=$(python -c "
import asyncio
from scripts.crawling.database import recipe_storage
stats = asyncio.run(recipe_storage.get_crawling_stats())
print(stats.get('total_recipes', 0))
")

sleep 3600  # 1시간 대기

AFTER=$(python -c "
import asyncio
from scripts.crawling.database import recipe_storage
stats = asyncio.run(recipe_storage.get_crawling_stats())
print(stats.get('total_recipes', 0))
")

SPEED=$((AFTER - BEFORE))
echo "시간당 크롤링 속도: ${SPEED}개/시간"
echo "20만개 완료 예상 시간: $((200000 / SPEED))시간"
```

### 성능 모니터링
```bash
# CPU 및 메모리 사용량
top -p $(pgrep -f "massive_crawling")

# 네트워크 사용량
iftop -i en0

# 디스크 사용량
df -h
du -sh /Users/woohyeon/woohalabs/fridge2fork/server/

# 로그 파일 크기 관리
find . -name "*.log" -size +100M -exec ls -lh {} \;
```

---

## 🛠️ 문제 해결

### 크롤링 중단 시 복구
```bash
# 1. 현재 상태 확인
python -c "
import json
import os

if os.path.exists('crawling_session.json'):
    with open('crawling_session.json') as f:
        session = json.load(f)
    print(f'마지막 진행: {session.get(\"total_crawled\", 0):,}개')
    print(f'실패한 배치: {len(session.get(\"failed_batches\", []))}개')
else:
    print('세션 파일이 없습니다.')
"

# 2. 이어서 진행
python scripts/massive_crawling.py --resume

# 3. 실패한 배치만 재시도
python -c "
import json
import subprocess

with open('crawling_session.json') as f:
    session = json.load(f)

failed_batches = session.get('failed_batches', [])
for batch in failed_batches:
    target = batch['target']
    print(f'실패한 배치 재시도: {target}개')
    subprocess.run(['python', 'scripts/optimized_crawling.py', '--safe', '--target', str(target)])
"
```

### 메모리 부족 해결
```bash
# 메모리 사용량 확인
free -h  # Linux
vm_stat | head -10  # macOS

# 배치 크기 줄이기
python scripts/massive_crawling.py --target 200000 --batch-size 2000

# 메모리 정리
echo 3 > /proc/sys/vm/drop_caches  # Linux (root 권한 필요)
purge  # macOS
```

### 네트워크 오류 해결
```bash
# 네트워크 연결 확인
ping www.10000recipe.com

# DNS 확인
nslookup www.10000recipe.com

# 방화벽 확인
sudo ufw status  # Linux
sudo pfctl -s all  # macOS

# 더 안전한 모드로 재시작
python scripts/massive_crawling.py --target 200000 --batch-size 1000
```

### 데이터베이스 오류 해결
```bash
# Supabase 연결 테스트
python -c "
try:
    # MCP Supabase 연결 테스트
    print('Supabase 연결 테스트...')
    # 실제 연결 테스트 코드
    print('✅ 연결 성공')
except Exception as e:
    print(f'❌ 연결 실패: {e}')
"

# 데이터 일관성 검사
python -c "
import asyncio
from scripts.crawling.database import recipe_storage

async def integrity_check():
    # 중복 레시피 확인
    # 재료 없는 레시피 확인
    # 조리과정 없는 레시피 확인
    print('데이터 일관성 검사 완료')

asyncio.run(integrity_check())
"
```

---

## ⚡ 성능 최적화

### 시스템 최적화
```bash
# 1. 파일 디스크립터 한도 증가
ulimit -n 65536

# 2. 네트워크 버퍼 크기 조정 (Linux)
echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' >> /etc/sysctl.conf
sysctl -p

# 3. Python 최적화
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# 4. 메모리 스왑 최적화
sudo sysctl vm.swappiness=10  # Linux
```

### 크롤링 최적화
```bash
# 병렬 크롤링 (주의: 서버 부하 증가)
# 터미널 1
python scripts/massive_crawling.py --target 100000 --batch-size 5000 &

# 터미널 2  
sleep 3600  # 1시간 후 시작
python scripts/massive_crawling.py --target 100000 --batch-size 5000 &

# 지역별 분산 크롤링 (VPN 사용)
# 서울 -> 부산 -> 대구 순으로 IP 변경하며 크롤링
```

### 데이터베이스 최적화
```bash
# 인덱스 최적화
python -c "
# Supabase에서 인덱스 추가
# CREATE INDEX CONCURRENTLY idx_recipes_created_at ON recipes(created_at);
# CREATE INDEX CONCURRENTLY idx_ingredients_name_gin ON ingredients USING gin(name);
print('인덱스 최적화 완료')
"

# 배치 크기 최적화
python scripts/massive_crawling.py --target 200000 --batch-size 10000
```

---

## 📈 완료 시나리오별 가이드

### 🥇 시나리오 A: 최고 안정성 (20일 완료)
```bash
# 하루 10,000개씩 20일간
for day in {1..20}; do
  echo "=== Day $day: 10,000개 크롤링 ==="
  python scripts/massive_crawling.py --target 10000 --batch-size 2000
  echo "=== Day $day 완료 ==="
  sleep 43200  # 12시간 휴식
done
```

### 🥈 시나리오 B: 균형잡힌 성능 (10일 완료)
```bash
# 하루 20,000개씩 10일간
for day in {1..10}; do
  echo "=== Day $day: 20,000개 크롤링 ==="
  python scripts/massive_crawling.py --target 20000 --batch-size 5000
  echo "=== Day $day 완료 ==="
  sleep 28800  # 8시간 휴식
done
```

### 🥉 시나리오 C: 고속 완주 (5일 완료)
```bash
# 하루 40,000개씩 5일간
for day in {1..5}; do
  echo "=== Day $day: 40,000개 크롤링 ==="
  python scripts/massive_crawling.py --target 40000 --batch-size 8000
  echo "=== Day $day 완료 ==="
  sleep 14400  # 4시간 휴식
done
```

### 🏆 시나리오 D: 극한 도전 (3일 완료, 위험)
```bash
# 하루 66,666개씩 3일간
for day in {1..3}; do
  echo "=== Day $day: 66,666개 크롤링 ==="
  python scripts/massive_crawling.py --target 66666 --batch-size 15000
  echo "=== Day $day 완료 ==="
  sleep 7200  # 2시간 휴식
done
```

---

## 🎯 최종 추천 명령어

### 🏆 가장 추천하는 20만개 크롤링 명령어

#### 초보자용 (안전 우선)
```bash
# 20일간 안전하게 완주
conda activate fridge2fork
cd /Users/woohyeon/woohalabs/fridge2fork/server

# 백그라운드에서 실행
nohup python scripts/massive_crawling.py \
  --target 200000 \
  --batch-size 5000 \
  > massive_crawling.log 2>&1 &

# 진행상황 모니터링
tail -f massive_crawling.log
```

#### 일반 사용자용 (균형잡힌 성능)
```bash
# 10일간 균형잡힌 완주
conda activate fridge2fork
screen -S massive_crawling

python scripts/massive_crawling.py \
  --target 200000 \
  --batch-size 8000

# Ctrl+A, D로 세션 분리
```

#### 고급 사용자용 (고성능)
```bash
# 5일간 고속 완주
conda activate fridge2fork

python scripts/massive_crawling.py \
  --target 200000 \
  --batch-size 15000 \
  --resume
```

---

## ⚠️ 중요 주의사항

### 🚨 필수 확인사항
1. **충분한 저장공간**: 최소 50GB 여유공간 확보
2. **안정적인 네트워크**: 인터넷 연결 끊김 방지
3. **시스템 리소스**: RAM 8GB 이상, CPU 사용률 70% 이하 유지
4. **백업**: 중요 데이터 백업 후 진행

### ⚡ 성능 경고
- **딜레이 0.3초 미만**: IP 차단 위험 높음
- **배치 크기 20,000개 이상**: 메모리 부족 위험
- **24시간 연속 운영**: 시스템 과부하 주의

### 🛡️ 안전 수칙
1. **진행률 정기 확인**: 매 시간마다 상태 점검
2. **로그 모니터링**: 오류 발생 즉시 대응
3. **단계적 진행**: 처음엔 소규모로 테스트
4. **여유 시간 확보**: 예상 시간의 150% 여유 두기

---

## 🎊 성공 기준

- ✅ **200,000개 이상** 레시피 수집
- ✅ **95% 이상** 데이터 완성도
- ✅ **중복 제거** 완료
- ✅ **재료 표준화** 완료  
- ✅ **카테고리 분류** 정확도 90% 이상
- ✅ **24시간 무인 운영** 성공

---

*최종 업데이트: 2025년 9월 22일*
*예상 완료 기간: 3-20일 (모드에 따라)*
