# 레시피 추천 API 문서 (GET)

## 개요

정규화된 재료 목록을 쿼리 파라미터로 받아 유사도 기반 레시피를 추천하는 API

## API 명세

### 엔드포인트

```
GET /fridge2fork/v1/recipes/recommendations
```

### 요청 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| ingredients | string | O | - | 쉼표로 구분된 정규화 재료명 (예: "돼지고기,배추,두부") |
| limit | int | X | 20 | 추천 레시피 최대 개수 (1-100) |
| algorithm | string | X | "jaccard" | 유사도 알고리즘 ("jaccard", "cosine") |
| exclude_seasonings | bool | X | true | 범용 조미료 제외 여부 |
| min_match_rate | float | X | 0.3 | 최소 매칭률 (0.0-1.0) |

### 응답 스키마

```json
{
  "recipes": [
    {
      "recipe_sno": "RCP600",
      "name": "김치찌개",
      "title": "돼지고기 김치찌개",
      "servings": "4.0",
      "difficulty": "아무나",
      "cooking_time": "30.0",
      "image_url": "http://example.com/image.jpg",
      "introduction": "맛있는 김치찌개",
      "match_score": 0.85,
      "matched_count": 8,
      "total_count": 10,
      "algorithm": "jaccard"
    }
  ],
  "total": 15,
  "algorithm": "jaccard",
  "summary": "85% 이상 매칭"
}
```

#### RecipeRecommendationsResponseSchema

| 필드 | 타입 | 설명 |
|------|------|------|
| recipes | List[RecommendedRecipeSchema] | 추천 레시피 목록 |
| total | int | 전체 추천 레시피 개수 |
| algorithm | str | 사용된 유사도 알고리즘 |
| summary | str | 매칭률 요약 (예: "85% 이상 매칭") |

#### RecommendedRecipeSchema

| 필드 | 타입 | 설명 |
|------|------|------|
| recipe_sno | str | 레시피 일련번호 |
| name | str | 요리명 |
| title | str | 레시피 제목 |
| servings | str | 인분 |
| difficulty | str | 난이도 |
| cooking_time | str | 조리 시간 |
| image_url | Optional[str] | 이미지 URL |
| introduction | Optional[str] | 소개 |
| match_score | float | 매칭 점수 (0.0-1.0) |
| matched_count | int | 매칭된 재료 수 |
| total_count | int | 레시피 전체 재료 수 |
| algorithm | str | 사용된 알고리즘 |

### 유사도 알고리즘

#### 1. Jaccard Similarity (기본값)

**정의**: 교집합을 합집합으로 나눈 값

```
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```

**장점**:
- 구현이 간단하고 직관적
- 재료 개수가 다른 레시피 간 비교에 유리
- 대칭적 유사도 (A→B = B→A)

**예시**:
- 사용자 재료: {돼지고기, 배추, 두부} (3개)
- 레시피 재료: {돼지고기, 배추, 김치, 된장} (4개)
- 교집합: {돼지고기, 배추} (2개)
- 합집합: {돼지고기, 배추, 두부, 김치, 된장} (5개)
- **Jaccard = 2/5 = 0.4**

#### 2. Cosine Similarity

**정의**: 두 벡터 간의 코사인 각도

```
Cosine(A, B) = (A · B) / (||A|| × ||B||)
```

**장점**:
- 방향성을 고려한 유사도
- 크기보다는 패턴 유사성 강조
- 문서 유사도에서 널리 사용

**구현**:
- 재료를 이진 벡터로 표현 (있으면 1, 없으면 0)
- 내적(dot product) 계산
- 각 벡터의 크기로 정규화

**예시**:
- 사용자 재료 벡터: [1, 1, 1, 0, 0] (돼지고기, 배추, 두부)
- 레시피 재료 벡터: [1, 1, 0, 1, 1] (돼지고기, 배추, 김치, 된장)
- 내적: 1×1 + 1×1 + 1×0 + 0×1 + 0×1 = 2
- ||A|| = √(1² + 1² + 1²) = √3
- ||B|| = √(1² + 1² + 1² + 1²) = 2
- **Cosine = 2 / (√3 × 2) ≈ 0.577**

### 비즈니스 로직

1. **재료 정규화**
   - 쿼리 파라미터로 받은 재료명으로 정규화 재료 조회
   - 존재하지 않는 재료는 무시

2. **조미료 제외**
   - `exclude_seasonings=true`일 때 범용 조미료 제외
   - `is_common_seasoning=True` 재료 필터링

3. **유사도 계산**
   - Jaccard: 교집합 / 합집합
   - Cosine: 내적 / (크기1 × 크기2)

4. **필터링 및 정렬**
   - `min_match_rate` 이상인 레시피만 포함
   - 유사도 점수 내림차순 정렬
   - `limit` 개수만큼 반환

5. **매칭률 요약**
   - 80% 이상: "80% 이상 매칭"
   - 50% 이상: "50% 이상 매칭"
   - 30% 이상: "30% 이상 매칭"

### 사용 사례

**UC-1: Jaccard 유사도로 레시피 추천**
- 요청: `GET /recipes/recommendations?ingredients=돼지고기,배추,두부&limit=10`
- 응답: Jaccard 유사도 기반 상위 10개 레시피
- 목적: 재료 개수 차이를 고려한 균형잡힌 추천

**UC-2: Cosine 유사도로 레시피 추천**
- 요청: `GET /recipes/recommendations?ingredients=돼지고기,배추&algorithm=cosine&limit=20`
- 응답: Cosine 유사도 기반 상위 20개 레시피
- 목적: 재료 패턴 유사성 강조

**UC-3: 조미료 포함 추천**
- 요청: `GET /recipes/recommendations?ingredients=소금,설탕,간장&exclude_seasonings=false`
- 응답: 조미료를 포함한 레시피 추천
- 목적: 조미료 위주 재료 검색

**UC-4: 높은 매칭률만 추천**
- 요청: `GET /recipes/recommendations?ingredients=돼지고기,배추,김치&min_match_rate=0.7`
- 응답: 70% 이상 매칭되는 레시피만 반환
- 목적: 거의 완벽히 만들 수 있는 레시피만 추천

### 성능 최적화

- **prefetch_related**: N+1 쿼리 방지
- **인덱스 활용**: `normalized_ingredient_id` 인덱스
- **메모리 계산**: DB 조회 후 Python에서 유사도 계산
- **필터링**: `min_match_rate`로 불필요한 레시피 제외

### 에러 케이스

| 상황 | HTTP 상태 | 응답 |
|------|-----------|------|
| 정상 조회 | 200 | 추천 레시피 목록 |
| 재료 없음 | 200 | `{"recipes": [], "total": 0}` |
| limit 범위 초과 | 200 | 자동으로 1-100 범위로 제한 |
| 잘못된 algorithm | 400 | `{"error": "InvalidAlgorithm"}` |

### 테스트 케이스

**TC-1: Jaccard 유사도 계산 (기본)**
- Given: 사용자 재료 [돼지고기, 배추], 레시피 재료 [돼지고기, 배추, 김치]
- When: `GET /recommendations?ingredients=돼지고기,배추`
- Then: Jaccard = 2/3 ≈ 0.67

**TC-2: Cosine 유사도 계산**
- Given: 사용자 재료 [돼지고기, 배추], 레시피 재료 [돼지고기, 배추, 김치]
- When: `GET /recommendations?ingredients=돼지고기,배추&algorithm=cosine`
- Then: Cosine ≈ 0.816

**TC-3: limit 파라미터**
- Given: 30개 레시피 매칭
- When: `GET /recommendations?ingredients=돼지고기&limit=5`
- Then: 상위 5개만 반환

**TC-4: 조미료 제외**
- Given: 레시피에 소금(조미료) 포함
- When: `GET /recommendations?ingredients=소금&exclude_seasonings=true`
- Then: 소금이 제외된 재료로 유사도 계산

**TC-5: min_match_rate 필터링**
- Given: 레시피 A(0.8), B(0.5), C(0.2)
- When: `GET /recommendations?ingredients=돼지고기&min_match_rate=0.5`
- Then: A, B만 반환 (C 제외)

**TC-6: 재료 없을 때**
- Given: 존재하지 않는 재료명
- When: `GET /recommendations?ingredients=존재하지않는재료`
- Then: `{"recipes": [], "total": 0}`

**TC-7: 유사도 내림차순 정렬**
- Given: 레시피 A(0.5), B(0.9), C(0.7)
- When: `GET /recommendations?ingredients=돼지고기`
- Then: 순서 [B(0.9), C(0.7), A(0.5)]

### 기존 /recommend (POST)와의 차이

| 항목 | /recommendations (GET) | /recommend (POST) |
|------|------------------------|-------------------|
| HTTP 메서드 | GET | POST |
| 재료 전달 | Query String | Request Body |
| 유사도 알고리즘 | Jaccard, Cosine (선택) | Jaccard 고정 |
| limit 지정 | 가능 (1-100) | 고정 20개 |
| min_match_rate | 사용자 지정 | 고정 0.3 |
| 캐싱 가능 | Yes (GET) | No (POST) |
| 사용 목적 | 검색, 탐색 | 냉장고 기반 추천 |
