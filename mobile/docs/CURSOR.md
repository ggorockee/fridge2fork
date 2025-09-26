# Fridge2Fork Mobile App - 프로젝트 개요

## 📱 프로젝트 정보
- **앱명**: Fridge2Fork (냉털레시피)
- **플랫폼**: Flutter 멀티플랫폼 (Android, iOS, Web, Windows, macOS, Linux)
- **버전**: 1.0.0+1
- **개발 환경**: Flutter SDK ^3.9.2, Dart

## 🎯 앱 목적 및 핵심 기능
Fridge2Fork는 사용자가 보유한 냉장고 재료를 기반으로 맞춤형 한식 레시피를 추천하는 모바일 앱입니다.

### 핵심 기능
1. **냉장고 관리**: 보유 재료 카테고리별 관리 (정육/계란, 수산물, 채소, 장/양념/오일)
2. **레시피 추천**: 보유 재료 기반 매칭율 계산으로 맞춤형 레시피 제공
3. **레시피 검색**: 이름, 재료, 카테고리별 레시피 검색
4. **요리 완료 기능**: 사용한 재료 자동 차감 시스템

## 🏗️ 아키텍처 및 기술 스택

### 상태 관리
- **Flutter Riverpod**: 전역 상태 관리
- **SharedPreferences**: 로컬 데이터 저장

### 데이터 관리
- **로컬 JSON**: 레시피 데이터 (assets/data/recipes.json)
- **Provider 패턴**: 재료 및 레시피 상태 관리
- **페이지네이션**: 레시피 목록 성능 최적화

### Firebase 통합
- **Firebase Core**: 기본 설정
- **Firebase Analytics**: 사용자 행동 분석
- **Firebase Crashlytics**: 크래시 리포팅
- **Firebase Performance**: 성능 모니터링

### 광고 시스템
- **Google Mobile Ads**: AdMob 배너/전면 광고
- **수익화 전략**: 전면광고 타이밍 최적화

### 환경 설정
- **flutter_dotenv**: 환경별 설정 관리 (.env.dev, .env.prod)
- **다중 환경**: 개발/운영 환경 분리

## 📱 화면 구조

### 메인 네비게이션 (Bottom Navigation)
1. **홈**: 맞춤 레시피 추천, 냉장고 요약
2. **내 냉장고**: 재료 관리 (추가/삭제/카테고리별 정리)
3. **레시피 검색**: 레시피 탐색 및 검색
4. **피드백**: 사용자 의견 수집

### 주요 화면 흐름
- **스플래시** → **홈** (로그인 상태에 따른 분기 준비)
- **재료 추가**: 홈 → 카테고리 선택 → 재료 선택 → 홈
- **레시피 상세**: 목록 → 상세 → 요리 완료 → 재료 차감

## 📊 데이터 모델

### Recipe (레시피)
- 기본 정보: id, name, description, imageUrl
- 요리 정보: cookingTimeMinutes, servings, difficulty, category
- 평가 정보: rating, reviewCount, isPopular
- 재료 목록: List<Ingredient>
- 조리 단계: List<CookingStep>

### Ingredient (재료)
- name: 재료명
- amount: 필요량
- isEssential: 필수 여부

### Product (상품) - 미래 확장용
- 배송/주문 기능을 위한 상품 모델 준비

## 🔧 주요 서비스

### RecipeDataService
- JSON 기반 레시피 데이터 로딩
- 페이지네이션 지원
- 검색/필터링 기능

### AnalyticsService
- Firebase Analytics 이벤트 추적
- 화면 뷰 로깅

### AdService
- AdMob 광고 관리
- 전면광고 타이밍 제어

## 🎨 UI/UX 특징

### 디자인 시스템
- **AppTheme**: 일관된 색상, 폰트, 간격 체계
- **커스텀 위젯**: 재사용 가능한 UI 컴포넌트
- **반응형 디자인**: 다양한 화면 크기 대응

### 사용자 경험
- **매칭율 시각화**: 보유 재료 기반 레시피 적합도 표시
- **재료 상태 표시**: 보유/부족 재료 구분
- **직관적 네비게이션**: 하단 탭 기반 구조

## 🚀 배포 및 환경

### 지원 플랫폼
- Android (API 21+)
- iOS (iOS 12.0+)
- Web
- Windows, macOS, Linux (데스크톱)

### 빌드 설정
- **개발 환경**: 디버그 로깅, 테스트 데이터
- **운영 환경**: 최적화, 프로덕션 광고 ID

## 📈 향후 확장 계획

### 인증 시스템
- Supabase 기반 사용자 인증 준비
- 소셜 로그인 (Google, Apple) 지원

### 개인화 기능
- 사용자별 즐겨찾기 레시피
- 요리 히스토리 관리
- 맞춤형 추천 알고리즘

### 커뮤니티 기능
- 레시피 리뷰/평점 시스템
- 사용자 생성 콘텐츠

## 🛠️ 개발 환경 설정

### 필수 파일
- `.env.common`, `.env.dev`, `.env.prod`: 환경 설정
- `firebase_options.dart`: Firebase 설정 (생성 필요)
- `google-services.json` (Android), `GoogleService-Info.plist` (iOS)

### 주요 의존성
- flutter_riverpod: 상태 관리
- firebase_core: Firebase 통합
- google_mobile_ads: 광고 시스템
- cached_network_image: 이미지 캐싱
- shared_preferences: 로컬 저장소
