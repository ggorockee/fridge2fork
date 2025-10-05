import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

/// 앱 환경 타입
enum AppEnvironment {
  local('local'),
  development('dev'),
  production('prod');

  const AppEnvironment(this.value);
  final String value;

  static AppEnvironment fromString(String value) {
    switch (value.toLowerCase()) {
      case 'local':
        return AppEnvironment.local;
      case 'development':
      case 'dev':
        return AppEnvironment.development;
      case 'production':
      case 'prod':
        return AppEnvironment.production;
      default:
        return AppEnvironment.local; // 기본값을 local로 변경
    }
  }
}

/// 앱 설정 관리 클래스
class AppConfig {
  static AppEnvironment _currentEnvironment = AppEnvironment.development;
  static bool _isInitialized = false;

  /// 현재 환경 반환
  static AppEnvironment get currentEnvironment => _currentEnvironment;

  /// 초기화 여부 확인
  static bool get isInitialized => _isInitialized;

  /// 로컬 환경 여부
  static bool get isLocal => _currentEnvironment == AppEnvironment.local;

  /// 개발 환경 여부
  static bool get isDevelopment => _currentEnvironment == AppEnvironment.development;

  /// 운영 환경 여부
  static bool get isProduction => _currentEnvironment == AppEnvironment.production;

  /// 환경 설정 초기화 (.env 파일의 ENVIRONMENT 값에 따라 자동 결정)
  static Future<void> initialize() async {
    try {
      // 1단계: .env 파일을 먼저 로드하여 ENVIRONMENT 값 확인
      try {
        await dotenv.load(fileName: '.env');
        debugPrint('✅ Loaded .env');
      } catch (e) {
        debugPrint('ℹ️ .env not found, will use .env.local as default: $e');
      }

      // 2단계: ENVIRONMENT 값으로 환경 결정
      final envValue = dotenv.env['ENVIRONMENT'] ?? 'local';
      _currentEnvironment = AppEnvironment.fromString(envValue);
      debugPrint('🌍 Environment: ${_currentEnvironment.value} (from ENVIRONMENT=$envValue)');

      // 3단계: .env.common 로드 (공통 설정)
      try {
        await dotenv.load(fileName: '.env.common', mergeWith: dotenv.env);
        debugPrint('✅ Loaded .env.common');
      } catch (e) {
        debugPrint('ℹ️ .env.common not found, using defaults: $e');
      }

      // 4단계: 환경별 설정 파일 로드 및 병합
      final envFile = _getEnvFileName(_currentEnvironment);
      try {
        await dotenv.load(fileName: envFile, mergeWith: dotenv.env);
        debugPrint('✅ Loaded $envFile');
      } catch (e) {
        debugPrint('ℹ️ $envFile not found, using defaults: $e');
      }

      _isInitialized = true;
      debugPrint('✅ AppConfig initialized for ${_currentEnvironment.value} environment');
      debugPrint('🔧 API Base URL: $apiBaseUrl');
      debugPrint('🔧 Environment from .env: $environment');
    } catch (e) {
      debugPrint('❌ Failed to initialize AppConfig: $e');
      _isInitialized = false;
      rethrow;
    }
  }

  /// 환경에 따른 .env 파일명 반환
  static String _getEnvFileName(AppEnvironment env) {
    switch (env) {
      case AppEnvironment.local:
        return '.env.local';
      case AppEnvironment.development:
        return '.env.dev';
      case AppEnvironment.production:
        return '.env.prod';
    }
  }

  // ===========================================
  // 앱 기본 정보
  // ===========================================

  static String get appName => dotenv.env['APP_NAME'] ?? '냉털레시피';
  static String get appVersion => dotenv.env['APP_VERSION'] ?? '1.0.0';
  static String get defaultLocale => dotenv.env['DEFAULT_LOCALE'] ?? 'ko_KR';
  static String get environment => dotenv.env['ENVIRONMENT'] ?? 'development';

  // ===========================================
  // 디버그 및 로깅
  // ===========================================

  static bool get debugMode => _getBool('DEBUG_MODE', defaultValue: false);
  static String get logLevel => dotenv.env['LOG_LEVEL'] ?? 'info';
  static bool get enableNetworkLogging => _getBool('ENABLE_NETWORK_LOGGING', defaultValue: false);
  static bool get enablePerformanceLogging => _getBool('ENABLE_PERFORMANCE_LOGGING', defaultValue: false);

  // ===========================================
  // API 설정
  // ===========================================

  static String get apiBaseUrl => dotenv.env['API_BASE_URL'] ?? 'https://api-dev.woohalabs.com';
  static String get apiKey => dotenv.env['API_KEY'] ?? '';
  static int get apiTimeoutMs => _getInt('API_TIMEOUT_MS', defaultValue: 30000);

  // ===========================================
  // 데이터베이스 설정
  // ===========================================

  static String get dbHost => dotenv.env['DB_HOST'] ?? 'localhost';
  static int get dbPort => _getInt('DB_PORT', defaultValue: 5432);
  static String get dbName => dotenv.env['DB_NAME'] ?? 'fridge2fork';

  // ===========================================
  // 기본 설정
  // ===========================================

  static int get cacheDurationHours => _getInt('CACHE_DURATION_HOURS', defaultValue: 24);
  static int get requestTimeoutSeconds => _getInt('REQUEST_TIMEOUT_SECONDS', defaultValue: 30);
  static int get maxRetryAttempts => _getInt('MAX_RETRY_ATTEMPTS', defaultValue: 3);

  // ===========================================
  // 외부 서비스
  // ===========================================

  static String get firebaseProjectId => dotenv.env['FIREBASE_PROJECT_ID'] ?? '';
  
  // ===========================================
  // AdMob 광고 설정
  // ===========================================
  
  // Android AdMob IDs
  static String get admobAndroidAppId => dotenv.env['ADMOB_ANDROID_APP_ID'] ?? '';
  static String get admobAndroidBannerTopId => dotenv.env['ADMOB_ANDROID_BANNER_TOP_ID'] ?? '';
  static String get admobAndroidBannerBottomId => dotenv.env['ADMOB_ANDROID_BANNER_BOTTOM_ID'] ?? '';
  static String get admobAndroidInterstitialId => dotenv.env['ADMOB_ANDROID_INTERSTITIAL_ID'] ?? '';
  static String get admobAndroidNativeId => dotenv.env['ADMOB_ANDROID_NATIVE_ID'] ?? '';
  
  // iOS AdMob IDs
  static String get admobIosAppId => dotenv.env['ADMOB_IOS_APP_ID'] ?? '';
  static String get admobIosBannerTopId => dotenv.env['ADMOB_IOS_BANNER_TOP_ID'] ?? '';
  static String get admobIosBannerBottomId => dotenv.env['ADMOB_IOS_BANNER_BOTTOM_ID'] ?? '';
  static String get admobIosInterstitialId => dotenv.env['ADMOB_IOS_INTERSTITIAL_ID'] ?? '';
  static String get admobIosNativeId => dotenv.env['ADMOB_IOS_NATIVE_ID'] ?? '';
  
  // 광고 설정
  static int get adRefreshRateSeconds => _getInt('AD_REFRESH_RATE_SECONDS', defaultValue: 30);
  static int get adInterstitialMinIntervalSeconds => _getInt('AD_INTERSTITIAL_MIN_INTERVAL_SECONDS', defaultValue: 60);
  static int get adNativeRefreshRateSeconds => _getInt('AD_NATIVE_REFRESH_RATE_SECONDS', defaultValue: 300);
  static String get analyticsTrackingId => dotenv.env['ANALYTICS_TRACKING_ID'] ?? '';
  static String get sentryDsn => dotenv.env['SENTRY_DSN'] ?? '';

  // ===========================================
  // 기능 플래그
  // ===========================================

  static bool get featureAnalyticsEnabled => _getBool('FEATURE_ANALYTICS_ENABLED', defaultValue: true);
  static bool get featureCrashReportingEnabled => _getBool('FEATURE_CRASH_REPORTING_ENABLED', defaultValue: true);
  static bool get featureOfflineModeEnabled => _getBool('FEATURE_OFFLINE_MODE_ENABLED', defaultValue: true);
  static bool get featureMockData => _getBool('FEATURE_MOCK_DATA', defaultValue: false);
  static bool get featureDebugPanel => _getBool('FEATURE_DEBUG_PANEL', defaultValue: false);
  static bool get featureTestRecipes => _getBool('FEATURE_TEST_RECIPES', defaultValue: false);

  // ===========================================
  // 헬퍼 메서드
  // ===========================================

  /// 환경 변수를 boolean으로 변환
  static bool _getBool(String key, {bool defaultValue = false}) {
    final value = dotenv.env[key]?.toLowerCase();
    if (value == null) return defaultValue;
    return value == 'true' || value == '1' || value == 'yes';
  }

  /// 환경 변수를 int로 변환
  static int _getInt(String key, {int defaultValue = 0}) {
    final value = dotenv.env[key];
    if (value == null) return defaultValue;
    return int.tryParse(value) ?? defaultValue;
  }


  /// 현재 설정을 디버그용으로 출력
  static void printConfig() {
    if (!_isInitialized) {
      debugPrint('❌ AppConfig not initialized');
      return;
    }

    debugPrint('=== AppConfig Debug Info ===');
    debugPrint('Environment: ${_currentEnvironment.value}');
    debugPrint('App Name: $appName');
    debugPrint('App Version: $appVersion');
    debugPrint('Debug Mode: $debugMode');
    debugPrint('API Base URL: $apiBaseUrl');
    debugPrint('Log Level: $logLevel');
    debugPrint('==========================');
  }

  /// 특정 환경 변수 값 가져오기
  static String? getEnv(String key) {
    return dotenv.env[key];
  }

  /// 모든 환경 변수 가져오기
  static Map<String, String> getAllEnv() {
    return Map.from(dotenv.env);
  }
}
