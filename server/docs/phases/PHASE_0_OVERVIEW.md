# Phase 0: 프로젝트 개요 및 전략

## 프로젝트 목표

냉장고에 있는 재료로 만들 수 있는 **현실적인 레시피 추천 서비스** 구축

### 타겟 사용자
- 요리 초보자
- 재료를 정확히 구분하지 못하는 사용자
- 예: "깨소금" vs "소금", "수육용 돼지고기" vs "구이용 돼지고기" 구분 어려움

## 핵심 기술 스택

- **Backend**: Django 5.2.7 + Django Ninja
- **Database**: PostgreSQL
- **Package Manager**: uv
- **Development**: TDD (Test-Driven Development)

## 데이터 구조 개요

### CSV 데이터 필드 (cleaned_recipes_100.csv)

| 필드명 | 설명 | 중요도 |
|--------|------|--------|
| RCP_SNO | 레시피일련번호 | ⭐⭐⭐ |
| RCP_TTL | 레시피제목 | ⭐⭐⭐ |
| CKG_NM | 요리명 | ⭐⭐⭐ |
| CKG_MTRL_CN | 요리재료내용 | ⭐⭐⭐⭐⭐ (최우선) |
| CKG_INBUN_NM | 요리인분명 | ⭐⭐⭐ |
| CKG_TIME_NM | 요리시간명 | ⭐⭐⭐ |
| CKG_DODF_NM | 요리난이도명 | ⭐⭐ |
| RCP_IMG_URL | 이미지 주소 | ⭐⭐ |
| INQ_CNT | 조회수 | ⭐ |
| RCMM_CNT | 추천수 | ⭐ |
| SRAP_CNT | 스크랩수 | ⭐ |

### 핵심 데이터 모델 관계

```
Recipe (레시피) 1 ─────── N Ingredient (재료)
                          │
                          └─ normalized_name (정규화된 재료명)
                          └─ original_name (원본 재료명)
                          └─ quantity (수량) - Phase 2 이후
```

## 핵심 도전 과제 및 해결 전략

### 1. 조미료 범용성 문제

**시나리오**: 소금, 후추, 간장 등 범용 조미료를 입력하면 거의 모든 레시피가 매칭됨

**해결 전략**:
- 재료 카테고리 분류: `essential` (필수재료) vs `seasoning` (조미료)
- 추천 알고리즘에서 조미료는 **보너스 점수**로만 활용
- 필수재료 매칭률을 우선 순위로 계산

### 2. 재료명 정규화 문제

**시나리오**:
- "깨소금" → "소금"으로 매칭되어야 함
- "수육용 돼지고기" → "돼지고기"로 매칭되어야 함
- 사용자는 "돼지고기" 검색 시 모든 돼지고기 요리가 나와야 함

**해결 전략**:
```
Ingredient 모델
├── original_name: "수육용 돼지고기 300g" (원본, 레시피에 표시)
├── normalized_name: "돼지고기" (정규화, 검색용)
└── category: "육류" (카테고리)
```

- 사용자 입력 → `normalized_name`으로 검색
- 레시피 표시 → `original_name` 그대로 표시
- 관리자가 정규화 매핑 관리

### 3. 데이터 관리 권한

**원칙**:
- 레시피 및 재료 등록: **관리자만** 가능
- 사용자: 냉장고 재료 입력 및 레시피 조회만 가능

**관리자 기능 요구사항**:
- 중복 재료 식별 및 병합
- 재료명 정규화 매핑 관리
- 재료 카테고리 분류 (필수/조미료)
- 레시피-재료 관계 수정

## 개발 원칙

### TDD (Test-Driven Development)
- 모든 기능은 테스트 작성 후 구현
- 테스트 커버리지 80% 이상 유지

### Django ORM 적극 활용
- Raw SQL 최소화
- QuerySet API 최대 활용
- 복잡한 쿼리는 Manager/QuerySet 메서드로 추상화
- 역참조 이용할 수있으면 최대한 이용

### Custom User Model
- `django.contrib.auth.User` 대신 `app.users.User` 사용
- **email + password** 기본 인증
- **username**: optional (없으면 email의 "@" 앞부분 사용, 중복 허용)

## 환경 설정

### 환경 변수 (.env)
```
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=f2f
POSTGRES_PASSWORD=<password>
POSTGRES_DB=f2f
```

**주의**: `.env` 파일은 절대 커밋하지 않음 (`.gitignore` 등록 필수)

## Phase 구성 개요

| Phase | 목표 | 예상 기간 |
|-------|------|-----------|
| Phase 1 | 기본 인프라 구축 (User, Recipe, Ingredient 모델) | 1주 |
| Phase 2 | 재료 정규화 시스템 구축 | 1주 |
| Phase 3 | 레시피 추천 알고리즘 구현 | 2주 |
| Phase 4 | 관리자 기능 구현 (Django Admin 커스터마이징) | 1주 |
| Phase 5 | API 엔드포인트 구현 (Django Ninja) | 1주 |
| Phase 6 | 테스트 및 최적화 | 1주 |

다음 문서로 각 Phase별 상세 체크리스트 참조
