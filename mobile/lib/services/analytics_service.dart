import 'package:firebase_analytics/firebase_analytics.dart';

/// Firebase Analytics 이벤트를 관리하는 서비스 클래스
///
/// 사용자 행동을 추적하고 데이터 기반 의사결정을 돕습니다.
/// 모든 이벤트 로그는 이 클래스를 통해 호출되어야 일관성이 유지됩니다.
class AnalyticsService {
  static final AnalyticsService _instance = AnalyticsService._internal();
  factory AnalyticsService() => _instance;
  AnalyticsService._internal();

  final FirebaseAnalytics _analytics = FirebaseAnalytics.instance;

  /// 현재 화면 추적 (screen_view)
  ///
  /// 사용자가 어떤 화면을 보고 있는지 추적합니다.
  /// 각 화면의 `build` 메소드나 `initState`에서 호출하는 것이 좋습니다.
  Future<void> logScreenView(String screenName) async {
    await _analytics.logScreenView(screenName: screenName);
  }

  /// 커스텀 이벤트 로그
  ///
  /// [name] 이벤트 이름 (snake_case 권장)
  /// [parameters] 이벤트와 함께 전송할 추가 데이터
  Future<void> logEvent(String name, {Map<String, Object>? parameters}) async {
    await _analytics.logEvent(name: name, parameters: parameters);
  }

  // =======================================================================
  // 아래는 앱의 주요 기능에 대한 구체적인 이벤트 로깅 메소드입니다.
  // =======================================================================

  /// 식재료 추가 이벤트
  Future<void> logAddIngredients(List<String> ingredients) async {
    await logEvent(
      'add_ingredients',
      parameters: {
        'ingredient_count': ingredients.length,
        'ingredient_list': ingredients.join(','),
      },
    );
  }

  /// 레시피 조회 이벤트
  Future<void> logViewRecipe(String recipeName, String recipeId) async {
    await logEvent(
      'view_recipe',
      parameters: {
        'recipe_name': recipeName,
        'recipe_id': recipeId,
      },
    );
  }

  /// 레시피 검색 이벤트 (재료 기반)
  Future<void> logSearchByIngredients(List<String> ingredients) async {
    await logEvent(
      'search_by_ingredients',
      parameters: {
        'ingredient_count': ingredients.length,
        'ingredient_list': ingredients.join(','),
      },
    );
  }

  /// 카테고리 선택 이벤트
  Future<void> logSelectCategory(String category) async {
    await logEvent(
      'select_category',
      parameters: {'category': category},
    );
  }

  /// 공유 이벤트
  Future<void> logShare(String contentType, String itemId) async {
    await _analytics.logShare(
      contentType: contentType,
      itemId: itemId,
      method: 'app_share', // 공유 방법 (예: 카카오톡, 링크 복사 등)
    );
  }
}
