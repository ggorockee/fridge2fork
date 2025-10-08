# AdMob 광고 ID 관리 및 앱 버전 관리 API 설계

## 문서 정보

- **작성일**: 2025-10-08
- **대상 시스템**: Fridge2Fork Django Backend
- **관련 앱**: `system` (시스템 설정 관리)
- **목적**: 광고 ID와 앱 버전을 서버에서 동적으로 관리하여 앱 재배포 없이 설정 변경 가능

---

## 1. 개요

### 1.1 배경 및 필요성

**문제점**:
- 광고 ID를 Flutter 앱에 하드코딩하면 변경 시 앱 재배포 필요
- iOS/Android 버전 업데이트 주기가 다르지만 통합 관리 시스템 부재
- 긴급 광고 비활성화 또는 A/B 테스트 진행 시 유연성 부족

**해결 방안**:
- Database에 광고 설정 및 앱 버전 정보 저장
- REST API로 Flutter 앱에 동적 제공
- Admin CRUD API로 실시간 설정 변경 가능

### 1.2 기대 효과

| 영역 | 효과 |
|------|------|
| **운영 효율성** | 앱 재배포 없이 광고 ID 변경 가능 |
| **사용자 경험** | 버전 체크 자동화로 최신 기능 안내 |
| **비즈니스** | A/B 테스트, 긴급 광고 비활성화 용이 |
| **개발 속도** | 설정 변경이 즉시 반영되어 반복 작업 감소 |

---

## 2. AdMob 광고 ID 관리 시스템

### 2.1 요구사항

**광고 타입** (총 6개):
- 배너 광고 2개: 상단(BANNER_TOP), 하단(BANNER_BOTTOM)
- 전면 광고 2개: INTERSTITIAL_1, INTERSTITIAL_2
- 네이티브 광고 2개: NATIVE_1, NATIVE_2

**플랫폼**:
- Android
- iOS

**기능 요구사항**:
- 플랫폼별 광고 ID 별도 관리
- 광고 활성화/비활성화 토글
- Flutter 앱에서 실시간 조회
- Admin에서 CRUD 관리

### 2.2 데이터 모델 설계

#### AdConfig 모델

| 필드명 | 타입 | 설명 | 제약조건 |
|--------|------|------|----------|
| id | Integer | PK | Auto Increment |
| ad_type | CharField(50) | 광고 타입 | Choices: BANNER_TOP, BANNER_BOTTOM, INTERSTITIAL_1, INTERSTITIAL_2, NATIVE_1, NATIVE_2 |
| platform | CharField(20) | 플랫폼 | Choices: ANDROID, IOS |
| ad_unit_id | CharField(255) | AdMob 광고 단위 ID | 예: "ca-app-pub-xxx/yyy" |
| is_active | Boolean | 활성화 여부 | Default: True |
| created_at | DateTime | 생성 일시 | Auto |
| updated_at | DateTime | 수정 일시 | Auto |

**인덱스**:
- `platform`, `is_active` 컬럼에 인덱스 추가 (조회 성능 최적화)

**Unique 제약조건**:
- `(ad_type, platform)` 조합은 유일해야 함 (중복 방지)

**Django Meta 설정**:
```
db_table: 'system_ad_config'
unique_together: [['ad_type', 'platform']]
ordering: ['platform', 'ad_type']
```

### 2.3 API 엔드포인트 설계

#### 2.3.1 Flutter용 조회 API (Public)

**엔드포인트**: `GET /fridge2fork/v1/system/ads/config`

**Query Parameters**:
```json
{
  "platform": "android | ios" (필수)
}
```

**Response** (200 OK):
```json
{
  "banner_top": "ca-app-pub-xxx/banner-top-id",
  "banner_bottom": "ca-app-pub-xxx/banner-bottom-id",
  "interstitial_1": "ca-app-pub-xxx/inter-1-id",
  "interstitial_2": "ca-app-pub-xxx/inter-2-id",
  "native_1": "ca-app-pub-xxx/native-1-id",
  "native_2": "ca-app-pub-xxx/native-2-id"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "InvalidPlatform",
  "message": "platform은 'android' 또는 'ios'여야 합니다."
}
```

**동작 방식**:
1. platform 파라미터로 필터링
2. `is_active=True`인 광고 설정만 반환
3. ad_type을 키로 하는 딕셔너리 형태로 응답
4. Redis 캐싱 적용 (TTL: 24시간)

#### 2.3.2 Admin CRUD API (인증 필요)

| HTTP Method | 엔드포인트 | 설명 | 인증 |
|-------------|-----------|------|------|
| GET | `/fridge2fork/v1/admin/ads` | 전체 광고 설정 목록 조회 | JWT |
| POST | `/fridge2fork/v1/admin/ads` | 새 광고 설정 생성 | JWT |
| PUT | `/fridge2fork/v1/admin/ads/{id}` | 광고 설정 수정 | JWT |
| DELETE | `/fridge2fork/v1/admin/ads/{id}` | 광고 설정 삭제 | JWT |

**POST/PUT Request Body**:
```json
{
  "ad_type": "BANNER_TOP",
  "platform": "ANDROID",
  "ad_unit_id": "ca-app-pub-xxx/yyy",
  "is_active": true
}
```

**Response** (201 Created / 200 OK):
```json
{
  "id": 1,
  "ad_type": "BANNER_TOP",
  "platform": "ANDROID",
  "ad_unit_id": "ca-app-pub-xxx/yyy",
  "is_active": true,
  "created_at": "2025-10-08T12:00:00Z",
  "updated_at": "2025-10-08T12:00:00Z"
}
```

### 2.4 Flutter 통합 시나리오

**앱 시작 시 (1회)**:
1. `GET /fridge2fork/v1/system/ads/config?platform=android` 호출
2. 응답받은 광고 ID를 SharedPreferences에 저장
3. AdMob 초기화 시 해당 ID 사용

**백그라운드 갱신 (일 1회)**:
1. 앱이 포그라운드로 전환될 때 마지막 갱신 시간 체크
2. 24시간 경과 시 API 재호출
3. 새 광고 ID로 교체 (다음 광고 표시 시 적용)

**캐싱 전략**:
```
로컬 캐싱: SharedPreferences (영구 저장)
갱신 주기: 24시간
Fallback: API 실패 시 기존 캐시 사용
```

---

## 3. 앱 버전 관리 시스템

### 3.1 요구사항

**버전 관리 정책**:
- iOS/Android 각각 독립적인 버전 관리
- 강제 업데이트 vs 선택 업데이트 구분
- 최소 지원 버전 설정 (이하 버전은 강제 업데이트)
- 업데이트 안내 메시지 커스터마이징

**기능 요구사항**:
- Flutter 앱 시작 시 버전 체크
- 업데이트 필요 시 다이얼로그 표시
- 강제 업데이트 시 "나중에" 버튼 비활성화
- 스토어 URL로 자동 이동

### 3.2 데이터 모델 설계

#### AppVersion 모델

| 필드명 | 타입 | 설명 | 제약조건 |
|--------|------|------|----------|
| id | Integer | PK | Auto Increment |
| platform | CharField(20) | 플랫폼 | Choices: ANDROID, IOS |
| version_name | CharField(50) | 버전명 | 예: "1.2.3" |
| version_code | Integer | 버전 코드 (비교용) | 예: 10203 (1.2.3 → 1*10000 + 2*100 + 3) |
| min_supported_version_code | Integer | 최소 지원 버전 | 이하 버전은 강제 업데이트 |
| force_update | Boolean | 강제 업데이트 여부 | Default: False |
| update_message | TextField | 업데이트 안내 메시지 | 예: "새로운 레시피 기능이 추가되었습니다!" |
| download_url | URLField | 앱 스토어 URL | Play Store or App Store |
| is_active | Boolean | 활성화 여부 | Default: True (최신 버전만 True) |
| release_date | DateTime | 출시 일시 | |
| created_at | DateTime | 생성 일시 | Auto |
| updated_at | DateTime | 수정 일시 | Auto |

**인덱스**:
- `platform`, `is_active`, `version_code` 컬럼에 인덱스

**Unique 제약조건**:
- `(platform, version_code)` 조합은 유일해야 함

**Django Meta 설정**:
```
db_table: 'system_app_version'
unique_together: [['platform', 'version_code']]
ordering: ['-version_code']  (최신 버전 우선)
```

### 3.3 버전 코드 변환 로직

**변환 공식**:
```
version_name "X.Y.Z" → version_code = X * 10000 + Y * 100 + Z
```

**예시**:
| version_name | version_code | 계산 |
|--------------|--------------|------|
| "1.0.0" | 10000 | 1*10000 + 0*100 + 0 |
| "1.2.3" | 10203 | 1*10000 + 2*100 + 3 |
| "2.0.15" | 20015 | 2*10000 + 0*100 + 15 |
| "3.5.27" | 30527 | 3*10000 + 5*100 + 27 |

**제한사항**:
- Y, Z는 0-99 사이 값 (100 이상 시 오버플로우)
- 최대 버전: 999.99.99

### 3.4 API 엔드포인트 설계

#### 3.4.1 Flutter용 버전 체크 API (Public)

**엔드포인트**: `GET /fridge2fork/v1/system/version/check`

**Query Parameters**:
```json
{
  "platform": "android | ios" (필수),
  "current_version": "1.2.0" (필수, 현재 앱 버전)
}
```

**Response** (200 OK):
```json
{
  "update_required": true,
  "force_update": false,
  "latest_version": "1.3.0",
  "current_version_code": 10200,
  "latest_version_code": 10300,
  "min_supported_version_code": 10000,
  "update_message": "새로운 레시피 추천 기능이 추가되었습니다!",
  "download_url": "https://play.google.com/store/apps/details?id=com.woohalabs.fridge2fork"
}
```

**Response 필드 설명**:
| 필드 | 설명 |
|------|------|
| update_required | 업데이트 필요 여부 (current < latest 또는 current < min_supported) |
| force_update | 강제 업데이트 여부 (current < min_supported 또는 DB의 force_update=True) |
| latest_version | 최신 버전명 |
| current_version_code | 클라이언트가 보낸 버전의 코드 |
| latest_version_code | 최신 버전 코드 |
| min_supported_version_code | 최소 지원 버전 코드 |
| update_message | 업데이트 안내 메시지 |
| download_url | 앱 스토어 다운로드 URL |

**버전 비교 로직**:
```
1. current_version을 version_code로 변환 (예: "1.2.0" → 10200)
2. DB에서 platform의 최신 버전(is_active=True) 조회
3. 비교:
   - current < min_supported → force_update=True
   - current < latest + DB.force_update=True → force_update=True
   - current < latest → update_required=True, force_update=False
   - current == latest → update_required=False
```

#### 3.4.2 Admin CRUD API (인증 필요)

| HTTP Method | 엔드포인트 | 설명 | 인증 |
|-------------|-----------|------|------|
| GET | `/fridge2fork/v1/admin/versions` | 전체 버전 목록 조회 | JWT |
| POST | `/fridge2fork/v1/admin/versions` | 새 버전 등록 | JWT |
| PUT | `/fridge2fork/v1/admin/versions/{id}` | 버전 정보 수정 | JWT |
| DELETE | `/fridge2fork/v1/admin/versions/{id}` | 버전 삭제 | JWT |

**POST/PUT Request Body**:
```json
{
  "platform": "ANDROID",
  "version_name": "1.3.0",
  "version_code": 10300,
  "min_supported_version_code": 10000,
  "force_update": false,
  "update_message": "새로운 레시피 추천 기능이 추가되었습니다!",
  "download_url": "https://play.google.com/store/apps/details?id=...",
  "is_active": true,
  "release_date": "2025-10-15T00:00:00Z"
}
```

**Response** (201 Created / 200 OK):
```json
{
  "id": 1,
  "platform": "ANDROID",
  "version_name": "1.3.0",
  "version_code": 10300,
  "min_supported_version_code": 10000,
  "force_update": false,
  "update_message": "새로운 레시피 추천 기능이 추가되었습니다!",
  "download_url": "https://play.google.com/store/apps/details?id=...",
  "is_active": true,
  "release_date": "2025-10-15T00:00:00Z",
  "created_at": "2025-10-08T12:00:00Z",
  "updated_at": "2025-10-08T12:00:00Z"
}
```

### 3.5 Flutter 통합 시나리오

**앱 시작 플로우**:
1. SplashScreen에서 `GET /fridge2fork/v1/system/version/check` 호출
2. API 응답 분석:
   - `update_required=false` → 메인 화면 진입
   - `update_required=true` + `force_update=false` → 선택 업데이트 다이얼로그
   - `update_required=true` + `force_update=true` → 강제 업데이트 다이얼로그

**다이얼로그 UI**:
| force_update | 버튼 구성 | 동작 |
|--------------|----------|------|
| true | "업데이트" (단일) | 스토어 이동, 앱 종료 |
| false | "나중에", "업데이트" | "나중에" → 메인 진입, "업데이트" → 스토어 이동 |

**스토어 이동**:
```
Android: Intent로 Play Store 앱 열기 (download_url)
iOS: URL Launcher로 App Store 열기 (download_url)
```

---

## 4. 구현 가이드

### 4.1 Phase 1: 모델 및 마이그레이션 (우선순위 1)

**작업 순서**:

1. `system/models.py`에 AdConfig, AppVersion 모델 추가
2. Django Choices 클래스 정의: AdType, Platform
3. 마이그레이션 생성 및 적용
4. Django Admin 등록 (`system/admin.py`)

**마이그레이션 명령어**:
```
python manage.py makemigrations system
python manage.py migrate
```

**검증**:
- Django Admin에서 수동으로 데이터 입력 테스트
- Unique 제약조건 동작 확인 (중복 데이터 입력 시 에러)

### 4.2 Phase 2: Flutter용 조회 API 구현 (우선순위 2)

**파일 위치**: `system/api.py`

**구현 내용**:
1. `@router.get("/ads/config")` 엔드포인트 추가
2. `@router.get("/version/check")` 엔드포인트 추가
3. Pydantic 스키마 정의 (`system/schemas.py`)

**스키마 예시**:
```
AdConfigResponseSchema:
  - banner_top: str
  - banner_bottom: str
  - interstitial_1: str
  - interstitial_2: str
  - native_1: str
  - native_2: str

VersionCheckResponseSchema:
  - update_required: bool
  - force_update: bool
  - latest_version: str
  - current_version_code: int
  - latest_version_code: int
  - min_supported_version_code: int
  - update_message: str
  - download_url: str
```

**테스트**:
```
curl "http://localhost:8000/fridge2fork/v1/system/ads/config?platform=android"
curl "http://localhost:8000/fridge2fork/v1/system/version/check?platform=android&current_version=1.0.0"
```

### 4.3 Phase 3: Admin CRUD API 구현 (우선순위 3)

**파일 위치**: `system/api.py` (Admin Router 분리 권장)

**구현 내용**:
1. JWT 인증 데코레이터 적용
2. Admin CRUD 엔드포인트 구현
3. 입력 검증 로직 추가
4. 감사 로그 기록 (변경 이력 추적)

**권한 체크**:
```
- 인증된 사용자만 접근 가능
- is_staff=True 또는 is_superuser=True 권한 필요
- 인증 실패 시 401 Unauthorized 응답
```

### 4.4 Phase 4: 캐싱 및 최적화 (우선순위 4)

**Redis 캐싱 전략**:
| API | 캐시 키 | TTL | 무효화 조건 |
|-----|---------|-----|------------|
| ads/config | `ads:config:{platform}` | 24시간 | Admin API에서 광고 설정 변경 시 |
| version/check | `version:{platform}:{version}` | 1시간 | Admin API에서 버전 정보 변경 시 |

**캐싱 구현**:
```
1. API 요청 시 Redis 캐시 확인
2. 캐시 Hit → 즉시 응답
3. 캐시 Miss → DB 조회 → 응답 + 캐시 저장
4. Admin API에서 변경 발생 → 관련 캐시 삭제 (invalidation)
```

### 4.5 초기 데이터 시딩

**Fixture 파일**: `system/fixtures/initial_ads_version.json`

**샘플 데이터**:
```json
[
  {
    "model": "system.adconfig",
    "pk": 1,
    "fields": {
      "ad_type": "BANNER_TOP",
      "platform": "ANDROID",
      "ad_unit_id": "ca-app-pub-3940256099942544/6300978111",
      "is_active": true
    }
  },
  {
    "model": "system.appversion",
    "pk": 1,
    "fields": {
      "platform": "ANDROID",
      "version_name": "1.0.0",
      "version_code": 10000,
      "min_supported_version_code": 10000,
      "force_update": false,
      "update_message": "Fridge2Fork 첫 출시 버전입니다!",
      "download_url": "https://play.google.com/store/apps/details?id=com.woohalabs.fridge2fork",
      "is_active": true,
      "release_date": "2025-10-01T00:00:00Z"
    }
  }
]
```

**적용 명령어**:
```
python manage.py loaddata initial_ads_version
```

---

## 5. 보안 및 성능 고려사항

### 5.1 보안

| 영역 | 조치 사항 |
|------|----------|
| **인증** | Admin CRUD API는 JWT Bearer Token 필수 |
| **권한** | is_staff 또는 is_superuser 권한 체크 |
| **Rate Limiting** | 조회 API: 초당 10회, Admin API: 초당 5회 제한 |
| **입력 검증** | Pydantic 스키마로 타입 및 값 검증 |
| **감사 로그** | 광고/버전 변경 시 누가, 언제, 무엇을 변경했는지 기록 |

**Rate Limiting 구현**:
```
Django Ninja + django-ratelimit 또는 Redis 기반 커스텀 미들웨어
```

### 5.2 성능

| 영역 | 최적화 방안 |
|------|------------|
| **Database** | platform, is_active 컬럼에 인덱스 추가 |
| **캐싱** | Redis 캐싱으로 DB 쿼리 90% 이상 감소 |
| **쿼리 최적화** | select_related/prefetch_related 사용 |
| **비동기 처리** | Django Ninja의 async 엔드포인트 활용 |

**예상 성능**:
- 광고 ID 조회: ~5ms (캐시 Hit), ~20ms (캐시 Miss)
- 버전 체크: ~10ms (캐시 Hit), ~30ms (캐시 Miss)
- Admin CRUD: ~50-100ms (DB 쓰기 포함)

### 5.3 모니터링

**모니터링 항목**:
| 항목 | 임계값 | 알림 조건 |
|------|--------|----------|
| API 응답 시간 | 100ms | 평균 응답 시간 초과 시 |
| 에러율 | 1% | 5분간 에러율 초과 시 |
| 캐시 히트율 | 95% | 히트율 하락 시 |
| 광고 설정 변경 | - | 변경 발생 시 즉시 알림 |
| 강제 업데이트 활성화 | - | force_update=True 설정 시 즉시 알림 |

---

## 6. 테스트 시나리오

### 6.1 단위 테스트

**테스트 파일**: `system/tests/test_ads_version.py`

**테스트 케이스**:

| 테스트명 | 검증 내용 |
|---------|----------|
| `test_ad_config_creation` | AdConfig 모델 생성 및 저장 |
| `test_ad_config_unique_constraint` | ad_type + platform 중복 방지 |
| `test_version_code_conversion` | version_name → version_code 변환 정확성 |
| `test_version_comparison_logic` | 버전 비교 로직 (강제/선택 업데이트 구분) |

### 6.2 API 통합 테스트

| 테스트명 | 시나리오 |
|---------|----------|
| `test_ads_config_api_android` | Android 플랫폼 광고 ID 조회 |
| `test_ads_config_api_ios` | iOS 플랫폼 광고 ID 조회 |
| `test_ads_config_api_invalid_platform` | 잘못된 플랫폼 파라미터 → 400 에러 |
| `test_version_check_update_required` | 업데이트 필요 케이스 (선택 업데이트) |
| `test_version_check_force_update` | 강제 업데이트 케이스 |
| `test_version_check_no_update` | 최신 버전인 경우 |
| `test_admin_ads_create_unauthorized` | JWT 없이 Admin API 접근 → 401 |
| `test_admin_ads_create_authorized` | JWT로 광고 설정 생성 |
| `test_admin_version_update` | 버전 정보 수정 |

### 6.3 Flutter 통합 시나리오 테스트

**테스트 환경**: 개발 서버 + Flutter Dev App

**시나리오 1: 광고 ID 조회**:
1. Flutter 앱 시작
2. API 호출: `GET /fridge2fork/v1/system/ads/config?platform=android`
3. 응답 검증: 6개 광고 ID 모두 존재
4. SharedPreferences에 저장 확인
5. AdMob 광고 로드 성공 여부 확인

**시나리오 2: 선택 업데이트**:
1. Flutter 앱 버전: 1.0.0
2. 서버 최신 버전: 1.2.0 (force_update=false)
3. API 호출: `GET /fridge2fork/v1/system/version/check?platform=android&current_version=1.0.0`
4. 응답: update_required=true, force_update=false
5. 다이얼로그 표시: "나중에", "업데이트" 버튼 확인
6. "나중에" 클릭 → 메인 화면 진입

**시나리오 3: 강제 업데이트**:
1. Flutter 앱 버전: 0.9.0
2. 서버 최소 지원 버전: 1.0.0
3. API 호출: `GET /fridge2fork/v1/system/version/check?platform=android&current_version=0.9.0`
4. 응답: update_required=true, force_update=true
5. 다이얼로그 표시: "업데이트" 버튼만 존재
6. "업데이트" 클릭 → Play Store 이동

---

## 7. 마이그레이션 및 배포 계획

### 7.1 개발 환경 배포

**순서**:
1. `develop` 브랜치에 코드 커밋
2. 개발 서버에 배포
3. 마이그레이션 실행
4. 초기 데이터 시딩
5. Postman/curl로 API 테스트
6. Flutter Dev App에서 통합 테스트

### 7.2 운영 환경 배포

**Pre-Deployment 체크리스트**:
- [ ] 모든 테스트 케이스 통과
- [ ] 성능 테스트 완료 (부하 테스트)
- [ ] 보안 검토 완료 (인증, Rate Limiting)
- [ ] Rollback 계획 수립
- [ ] 모니터링 알림 설정 확인

**배포 순서**:
1. 운영 DB 백업
2. Blue-Green 배포 또는 Rolling Update
3. 마이그레이션 실행 (무중단)
4. API 헬스 체크
5. Flutter 앱 버전 체크 API 검증
6. 모니터링 대시보드 확인 (1시간)

### 7.3 Rollback 시나리오

**Trigger**:
- API 에러율 5% 초과
- 응답 시간 500ms 초과
- 마이그레이션 실패

**Rollback 절차**:
1. 이전 버전으로 코드 롤백
2. 마이그레이션 롤백 (필요 시)
3. 캐시 클리어
4. 헬스 체크 재확인

---

## 8. FAQ 및 트러블슈팅

### 8.1 FAQ

**Q: 광고 ID를 변경하면 Flutter 앱에 즉시 반영되나요?**
A: 앱을 재시작하거나 24시간 후 자동 갱신 시 반영됩니다. 긴급 변경이 필요한 경우 TTL을 1시간으로 단축할 수 있습니다.

**Q: 강제 업데이트를 설정하면 모든 사용자가 즉시 업데이트해야 하나요?**
A: `force_update=True` + 앱 시작 시 버전 체크 → 강제 업데이트 다이얼로그 표시됩니다. 단, 이미 실행 중인 앱은 재시작 전까지는 영향 없습니다.

**Q: iOS와 Android 버전을 동일하게 관리할 수 있나요?**
A: 플랫폼별로 독립적으로 관리됩니다. 동일한 version_name을 사용할 수 있지만 출시 일정이 다를 수 있으므로 별도 관리 권장합니다.

### 8.2 트러블슈팅

| 문제 | 원인 | 해결 방안 |
|------|------|----------|
| 광고 ID 조회 시 404 에러 | platform 파라미터 누락 | Query parameter 확인 |
| 버전 체크 API가 항상 update_required=false | is_active=True인 버전이 없음 | DB에 최신 버전 등록 |
| Admin API 401 에러 | JWT 토큰 누락 또는 만료 | Authorization 헤더 확인, 토큰 재발급 |
| 캐시가 업데이트되지 않음 | 캐시 무효화 로직 미실행 | Admin API에서 변경 시 캐시 삭제 코드 확인 |

---

## 9. 참고 자료

**관련 문서**:
- `DATABASE_SCHEMA.md`: 전체 데이터베이스 스키마 가이드
- `API_ENDPOINTS.md`: 기존 API 엔드포인트 목록
- `mobile/CLAUDE.md`: Flutter 앱 구조 및 개발 가이드

**외부 문서**:
- Django Ninja 공식 문서: https://django-ninja.rest-framework.com/
- AdMob 광고 단위 ID 가이드: https://support.google.com/admob/
- 앱 버전 관리 Best Practices: https://developer.android.com/studio/publish/versioning

---

## 10. 변경 이력

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 2025-10-08 | 1.0 | 초안 작성 | Claude Code |
| 2025-10-08 | 1.1 | API 엔드포인트 경로 수정 (/fridge2fork/v1 prefix 추가) | Claude Code |
