# 카테고리 유니크 목록 조회 API 문서

## 개요

정규화된 재료(NormalizedIngredient)의 카테고리 유니크 목록을 조회하는 API 엔드포인트

## API 명세

### 엔드포인트

```
GET /fridge2fork/v1/recipes/categories
```

### 요청 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| category_type | string | X | "normalized" | 카테고리 타입 ("normalized", "ingredient") |

### 응답 스키마

```json
{
  "categories": [
    {
      "id": 1,
      "name": "육류",
      "code": "meat",
      "icon": "🥩",
      "display_order": 1
    }
  ],
  "total": 5
}
```

#### CategoryListResponseSchema

| 필드 | 타입 | 설명 |
|------|------|------|
| categories | List[IngredientCategorySchema] | 카테고리 목록 |
| total | int | 전체 카테고리 개수 |

#### IngredientCategorySchema (재사용)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | int | 카테고리 ID |
| name | str | 카테고리명 (예: "육류", "채소류") |
| code | str | 카테고리 코드 (예: "meat", "vegetable") |
| icon | Optional[str] | 아이콘 (이모지 또는 아이콘 클래스) |
| display_order | int | 표시 순서 |

### 비즈니스 로직

1. **카테고리 필터링**
   - `category_type`으로 필터링 (기본: "normalized")
   - `is_active=True`인 카테고리만 조회

2. **정렬**
   - `display_order` 오름차순
   - 동일 순서일 경우 `name` 오름차순

3. **응답 생성**
   - 활성화된 카테고리만 반환
   - 전체 개수 포함

### 사용 사례

**UC-1: 앱에서 냉장고 재료 추가 시 카테고리 필터 표시**
- 요청: `GET /recipes/categories?category_type=normalized`
- 응답: 정규화 재료용 카테고리 목록 (육류, 채소류, 해산물 등)
- 목적: 사용자가 카테고리별로 재료를 필터링하여 선택

**UC-2: 관리자 페이지에서 재료 카테고리 목록 표시**
- 요청: `GET /recipes/categories`
- 응답: 모든 활성 카테고리 목록
- 목적: 재료 등록 시 카테고리 선택 옵션 제공

### 성능 최적화

- **인덱스 활용**: `category_type_active_idx` 인덱스 사용
- **쿼리 최적화**: 활성 카테고리만 필터링하여 결과 최소화
- **정렬**: DB 레벨에서 `display_order` 정렬

### 에러 케이스

| 상황 | HTTP 상태 | 응답 |
|------|-----------|------|
| 정상 조회 | 200 | 카테고리 목록 반환 |
| 카테고리 없음 | 200 | `{"categories": [], "total": 0}` |

### 테스트 케이스

**TC-1: 정규화 재료 카테고리 조회**
- Given: 정규화 재료 카테고리 5개 존재 (모두 활성)
- When: `GET /recipes/categories?category_type=normalized`
- Then: 5개 카테고리 반환, display_order 순서로 정렬

**TC-2: 비활성 카테고리 제외**
- Given: 정규화 재료 카테고리 3개 (2개 활성, 1개 비활성)
- When: `GET /recipes/categories?category_type=normalized`
- Then: 활성 카테고리 2개만 반환

**TC-3: 기본값으로 조회**
- Given: 정규화 재료 카테고리 3개, 재료 카테고리 2개
- When: `GET /recipes/categories` (파라미터 없음)
- Then: 정규화 재료 카테고리 3개만 반환

**TC-4: 카테고리 없을 때**
- Given: 카테고리 0개
- When: `GET /recipes/categories`
- Then: `{"categories": [], "total": 0}` 반환

**TC-5: display_order 정렬 확인**
- Given: 카테고리 순서 [채소류(10), 육류(1), 해산물(5)]
- When: `GET /recipes/categories`
- Then: 반환 순서 [육류(1), 해산물(5), 채소류(10)]
