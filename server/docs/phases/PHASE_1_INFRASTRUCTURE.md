# Phase 1: 기본 인프라 구축

**목표**: Django 프로젝트 기본 설정 및 핵심 모델 구축
**예상 기간**: 1주
**우선순위**: 🔴 Critical

## 체크리스트

### 1.1 프로젝트 환경 설정

- [x] PostgreSQL 데이터베이스 연결 설정
  - [x] `.env` 파일 생성 및 DB 정보 입력
  - [x] `settings/settings.py`에 PostgreSQL 설정 추가
  - [x] `psycopg2-binary` 패키지 설치: `uv pip install psycopg2-binary`
  - [x] 데이터베이스 연결 테스트: `python app/manage.py dbshell`

- [x] Django Secret Key 환경 변수화
  - [x] `.env`에 `SECRET_KEY` 추가
  - [x] `settings.py`에서 환경 변수로 읽어오기
  - [x] 테스트: 서버 실행 확인

- [x] Git 설정
  - [x] `.gitignore`에 `.env` 추가 확인
  - [x] `.env.example` 템플릿 파일 생성

### 1.2 Custom User Model 구현 (TDD)

**파일**: `app/users/models.py`, `app/users/tests/test_models.py`

- [x] **테스트 작성** (Test-First)
  - [x] `test_create_user_with_email_and_password()`: email/password로 사용자 생성
  - [x] `test_create_user_without_username()`: username 없이 생성 시 email에서 자동 추출
  - [x] `test_username_is_optional()`: username이 선택적 필드임을 확인
  - [x] `test_duplicate_username_allowed()`: username 중복 허용 확인
  - [x] `test_email_is_unique()`: email은 unique 제약 확인
  - [x] `test_email_is_normalized()`: email 정규화 확인 (소문자 변환)

- [x] **User Model 구현**
  - [x] `AbstractBaseUser` 상속
  - [x] 필드 정의:
    - `email`: EmailField, unique=True, 필수
    - `username`: CharField, optional, 중복 허용
    - `is_active`: BooleanField, default=True
    - `is_staff`: BooleanField, default=False
    - `is_superuser`: BooleanField, default=False
    - `date_joined`: DateTimeField, auto_now_add=True
  - [x] `USERNAME_FIELD = 'email'` 설정
  - [x] `REQUIRED_FIELDS = []` 설정 (email은 자동 포함)

- [x] **UserManager 구현**
  - [x] `create_user()` 메서드: username 없으면 email에서 추출
  - [x] `create_superuser()` 메서드: is_staff, is_superuser 자동 설정

- [x] **settings.py 설정**
  - [x] `AUTH_USER_MODEL = 'users.User'` 설정

- [x] **마이그레이션**
  - [x] `python app/manage.py makemigrations users`
  - [x] 마이그레이션 파일 검토
  - [x] `python app/manage.py migrate`

- [x] **테스트 실행**
  - [x] `python app/manage.py test app.users`
  - [x] 모든 테스트 통과 확인

### 1.3 Recipe Model 구현 (TDD)

**파일**: `app/recipes/models.py`, `app/recipes/tests/test_models.py`

- [x] **테스트 작성** (Test-First)
  - [x] `test_create_recipe_with_required_fields()`: 필수 필드로 레시피 생성
  - [x] `test_recipe_str_representation()`: `__str__()` 메서드 확인
  - [x] `test_recipe_ordering()`: 기본 정렬 순서 확인 (생성일 역순)
  - [x] `test_recipe_image_url_optional()`: 이미지 URL 선택적 필드 확인

- [x] **CommonModel (Base Model) 구현** (`app/core/models.py`)
  - [x] `created_at`: DateTimeField(auto_now_add=True, verbose_name="생성일시")
  - [x] `updated_at`: DateTimeField(auto_now=True, verbose_name="수정일시")
  - [x] `class Meta`: abstract = True
  - [x] 모든 모델에서 CommonModel 상속하여 사용

- [x] **Recipe Model 구현**
  - [x] CommonModel 상속
  - [x] 필드 정의 (한글 verbose_name 포함):
    - `recipe_sno`: CharField, unique=True (원본 RCP_SNO)
    - `title`: CharField (RCP_TTL)
    - `name`: CharField (CKG_NM)
    - `introduction`: TextField, blank=True (CKG_IPDC)
    - `servings`: CharField (CKG_INBUN_NM, 예: "4.0")
    - `difficulty`: CharField (CKG_DODF_NM, 예: "아무나")
    - `cooking_time`: CharField (CKG_TIME_NM, 예: "30.0")
    - `method`: CharField, blank=True (CKG_MTH_ACTO_NM)
    - `situation`: CharField, blank=True (CKG_STA_ACTO_NM)
    - `ingredient_type`: CharField, blank=True (CKG_MTRL_ACTO_NM)
    - `recipe_type`: CharField, blank=True (CKG_KND_ACTO_NM)
    - `image_url`: URLField, blank=True (RCP_IMG_URL)
    - `views`: IntegerField, default=0 (INQ_CNT)
    - `recommendations`: IntegerField, default=0 (RCMM_CNT)
    - `scraps`: IntegerField, default=0 (SRAP_CNT)
  - [x] `__str__()` 메서드: `name` 반환 (직관적 표시)
  - [x] `class Meta`: ordering = ['-created_at'], verbose_name="레시피"

- [x] **마이그레이션**
  - [x] `python app/manage.py makemigrations recipes`
  - [x] `python app/manage.py migrate`

- [x] **테스트 실행**
  - [x] `python app/manage.py test app.recipes.tests.test_models`
  - [x] 모든 테스트 통과 확인

### 1.4 Ingredient Model 구현 (TDD)

**파일**: `app/recipes/models.py`, `app/recipes/tests/test_ingredient_model.py`

- [x] **테스트 작성** (Test-First)
  - [x] `test_create_ingredient_with_original_name()`: 원본 재료명으로 생성
  - [x] `test_normalized_name_defaults_to_original()`: normalized_name 기본값 확인
  - [x] `test_ingredient_recipe_relationship()`: Recipe와의 관계 확인
  - [x] `test_ingredient_category_choices()`: 카테고리 선택지 확인
  - [x] `test_ingredient_str_representation()`: `__str__()` 메서드 확인

- [x] **Ingredient Model 구현**
  - [x] CommonModel 상속
  - [x] 필드 정의 (한글 verbose_name 포함):
    - `recipe`: ForeignKey(Recipe, on_delete=CASCADE, related_name='ingredients', verbose_name="레시피")
    - `original_name`: CharField(verbose_name="원본 재료명")
    - `normalized_name`: CharField(verbose_name="정규화 재료명", default=original_name)
    - `category`: CharField(choices, verbose_name="카테고리")
    - `quantity`: CharField(blank=True, verbose_name="수량") - Phase 2 이후 활용
    - `is_essential`: BooleanField(default=True, verbose_name="필수 재료")
  - [x] Category 선택지:
    - `ESSENTIAL = 'essential'`: 필수 재료
    - `SEASONING = 'seasoning'`: 조미료
    - `OPTIONAL = 'optional'`: 선택 재료
  - [x] `__str__()` 메서드: `original_name` 반환 (단순 표시)
  - [x] 필요 시 관계 포함: `f"{self.recipe.name} - {self.original_name}"` (select_related 최적화 필요)

- [x] **마이그레이션**
  - [x] `python app/manage.py makemigrations recipes`
  - [x] `python app/manage.py migrate`

- [x] **테스트 실행**
  - [x] `python app/manage.py test app.recipes.tests.test_ingredient_model`
  - [x] 모든 테스트 통과 확인

### 1.5 Django Admin 기본 설정

**파일**: `app/users/admin.py`, `app/recipes/admin.py`

- [x] **User Admin 설정**
  - [x] UserAdmin 클래스 생성
  - [x] list_display: email, username, is_staff, date_joined
  - [x] list_filter: is_staff, is_active
  - [x] search_fields: email, username
  - [x] Admin 사이트에 등록

- [x] **Recipe Admin 설정**
  - [x] RecipeAdmin 클래스 생성
  - [x] list_display: name, title, servings, difficulty, cooking_time
  - [x] list_filter: difficulty, method, situation
  - [x] search_fields: name, title, introduction
  - [x] Admin 사이트에 등록

- [x] **Ingredient Admin 설정**
  - [x] IngredientInline 클래스 생성 (TabularInline)
  - [x] RecipeAdmin에 inlines 추가
  - [x] list_display: original_name, normalized_name, category, is_essential

- [x] **Superuser 생성 및 테스트**
  - [x] `python app/manage.py createsuperuser`
  - [x] 서버 실행: `python app/manage.py runserver`
  - [x] Admin 사이트 접속: http://localhost:8000/admin/
  - [x] User, Recipe, Ingredient CRUD 테스트

### 1.6 CSV 데이터 Import 스크립트 작성 (TDD)

**파일**: `app/recipes/management/commands/import_recipes.py`

- [x] **테스트 작성** (Test-First)
  - [x] `test_import_single_recipe()`: CSV 1개 행 import 확인
  - [x] `test_parse_ingredients_from_string()`: 재료 문자열 파싱 확인
  - [x] `test_skip_duplicate_recipe_sno()`: 중복 레시피 스킵 확인
  - [x] `test_ingredient_creation_with_recipe()`: 재료 자동 생성 확인

- [x] **Management Command 구현**
  - [x] `handle()` 메서드: CSV 파일 경로 인자 받기
  - [x] CSV 읽기 (pandas 또는 csv 모듈 사용)
  - [x] Recipe 객체 생성 (bulk_create 사용)
  - [x] 재료 파싱 로직:
    - `CKG_MTRL_CN` 필드에서 재료 추출
    - 형식: "[재료] 재료1, 재료2, ..." 또는 "재료1, 재료2, ..."
    - `,`로 split하여 개별 재료 생성
  - [x] Ingredient 객체 생성 (bulk_create 사용)
  - [x] 진행 상황 출력 (tqdm 사용 권장)

- [x] **실행 및 검증**
  - [x] `python app/manage.py import_recipes datas/cleaned_recipes_100.csv`
  - [x] 100개 레시피 import 확인
  - [x] Admin에서 데이터 확인

- [x] **테스트 실행**
  - [x] `python app/manage.py test app.recipes.tests.test_import_command`
  - [x] 모든 테스트 통과 확인

## Phase 1 완료 조건

- [x] 모든 테스트 통과 (커버리지 80% 이상)
- [x] PostgreSQL 연결 정상 작동
- [x] Custom User Model 완전 구현
- [x] Recipe 및 Ingredient 모델 완전 구현
- [x] Django Admin에서 CRUD 정상 작동
- [x] CSV 데이터 100개 정상 import
- [x] 코드 리뷰 및 리팩토링 완료

## 다음 단계

→ **Phase 2: 재료 정규화 시스템 구축**
