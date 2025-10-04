# 레시피 추천 API 문서 (GET)

## 개요

정규화된 재료 목록을 쿼리 파라미터로 받아 **레시피 기준 매칭률**로 레시피를 추천하는 API

> **Note**: 이전 버전의 Jaccard/Cosine 유사도 알고리즘은 사용자 재료가 많을수록 점수가 낮아지는 문제로 인해 **레시피 기준 매칭률**로 변경되었습니다. (algorithm 파라미터는 호환성을 위해 유지됩니다)

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
| algorithm | string | X | "jaccard" | 알고리즘 선택 (호환성 유지용, 실제로는 레시피 기준 매칭률 사용) |
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

### 매칭률 계산 방식

#### 레시피 기준 매칭률 (현재 사용 중)

**정의**: 사용자가 레시피에 필요한 재료를 얼마나 가지고 있는지를 백분율로 계산

```
match_score = 보유 재료 수 / 레시피 전체 재료 수
```

**장점**:
- 직관적: "레시피를 만들 수 있는가"를 명확하게 표현
- 사용자 재료가 많아도 점수가 낮아지지 않음
- 레시피 완성도를 백분율로 명확히 표시

**예시 1**: 레시피 재료를 모두 보유
- 사용자 재료: {대패삼겹살, 배추}
- 레시피 재료: {대패삼겹살, 배추}
- **매칭률: 2/2 = 1.0 (100%)** ✅

**예시 2**: 사용자가 재료를 더 많이 보유
- 사용자 재료: {대패삼겹살, 배추, 양파, 마늘, 고추}
- 레시피 재료: {대패삼겹살, 배추}
- **매칭률: 2/2 = 1.0 (100%)** ✅

**예시 3**: 일부 재료만 보유
- 사용자 재료: {대패삼겹살}
- 레시피 재료: {대패삼겹살, 배추}
- **매칭률: 1/2 = 0.5 (50%)** ⚠️

**정렬 우선순위**:
1. 매칭률 (높은 순)
2. 매칭된 재료 수 (많은 순, 동률일 때)

### 비즈니스 로직

1. **재료 정규화**
   - 쿼리 파라미터로 받은 재료명으로 정규화 재료 조회
   - 존재하지 않는 재료는 무시

2. **조미료 제외**
   - `exclude_seasonings=true`일 때 범용 조미료 제외
   - `is_common_seasoning=True` 재료 필터링

3. **매칭률 계산**
   - match_score = 보유 재료 수 / 레시피 전체 재료 수
   - 사용자 재료가 많아도 점수 유지

4. **필터링 및 정렬**
   - `min_match_rate` 이상인 레시피만 포함
   - 1차: 매칭률 내림차순, 2차: 매칭 재료 수 내림차순
   - `limit` 개수만큼 반환

5. **매칭률 요약**
   - 80% 이상: "80% 이상 매칭"
   - 50% 이상: "50% 이상 매칭"
   - 30% 이상: "30% 이상 매칭"

### 사용 사례

**UC-1: 기본 레시피 추천**
- 요청: `GET /recipes/recommendations?ingredients=대패삼겹살,배추&limit=10`
- 응답: 매칭률 기반 상위 10개 레시피
- 목적: 레시피 재료를 얼마나 가지고 있는지 표시

**UC-2: 많은 재료로 추천**
- 요청: `GET /recipes/recommendations?ingredients=대패삼겹살,배추,양파,마늘,고추&limit=20`
- 응답: 레시피 재료를 모두 가진 경우 100% 표시
- 목적: 사용자 재료가 많아도 정확한 매칭률 표시

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

**TC-1: 레시피 기준 매칭률 계산 (100%)**
- Given: 사용자 재료 [대패삼겹살, 배추], 레시피 재료 [대패삼겹살, 배추]
- When: `GET /recommendations?ingredients=대패삼겹살,배추`
- Then: match_score = 2/2 = 1.0 (100%)

**TC-2: 사용자 재료가 많은 경우 (여전히 100%)**
- Given: 사용자 재료 [대패삼겹살, 배추, 양파, 마늘], 레시피 재료 [대패삼겹살, 배추]
- When: `GET /recommendations?ingredients=대패삼겹살,배추,양파,마늘`
- Then: match_score = 2/2 = 1.0 (100%)

**TC-2.5: 일부 재료만 보유**
- Given: 사용자 재료 [대패삼겹살], 레시피 재료 [대패삼겹살, 배추]
- When: `GET /recommendations?ingredients=대패삼겹살`
- Then: match_score = 1/2 = 0.5 (50%)

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

**TC-7: 매칭률 및 재료 수 정렬**
- Given: 레시피 A(0.5, 2개), B(0.9, 3개), C(0.9, 5개)
- When: `GET /recommendations?ingredients=돼지고기`
- Then: 순서 [C(0.9, 5개), B(0.9, 3개), A(0.5, 2개)]
  - 1차 정렬: 매칭률 (0.9 > 0.5)
  - 2차 정렬: 매칭 재료 수 (5 > 3)

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
