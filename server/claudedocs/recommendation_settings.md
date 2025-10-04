# 추천 설정 관리 문서

## 개요

관리자가 레시피 추천 API의 기본 설정값을 관리할 수 있는 기능

## 설정 항목

### RecommendationSettings 모델

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| min_match_rate | float | 0.3 | 최소 매칭률 (0.0-1.0) |
| default_algorithm | str | "jaccard" | 기본 유사도 알고리즘 |
| default_limit | int | 20 | 기본 추천 개수 (1-100) |
| exclude_seasonings_default | bool | true | 기본 조미료 제외 여부 |
| updated_at | datetime | - | 마지막 수정 시간 |

### 설정 적용 우선순위

1. **API 요청 파라미터** (가장 높음)
   - 사용자가 명시적으로 전달한 값

2. **관리자 설정값**
   - DB에 저장된 설정값

3. **하드코딩된 기본값** (가장 낮음)
   - 코드에 정의된 폴백 값

### 예시

```python
# 사용자가 min_match_rate를 전달하지 않은 경우
GET /recommendations?ingredients=돼지고기

# 1. API 파라미터: 없음
# 2. 관리자 설정: 0.5 (DB에서 조회)
# 3. 하드코딩 기본값: 0.3
# 결과: 0.5 사용 (관리자 설정)

# 사용자가 min_match_rate를 전달한 경우
GET /recommendations?ingredients=돼지고기&min_match_rate=0.7

# 1. API 파라미터: 0.7
# 2. 관리자 설정: 0.5
# 3. 하드코딩 기본값: 0.3
# 결과: 0.7 사용 (API 파라미터 우선)
```

## 구현 방식

### 1. 싱글톤 패턴

RecommendationSettings 모델은 항상 1개의 레코드만 존재:
- ID=1로 고정
- get_or_create로 조회/생성
- Django Admin에서 수정

### 2. 설정 조회 함수

```python
def get_recommendation_settings():
    """추천 설정 조회 (캐싱 적용)"""
    settings, created = RecommendationSettings.objects.get_or_create(
        id=1,
        defaults={
            'min_match_rate': 0.3,
            'default_algorithm': 'jaccard',
            'default_limit': 20,
            'exclude_seasonings_default': True
        }
    )
    return settings
```

### 3. API에서 사용

```python
@router.get("/recommendations")
def get_recipe_recommendations(
    request,
    ingredients: str,
    limit: Optional[int] = None,
    algorithm: Optional[str] = None,
    exclude_seasonings: Optional[bool] = None,
    min_match_rate: Optional[float] = None
):
    # 관리자 설정 조회
    settings = get_recommendation_settings()

    # 파라미터 우선순위 적용
    limit = limit if limit is not None else settings.default_limit
    algorithm = algorithm if algorithm else settings.default_algorithm
    exclude_seasonings = exclude_seasonings if exclude_seasonings is not None else settings.exclude_seasonings_default
    min_match_rate = min_match_rate if min_match_rate is not None else settings.min_match_rate

    # ... 추천 로직
```

## Django Admin 설정

### 관리자 페이지

- **경로**: `/fridge2fork/admin/recipes/recommendationsettings/1/change/`
- **권한**: 슈퍼유저만 접근
- **필드**:
  - Min Match Rate (최소 매칭률)
  - Default Algorithm (기본 알고리즘)
  - Default Limit (기본 추천 개수)
  - Exclude Seasonings Default (기본 조미료 제외)

### 유효성 검증

```python
class RecommendationSettings(models.Model):
    min_match_rate = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )

    def clean(self):
        # 추가 비즈니스 로직 검증
        if self.min_match_rate < 0.0 or self.min_match_rate > 1.0:
            raise ValidationError('min_match_rate must be between 0.0 and 1.0')
```

## 테스트 케이스

**TC-1: 관리자 설정값 사용**
- Given: 관리자가 min_match_rate=0.5 설정
- When: `GET /recommendations?ingredients=돼지고기` (파라미터 없음)
- Then: min_match_rate=0.5로 추천

**TC-2: API 파라미터 우선**
- Given: 관리자가 min_match_rate=0.5 설정
- When: `GET /recommendations?ingredients=돼지고기&min_match_rate=0.7`
- Then: min_match_rate=0.7로 추천 (파라미터 우선)

**TC-3: 기본값 폴백**
- Given: DB에 설정 없음
- When: `GET /recommendations?ingredients=돼지고기`
- Then: min_match_rate=0.3로 추천 (하드코딩 기본값)

**TC-4: 설정 생성 및 수정**
- Given: 초기 상태
- When: 관리자가 설정 수정
- Then: 이후 API 요청에 반영

**TC-5: 유효성 검증**
- Given: 관리자 페이지
- When: min_match_rate=-0.5 입력
- Then: ValidationError 발생

## 성능 최적화

### 캐싱 전략 (선택사항)

```python
from django.core.cache import cache

def get_recommendation_settings():
    """추천 설정 조회 (캐싱)"""
    cache_key = 'recommendation_settings'
    settings = cache.get(cache_key)

    if settings is None:
        settings, created = RecommendationSettings.objects.get_or_create(
            id=1,
            defaults={...}
        )
        cache.set(cache_key, settings, timeout=300)  # 5분 캐싱

    return settings
```

### 캐시 무효화

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=RecommendationSettings)
def invalidate_settings_cache(sender, instance, **kwargs):
    cache.delete('recommendation_settings')
```

## 마이그레이션

### 마이그레이션 파일 생성

```bash
python app/manage.py makemigrations recipes
```

### 초기 데이터 생성

```python
# recipes/migrations/000X_add_recommendation_settings.py

def create_default_settings(apps, schema_editor):
    RecommendationSettings = apps.get_model('recipes', 'RecommendationSettings')
    RecommendationSettings.objects.get_or_create(
        id=1,
        defaults={
            'min_match_rate': 0.3,
            'default_algorithm': 'jaccard',
            'default_limit': 20,
            'exclude_seasonings_default': True
        }
    )

class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '000X_previous_migration'),
    ]

    operations = [
        migrations.RunPython(create_default_settings),
    ]
```

## 사용 예시

### 관리자 작업

1. Django Admin 로그인
2. "Recommendation Settings" 메뉴 클릭
3. Min Match Rate를 0.5로 변경
4. 저장

### 사용자 영향

```bash
# 변경 전 (min_match_rate=0.3)
GET /recommendations?ingredients=돼지고기
→ 30% 이상 매칭된 레시피 반환

# 변경 후 (min_match_rate=0.5)
GET /recommendations?ingredients=돼지고기
→ 50% 이상 매칭된 레시피 반환 (품질 향상)
```

## 보안 고려사항

- **권한 제한**: 슈퍼유저만 설정 변경 가능
- **감사 로그**: 설정 변경 이력 기록
- **롤백**: 이전 값으로 쉽게 복원 가능
