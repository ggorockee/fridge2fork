import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/api/api_ad_config.dart';
import 'api/system_api_service.dart';
import '../config/app_config.dart';

/// AdMob 광고 설정 관리자
///
/// 서버에서 광고 설정을 동적으로 로드하고 로컬에 캐싱합니다.
/// 앱 재배포 없이 광고 ID를 변경할 수 있습니다.
class AdConfigManager {
  static final AdConfigManager _instance = AdConfigManager._internal();
  factory AdConfigManager() => _instance;
  AdConfigManager._internal();

  // 캐시된 광고 설정
  AdConfigResponse? _cachedConfig;
  DateTime? _lastFetchTime;

  // SharedPreferences 키
  static const String _adConfigKey = 'ad_config_cache';
  static const String _lastFetchTimeKey = 'ad_config_last_fetch';

  // 캐시 유효 기간 (24시간)
  static const Duration _cacheDuration = Duration(hours: 24);

  /// 광고 설정 초기화 및 로드
  ///
  /// 앱 시작 시 호출하여 광고 설정을 로드합니다.
  /// 캐시가 유효하면 로컬 캐시를 사용하고, 그렇지 않으면 서버에서 가져옵니다.
  Future<bool> initialize() async {
    try {
      debugPrint('🎯 AdConfigManager 초기화 시작');

      // 1. 로컬 캐시 확인
      await _loadFromCache();

      // 2. 캐시가 유효한지 확인
      if (_isCacheValid()) {
        debugPrint('✅ 광고 설정 캐시가 유효함 - 서버 요청 생략');
        return true;
      }

      // 3. 캐시가 유효하지 않으면 서버에서 가져오기
      debugPrint('🔄 광고 설정 캐시가 만료됨 - 서버에서 다시 로드');
      return await fetchFromServer();
    } catch (e) {
      debugPrint('❌ AdConfigManager 초기화 실패: $e');

      // 초기화 실패 시에도 캐시된 설정이 있으면 사용
      if (_cachedConfig != null) {
        debugPrint('⚠️ 캐시된 광고 설정으로 대체');
        return true;
      }

      // 캐시도 없으면 환경 변수 fallback 사용
      debugPrint('⚠️ 환경 변수 fallback 사용');
      return false;
    }
  }

  /// 서버에서 광고 설정 가져오기
  Future<bool> fetchFromServer() async {
    try {
      final response = await SystemApiService.getAdConfig();

      if (response.success && response.data != null) {
        _cachedConfig = response.data!;
        _lastFetchTime = DateTime.now();

        // 로컬에 저장
        await _saveToCache();

        debugPrint('✅ 광고 설정 로드 성공');
        debugPrint('📊 광고 설정: $_cachedConfig');
        return true;
      } else {
        debugPrint('❌ 광고 설정 로드 실패: ${response.message}');
        return false;
      }
    } catch (e) {
      debugPrint('❌ 광고 설정 로드 중 오류: $e');
      return false;
    }
  }

  /// 캐시가 유효한지 확인
  bool _isCacheValid() {
    if (_cachedConfig == null || _lastFetchTime == null) {
      return false;
    }

    final elapsed = DateTime.now().difference(_lastFetchTime!);
    return elapsed < _cacheDuration;
  }

  /// SharedPreferences에서 캐시 로드
  Future<void> _loadFromCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final configJson = prefs.getString(_adConfigKey);
      final lastFetchTimeStr = prefs.getString(_lastFetchTimeKey);

      if (configJson != null && lastFetchTimeStr != null) {
        final json = jsonDecode(configJson) as Map<String, dynamic>;
        _cachedConfig = AdConfigResponse.fromJson(json);
        _lastFetchTime = DateTime.parse(lastFetchTimeStr);

        debugPrint('✅ 광고 설정 캐시 로드 성공');
      } else {
        debugPrint('ℹ️ 광고 설정 캐시 없음');
      }
    } catch (e) {
      debugPrint('❌ 광고 설정 캐시 로드 실패: $e');
    }
  }

  /// SharedPreferences에 캐시 저장
  Future<void> _saveToCache() async {
    try {
      if (_cachedConfig == null || _lastFetchTime == null) return;

      final prefs = await SharedPreferences.getInstance();
      final configJson = jsonEncode(_cachedConfig!.toJson());
      final lastFetchTimeStr = _lastFetchTime!.toIso8601String();

      await prefs.setString(_adConfigKey, configJson);
      await prefs.setString(_lastFetchTimeKey, lastFetchTimeStr);

      debugPrint('✅ 광고 설정 캐시 저장 성공');
    } catch (e) {
      debugPrint('❌ 광고 설정 캐시 저장 실패: $e');
    }
  }

  /// 캐시 삭제 (테스트용)
  Future<void> clearCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_adConfigKey);
      await prefs.remove(_lastFetchTimeKey);

      _cachedConfig = null;
      _lastFetchTime = null;

      debugPrint('🗑️ 광고 설정 캐시 삭제 완료');
    } catch (e) {
      debugPrint('❌ 광고 설정 캐시 삭제 실패: $e');
    }
  }

  /// 광고 설정 강제 갱신
  Future<bool> refresh() async {
    debugPrint('🔄 광고 설정 강제 갱신');
    return await fetchFromServer();
  }

  // ===========================================
  // 광고 ID Getters (동적 fallback 지원)
  // ===========================================

  /// 상단 배너 광고 ID
  String get bannerTopId {
    // 1순위: 서버에서 가져온 설정
    if (_cachedConfig?.bannerTop != null && _cachedConfig!.bannerTop!.isNotEmpty) {
      return _cachedConfig!.bannerTop!;
    }

    // 2순위: 환경 변수 fallback
    if (Platform.isAndroid) {
      return AppConfig.admobAndroidBannerTopId;
    } else if (Platform.isIOS) {
      return AppConfig.admobIosBannerTopId;
    }

    return '';
  }

  /// 하단 배너 광고 ID
  String get bannerBottomId {
    if (_cachedConfig?.bannerBottom != null && _cachedConfig!.bannerBottom!.isNotEmpty) {
      return _cachedConfig!.bannerBottom!;
    }

    if (Platform.isAndroid) {
      return AppConfig.admobAndroidBannerBottomId;
    } else if (Platform.isIOS) {
      return AppConfig.admobIosBannerBottomId;
    }

    return '';
  }

  /// 전면 광고 1 ID
  String get interstitial1Id {
    if (_cachedConfig?.interstitial1 != null && _cachedConfig!.interstitial1!.isNotEmpty) {
      return _cachedConfig!.interstitial1!;
    }

    if (Platform.isAndroid) {
      return AppConfig.admobAndroidInterstitialId;
    } else if (Platform.isIOS) {
      return AppConfig.admobIosInterstitialId;
    }

    return '';
  }

  /// 전면 광고 2 ID
  String get interstitial2Id {
    if (_cachedConfig?.interstitial2 != null && _cachedConfig!.interstitial2!.isNotEmpty) {
      return _cachedConfig!.interstitial2!;
    }

    // Fallback: interstitial1Id와 동일
    return interstitial1Id;
  }

  /// 네이티브 광고 1 ID
  String get native1Id {
    if (_cachedConfig?.native1 != null && _cachedConfig!.native1!.isNotEmpty) {
      return _cachedConfig!.native1!;
    }

    if (Platform.isAndroid) {
      return AppConfig.admobAndroidNativeId;
    } else if (Platform.isIOS) {
      return AppConfig.admobIosNativeId;
    }

    return '';
  }

  /// 네이티브 광고 2 ID
  String get native2Id {
    if (_cachedConfig?.native2 != null && _cachedConfig!.native2!.isNotEmpty) {
      return _cachedConfig!.native2!;
    }

    // Fallback: native1Id와 동일
    return native1Id;
  }

  /// 광고 설정이 로드되었는지 확인
  bool get isLoaded => _cachedConfig != null;

  /// 캐시된 광고 설정
  AdConfigResponse? get cachedConfig => _cachedConfig;

  /// 마지막 갱신 시간
  DateTime? get lastFetchTime => _lastFetchTime;

  /// 디버그 정보 출력
  void printDebugInfo() {
    debugPrint('=== AdConfigManager 상태 ===');
    debugPrint('광고 설정 로드 여부: $isLoaded');
    debugPrint('마지막 갱신 시간: $_lastFetchTime');
    debugPrint('캐시 유효 여부: ${_isCacheValid()}');
    debugPrint('상단 배너 ID: $bannerTopId');
    debugPrint('하단 배너 ID: $bannerBottomId');
    debugPrint('전면 광고 1 ID: $interstitial1Id');
    debugPrint('전면 광고 2 ID: $interstitial2Id');
    debugPrint('네이티브 광고 1 ID: $native1Id');
    debugPrint('네이티브 광고 2 ID: $native2Id');
    debugPrint('========================');
  }
}
