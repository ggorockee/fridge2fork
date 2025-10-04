# 관리자 페이지 추천 설정 표시 문제 해결

## 문제 증상

- 관리자 페이지에서 "추천 설정" 메뉴는 표시됨
- 목록 페이지에서 "0 추천 설정"으로 레코드가 없음
- URL: `localhost:8000/fridge2fork/admin/recipes/recommendationsettings/`

## 원인 분석

RecommendationSettings 모델은 Singleton 패턴으로 설계되어 항상 1개의 레코드(pk=1)만 존재해야 하지만, 초기 마이그레이션 시 기본 레코드가 자동 생성되지 않음.

## 해결 방법

### 방법 1: 데이터 마이그레이션 추가 (권장)

마이그레이션 파일에 초기 데이터 생성 로직 추가:

```python
# recipes/migrations/0010_create_default_recommendation_settings.py

def create_default_settings(apps, schema_editor):
    RecommendationSettings = apps.get_model('recipes', 'RecommendationSettings')
    RecommendationSettings.objects.get_or_create(
        pk=1,
        defaults={
            'min_match_rate': 0.3,
            'default_algorithm': 'jaccard',
            'default_limit': 20,
            'exclude_seasonings_default': True
        }
    )

class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0009_recommendationsettings'),
    ]

    operations = [
        migrations.RunPython(create_default_settings),
    ]
```

### 방법 2: 관리 명령어 실행

```bash
python manage.py shell -c "from recipes.models import RecommendationSettings; RecommendationSettings.objects.get_or_create(pk=1)"
```

### 방법 3: Admin 페이지에서 직접 추가 (비권장)

Singleton 패턴이므로 add 권한을 비활성화했지만, 초기에는 직접 생성 필요.

## 구현된 해결책

데이터 마이그레이션을 추가하여 마이그레이션 시 자동으로 기본 설정 레코드 생성.

### 검증 방법

1. 마이그레이션 적용 후 확인:
   ```bash
   python manage.py migrate recipes
   python manage.py shell -c "from recipes.models import RecommendationSettings; print(RecommendationSettings.objects.count())"
   ```
   - 출력: `1` (정상)

2. 관리자 페이지 확인:
   - URL: `/fridge2fork/admin/recipes/recommendationsettings/`
   - 목록에 "추천 설정" 레코드 1개 표시
   - 클릭하여 수정 페이지 접근 가능

## 예방 조치

- 향후 유사한 Singleton 모델은 마이그레이션에 초기 데이터 생성 로직 포함
- `get_settings()` 클래스 메서드에서 자동 생성하지만, 마이그레이션에서도 보장
