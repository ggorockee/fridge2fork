# Redis 도입 권장사항

## 🤔 Redis 도입 여부 결정 가이드

### 현재 상황 분석
- **배포 환경**: 헬름차트(Kubernetes) 배포 예정
- **클라이언트**: Flutter + Riverpod 상태관리
- **사용자**: 비회원 포함 세션 기반 관리
- **데이터**: 세션별 냉장고 재료 목록

## ✅ Redis 도입 권장 이유

### 1. 성능상 이점
- **빠른 세션 조회**: 메모리 기반으로 PostgreSQL 대비 10배 이상 빠름
- **자동 만료**: TTL 설정으로 24시간 후 자동 삭제 (메모리 효율)
- **캐싱 효과**: 자주 조회되는 레시피-재료 매핑 캐싱 가능

### 2. 운영상 이점
- **별도 정리 불필요**: 만료된 세션 자동 삭제로 관리 부담 없음
- **확장성**: 사용자 증가 시에도 안정적인 세션 관리
- **장애 격리**: Redis 장애 시에도 PostgreSQL은 정상 동작

### 3. 배포 환경 적합성
- **헬름차트 지원**: Redis 공식 헬름차트로 쉬운 설치/관리
- **설정 간소화**: 기본 설정으로도 충분한 성능
- **모니터링 통합**: Kubernetes 환경에서 리소스 모니터링 가능

## ⚖️ 비교 분석

| 항목 | PostgreSQL 세션 | Redis 세션 |
|------|----------------|-----------|
| **성능** | 느림 (디스크 I/O) | 빠름 (메모리) |
| **설치** | 불필요 | 헬름차트로 간단 |
| **자동 만료** | 수동 정리 필요 | 자동 TTL |
| **메모리 사용** | 낮음 | 높음 |
| **확장성** | 제한적 | 우수함 |
| **장애 복구** | 데이터 보존됨 | 세션 유실됨 |

## 🎯 권장 도입 전략

### Phase 1: PostgreSQL 시작
```python
# 간단한 세션 테이블로 MVP 구현
class UserFridgeSession(Base):
    session_id = Column(String(50), primary_key=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)
```

### Phase 2: Redis 병렬 구현
```python
# PostgreSQL과 Redis 동시 지원
async def create_session(use_redis=True):
    if use_redis and redis_client:
        await redis_client.setex(session_id, 86400, session_data)
    else:
        # PostgreSQL fallback
        await db.add(UserFridgeSession(...))
```

### Phase 3: Redis 완전 이전
- PostgreSQL 세션은 백업용으로만 유지
- Redis를 메인 세션 저장소로 사용

## 🛠️ 헬름차트 설정 예시

```yaml
# redis-values.yaml
redis:
  auth:
    enabled: false  # 개발 환경에서는 비활성화
  master:
    persistence:
      enabled: false  # 세션 데이터는 영속성 불필요
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "200m"
```

```bash
# Redis 설치 명령어
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install fridge2fork-redis bitnami/redis -f redis-values.yaml
```

## 💡 구현 가이드

### 세션 생성
```python
import aioredis
import uuid
from datetime import datetime, timedelta

async def create_session():
    session_id = str(uuid.uuid4())
    session_data = {
        "created_at": datetime.now().isoformat(),
        "ingredients": []
    }

    # 24시간 TTL 설정
    await redis.setex(
        f"session:{session_id}",
        86400,  # 24시간
        json.dumps(session_data)
    )
    return session_id
```

### 재료 추가
```python
async def add_ingredients(session_id: str, ingredients: List[str]):
    key = f"session:{session_id}"
    session_data = await redis.get(key)

    if session_data:
        data = json.loads(session_data)
        data["ingredients"].extend(ingredients)
        # TTL 연장 (24시간 갱신)
        await redis.setex(key, 86400, json.dumps(data))
```

## 🚀 최종 권장사항

**Redis 도입을 강력히 권장합니다!**

**이유**:
1. **성능**: 세션 조회 속도 대폭 개선
2. **운영**: 자동 세션 관리로 운영 부담 최소화
3. **확장성**: 사용자 증가에 대비한 확장성 확보
4. **배포**: 헬름차트 환경에 완벽 적합

**구현 순서**:
1. **1주차**: PostgreSQL 기반 MVP 완성
2. **2주차**: Redis 헬름차트 설치 및 병렬 구현
3. **3주차**: Redis 메인 전환 및 성능 테스트

헬름차트 배포 환경에서는 Redis 설치가 전혀 부담되지 않으며, 오히려 성능과 사용자 경험 향상에 크게 기여할 것입니다.