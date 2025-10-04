# Phase 5: API 엔드포인트 구현 (Django Ninja)

**목표**: 모바일 앱을 위한 RESTful API 구축
**예상 기간**: 1주
**우선순위**: 🔴 Critical

## 개요

Django Ninja를 사용하여 타입 안전한 API를 구축합니다. 회원/비회원 모두 냉장고 관리 및 레시피 추천 기능을 사용할 수 있도록 합니다.

### API 설계 원칙
- **RESTful 규칙** 준수
- **Type Safety**: Pydantic 스키마 사용
- **인증**: JWT (회원) + Session (비회원)
- **자동 문서화**: OpenAPI (Swagger)

## 체크리스트

### 5.1 프로젝트 구조 및 기본 설정

**파일**: `app/settings/settings.py`, `app/settings/urls.py`

- [ ] **Django Ninja 설정**
  - [ ] `pyproject.toml`에 django-ninja 추가 확인
  - [ ] NinjaAPI 인스턴스 생성
  - [ ] URL 라우팅 설정: `/api/v1/`
  - [ ] CORS 설정 (모바일 앱 허용)

- [ ] **API 디렉토리 구조 생성**
  ```
  app/api/
  ├── __init__.py
  ├── v1/
  │   ├── __init__.py
  │   ├── auth.py         # 인증 관련
  │   ├── fridge.py       # 냉장고 관리
  │   ├── recipes.py      # 레시피 조회
  │   ├── recommendations.py  # 추천
  │   └── users.py        # 사용자 프로필
  └── schemas.py          # Pydantic 스키마
  ```

- [ ] **기본 스키마 정의**
  - [ ] ErrorSchema: 에러 응답 형식
  - [ ] SuccessSchema: 성공 응답 형식
  - [ ] PaginationSchema: 페이지네이션

### 5.2 인증 API (TDD)

**파일**: `app/api/v1/auth.py`, `app/api/tests/test_auth_api.py`

- [ ] **Pydantic 스키마 정의** (`app/api/schemas.py`)
  ```python
  class RegisterSchema:
      email: EmailStr
      password: str
      username: Optional[str] = None

  class LoginSchema:
      email: EmailStr
      password: str

  class TokenSchema:
      access_token: str
      token_type: str = "bearer"

  class UserSchema:
      id: int
      email: str
      username: str
  ```

- [ ] **테스트 작성** (Test-First)
  - [ ] `test_register_with_email_password()`: 회원가입 성공
  - [ ] `test_register_without_username()`: username 자동 생성
  - [ ] `test_register_duplicate_email()`: 중복 이메일 에러
  - [ ] `test_login_success()`: 로그인 성공, 토큰 반환
  - [ ] `test_login_invalid_credentials()`: 잘못된 인증 정보
  - [ ] `test_get_current_user()`: 토큰으로 사용자 정보 조회

- [ ] **API 엔드포인트 구현**

  **POST `/api/v1/auth/register`**
  - [ ] 요청: RegisterSchema
  - [ ] 응답: TokenSchema + UserSchema
  - [ ] 로직: User 생성 → 토큰 발급

  **POST `/api/v1/auth/login`**
  - [ ] 요청: LoginSchema
  - [ ] 응답: TokenSchema + UserSchema
  - [ ] 로직: 인증 → 토큰 발급

  **GET `/api/v1/auth/me`**
  - [ ] 인증: Required (JWT)
  - [ ] 응답: UserSchema
  - [ ] 로직: 현재 사용자 정보 반환

- [ ] **JWT 인증 구현**
  - [ ] `pyproject.toml`에 `PyJWT` 추가
  - [ ] `create_access_token(user_id)` 함수
  - [ ] `decode_access_token(token)` 함수
  - [ ] Django Ninja Auth 클래스: `JWTAuth`

- [ ] **테스트 실행**
  - [ ] `python app/manage.py test app.api.tests.test_auth_api`
  - [ ] 모든 테스트 통과 확인

### 5.3 냉장고 관리 API (TDD)

**파일**: `app/api/v1/fridge.py`, `app/api/tests/test_fridge_api.py`

- [ ] **Pydantic 스키마 정의**
  ```python
  class FridgeIngredientSchema:
      id: int
      name: str  # normalized_ingredient.name
      category: str
      added_at: datetime

  class FridgeSchema:
      id: int
      ingredients: List[FridgeIngredientSchema]
      updated_at: datetime

  class AddIngredientSchema:
      ingredient_name: str  # 정규화 재료명

  class RemoveIngredientSchema:
      ingredient_id: int
  ```

- [ ] **테스트 작성** (Test-First)
  - [ ] `test_get_fridge_authenticated()`: 회원 냉장고 조회
  - [ ] `test_get_fridge_anonymous()`: 비회원 냉장고 조회 (세션 기반)
  - [ ] `test_add_ingredient_to_fridge()`: 재료 추가
  - [ ] `test_add_duplicate_ingredient()`: 중복 재료 에러
  - [ ] `test_remove_ingredient_from_fridge()`: 재료 제거
  - [ ] `test_clear_fridge()`: 냉장고 비우기
  - [ ] `test_search_ingredient_autocomplete()`: 재료 자동완성 검색

- [ ] **API 엔드포인트 구현**

  **GET `/api/v1/fridge`**
  - [ ] 인증: Optional (JWT 또는 Session)
  - [ ] 응답: FridgeSchema
  - [ ] 로직: 회원/비회원 냉장고 조회

  **POST `/api/v1/fridge/ingredients`**
  - [ ] 인증: Optional
  - [ ] 요청: AddIngredientSchema
  - [ ] 응답: FridgeSchema
  - [ ] 로직:
    - ingredient_name으로 NormalizedIngredient 조회
    - 없으면 404 에러
    - 중복 체크 후 FridgeIngredient 생성

  **DELETE `/api/v1/fridge/ingredients/{ingredient_id}`**
  - [ ] 인증: Optional
  - [ ] 응답: SuccessSchema
  - [ ] 로직: FridgeIngredient 삭제

  **DELETE `/api/v1/fridge/clear`**
  - [ ] 인증: Optional
  - [ ] 응답: SuccessSchema
  - [ ] 로직: 모든 FridgeIngredient 삭제

  **GET `/api/v1/fridge/ingredients/search`**
  - [ ] 쿼리 파라미터: `q` (검색어)
  - [ ] 응답: List[NormalizedIngredientSchema]
  - [ ] 로직: NormalizedIngredient 자동완성 검색 (ILIKE)

- [ ] **세션 기반 비회원 처리**
  - [ ] 세션 키 생성 로직
  - [ ] Fridge 조회/생성 시 session_key 활용

- [ ] **테스트 실행**
  - [ ] `python app/manage.py test app.api.tests.test_fridge_api`
  - [ ] 모든 테스트 통과 확인

### 5.4 레시피 조회 API (TDD)

**파일**: `app/api/v1/recipes.py`, `app/api/tests/test_recipes_api.py`

- [ ] **Pydantic 스키마 정의**
  ```python
  class RecipeListSchema:
      id: int
      name: str
      title: str
      image_url: Optional[str]
      difficulty: str
      cooking_time: str
      servings: str

  class IngredientDetailSchema:
      original_name: str
      normalized_name: str
      is_essential: bool

  class RecipeDetailSchema:
      id: int
      name: str
      title: str
      introduction: str
      ingredients: List[IngredientDetailSchema]
      servings: str
      difficulty: str
      cooking_time: str
      method: str
      situation: str
      recipe_type: str
      image_url: Optional[str]
      views: int
  ```

- [ ] **테스트 작성** (Test-First)
  - [ ] `test_list_recipes()`: 레시피 목록 조회
  - [ ] `test_list_recipes_with_pagination()`: 페이지네이션
  - [ ] `test_list_recipes_filter_by_difficulty()`: 난이도 필터
  - [ ] `test_get_recipe_detail()`: 레시피 상세 조회
  - [ ] `test_get_recipe_detail_not_found()`: 404 에러
  - [ ] `test_search_recipes_by_name()`: 이름 검색

- [ ] **API 엔드포인트 구현**

  **GET `/api/v1/recipes`**
  - [ ] 쿼리 파라미터:
    - `page`: 페이지 번호 (기본: 1)
    - `limit`: 페이지 크기 (기본: 20)
    - `difficulty`: 난이도 필터
    - `search`: 검색어 (name, title)
  - [ ] 응답: Paginated[RecipeListSchema]
  - [ ] 로직: Recipe 목록 조회, 페이지네이션 적용

  **GET `/api/v1/recipes/{recipe_id}`**
  - [ ] 응답: RecipeDetailSchema
  - [ ] 로직: Recipe 상세 조회, views+1 증가

- [ ] **페이지네이션 구현**
  - [ ] Django Ninja Pagination 사용
  - [ ] 총 페이지 수, 총 아이템 수 포함

- [ ] **테스트 실행**
  - [ ] `python app/manage.py test app.api.tests.test_recipes_api`
  - [ ] 모든 테스트 통과 확인

### 5.5 레시피 추천 API (TDD)

**파일**: `app/api/v1/recommendations.py`, `app/api/tests/test_recommendations_api.py`

- [ ] **Pydantic 스키마 정의**
  ```python
  class RecommendationSchema:
      recipe: RecipeListSchema
      score: int  # 0-100
      missing_ingredients: List[str]
      missing_count: int

  class RecommendationListSchema:
      recommendations: List[RecommendationSchema]
      total_count: int
  ```

- [ ] **테스트 작성** (Test-First)
  - [ ] `test_get_recommendations_authenticated()`: 회원 추천
  - [ ] `test_get_recommendations_anonymous()`: 비회원 추천
  - [ ] `test_get_recommendations_empty_fridge()`: 빈 냉장고
  - [ ] `test_get_recommendations_with_filters()`: 난이도/시간 필터
  - [ ] `test_get_recommendations_sorted_by_score()`: 점수순 정렬 확인

- [ ] **API 엔드포인트 구현**

  **GET `/api/v1/recommendations`**
  - [ ] 인증: Optional
  - [ ] 쿼리 파라미터:
    - `limit`: 추천 개수 (기본: 10, 최대: 50)
    - `min_score`: 최소 매칭 점수 (기본: 30)
    - `difficulty`: 난이도 필터
    - `max_time`: 최대 조리 시간 (분)
  - [ ] 응답: RecommendationListSchema
  - [ ] 로직:
    - 사용자 Fridge 조회
    - RecommendationService 호출
    - 필터 적용 및 정렬

- [ ] **캐싱 적용 (선택사항)**
  - [ ] 동일한 Fridge에 대한 추천은 캐시에서 반환
  - [ ] 캐시 만료: 1시간

- [ ] **테스트 실행**
  - [ ] `python app/manage.py test app.api.tests.test_recommendations_api`
  - [ ] 모든 테스트 통과 확인

### 5.6 에러 처리 및 검증

**파일**: `app/api/v1/__init__.py`, `app/api/exception_handlers.py`

- [ ] **커스텀 예외 클래스**
  - [ ] `NotFoundException`: 리소스 없음 (404)
  - [ ] `ValidationException`: 유효성 검사 실패 (400)
  - [ ] `AuthenticationException`: 인증 실패 (401)
  - [ ] `PermissionException`: 권한 없음 (403)

- [ ] **Exception Handler 구현**
  - [ ] Django Ninja의 exception_handlers 활용
  - [ ] 일관된 에러 응답 형식:
    ```json
    {
      "error": "NotFound",
      "message": "Recipe not found",
      "detail": {}
    }
    ```

- [ ] **Validation 강화**
  - [ ] Pydantic 스키마 활용
  - [ ] 커스텀 validator 추가

### 5.7 API 문서화

**파일**: `app/api/v1/__init__.py`

- [ ] **OpenAPI 설정**
  - [ ] API 제목, 버전, 설명 추가
  - [ ] 인증 스키마 문서화 (JWT)
  - [ ] 예제 요청/응답 추가

- [ ] **문서 접근**
  - [ ] Swagger UI: `/api/v1/docs`
  - [ ] ReDoc: `/api/v1/redoc`

- [ ] **README 작성**
  - [ ] API 사용 가이드
  - [ ] 인증 방법
  - [ ] 예제 코드 (Python, JavaScript)

## Phase 5 완료 조건

- [ ] 모든 테스트 통과 (커버리지 80% 이상)
- [ ] 모든 API 엔드포인트 구현 완료
- [ ] 인증 시스템 정상 작동 (JWT + Session)
- [ ] 에러 처리 일관성 확보
- [ ] API 문서 자동 생성 확인
- [ ] Postman/Insomnia Collection 생성 (선택사항)
- [ ] 코드 리뷰 및 리팩토링 완료

## 성공 지표

- [ ] API 응답 시간 500ms 이내
- [ ] 동시 사용자 100명 처리 가능
- [ ] API 문서 완성도 90% 이상
- [ ] 모바일 앱 통합 테스트 통과

## API 엔드포인트 요약

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| POST | `/api/v1/auth/register` | No | 회원가입 |
| POST | `/api/v1/auth/login` | No | 로그인 |
| GET | `/api/v1/auth/me` | Yes | 사용자 정보 |
| GET | `/api/v1/fridge` | Optional | 냉장고 조회 |
| POST | `/api/v1/fridge/ingredients` | Optional | 재료 추가 |
| DELETE | `/api/v1/fridge/ingredients/{id}` | Optional | 재료 제거 |
| DELETE | `/api/v1/fridge/clear` | Optional | 냉장고 비우기 |
| GET | `/api/v1/fridge/ingredients/search` | No | 재료 검색 |
| GET | `/api/v1/recipes` | No | 레시피 목록 |
| GET | `/api/v1/recipes/{id}` | No | 레시피 상세 |
| GET | `/api/v1/recommendations` | Optional | 추천 |

## 다음 단계

→ **Phase 6: 테스트 및 최적화**
