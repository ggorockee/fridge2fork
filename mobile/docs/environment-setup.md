# 환경 설정 가이드

## 개요

냉털레시피 앱은 개발환경과 운영환경을 분리하여 관리할 수 있는 환경 설정 시스템을 제공합니다.

## 환경 파일 구조

```
.env.common  # 공통 설정
.env.dev     # 개발환경 설정  
.env.prod    # 운영환경 설정
```

## 빌드 명령어

### 개발환경
```bash
# 디버그 모드 실행
flutter run --flavor dev

# 릴리즈 APK 빌드
flutter build apk --flavor dev

# iOS 빌드
flutter build ios --flavor dev
```

### 운영환경
```bash
# 디버그 모드 실행
flutter run --flavor prod

# 릴리즈 APK 빌드  
flutter build apk --flavor prod

# iOS 빌드
flutter build ios --flavor prod
```

## 환경 설정 사용법

### 1. 기본 사용법
```dart
import 'package:myapp/config/app_config.dart';

// 현재 환경 확인
if (AppConfig.isDevelopment) {
  print('개발 환경에서 실행 중');
}

// API URL 사용
final apiUrl = AppConfig.apiBaseUrl;

// 디버그 모드 확인
if (AppConfig.debugMode) {
  print('디버그 모드 활성화');
}
```

### 2. 기능 플래그 사용
```dart
// 기능 플래그 확인
if (AppConfig.featureMockData) {
  // 목 데이터 사용
  return MockDataService();
} else {
  // 실제 API 사용
  return ApiService();
}
```

### 3. 환경별 조건부 실행
```dart
// 환경별 다른 동작
void initializeServices() {
  if (AppConfig.isDevelopment) {
    // 개발환경 전용 서비스 초기화
    initializeDevServices();
  } else {
    // 운영환경 서비스 초기화
    initializeProductionServices();
  }
}
```

## 환경 변수 추가하기

### 1. .env 파일에 변수 추가
```bash
# .env.dev
NEW_FEATURE_ENABLED=true
CUSTOM_API_ENDPOINT=https://dev-api.example.com
```

### 2. AppConfig 클래스에 getter 추가
```dart
// lib/config/app_config.dart
static bool get newFeatureEnabled => _getBool('NEW_FEATURE_ENABLED', defaultValue: false);
static String get customApiEndpoint => dotenv.env['CUSTOM_API_ENDPOINT'] ?? '';
```

### 3. 앱에서 사용
```dart
if (AppConfig.newFeatureEnabled) {
  // 새 기능 활성화
}
```

## 주의사항

1. **민감한 정보**: API 키나 비밀번호 같은 민감한 정보는 실제 프로덕션에서는 별도 보안 저장소 사용 권장
2. **환경 파일 관리**: .env.dev와 .env.prod는 Git에 포함되어 있으므로 실제 운영 정보는 배포 시 교체 필요
3. **초기화 확인**: AppConfig.isInitialized로 초기화 완료 여부 확인 후 사용

## 디버깅

환경 설정 디버깅을 위해 다음 메서드 사용:
```dart
// 현재 설정 출력
AppConfig.printConfig();

// 특정 환경 변수 확인
final value = AppConfig.getEnv('CUSTOM_KEY');

// 모든 환경 변수 확인
final allEnv = AppConfig.getAllEnv();
```

## 예제 코드

```dart
// lib/services/api_service.dart
class ApiService {
  late final String _baseUrl;
  late final Duration _timeout;

  ApiService() {
    _baseUrl = AppConfig.apiBaseUrl;
    _timeout = Duration(milliseconds: AppConfig.apiTimeoutMs);
  }

  Future<Response> getData() async {
    final client = http.Client();
    
    try {
      final response = await client
          .get(Uri.parse('$_baseUrl/data'))
          .timeout(_timeout);
      
      if (AppConfig.enableNetworkLogging) {
        print('API Response: ${response.body}');
      }
      
      return response;
    } catch (e) {
      if (AppConfig.debugMode) {
        print('API Error: $e');
      }
      rethrow;
    }
  }
}
```
