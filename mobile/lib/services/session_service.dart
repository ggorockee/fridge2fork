import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

/// 세션 관리 서비스
/// API 호출시 필요한 session_id를 관리하고 영속성을 제공
class SessionService {
  static const String _sessionIdKey = 'session_id';
  static const String _sessionCreatedAtKey = 'session_created_at';
  static const String _sessionExpiresAtKey = 'session_expires_at';

  // 세션 만료 시간 (24시간)
  static const Duration sessionDuration = Duration(hours: 24);

  static SessionService? _instance;
  static SharedPreferences? _prefs;

  SessionService._internal();

  /// 싱글톤 인스턴스 반환
  static SessionService get instance {
    _instance ??= SessionService._internal();
    return _instance!;
  }

  /// 서비스 초기화
  static Future<void> initialize() async {
    _prefs = await SharedPreferences.getInstance();
    if (kDebugMode) {
      debugPrint('🔐 SessionService initialized');
    }
  }

  /// SharedPreferences 인스턴스 반환
  SharedPreferences get _preferences {
    if (_prefs == null) {
      throw Exception('SessionService not initialized. Call SessionService.initialize() first.');
    }
    return _prefs!;
  }

  /// 새로운 세션 ID 생성
  String _generateSessionId() {
    const uuid = Uuid();
    return uuid.v4();
  }

  /// 현재 세션 ID 반환 (없거나 만료된 경우 null 반환, 서버에서 생성)
  Future<String?> getSessionId() async {
    final sessionId = _preferences.getString(_sessionIdKey);
    final expiresAtString = _preferences.getString(_sessionExpiresAtKey);

    // 세션이 없는 경우 null 반환 (서버가 생성)
    if (sessionId == null) {
      if (kDebugMode) {
        debugPrint('🔐 No session found, server will create one');
      }
      return null;
    }

    // 만료 시간이 없는 경우 null 반환
    if (expiresAtString == null) {
      if (kDebugMode) {
        debugPrint('🔐 No expiration found, requesting new session from server');
      }
      return null;
    }

    // 세션 만료 확인
    final expiresAt = DateTime.parse(expiresAtString);
    if (DateTime.now().isAfter(expiresAt)) {
      if (kDebugMode) {
        debugPrint('🔐 Session expired, requesting new session from server');
      }
      await clearSession();
      return null;
    }

    if (kDebugMode) {
      debugPrint('🔐 Using existing session: ${sessionId.substring(0, 8)}...');
    }

    return sessionId;
  }

  /// 서버로부터 받은 세션 ID 저장
  Future<void> saveSessionId(String sessionId) async {
    final existingSession = _preferences.getString(_sessionIdKey);

    final createdAt = DateTime.now();
    final expiresAt = createdAt.add(sessionDuration);

    await _preferences.setString(_sessionIdKey, sessionId);
    await _preferences.setString(_sessionCreatedAtKey, createdAt.toIso8601String());
    await _preferences.setString(_sessionExpiresAtKey, expiresAt.toIso8601String());

    if (kDebugMode) {
      if (existingSession != null && existingSession != sessionId) {
        debugPrint('🔍 [DEBUG] ⚠️ Session ID CHANGED!');
        debugPrint('🔍 [DEBUG] Old: ${existingSession.substring(0, 8)}...');
        debugPrint('🔍 [DEBUG] New: ${sessionId.substring(0, 8)}...');
      } else if (existingSession == null) {
        debugPrint('🔍 [DEBUG] ✅ First session ID saved: ${sessionId.substring(0, 8)}...');
      } else {
        debugPrint('🔍 [DEBUG] ✅ Session ID unchanged: ${sessionId.substring(0, 8)}...');
      }
      debugPrint('🔐 Session expires at: ${expiresAt.toLocal()}');
    }
  }

  /// 새로운 세션 생성 및 저장
  Future<String> _createNewSession() async {
    final sessionId = _generateSessionId();
    final createdAt = DateTime.now();
    final expiresAt = createdAt.add(sessionDuration);

    await _preferences.setString(_sessionIdKey, sessionId);
    await _preferences.setString(_sessionCreatedAtKey, createdAt.toIso8601String());
    await _preferences.setString(_sessionExpiresAtKey, expiresAt.toIso8601String());

    if (kDebugMode) {
      debugPrint('🔐 Created new session: ${sessionId.substring(0, 8)}...');
      debugPrint('🔐 Session expires at: ${expiresAt.toLocal()}');
    }

    return sessionId;
  }

  /// 세션 강제 새로 생성
  Future<String> renewSession() async {
    if (kDebugMode) {
      debugPrint('🔐 Renewing session...');
    }
    return await _createNewSession();
  }

  /// 세션 정보 반환
  Future<Map<String, dynamic>?> getSessionInfo() async {
    final sessionId = _preferences.getString(_sessionIdKey);
    final createdAtString = _preferences.getString(_sessionCreatedAtKey);
    final expiresAtString = _preferences.getString(_sessionExpiresAtKey);

    if (sessionId == null || createdAtString == null || expiresAtString == null) {
      return null;
    }

    final createdAt = DateTime.parse(createdAtString);
    final expiresAt = DateTime.parse(expiresAtString);
    final isExpired = DateTime.now().isAfter(expiresAt);

    return {
      'session_id': sessionId,
      'created_at': createdAt,
      'expires_at': expiresAt,
      'is_expired': isExpired,
      'remaining_hours': expiresAt.difference(DateTime.now()).inHours,
    };
  }

  /// 세션 삭제
  Future<void> clearSession() async {
    await _preferences.remove(_sessionIdKey);
    await _preferences.remove(_sessionCreatedAtKey);
    await _preferences.remove(_sessionExpiresAtKey);

    if (kDebugMode) {
      debugPrint('🔐 Session cleared');
    }
  }

  /// 세션 연장 (현재 시점부터 24시간)
  Future<void> extendSession() async {
    final sessionId = _preferences.getString(_sessionIdKey);
    if (sessionId != null) {
      final expiresAt = DateTime.now().add(sessionDuration);
      await _preferences.setString(_sessionExpiresAtKey, expiresAt.toIso8601String());

      if (kDebugMode) {
        debugPrint('🔐 Session extended until: ${expiresAt.toLocal()}');
      }
    }
  }
}