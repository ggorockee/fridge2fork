import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/app_config.dart';
import '../services/api/api_client.dart';
import '../providers/session_provider.dart';

/// API 초기화 서비스
class ApiInitializationService {
  static bool _initialized = false;

  /// API 클라이언트 초기화 및 연결 테스트
  static Future<bool> initialize({Ref? ref}) async {
    if (_initialized) {
      if (kDebugMode) {
        debugPrint('🔧 API Client already initialized');
      }
      return true;
    }

    try {
      if (kDebugMode) {
        debugPrint('🔧 Starting API Client initialization...');
      }

      // 1. API 클라이언트 초기화
      ApiClient.initialize(
        baseUrl: AppConfig.apiBaseUrl,
        timeout: Duration(milliseconds: AppConfig.apiTimeoutMs),
        defaultHeaders: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'User-Agent': 'Fridge2Fork-Mobile/1.0.0',
        },
      );

      if (kDebugMode) {
        debugPrint('🔧 API Client configuration:');
        debugPrint('   Base URL: ${AppConfig.apiBaseUrl}');
        debugPrint('   Timeout: ${AppConfig.apiTimeoutMs}ms');
      }

      // 2. 기본 연결 테스트
      final connectionTest = await ApiClient.testConnection();
      if (!connectionTest) {
        if (kDebugMode) {
          debugPrint('❌ API connection test failed, but continuing...');
        }
        // 연결 실패해도 계속 진행 (오프라인 모드 지원)
      } else {
        if (kDebugMode) {
          debugPrint('✅ API connection test successful');
        }
      }

      // 3. 시스템 정보 조회 (선택사항)
      try {
        final versionResponse = await ApiClient.getSystemVersion();
        if (versionResponse.success) {
          if (kDebugMode) {
            debugPrint('🔧 API Version: ${versionResponse.data}');
          }
        }
      } catch (e) {
        if (kDebugMode) {
          debugPrint('⚠️ Could not retrieve API version: $e');
        }
      }

      // 4. Provider 연동 (있는 경우)
      if (ref != null) {
        // 세션 Provider 초기화
        final sessionNotifier = ref.read(sessionProvider.notifier);
        await sessionNotifier.getSessionId(); // 세션 ID 생성/로드

        if (kDebugMode) {
          final sessionState = ref.read(sessionProvider);
          if (sessionState != null) {
            debugPrint('🔐 Session initialized: ${sessionState.sessionId.substring(0, 8)}...');
            debugPrint('🔐 Session expires: ${sessionState.expiresAt.toLocal()}');
          }
        }
      }

      _initialized = true;

      if (kDebugMode) {
        debugPrint('✅ API initialization completed successfully');
      }

      return true;
    } catch (e) {
      if (kDebugMode) {
        debugPrint('❌ API initialization failed: $e');
      }
      return false;
    }
  }

  /// API 초기화 상태 확인
  static bool get isInitialized => _initialized;

  /// API 초기화 재설정
  static void reset() {
    _initialized = false;
  }

  /// 연결 상태 확인 (헬스체크)
  static Future<Map<String, dynamic>> getConnectionStatus() async {
    if (!_initialized) {
      return {
        'initialized': false,
        'connected': false,
        'message': 'API not initialized',
      };
    }

    try {
      final healthResponse = await ApiClient.getSystemHealth();
      final versionResponse = await ApiClient.getSystemVersion();

      return {
        'initialized': true,
        'connected': healthResponse.success,
        'health': healthResponse.data,
        'version': versionResponse.data,
        'message': healthResponse.success
          ? 'API connection healthy'
          : 'API connection issues',
      };
    } catch (e) {
      return {
        'initialized': true,
        'connected': false,
        'error': e.toString(),
        'message': 'Connection test failed',
      };
    }
  }
}

/// API 초기화 상태 Provider
final apiInitializationProvider = StateNotifierProvider<ApiInitializationNotifier, bool>(
  (ref) => ApiInitializationNotifier(ref),
);

/// API 초기화 상태 관리자
class ApiInitializationNotifier extends StateNotifier<bool> {
  final Ref _ref;

  ApiInitializationNotifier(this._ref) : super(false) {
    _initialize();
  }

  /// 초기화 수행
  Future<void> _initialize() async {
    final success = await ApiInitializationService.initialize(ref: _ref);
    state = success;
  }

  /// 초기화 재시도
  Future<void> retry() async {
    ApiInitializationService.reset();
    final success = await ApiInitializationService.initialize(ref: _ref);
    state = success;
  }
}

/// 연결 상태 Provider
final apiConnectionStatusProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  // API 초기화 상태 확인 후 연결 상태 조회
  final initialized = ref.watch(apiInitializationProvider);
  if (!initialized) {
    return {
      'initialized': false,
      'connected': false,
      'message': 'API not initialized',
    };
  }

  return await ApiInitializationService.getConnectionStatus();
});