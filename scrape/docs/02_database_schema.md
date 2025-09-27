# 데이터베이스 스키마 설계

## 개요

한국 레시피 데이터 3개 CSV 파일을 PostgreSQL에 저장하고, 냉장고 재료 기반 레시피 추천 시스템을 위한 데이터베이스 스키마를 설계합니다.

## CSV 데이터 구조 분석

### 원본 CSV 컬럼 구조
```
RCP_SNO: 레시피 고유번호
RCP_TTL: 레시피 제목
CKG_NM: 요리명
RGTR_ID, RGTR_NM: 등록자 정보
INQ_CNT, RCMM_CNT, SRAP_CNT: 조회수, 추천수, 스크랩수
CKG_MTH_ACTO_NM: 요리방법 (튀김, 부침 등)
CKG_STA_ACTO_NM: 요리상황 (간식, 일상 등)
CKG_MTRL_ACTO_NM: 요리재료분류 (가공식품류, 해물류 등)
CKG_KND_ACTO_NM: 요리종류 (디저트, 밑반찬 등)
CKG_IPDC: 요리소개
CKG_MTRL_CN: 재료내용 (정규화 핵심 대상)
CKG_INBUN_NM: 인분수
CKG_DODF_NM: 난이도
CKG_TIME_NM: 조리시간
FIRST_REG_DT: 등록일시
RCP_IMG_URL: 이미지 URL (선택적)
```

### CKG_MTRL_CN 재료 데이터 패턴
```
[재료] 어묵 2개| 김밥용김 3장| 당면 1움큼| 양파 1/2개| 당근 1/2개| 깻잎 6장| 튀김가루 1컵 | 올리브유 적당량| 간장 1T| 참기름 1T
```

## 정규화된 데이터베이스 스키마

### 1. recipes 테이블 (레시피 기본 정보)

**주요 컬럼**:
- `id`: 기본키 (SERIAL)
- `rcp_sno`: 원본 레시피 번호 (UNIQUE)
- `title`: 레시피 제목
- `cooking_name`: 요리명
- `registrant_id/name`: 등록자 정보
- `inquiry_count/recommendation_count/scrap_count`: 통계 정보
- `cooking_method`: 요리방법 (튀김, 부침 등)
- `cooking_situation`: 요리상황 (간식, 일상 등)
- `cooking_material_category`: 요리재료분류
- `cooking_kind`: 요리종류
- `introduction`: 요리소개
- `raw_ingredients`: 원본 재료 문자열 (CKG_MTRL_CN)
- `serving_size`: 인분수
- `difficulty`: 난이도
- `cooking_time`: 조리시간
- `registered_at`: 등록일시
- `image_url`: 이미지 URL

**인덱스**: rcp_sno, title, cooking_method, cooking_situation, difficulty, cooking_time

### 2. ingredients 테이블 (정규화된 재료 마스터)

**주요 컬럼**:
- `id`: 기본키 (SERIAL)
- `name`: 정규화된 재료명 (UNIQUE)
- `normalized_name`: 검색용 정규화된 이름
- `category`: 재료 카테고리 (육류, 채소류, 양념류 등)
- `is_vague`: 모호한 표현 여부 (적당량, 약간 등)

**인덱스**: name, normalized_name, category, is_vague
**전문검색**: 한국어 GIN 인덱스

### 3. recipe_ingredients 테이블 (레시피-재료 관계)

**주요 컬럼**:
- `id`: 기본키 (SERIAL)
- `recipe_id`: 레시피 외래키
- `ingredient_id`: 재료 외래키
- `quantity_text`: 원본 수량 표현 ("2개", "1/2개", "적당량")
- `quantity_from`: 수량 시작값
- `quantity_to`: 수량 끝값 (범위 표현시)
- `unit`: 단위 (개, 큰술, g, kg 등)
- `is_essential`: 필수 재료 여부
- `display_order`: 표시 순서

**인덱스**: recipe_id, ingredient_id, is_essential, unit
**복합 인덱스**: (ingredient_id, is_essential) - 재료 기반 검색 최적화

### 4. ingredient_categories 테이블 (재료 카테고리 관리)

**주요 컬럼**:
- `id`: 기본키 (SERIAL)
- `name`: 카테고리명 (UNIQUE)
- `parent_id`: 상위 카테고리 (계층 구조)
- `description`: 카테고리 설명

**기본 카테고리**: 육류, 해산물, 채소류, 양념류, 곡류, 유제품, 가공식품, 조미료

## 재료 정규화 로직

### 재료 파싱 알고리즘
1. "[재료]" 접두사 제거
2. "|" 기준으로 재료 분리
3. 각 재료에서 수량과 단위 분리

**파싱 패턴**:
- "재료명 수량단위" (어묵 2개)
- "재료명 분수단위" (양파 1/2개)
- "재료명 범위단위" (소금 1~2큰술)
- "재료명 모호표현" (올리브유 적당량)

**정규화 규칙**:
- 공백 제거
- 일반적인 표기 통일 (대파→파, 계란→달걀)
- 카테고리 자동 분류

## 성능 최적화

### 1. 인덱스 전략
- **기본 인덱스**: Primary Key, Foreign Key, UNIQUE 제약조건
- **검색 최적화**: 재료명, 레시피명에 대한 GIN 인덱스 (한국어 전문검색)
- **복합 인덱스**: 재료 기반 레시피 검색을 위한 복합 인덱스

### 2. 냉장고 재료 기반 레시피 검색 쿼리

**검색 로직**:
1. 사용자 입력 재료를 정규화
2. ingredients 테이블에서 매칭되는 재료 ID 찾기
3. recipe_ingredients에서 해당 재료를 사용하는 레시피 검색
4. 매칭된 필수 재료 수에 따라 정렬

### 3. 데이터 무결성 제약조건
- 레시피 제목 비어있음 방지
- 재료명 비어있음 방지
- 수량 양수 검증
- 수량 범위 유효성 검증

이 스키마는 한국어 레시피 데이터의 특성을 고려하여 설계되었으며, 효율적인 재료 기반 검색과 확장성을 제공합니다.