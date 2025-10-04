# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

이 프로젝트는 "냉털레시피" - 냉장고에 있는 재료로 한식 요리를 추천하는 Flutter 모바일 앱입니다. 사용자가 보유한 식재료를 기반으로 만들 수 있는 레시피를 추천하고, Firebase Analytics와 AdMob 광고가 통합되어 있습니다.

## Development Commands

### Running the App
```bash
# 개발환경에서 실행 (기본)
flutter run

# 디버그 모드에서 실행
flutter run --debug

# 릴리즈 모드에서 실행
flutter run --release

# 핫 리로드 중 상태 초기화
flutter run --hot
```

### Building
```bash
# APK 빌드 (디버그)
flutter build apk --debug

# APK 빌드 (릴리즈)
flutter build apk --release

# iOS 빌드 (디버그)
flutter build ios --debug

# iOS 빌드 (릴리즈)
flutter build ios --release
```

### Testing and Quality
```bash
# 단위 테스트 실행
flutter test

# 코드 분석 (linting)
flutter analyze

# 의존성 업데이트
flutter pub get
flutter pub upgrade

# 코드 포맷팅
dart format lib/
```

### Environment Setup
```bash
# Firebase 설정 확인
flutterfire configure

# iOS 의존성 설치 (iOS 개발시)
cd ios && pod install

# Android 빌드 클린
flutter clean && flutter pub get
```

## Architecture

### State Management
- **Primary**: Flutter Riverpod을 사용한 상태 관리
- **Core Providers**:
  - `app_state_provider.dart`: 전역 앱 상태 관리
  - `ingredients_provider.dart`: 로컬 식재료 관리
  - `recipe_provider.dart`: 로컬 레시피 데이터 관리
  - `api_ingredients_provider.dart`: API 기반 식재료 상태
- **API Providers** (`providers/api/`):
  - `api_connection_provider.dart`: API 연결 상태
  - `ingredient_api_provider.dart`: 식재료 API 호출
  - `recipe_api_provider.dart`: 레시피 API 호출

### App Structure
```
lib/
├── main.dart                    # 앱 진입점, Firebase/AdMob 초기화
├── config/
│   └── app_config.dart         # 환경별 설정 관리 (.env 파일 기반)
├── screens/                    # 화면 컴포넌트
│   ├── splash_screen.dart      # 스플래시 화면
│   ├── main_screen.dart        # 하단 네비게이션 컨테이너
│   ├── home_screen.dart        # 홈 화면 (빈 냉장고 상태)
│   ├── my_fridge_screen.dart   # 식재료 관리 화면
│   ├── add_ingredient_screen.dart # 식재료 추가 모달
│   ├── recipe_screen.dart      # 레시피 검색/목록
│   ├── recipe_list_screen.dart # 레시피 목록 화면
│   ├── recipe_detail_screen.dart # 레시피 상세 정보
│   └── feedback_screen.dart    # 피드백 화면
├── providers/                  # Riverpod 상태 관리
│   ├── app_state_provider.dart
│   ├── ingredients_provider.dart
│   ├── api_ingredients_provider.dart
│   ├── recipe_provider.dart
│   └── api/                   # API 관련 프로바이더
├── services/                   # 비즈니스 로직 및 외부 서비스
│   ├── api/                   # API 서비스 레이어
│   │   ├── api_client.dart   # HTTP 클라이언트
│   │   ├── ingredient_api_service.dart
│   │   ├── recipe_api_service.dart
│   │   └── system_api_service.dart
│   ├── analytics_service.dart # Firebase Analytics
│   ├── ad_service.dart        # AdMob 광고 관리
│   ├── interstitial_ad_manager.dart # 전면 광고 관리
│   ├── cache_service.dart     # 로컬 캐시
│   ├── offline_service.dart   # 오프라인 모드 지원
│   ├── sample_data.dart       # 샘플 데이터
│   └── recipe_data.dart       # 레시피 데이터
├── models/                    # 데이터 모델
│   ├── product.dart           # 로컬 제품 모델
│   ├── recipe.dart           # 로컬 레시피 모델
│   └── api/                  # API 응답 모델
│       ├── api_response.dart  # API 응답 래퍼
│       ├── api_ingredient.dart
│       └── api_recipe.dart
├── widgets/                   # 재사용 가능한 UI 컴포넌트
│   ├── custom_button.dart
│   ├── custom_text_field.dart
│   ├── quantity_selector.dart
│   ├── category_tabs.dart
│   ├── custom_toggle_switch.dart
│   ├── custom_app_bar.dart
│   ├── status_bar.dart
│   ├── product_card.dart
│   ├── ad_banner_widget.dart
│   └── widgets.dart           # 위젯 exports
├── utils/
│   └── app_assets.dart       # 앱 애셋 경로 관리
└── theme/
    └── app_theme.dart        # Material Design 테마
```

### API Integration
- **Base URLs**:
  - Development: `https://api-dev.woohalabs.com/fridge2fork/v1`
  - Production: `https://api.woohalabs.com/fridge2fork/v1`
- **API Client**: Custom HTTP client with error handling (`services/api/api_client.dart`)
- **Endpoints**: Centralized in `ApiEndpoints` class
- **Offline Support**: Local caching with fallback to sample data

### Environment Configuration
- **Environment Files**:
  - `.env.common` - 공통 설정 (모든 환경에서 로드)
  - `.env.dev` - 개발환경 전용 설정
  - `.env.prod` - 운영환경 전용 설정
- **Configuration Management**:
  - `AppConfig` 클래스로 환경 변수 관리
  - `kReleaseMode`로 환경 자동 감지 (dev/prod)
  - Firebase 네이티브 설정 파일 사용

### Firebase Integration
- **Analytics**: 사용자 행동 추적 및 이벤트 로깅
- **Crashlytics**: 앱 크래시 모니터링
- **Performance**: 앱 성능 모니터링
- **AdMob**: 배너 및 전면 광고 통합 (`ad_service.dart`, `interstitial_ad_manager.dart`)

### Key Architecture Patterns
- **Layer Separation**: Clear separation between UI (screens), business logic (providers), and data (services/models)
- **Error Handling**: `ApiResponse<T>` wrapper pattern for consistent API error handling
- **Offline-First**: Local caching with `CacheService` and fallback to sample data via `OfflineService`
- **Ad Integration**: Centralized ad management with preloading and strategic placement
- **Environment Management**: Multi-environment support with `.env` files and `AppConfig` class

## Key Features & Components

### Ingredient Management
- 식재료 검색 및 추가 기능
- 카테고리별 분류 (채소, 육류, 해산물 등)
- 수량 관리 및 만료일 추적
- API 연동 및 로컬 캐시 지원

### Recipe Recommendations
- 보유 식재료 기반 레시피 추천
- 단계별 요리 과정 표시
- 영양 정보 및 조리 시간 정보
- 즐겨찾기 기능

### AdMob Monetization
- 전면 광고: 주요 액션 완료 후 표시
- 배너 광고: 화면 상단/하단 배치
- 광고 주기: 환경 설정에서 관리

## Development Guidelines

### Code Style
- Flutter/Dart 표준 린트 규칙 적용 (`flutter_lints`)
- 모든 API 호출은 `ApiClient` 클래스 사용
- Riverpod Provider는 별도 파일로 분리
- 한국어 주석으로 비즈니스 로직 설명

### Testing Strategy
- 단위 테스트: `test/` 디렉토리
- 위젯 테스트: 주요 화면 컴포넌트
- API 모킹: 개발 중 실제 API 대신 사용

### Error Handling
- API 에러: `ApiResponse<T>` 래퍼 클래스 사용
- Network 에러: 오프라인 모드로 자동 전환
- UI 에러: `SnackBarHelper`로 사용자 알림

### Performance Considerations
- 이미지 캐싱: `cached_network_image` 패키지 사용
- 상태 관리: Riverpod의 자동 캐싱 및 최적화 활용
- 광고 프리로딩: 앱 시작시 전면 광고 미리 로드

## Common Tasks

### Adding New Screens
1. `screens/` 디렉토리에 새 화면 파일 생성
2. `main_screen.dart`의 네비게이션에 추가 (필요시)
3. 필요한 Provider 생성 및 연결
4. Firebase Analytics 이벤트 추가

### API Integration
1. `models/api/` 에서 데이터 모델 정의
2. `services/api/` 에서 API 서비스 클래스 생성
3. `providers/api/` 에서 Riverpod Provider 생성
4. UI 컴포넌트에서 Provider 소비

### Environment Variables
1. `.env.common`, `.env.dev`, `.env.prod` 파일 수정
2. `app_config.dart`에서 새 변수 getter 추가
3. 코드에서 `AppConfig.변수명` 형태로 사용

### Adding Analytics Events
1. `analytics_service.dart`에 새 이벤트 메서드 추가
2. 해당 화면/액션에서 이벤트 호출
3. Firebase Console에서 이벤트 확인

## Security & Privacy
- API 키 및 민감한 정보는 환경 변수로 관리
- Firebase 설정은 네이티브 설정 파일 사용
- 사용자 개인정보는 로컬에만 저장 (현재 인증 시스템 없음)

## Troubleshooting

### Common Issues
- **Firebase 초기화 실패**: `google-services.json` (Android) 및 `GoogleService-Info.plist` (iOS) 확인
- **API 연결 실패**: 환경 변수의 `API_BASE_URL` 확인
- **광고 로드 실패**: AdMob 앱 ID 및 광고 단위 ID 확인
- **빌드 에러**: `flutter clean && flutter pub get` 실행 후 재빌드

### Development Environment
- Flutter SDK 3.9.2 이상 필요
- Android Studio / Xcode 최신 버전 권장
- Firebase CLI 설치 및 프로젝트 연결 필요

## Project Dependencies

### Key Packages
- `flutter_riverpod: ^2.4.9` - 상태 관리
- `http: ^1.1.0` - HTTP 클라이언트
- `shared_preferences: ^2.5.3` - 로컬 저장소
- `cached_network_image: ^3.3.0` - 이미지 캐싱
- `connectivity_plus: ^6.0.5` - 네트워크 상태 확인
- `flutter_dotenv: ^5.1.0` - 환경 변수 관리
- `firebase_core: ^3.8.0` - Firebase 코어
- `google_mobile_ads: ^5.3.0` - AdMob 광고

### UI/UX Packages
- `showcaseview: ^4.0.1` - 앱 투어 및 기능 소개
- `another_flushbar: ^1.12.32` - 사용자 알림
- `url_launcher: ^6.2.2` - 외부 링크 실행