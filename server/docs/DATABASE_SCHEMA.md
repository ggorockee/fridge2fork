# 데이터베이스 스키마 설계

## 개요

Fridge2Fork 프로젝트의 PostgreSQL 데이터베이스 스키마 설계 문서입니다.

### 설계 원칙
- **정규화 우선**: 데이터 중복 최소화
- **재료 정규화**: 원본 재료명과 정규화된 재료명 분리
- **확장 가능성**: 향후 기능 추가를 고려한 설계
- **TDD**: 모든 모델은 테스트 주도 개발

## ERD (Entity-Relationship Diagram)

```
┌─────────────────┐
│      User       │
├─────────────────┤
│ id (PK)         │
│ email (UNIQUE)  │
│ password        │
│ username        │
│ is_active       │
│ is_staff        │
│ date_joined     │
└─────────────────┘
         │ 1
         │
         │ 0..1
         ▼
┌─────────────────┐
│     Fridge      │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │── nullable (비회원 지원)
│ session_key     │── nullable (비회원용)
│ created_at      │
│ updated_at      │
└─────────────────┘
         │ 1
         │
         │ N
         ▼
┌──────────────────────┐
│  FridgeIngredient    │
├──────────────────────┤
│ id (PK)              │
│ fridge_id (FK)       │
│ normalized_ingredient_id (FK)
│ added_at             │
└──────────────────────┘
         │ N
         │
         │ 1
         ▼
┌──────────────────────┐         ┌─────────────────┐
│ NormalizedIngredient │         │     Recipe      │
├──────────────────────┤         ├─────────────────┤
│ id (PK)              │         │ id (PK)         │
│ name (UNIQUE)        │         │ recipe_sno      │
│ category             │         │ title           │
│ is_common_seasoning  │         │ name            │
│ description          │         │ introduction    │
│ created_at           │         │ servings        │
└──────────────────────┘         │ difficulty      │
         │ 1                     │ cooking_time    │
         │                       │ method          │
         │ N                     │ situation       │
         ▼                       │ ingredient_type │
┌──────────────────────┐         │ recipe_type     │
│     Ingredient       │         │ image_url       │
├──────────────────────┤         │ views           │
│ id (PK)              │         │ recommendations │
│ recipe_id (FK)       │◄────┐   │ scraps          │
│ normalized_ingredient_id (FK) │ created_at      │
│ original_name        │     └───│ updated_at      │
│ quantity             │         └─────────────────┘
│ is_essential         │                 │ 1
└──────────────────────┘                 │
                                         │ N
                                         ▼
                              (Ingredient 테이블)
```

## 테이블 상세 설계

### 1. User (사용자)

**용도**: Custom User 모델 (email 기반 인증)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigAutoField | PK | 자동 증가 ID |
| email | EmailField(255) | UNIQUE, NOT NULL | 이메일 (로그인 ID) |
| password | CharField(128) | NOT NULL | 해시된 비밀번호 |
| username | CharField(150) | NULL, 중복 허용 | 닉네임 (optional) |
| is_active | BooleanField | DEFAULT TRUE | 활성 상태 |
| is_staff | BooleanField | DEFAULT FALSE | 관리자 여부 |
| is_superuser | BooleanField | DEFAULT FALSE | 슈퍼유저 여부 |
| date_joined | DateTimeField | AUTO NOW ADD | 가입일 |

**인덱스**:
- `email` (UNIQUE 인덱스)

**비즈니스 로직**:
- username이 없으면 email의 "@" 앞부분 사용
- username 중복 허용

### 2. Recipe (레시피)

**용도**: 레시피 정보 저장

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigAutoField | PK | 자동 증가 ID |
| recipe_sno | CharField(50) | UNIQUE, NOT NULL | 원본 레시피 일련번호 |
| title | CharField(500) | NOT NULL | 레시피 제목 |
| name | CharField(200) | NOT NULL | 요리명 |
| introduction | TextField | NULL | 요리 소개 |
| servings | CharField(20) | NULL | 인분 (예: "4.0") |
| difficulty | CharField(50) | NULL | 난이도 (예: "아무나") |
| cooking_time | CharField(20) | NULL | 조리 시간 (예: "30.0") |
| method | CharField(100) | NULL | 조리 방법 (예: "볶음") |
| situation | CharField(100) | NULL | 조리 상황 (예: "일상") |
| ingredient_type | CharField(100) | NULL | 재료 유형 (예: "육류") |
| recipe_type | CharField(100) | NULL | 요리 종류 (예: "메인반찬") |
| image_url | URLField | NULL | 이미지 URL |
| views | IntegerField | DEFAULT 0 | 조회수 |
| recommendations | IntegerField | DEFAULT 0 | 추천수 |
| scraps | IntegerField | DEFAULT 0 | 스크랩수 |
| created_at | DateTimeField | AUTO NOW ADD | 생성일 |
| updated_at | DateTimeField | AUTO NOW | 수정일 |

**인덱스**:
- `recipe_sno` (UNIQUE 인덱스)
- `difficulty, cooking_time` (복합 인덱스 - 필터링용)
- `name` (검색용)

**정렬 기본값**: `-created_at` (최신순)

### 3. NormalizedIngredient (정규화 재료)

**용도**: 정규화된 재료명 관리

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigAutoField | PK | 자동 증가 ID |
| name | CharField(100) | UNIQUE, NOT NULL | 정규화된 재료명 |
| category | CharField(50) | NOT NULL | 카테고리 |
| is_common_seasoning | BooleanField | DEFAULT FALSE | 범용 조미료 여부 |
| description | TextField | NULL | 관리자용 메모 |
| created_at | DateTimeField | AUTO NOW ADD | 생성일 |

**카테고리 선택지**:
- `meat`: 육류
- `vegetable`: 채소류
- `seafood`: 해산물
- `seasoning`: 조미료
- `grain`: 곡물
- `dairy`: 유제품
- `etc`: 기타

**인덱스**:
- `name` (UNIQUE, 검색용)
- `category` (필터링용)

**비즈니스 로직**:
- 사용자 검색 시 이 테이블 기준
- `is_common_seasoning=True`: 소금, 후추 등 범용 조미료 (추천 알고리즘에서 낮은 가중치)

### 4. Ingredient (레시피별 재료)

**용도**: 레시피에 포함된 개별 재료

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigAutoField | PK | 자동 증가 ID |
| recipe_id | BigIntegerField | FK (Recipe), NOT NULL | 레시피 ID |
| normalized_ingredient_id | BigIntegerField | FK (NormalizedIngredient), NULL | 정규화 재료 ID |
| original_name | CharField(200) | NOT NULL | 원본 재료명 |
| quantity | CharField(100) | NULL | 수량 (예: "300g") |
| is_essential | BooleanField | DEFAULT TRUE | 필수 재료 여부 |

**관계**:
- `recipe`: Recipe.ingredients (역참조)
- `normalized_ingredient`: NormalizedIngredient (정규화 매핑)

**인덱스**:
- `recipe_id, normalized_ingredient_id` (복합 인덱스)
- `normalized_ingredient_id` (검색용)

**비즈니스 로직**:
- `original_name`: CSV에서 파싱된 원본 재료명 (레시피 표시용)
- `normalized_ingredient`: 정규화 매핑 (검색용)
- `is_essential`: 필수 재료 (추천 알고리즘에서 높은 가중치)

### 5. Fridge (냉장고)

**용도**: 사용자별/세션별 냉장고 관리

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigAutoField | PK | 자동 증가 ID |
| user_id | BigIntegerField | FK (User), NULL | 회원 ID |
| session_key | CharField(40) | NULL | 비회원 세션 키 |
| created_at | DateTimeField | AUTO NOW ADD | 생성일 |
| updated_at | DateTimeField | AUTO NOW | 수정일 |

**제약조건**:
- `user_id`와 `session_key` 중 하나는 필수 (체크 제약)
- 회원: `user_id` NOT NULL, `session_key` NULL
- 비회원: `user_id` NULL, `session_key` NOT NULL

**인덱스**:
- `user_id` (회원 냉장고 조회)
- `session_key` (비회원 냉장고 조회)

### 6. FridgeIngredient (냉장고-재료 중간 테이블)

**용도**: 냉장고에 담긴 재료 관리

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigAutoField | PK | 자동 증가 ID |
| fridge_id | BigIntegerField | FK (Fridge), NOT NULL | 냉장고 ID |
| normalized_ingredient_id | BigIntegerField | FK (NormalizedIngredient), NOT NULL | 재료 ID |
| added_at | DateTimeField | AUTO NOW ADD | 추가일 |

**제약조건**:
- `(fridge_id, normalized_ingredient_id)` UNIQUE (중복 방지)

**인덱스**:
- `fridge_id` (냉장고별 재료 조회)
- `normalized_ingredient_id` (재료별 사용 통계)

## 데이터 흐름

### 1. 레시피 등록 (관리자)

```
1. CSV 파일 업로드
2. Recipe 생성 (recipe_sno, name, title, ...)
3. 재료 파싱 (CKG_MTRL_CN 필드)
4. Ingredient 생성 (original_name만)
5. (관리자) 정규화 분석 실행
6. NormalizedIngredient 생성
7. Ingredient.normalized_ingredient 연결
```

### 2. 냉장고 재료 추가 (사용자)

```
1. 사용자가 "돼지고기" 검색
2. NormalizedIngredient.name으로 검색 (ILIKE)
3. 선택한 재료의 id를 FridgeIngredient에 추가
4. Fridge.updated_at 업데이트
```

### 3. 레시피 추천

```
1. 사용자의 Fridge 조회
2. FridgeIngredient 목록 조회 (정규화 재료 ID)
3. Recipe별 매칭 점수 계산:
   - Recipe의 Ingredient 조회
   - 필수 재료 (is_essential=True, is_common_seasoning=False) 추출
   - 매칭된 필수 재료 수 / 전체 필수 재료 수 = 점수
4. 점수순 정렬 및 반환
```

## 마이그레이션 순서

```
1. 0001_initial_user: User 모델
2. 0002_recipe: Recipe 모델
3. 0003_normalized_ingredient: NormalizedIngredient 모델
4. 0004_ingredient: Ingredient 모델 (Recipe, NormalizedIngredient FK)
5. 0005_fridge: Fridge, FridgeIngredient 모델
6. 0006_add_indexes: 인덱스 추가
```

## 데이터 크기 추정

**100개 레시피 기준** (MVP):
- Recipe: 100 rows
- Ingredient: ~500 rows (평균 5개/레시피)
- NormalizedIngredient: ~150 rows (정규화 후)
- User: ~100 rows (테스트)
- Fridge: ~100 rows
- FridgeIngredient: ~500 rows (평균 5개/냉장고)

**1000개 레시피 기준** (확장):
- Recipe: 1,000 rows
- Ingredient: ~5,000 rows
- NormalizedIngredient: ~500 rows
- User: ~10,000 rows
- Fridge: ~10,000 rows
- FridgeIngredient: ~50,000 rows

## 성능 최적화 전략

### 쿼리 최적화
- `select_related`: Recipe → Ingredient (FK)
- `prefetch_related`: Recipe → Ingredients (역참조)
- `annotate`: 재료 수, 매칭 수 계산

### 인덱스 전략
- 검색 필드: `NormalizedIngredient.name`
- 필터링 필드: `Recipe.difficulty`, `Recipe.cooking_time`
- FK 필드: 자동 인덱스

### 캐싱 전략
- 추천 결과: 1시간 캐시
- 레시피 상세: 24시간 캐시
- 정규화 재료 목록: 6시간 캐시

## 데이터 무결성

### 제약조건
- User.email: UNIQUE
- Recipe.recipe_sno: UNIQUE
- NormalizedIngredient.name: UNIQUE
- (Fridge.user_id, Fridge.session_key): 하나는 필수
- (FridgeIngredient.fridge_id, normalized_ingredient_id): UNIQUE

### Cascade 규칙
- Recipe 삭제 → Ingredient CASCADE (재료도 삭제)
- Fridge 삭제 → FridgeIngredient CASCADE
- NormalizedIngredient 삭제 → Ingredient SET NULL (원본은 유지)
- User 삭제 → Fridge CASCADE

## 확장 고려사항

### 향후 추가 가능한 필드
- Recipe.steps: JSON (조리 단계)
- Recipe.nutrition: JSON (영양 정보)
- Ingredient.quantity_value, quantity_unit: 수량 파싱
- User.profile_image, User.bio: 프로필 확장
- FavoriteRecipe: 즐겨찾기 테이블
- RecipeRating: 평점 테이블
