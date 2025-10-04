# Phase 4: 데이터 검증 및 품질 관리 시스템

## 진행상황

- [x] 데이터 무결성 검증 시스템 구현 완료
- [x] 재료 분포 분석 시스템 구현 완료
- [x] main.py 검증 모드 구현 완료
- [ ] 자동화된 품질 체크 스케줄 구성
- [ ] 데이터 품질 대시보드 구현
- [ ] 이상 데이터 알림 시스템 구현
- [ ] 정기적인 데이터 정제 작업 자동화
- [ ] 성능 모니터링 시스템 구축

## 개요

데이터베이스에 저장된 레시피 데이터의 품질을 지속적으로 모니터링하고 관리하는 시스템 구축

## 데이터 품질 관리 시스템

### 1. 데이터 무결성 검증

데이터베이스의 참조 무결성과 데이터 일관성을 체계적으로 검증합니다.

#### 무결성 검사 항목

```python
def validate_data_integrity():
    """
    데이터 무결성 종합 검증

    Returns:
        integrity_report: 검증 결과 보고서
    """
    checks = {
        'basic_stats': get_basic_statistics(),
        'data_quality': check_data_quality(),
        'integrity_issues': check_integrity_issues(),
        'performance_metrics': measure_query_performance()
    }

    return generate_integrity_report(checks)

def check_data_quality():
    return {
        'recipes_without_title': count_empty_titles(),
        'ingredients_without_name': count_unnamed_ingredients(),
        'relations_without_quantity': count_missing_quantities(),
        'duplicate_data': detect_duplicates()
    }
```

#### 품질 지표 기준

| 지표 | 양호 기준 | 경고 기준 | 설명 |
|------|----------|----------|------|
| 제목 누락률 | < 1% | < 5% | 레시피 제목이 없는 비율 |
| 재료명 누락률 | < 0.1% | < 1% | 재료명이 없는 비율 |
| 고아 데이터 | 0건 | < 10건 | 외래키 참조 오류 |
| 중복 데이터 | < 0.1% | < 1% | 완전 중복 레코드 비율 |

### 2. 재료 분포 분석

#### 재료 사용 패턴 분석

```python
def analyze_ingredient_distribution():
    """
    재료 사용 패턴 및 분포 분석

    Returns:
        distribution_report: 분포 분석 결과
    """
    analysis = {
        'category_distribution': get_category_distribution(),
        'popularity_ranking': get_popularity_ranking(),
        'usage_frequency': analyze_usage_frequency(),
        'seasonal_patterns': detect_seasonal_patterns()
    }

    return generate_distribution_report(analysis)

def get_popularity_ranking(limit=50):
    return {
        'most_used': get_most_used_ingredients(limit),
        'trending': get_trending_ingredients(),
        'rare_ingredients': get_rare_ingredients()
    }
```

#### 데이터 이상 탐지

```python
def detect_data_anomalies():
    """
    데이터 이상 상황 탐지

    Returns:
        anomaly_report: 이상 탐지 결과
    """
    anomalies = {
        'outlier_recipes': detect_outlier_recipes(),
        'suspicious_patterns': find_suspicious_patterns(),
        'data_drift': detect_data_drift(),
        'quality_degradation': monitor_quality_trends()
    }

    return generate_anomaly_report(anomalies)

def detect_outlier_recipes():
    return {
        'too_many_ingredients': find_recipes_with_excessive_ingredients(),
        'no_ingredients': find_recipes_without_ingredients(),
        'duplicate_titles': find_recipes_with_duplicate_titles()
    }
```

### 3. 품질 모니터링 대시보드

#### 실시간 품질 대시보드

```python
def generate_quality_dashboard():
    """
    데이터 품질 현황 대시보드 생성

    Returns:
        dashboard_data: 대시보드 표시용 데이터
    """
    dashboard = {
        'summary': generate_quality_summary(),
        'trends': analyze_quality_trends(),
        'alerts': get_active_alerts(),
        'recommendations': get_improvement_recommendations()
    }

    return format_dashboard_data(dashboard)

def generate_quality_summary():
    return {
        'overall_score': calculate_overall_quality_score(),
        'key_metrics': get_key_quality_metrics(),
        'recent_changes': track_recent_quality_changes(),
        'health_status': determine_system_health()
    }
```

#### 자동화된 품질 관리

```python
def automated_quality_management():
    """
    자동화된 품질 관리 작업 실행

    Returns:
        management_report: 관리 작업 실행 결과
    """
    tasks = {
        'data_cleanup': perform_automated_cleanup(),
        'integrity_fixes': fix_integrity_issues(),
        'optimization': optimize_database_performance(),
        'backup_verification': verify_backup_integrity()
    }

    return generate_management_report(tasks)

def perform_automated_cleanup():
    return {
        'duplicate_removal': remove_duplicate_entries(),
        'orphan_cleanup': clean_orphaned_records(),
        'data_normalization': normalize_inconsistent_data(),
        'index_maintenance': rebuild_fragmented_indexes()
    }
```

## 품질 관리 API 구현

### 1. 품질 관리 API 엔드포인트

```python
from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, List, Optional

app = FastAPI(title="Fridge2Fork 데이터 품질 관리 API")

@app.get("/api/v1/quality/integrity-check")
async def check_data_integrity():
    """
    데이터 무결성 종합 검사

    Returns:
        무결성 검사 결과 보고서
    """
    try:
        integrity_report = await validate_data_integrity()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "integrity_report": integrity_report,
            "overall_health": calculate_overall_health_score(integrity_report)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/quality/distribution-analysis")
async def analyze_ingredient_distribution():
    """
    재료 분포 분석

    Returns:
        재료 사용 패턴 및 분포 분석 결과
    """
    try:
        distribution_report = await analyze_ingredient_distribution()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "distribution_analysis": distribution_report,
            "insights": generate_distribution_insights(distribution_report)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/quality/dashboard")
async def get_quality_dashboard():
    """
    품질 관리 대시보드 데이터

    Returns:
        대시보드 표시용 품질 현황 데이터
    """
    try:
        dashboard_data = await generate_quality_dashboard()

        return {
            "status": "success",
            "dashboard": dashboard_data,
            "last_updated": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. 품질 보고서 형식 정의

```python
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class IntegrityStats(BaseModel):
    total_recipes: int
    total_ingredients: int
    total_relations: int

class DataQualityMetrics(BaseModel):
    recipes_without_title: int
    ingredients_without_name: int
    relations_without_quantity: int
    orphaned_records: int
    duplicate_entries: int

class IntegrityReportResponse(BaseModel):
    status: str
    timestamp: datetime
    basic_stats: IntegrityStats
    quality_metrics: DataQualityMetrics
    overall_health_score: float
    recommendations: List[str]

class DistributionAnalysis(BaseModel):
    category_distribution: List[Dict[str, any]]
    top_ingredients: List[Dict[str, any]]
    usage_patterns: Dict[str, any]
    seasonal_trends: Optional[Dict[str, any]]

class QualityDashboard(BaseModel):
    summary: Dict[str, any]
    trends: Dict[str, any]
    alerts: List[Dict[str, any]]
    recommendations: List[str]
    last_updated: datetime

def format_integrity_report(integrity_data) -> IntegrityReportResponse:
    """
    무결성 검사 결과를 API 응답 형식으로 변환
    """
    return IntegrityReportResponse(
        status="success",
        timestamp=datetime.utcnow(),
        basic_stats=IntegrityStats(**integrity_data['basic_stats']),
        quality_metrics=DataQualityMetrics(**integrity_data['data_quality']),
        overall_health_score=calculate_health_score(integrity_data),
        recommendations=generate_improvement_recommendations(integrity_data)
    )
```

### 3. 품질 모니터링 최적화

#### 모니터링 성능 최적화

```python
import redis
from functools import wraps
import json
import hashlib
from datetime import datetime, timedelta

# Redis 클라이언트 설정
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_quality_metrics(expire_time=1800):
    """
    품질 지표 캐싱 데코레이터

    Args:
        expire_time: 캐시 만료 시간 (초, 기본 30분)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. 캐시 키 생성
            cache_key = generate_quality_cache_key(func.__name__, args, kwargs)

            # 2. 캐시에서 결과 확인
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            # 3. 캐시 미스 시 실제 함수 실행
            result = await func(*args, **kwargs)

            # 4. 결과를 캐시에 저장
            redis_client.setex(
                cache_key,
                expire_time,
                json.dumps(result, default=str)
            )

            return result
        return wrapper
    return decorator

def generate_quality_cache_key(func_name, args, kwargs):
    """
    품질 모니터링용 캐시 키 생성
    """
    # 시간 기반 키로 정기적인 갱신 보장
    hour_key = datetime.now().strftime("%Y%m%d_%H")
    key_data = {
        'function': func_name,
        'hour': hour_key,
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return f"quality_cache:{hashlib.md5(key_string.encode()).hexdigest()}"

# 사용 예시
@cache_quality_metrics(expire_time=1800)  # 30분 캐시
async def validate_data_integrity():
    # 실제 무결성 검사 로직
    pass

@cache_quality_metrics(expire_time=3600)  # 1시간 캐시
async def analyze_ingredient_distribution():
    # 실제 분포 분석 로직
    pass
```

#### 품질 검사 쿼리 최적화

```python
from sqlalchemy import text
from sqlalchemy.orm import selectinload

# 1. 무결성 검사 최적화 쿼리
OPTIMIZED_INTEGRITY_CHECK_QUERY = """
WITH integrity_stats AS (
    SELECT
        -- 기본 통계
        (SELECT COUNT(*) FROM recipes) as total_recipes,
        (SELECT COUNT(*) FROM ingredients) as total_ingredients,
        (SELECT COUNT(*) FROM recipe_ingredients) as total_relations,

        -- 품질 지표
        (SELECT COUNT(*) FROM recipes WHERE rcp_ttl IS NULL OR rcp_ttl = '') as recipes_without_title,
        (SELECT COUNT(*) FROM ingredients WHERE name IS NULL OR name = '') as ingredients_without_name,
        (SELECT COUNT(*) FROM recipe_ingredients WHERE quantity_text IS NULL) as relations_without_quantity,

        -- 무결성 이슈
        (SELECT COUNT(*) FROM recipe_ingredients ri
         LEFT JOIN recipes r ON ri.rcp_sno = r.rcp_sno
         WHERE r.rcp_sno IS NULL) as orphaned_recipe_relations,
        (SELECT COUNT(*) FROM recipe_ingredients ri
         LEFT JOIN ingredients i ON ri.ingredient_id = i.id
         WHERE i.id IS NULL) as orphaned_ingredient_relations,

        -- 중복 데이터
        (SELECT COUNT(*) - COUNT(DISTINCT name) FROM ingredients) as duplicate_ingredients,
        (SELECT COUNT(*) - COUNT(DISTINCT (rcp_sno, ingredient_id)) FROM recipe_ingredients) as duplicate_relations
),
performance_metrics AS (
    SELECT
        -- 쿼리 성능 지표
        pg_total_relation_size('recipes') as recipes_size,
        pg_total_relation_size('ingredients') as ingredients_size,
        pg_total_relation_size('recipe_ingredients') as relations_size
)
SELECT
    i.*,
    p.recipes_size,
    p.ingredients_size,
    p.relations_size,
    CURRENT_TIMESTAMP as check_timestamp
FROM integrity_stats i, performance_metrics p;
"""

# 2. 재료 분포 분석 최적화
OPTIMIZED_DISTRIBUTION_ANALYSIS_QUERY = """
WITH category_stats AS (
    SELECT
        COALESCE(category, 'unknown') as category,
        COUNT(*) as ingredient_count,
        COUNT(CASE WHEN is_common THEN 1 END) as common_count
    FROM ingredients
    GROUP BY category
),
popularity_stats AS (
    SELECT
        i.id,
        i.name,
        i.category,
        COUNT(ri.rcp_sno) as usage_count,
        COUNT(CASE WHEN ri.importance = 'essential' THEN 1 END) as essential_count,
        AVG(CASE WHEN ri.quantity_from IS NOT NULL THEN ri.quantity_from END) as avg_quantity
    FROM ingredients i
    LEFT JOIN recipe_ingredients ri ON i.id = ri.ingredient_id
    GROUP BY i.id, i.name, i.category
),
recipe_complexity AS (
    SELECT
        AVG(ingredient_count) as avg_ingredients_per_recipe,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ingredient_count) as median_ingredients,
        MAX(ingredient_count) as max_ingredients,
        MIN(ingredient_count) as min_ingredients
    FROM (
        SELECT rcp_sno, COUNT(*) as ingredient_count
        FROM recipe_ingredients
        GROUP BY rcp_sno
    ) recipe_counts
)
SELECT
    json_agg(DISTINCT cs.*) as category_distribution,
    json_agg(ps.* ORDER BY ps.usage_count DESC) FILTER (WHERE ps.usage_count > 0) as ingredient_popularity,
    to_json(rc.*) as recipe_complexity,
    CURRENT_TIMESTAMP as analysis_timestamp
FROM category_stats cs, popularity_stats ps, recipe_complexity rc
GROUP BY rc.*;
"""

# 3. 품질 트렌드 분석
def get_quality_trend_query(days: int = 30):
    """
    품질 지표 트렌드 분석 (지정된 기간)
    """
    return text("""
        WITH daily_quality AS (
            SELECT
                DATE_TRUNC('day', created_at) as check_date,
                COUNT(*) as records_added,
                COUNT(CASE WHEN rcp_ttl IS NULL OR rcp_ttl = '' THEN 1 END) as quality_issues
            FROM recipes
            WHERE created_at >= NOW() - INTERVAL ':days days'
            GROUP BY DATE_TRUNC('day', created_at)
        )
        SELECT
            check_date,
            records_added,
            quality_issues,
            ROUND(quality_issues::numeric / NULLIF(records_added, 0) * 100, 2) as quality_issue_rate
        FROM daily_quality
        ORDER BY check_date
    """).bindparam(days=days)
```

## 품질 지표 및 모니터링

### 1. 핵심 품질 지표 (KQI - Key Quality Indicators)

#### 데이터 품질 지표

| 지표 | 목표값 | 측정 방법 |
|------|--------|----------|
| 데이터 완성도 | > 95% | 필수 필드 null 비율 |
| 데이터 일관성 | > 98% | 참조 무결성 검사 |
| 데이터 정확성 | > 90% | 재료 파싱 성공률 |
| 중복 데이터 비율 | < 1% | 중복 레코드 탐지 |
| 시스템 가용성 | > 99% | 서비스 응답률 |

#### 시스템 건강성 지표

| 지표 | 목표값 | 모니터링 도구 |
|------|--------|---------------|
| 데이터베이스 응답시간 | < 100ms | PostgreSQL logs |
| 인덱스 효율성 | > 95% | pg_stat_user_indexes |
| 디스크 사용률 | < 80% | System metrics |
| 백업 성공률 | 100% | Backup logs |
| 품질 체크 주기 | 일 1회 | Cron job logs |

### 2. 품질 모니터링 대시보드

#### Grafana 대시보드 설정

```yaml
# quality-dashboard.json
{
  "dashboard": {
    "title": "Fridge2Fork 데이터 품질 모니터링",
    "panels": [
      {
        "title": "데이터 완성도",
        "type": "gauge",
        "targets": [
          {
            "expr": "data_completeness_percentage",
            "legendFormat": "완성도 %"
          }
        ]
      },
      {
        "title": "무결성 이슈 수",
        "type": "stat",
        "targets": [
          {
            "expr": "integrity_issues_total",
            "legendFormat": "이슈 건수"
          }
        ]
      },
      {
        "title": "품질 점수 트렌드",
        "type": "graph",
        "targets": [
          {
            "expr": "quality_score_trend",
            "legendFormat": "품질 점수"
          }
        ]
      },
      {
        "title": "데이터 증가율",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(total_records[24h])",
            "legendFormat": "레코드/일"
          }
        ]
      }
    ]
  }
}
```

#### 품질 알림 설정

```yaml
# quality-alerts.yml
groups:
  - name: data_quality
    rules:
      - alert: LowDataCompleteness
        expr: data_completeness_percentage < 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "데이터 완성도가 낮습니다"
          description: "데이터 완성도가 {{ $value }}%입니다"

      - alert: IntegrityIssuesDetected
        expr: integrity_issues_total > 100
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "데이터 무결성 이슈 감지"
          description: "{{ $value }}건의 무결성 이슈가 발견되었습니다"

      - alert: QualityCheckFailed
        expr: time() - last_quality_check_timestamp > 86400
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "품질 검사가 실행되지 않음"
          description: "24시간 이상 품질 검사가 실행되지 않았습니다"

      - alert: DataGrowthAnomalous
        expr: rate(total_records[1h]) > 1000 OR rate(total_records[1h]) < 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "비정상적인 데이터 증가율"
          description: "시간당 {{ $value }}개의 레코드가 추가되고 있습니다"
```

### 3. 자동화된 품질 관리 프레임워크

```python
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Callable

class QualityManagementFramework:
    def __init__(self):
        self.quality_checks = {}
        self.alert_handlers = []
        self.quality_history = []

    def register_quality_check(self, check_id: str, check_function: Callable,
                              frequency: str, threshold: Dict[str, float]):
        """
        품질 검사 등록

        Args:
            check_id: 검사 ID
            check_function: 검사 실행 함수
            frequency: 실행 주기 ('hourly', 'daily', 'weekly')
            threshold: 임계값 설정
        """
        self.quality_checks[check_id] = {
            'function': check_function,
            'frequency': frequency,
            'threshold': threshold,
            'last_run': None,
            'last_result': None
        }

    def execute_quality_check(self, check_id: str) -> Dict[str, Any]:
        """
        품질 검사 실행

        Args:
            check_id: 검사 ID

        Returns:
            검사 결과
        """
        check_config = self.quality_checks.get(check_id)
        if not check_config:
            raise ValueError(f"Unknown quality check: {check_id}")

        try:
            # 검사 실행
            result = check_config['function']()

            # 결과 평가
            quality_score = self.evaluate_quality_score(result, check_config['threshold'])

            # 결과 저장
            check_result = {
                'check_id': check_id,
                'timestamp': datetime.utcnow(),
                'result': result,
                'quality_score': quality_score,
                'status': 'passed' if quality_score >= 0.8 else 'failed'
            }

            check_config['last_run'] = check_result['timestamp']
            check_config['last_result'] = check_result
            self.quality_history.append(check_result)

            # 임계값 위반 시 알림
            if quality_score < 0.7:
                self.trigger_alert(check_result)

            return check_result

        except Exception as e:
            error_result = {
                'check_id': check_id,
                'timestamp': datetime.utcnow(),
                'error': str(e),
                'status': 'error'
            }
            self.quality_history.append(error_result)
            return error_result

    def evaluate_quality_score(self, result: Dict, thresholds: Dict[str, float]) -> float:
        """
        품질 점수 계산

        Args:
            result: 검사 결과
            thresholds: 임계값 설정

        Returns:
            0.0 ~ 1.0 사이의 품질 점수
        """
        scores = []

        for metric, threshold in thresholds.items():
            if metric in result:
                value = result[metric]
                if isinstance(value, (int, float)):
                    # 값이 작을수록 좋은 지표 (에러 수 등)
                    if metric.endswith('_errors') or metric.endswith('_issues'):
                        score = max(0, 1 - (value / threshold))
                    else:
                        # 값이 클수록 좋은 지표 (완성도 등)
                        score = min(1, value / threshold)
                    scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    def trigger_alert(self, check_result: Dict):
        """
        품질 알림 발생

        Args:
            check_result: 검사 결과
        """
        alert_data = {
            'type': 'quality_alert',
            'check_id': check_result['check_id'],
            'quality_score': check_result.get('quality_score', 0),
            'timestamp': check_result['timestamp'],
            'details': check_result.get('result', {})
        }

        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                print(f"Alert handler failed: {e}")

    def schedule_quality_checks(self):
        """
        품질 검사 스케줄링
        """
        for check_id, config in self.quality_checks.items():
            frequency = config['frequency']

            if frequency == 'hourly':
                schedule.every().hour.do(self.execute_quality_check, check_id)
            elif frequency == 'daily':
                schedule.every().day.at("02:00").do(self.execute_quality_check, check_id)
            elif frequency == 'weekly':
                schedule.every().week.do(self.execute_quality_check, check_id)

    def start_monitoring(self):
        """
        품질 모니터링 시작
        """
        self.schedule_quality_checks()

        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크

# 사용 예시
quality_manager = QualityManagementFramework()

# 무결성 검사 등록
quality_manager.register_quality_check(
    'data_integrity',
    validate_data_integrity,
    'daily',
    {
        'completeness_rate': 0.95,
        'integrity_errors': 10,
        'duplicate_rate': 0.01
    }
)

# 분포 분석 등록
quality_manager.register_quality_check(
    'ingredient_distribution',
    analyze_ingredient_distribution,
    'weekly',
    {
        'category_coverage': 0.8,
        'outlier_ingredients': 50
    }
)
```

## 다음 단계

1. **Phase 5**: Kubernetes 배포 및 운영 자동화
2. **품질 대시보드**: 실시간 품질 모니터링 웹 인터페이스
3. **자동 복구**: 품질 이슈 자동 감지 및 복구 시스템
4. **FastAPI 백엔드**: 레시피 추천 API 구현 (별도 프로젝트)