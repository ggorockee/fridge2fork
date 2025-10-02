# 재료 정규화 전략

## 개요

**문제**: 요리 초보자가 "돼지고기"를 검색하면 "수육용 돼지고기", "구이용 돼지고기" 등 모든 관련 레시피가 나와야 하지만, 재료명이 다양하게 표기되어 있어 매칭이 어려움.

**해결책**: 원본 재료명을 유지하면서, 정규화된 재료명으로 검색 및 매칭을 수행하는 이중 구조 설계.

## 핵심 원칙

### 1. 원본 유지 (Display Layer)
- 레시피에는 **원본 재료명** 그대로 표시
- 예: "수육용 돼지고기 300g"
- 사용자는 정확한 레시피 정보를 볼 수 있음

### 2. 정규화 검색 (Search Layer)
- 검색 및 매칭은 **정규화된 재료명** 사용
- 예: "돼지고기"
- 사용자는 간단한 검색어로 모든 관련 레시피 찾기 가능

### 3. 관리자 통제
- 정규화 매핑은 **관리자가 검증 및 관리**
- 자동 제안 + 수동 확인 방식
- 데이터 품질 보장

## 데이터 구조

### Ingredient (레시피별 재료)
```python
class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe)
    original_name = models.CharField()        # "수육용 돼지고기 300g"
    normalized_ingredient = models.ForeignKey(NormalizedIngredient, null=True)
    quantity = models.CharField(blank=True)   # "300g" (향후 파싱)
    is_essential = models.BooleanField()      # 필수 재료 여부
```

### NormalizedIngredient (정규화 재료)
```python
class NormalizedIngredient(models.Model):
    name = models.CharField(unique=True)      # "돼지고기"
    category = models.CharField()             # "meat"
    is_common_seasoning = models.BooleanField()  # 범용 조미료 여부
    description = models.TextField()          # 관리자용 메모
```

## 정규화 프로세스

### Phase 1: 자동 분석

**스크립트**: `app/recipes/management/commands/analyze_ingredients.py`

#### 1.1 기본 재료명 추출

**규칙**:
- 수량 제거: `300g`, `1큰술`, `2개` 등
- 용도 제거: `수육용`, `구이용`, `국거리용` 등
- 수식어 제거: `신선한`, `국내산`, `유기농` 등
- 특수 표현 제거: `(선택)`, `[optional]` 등

**예시**:
```python
"수육용 돼지고기 300g" → "돼지고기"
"신선한 양파 2개" → "양파"
"깨소금 1큰술" → "소금"
"국거리용 무 200g" → "무"
```

**구현**:
```python
def extract_base_name(original_name: str) -> str:
    # 1. 수량 패턴 제거 (정규식)
    patterns = [
        r'\d+g',       # 300g
        r'\d+ml',      # 500ml
        r'\d+큰술',     # 1큰술
        r'\d+작은술',   # 2작은술
        r'\d+개',      # 3개
        r'\d+컵',      # 1컵
    ]

    # 2. 용도 패턴 제거
    purpose_patterns = ['수육용', '구이용', '국거리용', '볶음용']

    # 3. 수식어 제거
    modifiers = ['신선한', '국내산', '유기농', '손질된']

    # 4. 특수 표현 제거
    # (선택), [optional] 등

    return cleaned_name
```

#### 1.2 유사 재료 그룹화

**방법**: Fuzzy Matching (문자열 유사도)

**라이브러리**: `python-Levenshtein`, `fuzzywuzzy`

**기준**:
- 유사도 80% 이상: 같은 재료로 판단
- 예: "돼지고기", "돼지 고기", "돼지고기살" → "돼지고기"

**구현**:
```python
from fuzzywuzzy import fuzz

def group_similar_ingredients(ingredients: List[str]) -> List[List[str]]:
    groups = []
    threshold = 80

    for ingredient in ingredients:
        matched = False
        for group in groups:
            if fuzz.ratio(ingredient, group[0]) >= threshold:
                group.append(ingredient)
                matched = True
                break

        if not matched:
            groups.append([ingredient])

    return groups
```

#### 1.3 범용 조미료 탐지

**정의**: 거의 모든 레시피에 등장하는 조미료

**탐지 기준**:
- 등장 빈도 80% 이상인 재료
- 예: 소금, 후추, 간장, 참기름, 식용유

**목적**: 추천 알고리즘에서 낮은 가중치 부여

**구현**:
```python
def detect_common_seasonings(recipes: List[Recipe]) -> List[str]:
    total_recipes = len(recipes)
    ingredient_count = defaultdict(int)

    for recipe in recipes:
        for ingredient in recipe.ingredients.all():
            normalized = extract_base_name(ingredient.original_name)
            ingredient_count[normalized] += 1

    common_seasonings = []
    for ingredient, count in ingredient_count.items():
        if count / total_recipes >= 0.8:  # 80% 이상
            common_seasonings.append(ingredient)

    return common_seasonings
```

#### 1.4 제안 생성

**출력**: JSON 파일

**파일 1**: `suggestions.json`
```json
[
  {
    "normalized_name": "돼지고기",
    "category": "meat",
    "variations": [
      "수육용 돼지고기 300g",
      "구이용 돼지고기 200g",
      "돼지고기 앞다리 500g"
    ],
    "confidence": 0.95
  },
  {
    "normalized_name": "소금",
    "category": "seasoning",
    "variations": [
      "소금 1작은술",
      "굵은소금 1큰술",
      "깨소금 조금"
    ],
    "confidence": 0.88
  }
]
```

**파일 2**: `common_seasonings.json`
```json
[
  {
    "name": "소금",
    "frequency": 0.95,
    "recipe_count": 95
  },
  {
    "name": "후추",
    "frequency": 0.82,
    "recipe_count": 82
  }
]
```

### Phase 2: 관리자 검증

**도구**: Django Admin 커스텀 페이지

#### 2.1 제안 검토

**UI 구성**:
- 정규화 제안 목록 테이블
- 각 제안의 variations 표시
- 승인/거부/수정 버튼

**워크플로우**:
1. 관리자가 제안 목록 확인
2. 정규화명 수정 가능
3. 카테고리 선택
4. 범용 조미료 체크
5. 승인 → NormalizedIngredient 생성

#### 2.2 수동 정규화

**경우**:
- 자동 제안이 부정확한 경우
- 새로운 재료 추가
- 복잡한 재료명 (예: "돼지고기 + 쇠고기 섞은것")

**방법**:
- Ingredient Admin에서 직접 normalized_ingredient 선택
- 또는 새 NormalizedIngredient 생성 후 연결

#### 2.3 중복 병합

**시나리오**: 실수로 "돼지고기"와 "돼지 고기"가 별도로 생성됨

**기능**: Admin Action - "병합"
```python
def merge_normalized_ingredients(admin, request, queryset):
    # 1. 선택한 NormalizedIngredient 중 하나를 기준으로 선택
    # 2. 나머지 NormalizedIngredient의 Ingredient들을 기준으로 이동
    # 3. 나머지 NormalizedIngredient 삭제
    pass
```

### Phase 3: 자동 적용

**스크립트**: `app/recipes/management/commands/apply_normalization.py`

**워크플로우**:
1. `suggestions.json` 읽기
2. NormalizedIngredient 생성 (bulk_create)
3. Ingredient.normalized_ingredient 연결 (bulk_update)
4. `common_seasonings.json` 기반 is_common_seasoning 설정

**실행**:
```bash
python app/manage.py apply_normalization suggestions.json common_seasonings.json
```

## 추천 알고리즘 통합

### 매칭 로직

```python
def calculate_match_score(recipe: Recipe, fridge_ingredients: List[NormalizedIngredient]) -> int:
    # 1. Recipe의 필수 재료 추출 (조미료 제외)
    essential_ingredients = recipe.ingredients.filter(
        is_essential=True
    ).exclude(
        normalized_ingredient__is_common_seasoning=True
    )

    # 2. 필수 재료와 냉장고 재료 매칭
    matched_count = essential_ingredients.filter(
        normalized_ingredient__in=fridge_ingredients
    ).count()

    total_count = essential_ingredients.count()

    # 3. 매칭률 계산 (0-100)
    if total_count == 0:
        return 0

    base_score = (matched_count / total_count) * 100

    # 4. 조미료 보너스 (최대 +5점)
    seasoning_ingredients = recipe.ingredients.filter(
        normalized_ingredient__is_common_seasoning=True,
        normalized_ingredient__in=fridge_ingredients
    )
    bonus = min(seasoning_ingredients.count(), 5)

    return int(base_score + bonus)
```

### 정렬 전략

**우선순위**:
1. **매칭 점수** (내림차순) - 가장 중요
2. **부족한 필수 재료 수** (오름차순) - 적을수록 좋음
3. **난이도** (오름차순) - "아무나" 우선
4. **조리 시간** (오름차순) - 짧을수록 좋음

## 시나리오별 처리 방법

### 시나리오 1: 범용 조미료 처리

**문제**: 사용자가 "소금"을 입력하면 거의 모든 레시피가 매칭됨

**해결책**:
1. NormalizedIngredient에서 `is_common_seasoning=True` 표시
2. 추천 알고리즘에서 조미료는 **보너스 점수**로만 활용
3. 필수 재료 매칭률을 주요 점수로 사용

**예시**:
- 레시피 A: 필수 재료 5개 중 4개 매칭 (80%) + 조미료 3개 매칭 (+3) = **83점**
- 레시피 B: 필수 재료 5개 중 2개 매칭 (40%) + 조미료 5개 매칭 (+5) = **45점**
- 결과: 레시피 A가 우선 추천

### 시나리오 2: 재료명 모호성 처리

**문제**: 사용자가 "깨소금"과 "소금"의 차이를 모름

**해결책**:
1. 자동 정규화에서 "깨소금" → "소금"으로 매핑
2. 검색 시 "소금"을 입력하면 "깨소금" 포함 레시피도 매칭
3. 레시피에는 "깨소금 1큰술"로 정확히 표시

**예시**:
- 사용자 냉장고: "소금"
- 레시피 A 재료: "깨소금 1큰술" (normalized: "소금")
- 레시피 B 재료: "굵은소금 1작은술" (normalized: "소금")
- 결과: 레시피 A, B 모두 매칭

### 시나리오 3: 돼지고기 세부 부위 처리

**문제**: "수육용 돼지고기"와 "구이용 돼지고기"의 차이를 모름

**해결책**:
1. 모두 "돼지고기"로 정규화
2. 사용자가 "돼지고기" 입력 시 모든 관련 레시피 매칭
3. 레시피에는 원본대로 표시하여 사용자가 선택 가능

**고도화 (향후)**:
- 부위별 상세 분류: "돼지고기 삼겹살", "돼지고기 목살"
- 사용자가 상세 검색 가능하도록 옵션 제공

## 데이터 품질 검증

### 검증 스크립트

**파일**: `app/recipes/management/commands/validate_normalization.py`

**검증 항목**:

1. **정규화 누락 검사**
   ```python
   unnormalized = Ingredient.objects.filter(
       normalized_ingredient__isnull=True
   ).count()
   # 경고: 정규화되지 않은 재료 {count}개
   ```

2. **고아 정규화 재료 검사**
   ```python
   orphan_normalized = NormalizedIngredient.objects.annotate(
       ingredient_count=Count('ingredient')
   ).filter(ingredient_count=0)
   # 경고: 사용되지 않는 정규화 재료 {count}개 (삭제 권장)
   ```

3. **중복 의심 검사**
   ```python
   from fuzzywuzzy import fuzz

   normalized_ingredients = NormalizedIngredient.objects.all()
   duplicates = []

   for i, ing1 in enumerate(normalized_ingredients):
       for ing2 in normalized_ingredients[i+1:]:
           if fuzz.ratio(ing1.name, ing2.name) >= 80:
               duplicates.append((ing1, ing2))
   # 경고: 중복 의심 {count}쌍
   ```

4. **범용 조미료 재검증**
   ```python
   total_recipes = Recipe.objects.count()

   for seasoning in NormalizedIngredient.objects.filter(is_common_seasoning=True):
       usage_count = Ingredient.objects.filter(
           normalized_ingredient=seasoning
       ).values('recipe').distinct().count()

       if usage_count / total_recipes < 0.7:
           # 경고: {seasoning.name}의 사용 빈도가 70% 미만
   ```

### 리포트 형식

```json
{
  "validation_date": "2024-01-01T00:00:00Z",
  "errors": [
    {
      "type": "unnormalized_ingredient",
      "count": 5,
      "samples": ["신비한 재료1", "알 수 없는 재료2"]
    }
  ],
  "warnings": [
    {
      "type": "orphan_normalized",
      "count": 3,
      "items": ["사용안됨1", "사용안됨2"]
    },
    {
      "type": "possible_duplicate",
      "count": 2,
      "pairs": [
        ["돼지고기", "돼지 고기"],
        ["양파", "양 파"]
      ]
    }
  ],
  "summary": {
    "total_recipes": 100,
    "total_ingredients": 500,
    "total_normalized": 150,
    "normalized_rate": 0.95
  }
}
```

## 성과 지표

### 정량적 지표
- **정규화율**: 95% 이상 (Ingredient 중 normalized_ingredient 연결 비율)
- **중복 제거율**: 80% 이상 (유사 재료 병합 비율)
- **범용 조미료 탐지 정확도**: 90% 이상
- **검색 재현율**: 사용자가 "돼지고기" 검색 시 관련 레시피 95% 이상 매칭

### 정성적 지표
- 관리자가 정규화 작업을 5분 이내에 10개 수행 가능
- 사용자가 간단한 검색어로 원하는 레시피 찾기 가능
- 레시피 정보의 정확성 유지 (원본 재료명 표시)

## 도구 및 라이브러리

### 필수
- `python-Levenshtein`: 문자열 유사도 계산
- `fuzzywuzzy`: Fuzzy matching
- Django ORM: 데이터베이스 작업

### 선택사항
- `konlpy`: 한국어 형태소 분석 (고도화 시)
- `pandas`: CSV 데이터 분석
- `scikit-learn`: 머신러닝 기반 분류 (고도화 시)

## 향후 개선 방향

### 1. 수량 파싱 및 매칭
- "300g" → {value: 300, unit: "g"}
- 사용자 냉장고에 수량 입력 가능
- 레시피 추천 시 수량 고려

### 2. 동의어 사전
- "대파" ↔ "파"
- "애호박" ↔ "호박"
- 수동 관리 또는 자동 학습

### 3. 머신러닝 기반 분류
- 재료 카테고리 자동 분류
- 범용 조미료 자동 탐지
- 학습 데이터 축적 필요

### 4. 사용자 피드백 반영
- 사용자가 재료 매칭 오류 신고
- 관리자가 검토 후 정규화 수정
- 지속적인 품질 개선
