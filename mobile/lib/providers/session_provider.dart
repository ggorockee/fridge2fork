import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/foundation.dart';
import '../services/session_service.dart';

/// 세션 상태 클래스
class SessionState {
  final String sessionId;
  final DateTime createdAt;
  final DateTime expiresAt;
  final bool isExpired;
  final int remainingHours;

  const SessionState({
    required this.sessionId,
    required this.createdAt,
    required this.expiresAt,
    required this.isExpired,
    required this.remainingHours,
  });

  SessionState copyWith({
    String? sessionId,
    DateTime? createdAt,
    DateTime? expiresAt,
    bool? isExpired,
    int? remainingHours,
  }) {
    return SessionState(
      sessionId: sessionId ?? this.sessionId,
      createdAt: createdAt ?? this.createdAt,
      expiresAt: expiresAt ?? this.expiresAt,
      isExpired: isExpired ?? this.isExpired,
      remainingHours: remainingHours ?? this.remainingHours,
    );
  }
}

/// 세션 Provider
class SessionNotifier extends StateNotifier<SessionState?> {
  SessionNotifier() : super(null) {
    _initializeSession();
  }

  /// 세션 초기화
  Future<void> _initializeSession() async {
    try {
      await _refreshSessionState();
    } catch (e) {
      if (kDebugMode) {
        debugPrint('🔐 Session initialization error: $e');
      }
      // 세션 초기화 실패시 새 세션 생성
      await renewSession();
    }
  }

  /// 세션 상태 새로고침
  Future<void> _refreshSessionState() async {
    final sessionInfo = await SessionService.instance.getSessionInfo();

    if (sessionInfo != null) {
      state = SessionState(
        sessionId: sessionInfo['session_id'],
        createdAt: sessionInfo['created_at'],
        expiresAt: sessionInfo['expires_at'],
        isExpired: sessionInfo['is_expired'],
        remainingHours: sessionInfo['remaining_hours'],
      );
    }
  }

  /// 현재 세션 ID 반환 (없으면 null - 서버가 새로 생성)
  Future<String?> getSessionId() async {
    final sessionId = await SessionService.instance.getSessionId();
    await _refreshSessionState(); // 세션 정보 업데이트
    return sessionId;
  }

  /// 세션 새로 생성
  Future<void> renewSession() async {
    try {
      await SessionService.instance.renewSession();
      await _refreshSessionState();

      if (kDebugMode) {
        debugPrint('🔐 Session renewed successfully');
      }
    } catch (e) {
      if (kDebugMode) {
        debugPrint('🔐 Session renewal error: $e');
      }
    }
  }

  /// 세션 연장
  Future<void> extendSession() async {
    try {
      await SessionService.instance.extendSession();
      await _refreshSessionState();

      if (kDebugMode) {
        debugPrint('🔐 Session extended successfully');
      }
    } catch (e) {
      if (kDebugMode) {
        debugPrint('🔐 Session extension error: $e');
      }
    }
  }

  /// 세션 삭제
  Future<void> clearSession() async {
    try {
      await SessionService.instance.clearSession();
      state = null;

      if (kDebugMode) {
        debugPrint('🔐 Session cleared successfully');
      }
    } catch (e) {
      if (kDebugMode) {
        debugPrint('🔐 Session clear error: $e');
      }
    }
  }

  /// 세션 만료 체크 및 자동 갱신
  Future<bool> checkAndRenewIfExpired() async {
    try {
      await _refreshSessionState();

      if (state?.isExpired == true) {
        await renewSession();
        return true; // 세션이 갱신됨
      }

      return false; // 세션이 유효함
    } catch (e) {
      if (kDebugMode) {
        debugPrint('🔐 Session check error: $e');
      }
      return false;
    }
  }
}

/// 세션 상태 Provider
final sessionProvider = StateNotifierProvider<SessionNotifier, SessionState?>(
  (ref) => SessionNotifier(),
);

/// 현재 세션 ID Provider (없으면 null - 서버가 새로 생성)
final currentSessionIdProvider = FutureProvider<String?>((ref) async {
  final sessionNotifier = ref.read(sessionProvider.notifier);
  return await sessionNotifier.getSessionId();
});

/// 세션 유효성 Provider
final sessionValidityProvider = Provider<bool>((ref) {
  final session = ref.watch(sessionProvider);
  return session != null && !session.isExpired;
});