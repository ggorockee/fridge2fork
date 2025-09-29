import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../models/api/api_response.dart';
import '../../services/api/api_client.dart';
import '../../services/api/system_api_service.dart';

/// API 연결 상태
class ApiConnectionState {
  final bool isOnline;
  final bool isChecking;
  final Duration? responseTime;
  final DateTime? lastChecked;
  final String? errorMessage;
  final Map<String, dynamic>? serverInfo;

  const ApiConnectionState({
    this.isOnline = false,
    this.isChecking = false,
    this.responseTime,
    this.lastChecked,
    this.errorMessage,
    this.serverInfo,
  });

  /// 복사본 생성
  ApiConnectionState copyWith({
    bool? isOnline,
    bool? isChecking,
    Duration? responseTime,
    DateTime? lastChecked,
    String? errorMessage,
    Map<String, dynamic>? serverInfo,
  }) {
    return ApiConnectionState(
      isOnline: isOnline ?? this.isOnline,
      isChecking: isChecking ?? this.isChecking,
      responseTime: responseTime ?? this.responseTime,
      lastChecked: lastChecked ?? this.lastChecked,
      errorMessage: errorMessage ?? this.errorMessage,
      serverInfo: serverInfo ?? this.serverInfo,
    );
  }

  /// 오프라인 상태인지 확인
  bool get isOffline => !isOnline && !isChecking;

  /// 연결 상태 텍스트
  String get statusText {
    if (isChecking) return '연결 확인 중...';
    if (isOnline) return '연결됨';
    return '연결 안됨';
  }

  @override
  String toString() {
    return 'ApiConnectionState(isOnline: $isOnline, isChecking: $isChecking, responseTime: $responseTime)';
  }
}

/// API 연결 상태 관리 Notifier
class ApiConnectionNotifier extends StateNotifier<ApiConnectionState> {
  ApiConnectionNotifier() : super(const ApiConnectionState());

  /// API 서버 연결 상태 확인
  Future<void> checkConnection() async {
    state = state.copyWith(isChecking: true, errorMessage: null);

    try {
      // 간단한 헬스체크 엔드포인트로 연결 확인
      // 먼저 간단한 health 체크를 시도하고, 실패하면 recipes 엔드포인트로 확인
      ApiResponse<Map<String, dynamic>> response;
      try {
        response = await SystemApiService.getSimpleHealth();
      } catch (e) {
        // 간단한 health 체크가 실패하면 recipes 엔드포인트로 연결 확인
        debugPrint('🔄 Simple health check failed, trying recipes endpoint...');
        response = await SystemApiService.monitorServerStatus();
      }
      
      state = state.copyWith(
        isChecking: false,
        isOnline: response.success,
        responseTime: response.data?['response_time_ms'] != null 
            ? Duration(milliseconds: response.data!['response_time_ms'])
            : null,
        lastChecked: DateTime.now(),
        serverInfo: response.data,
        errorMessage: response.success ? null : response.message,
      );
      
      debugPrint('📡 API Connection Check: ${response.success ? "SUCCESS" : "FAILED"} - ${response.message}');
    } catch (e) {
      debugPrint('❌ API Connection Check Failed: $e');
      state = state.copyWith(
        isChecking: false,
        isOnline: false,
        lastChecked: DateTime.now(),
        errorMessage: e.toString(),
      );
    }
  }

  /// 연결 상태 강제 설정
  void setConnectionStatus(bool isOnline, {String? errorMessage}) {
    state = state.copyWith(
      isOnline: isOnline,
      isChecking: false,
      errorMessage: errorMessage,
      lastChecked: DateTime.now(),
    );
  }

  /// 오프라인 모드로 설정
  void setOffline() {
    state = state.copyWith(
      isOnline: false,
      isChecking: false,
      errorMessage: '오프라인 모드',
      lastChecked: DateTime.now(),
    );
  }

  /// 상태 초기화
  void reset() {
    state = const ApiConnectionState();
  }
}

/// API 연결 상태 Provider
final apiConnectionProvider = StateNotifierProvider<ApiConnectionNotifier, ApiConnectionState>((ref) {
  return ApiConnectionNotifier();
});

/// API 연결 상태 간편 접근 Provider들
final isApiOnlineProvider = Provider<bool>((ref) {
  return ref.watch(apiConnectionProvider).isOnline;
});

final isApiCheckingProvider = Provider<bool>((ref) {
  return ref.watch(apiConnectionProvider).isChecking;
});

final apiResponseTimeProvider = Provider<Duration?>((ref) {
  return ref.watch(apiConnectionProvider).responseTime;
});

final apiLastCheckedProvider = Provider<DateTime?>((ref) {
  return ref.watch(apiConnectionProvider).lastChecked;
});

final apiErrorMessageProvider = Provider<String?>((ref) {
  return ref.watch(apiConnectionProvider).errorMessage;
});

/// API 클라이언트 초기화 상태 관리
class ApiClientInitializationNotifier extends StateNotifier<bool> {
  ApiClientInitializationNotifier() : super(false);

  void setInitialized(bool isInitialized) {
    state = isInitialized;
  }
}

/// API 클라이언트 초기화 상태 Provider
final apiClientInitializationProvider = StateNotifierProvider<ApiClientInitializationNotifier, bool>((ref) {
  return ApiClientInitializationNotifier();
});

/// API 클라이언트 초기화 Provider (호환성)
final apiClientInitializedProvider = Provider<bool>((ref) {
  return ref.watch(apiClientInitializationProvider);
});

/// API 클라이언트 초기화 함수
Future<void> initializeApiClient(WidgetRef ref) async {
  try {
    // API 클라이언트 초기화
    ApiClient.initialize();

    // 초기화 상태 업데이트
    ref.read(apiClientInitializationProvider.notifier).setInitialized(true);

    // 연결 상태 확인
    final connectionNotifier = ref.read(apiConnectionProvider.notifier);
    await connectionNotifier.checkConnection();

    debugPrint('✅ API Client initialized successfully');
  } catch (e) {
    debugPrint('❌ Failed to initialize API Client: $e');

    // 초기화 실패 상태 업데이트
    ref.read(apiClientInitializationProvider.notifier).setInitialized(false);

    final connectionNotifier = ref.read(apiConnectionProvider.notifier);
    connectionNotifier.setConnectionStatus(false, errorMessage: e.toString());
  }
}
