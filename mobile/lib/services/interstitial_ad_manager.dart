import 'package:flutter/foundation.dart';
import 'ad_service.dart';

/// 전면 광고 표시 관리자
/// 
/// 🎯 수익성 극대화 전략:
/// - 사용자 액션 완료 후 적절한 타이밍에 표시
/// - 과도한 광고로 인한 사용자 이탈 방지
/// - 앱 플로우를 방해하지 않는 자연스러운 배치
class InterstitialAdManager {
  static final InterstitialAdManager _instance = InterstitialAdManager._internal();
  factory InterstitialAdManager() => _instance;
  InterstitialAdManager._internal();

  final AdService _adService = AdService();
  
  // 광고 표시 조건
  int _recipeViewCount = 0;
  int _ingredientAddCount = 0;
  DateTime? _lastAdShown;
  
  // 설정값 (수익성 최적화)
  static const int _recipeViewThreshold = 3; // 레시피 3개 볼 때마다
  static const int _ingredientAddThreshold = 5; // 식재료 5개 추가할 때마다
  static const int _minIntervalMinutes = 2; // 최소 2분 간격

  /// 레시피 상세보기 시 호출
  Future<void> onRecipeViewed() async {
    _recipeViewCount++;
    debugPrint('📊 레시피 조회 카운트: $_recipeViewCount');
    
    if (_recipeViewCount >= _recipeViewThreshold) {
      await _tryShowInterstitial('recipe_view');
      _recipeViewCount = 0; // 카운트 리셋
    }
  }

  /// 식재료 추가 완료 시 호출
  Future<void> onIngredientAdded() async {
    _ingredientAddCount++;
    debugPrint('📊 식재료 추가 카운트: $_ingredientAddCount');
    
    if (_ingredientAddCount >= _ingredientAddThreshold) {
      await _tryShowInterstitial('ingredient_add');
      _ingredientAddCount = 0; // 카운트 리셋
    }
  }

  /// 앱 시작 후 일정 시간 후 호출 (첫 방문자용)
  Future<void> onAppLaunched() async {
    // 3분 후에 첫 광고 표시 기회 제공
    Future.delayed(const Duration(minutes: 3), () {
      _tryShowInterstitial('app_launch');
    });
  }

  /// 레시피 검색 완료 후 호출
  Future<void> onRecipeSearchCompleted() async {
    // 검색 결과를 본 후 광고 표시 기회
    await _tryShowInterstitial('recipe_search');
  }

  /// 전면 광고 표시 시도
  Future<void> _tryShowInterstitial(String trigger) async {
    // 최소 간격 확인
    if (_lastAdShown != null) {
      final timeSinceLastAd = DateTime.now().difference(_lastAdShown!);
      if (timeSinceLastAd.inMinutes < _minIntervalMinutes) {
        debugPrint('⏰ 전면 광고 최소 간격 미충족: ${timeSinceLastAd.inMinutes}분 < ${_minIntervalMinutes}분');
        return;
      }
    }

    // 광고 준비 상태 확인
    if (!_adService.isInterstitialReady) {
      debugPrint('⚠️ 전면 광고가 준비되지 않음 - 프리로드 시작');
      await _adService.loadInterstitialAd();
      return;
    }

    // 광고 표시
    final success = await _adService.showInterstitialAd();
    if (success) {
      _lastAdShown = DateTime.now();
      debugPrint('🎯 전면 광고 표시 성공 - 트리거: $trigger');
    } else {
      debugPrint('❌ 전면 광고 표시 실패 - 트리거: $trigger');
    }
  }

  /// 통계 리셋 (테스트용)
  void resetCounters() {
    _recipeViewCount = 0;
    _ingredientAddCount = 0;
    _lastAdShown = null;
    debugPrint('🔄 전면 광고 카운터 리셋');
  }

  /// 현재 상태 확인 (디버깅용)
  void printStatus() {
    debugPrint('=== 전면 광고 관리자 상태 ===');
    debugPrint('레시피 조회 카운트: $_recipeViewCount / $_recipeViewThreshold');
    debugPrint('식재료 추가 카운트: $_ingredientAddCount / $_ingredientAddThreshold');
    debugPrint('마지막 광고 표시: $_lastAdShown');
    debugPrint('광고 준비 상태: ${_adService.isInterstitialReady}');
    debugPrint('========================');
  }
}
