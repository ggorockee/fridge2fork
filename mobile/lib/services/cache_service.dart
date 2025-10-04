import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart';

/// 캐시 서비스 - 오프라인 지원을 위한 로컬 데이터 저장
class CacheService {
  static const String _ingredientsCacheKey = 'cached_ingredients';
  static const String _recipesCacheKey = 'cached_recipes';
  static const String _recipesByIngredientsKey = 'cached_recipes_by_ingredients';
  static const String _lastUpdateKey = 'last_cache_update';
  static const String _apiConnectionKey = 'api_connection_status';
  
  /// SharedPreferences 인스턴스
  static SharedPreferences? _prefs;
  
  /// SharedPreferences 초기화
  static Future<void> initialize() async {
    _prefs ??= await SharedPreferences.getInstance();
  }
  
  /// 캐시 만료 시간 (24시간)
  static const Duration _cacheExpiry = Duration(hours: 24);
  
  // ===========================================
  // 식재료 캐시 관리
  // ===========================================
  
  /// 식재료 목록 캐시 저장
  static Future<void> cacheIngredients(List<Map<String, dynamic>> ingredients) async {
    await _initializeIfNeeded();
    
    final ingredientsJson = jsonEncode(ingredients);
    await _prefs!.setString(_ingredientsCacheKey, ingredientsJson);
    await _updateLastCacheTime();
    
    if (kDebugMode) {
      print('📦 Cached ${ingredients.length} ingredients');
    }
  }
  
  /// 캐시된 식재료 목록 가져오기
  static Future<List<Map<String, dynamic>>?> getCachedIngredients() async {
    await _initializeIfNeeded();
    
    final ingredientsJson = _prefs!.getString(_ingredientsCacheKey);
    if (ingredientsJson == null) return null;
    
    try {
      final List<dynamic> ingredientsList = jsonDecode(ingredientsJson);
      return ingredientsList.cast<Map<String, dynamic>>();
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to parse cached ingredients: $e');
      }
      return null;
    }
  }
  
  // ===========================================
  // 레시피 캐시 관리
  // ===========================================
  
  /// 레시피 목록 캐시 저장
  static Future<void> cacheRecipes(List<Map<String, dynamic>> recipes) async {
    await _initializeIfNeeded();
    
    final recipesJson = jsonEncode(recipes);
    await _prefs!.setString(_recipesCacheKey, recipesJson);
    await _updateLastCacheTime();
    
    if (kDebugMode) {
      print('📦 Cached ${recipes.length} recipes');
    }
  }
  
  /// 캐시된 레시피 목록 가져오기
  static Future<List<Map<String, dynamic>>?> getCachedRecipes() async {
    await _initializeIfNeeded();
    
    final recipesJson = _prefs!.getString(_recipesCacheKey);
    if (recipesJson == null) return null;
    
    try {
      final List<dynamic> recipesList = jsonDecode(recipesJson);
      return recipesList.cast<Map<String, dynamic>>();
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to parse cached recipes: $e');
      }
      return null;
    }
  }
  
  // ===========================================
  // API 연결 상태 관리
  // ===========================================
  
  /// API 연결 상태 저장
  static Future<void> setApiConnectionStatus(bool isConnected) async {
    await _initializeIfNeeded();
    await _prefs!.setBool(_apiConnectionKey, isConnected);
  }
  
  /// 마지막 API 연결 상태 가져오기
  static Future<bool?> getLastApiConnectionStatus() async {
    await _initializeIfNeeded();
    return _prefs!.getBool(_apiConnectionKey);
  }
  
  // ===========================================
  // 캐시 유효성 검사
  // ===========================================
  
  /// 캐시가 유효한지 확인 (만료되지 않았는지)
  static Future<bool> isCacheValid() async {
    await _initializeIfNeeded();
    
    final lastUpdateString = _prefs!.getString(_lastUpdateKey);
    if (lastUpdateString == null) return false;
    
    try {
      final lastUpdate = DateTime.parse(lastUpdateString);
      final now = DateTime.now();
      final difference = now.difference(lastUpdate);
      
      return difference < _cacheExpiry;
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to parse last update time: $e');
      }
      return false;
    }
  }
  
  /// 캐시 업데이트 시간 갱신
  static Future<void> _updateLastCacheTime() async {
    await _prefs!.setString(_lastUpdateKey, DateTime.now().toIso8601String());
  }
  
  /// 캐시 마지막 업데이트 시간 가져오기
  static Future<DateTime?> getLastCacheUpdateTime() async {
    await _initializeIfNeeded();
    
    final lastUpdateString = _prefs!.getString(_lastUpdateKey);
    if (lastUpdateString == null) return null;
    
    try {
      return DateTime.parse(lastUpdateString);
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to parse last update time: $e');
      }
      return null;
    }
  }
  
  // ===========================================
  // 캐시 관리
  // ===========================================
  
  /// 재료 기반 레시피 목록 캐시 저장 (Phase 2 핵심 기능)
  static Future<void> cacheRecipesByIngredients(
    List<String> ingredients,
    List<dynamic> recipes,
  ) async {
    await _initializeIfNeeded();

    final cacheKey = '${_recipesByIngredientsKey}_${ingredients.join('_')}';
    final cacheData = {
      'ingredients': ingredients,
      'recipes': recipes.map((recipe) => recipe.toJson()).toList(),
      'cached_at': DateTime.now().toIso8601String(),
    };

    final cacheJson = jsonEncode(cacheData);
    await _prefs!.setString(cacheKey, cacheJson);

    if (kDebugMode) {
      print('📦 Cached ${recipes.length} recipes for ingredients: ${ingredients.join(", ")}');
    }
  }

  /// 재료 기반 캐시된 레시피 목록 가져오기 (Phase 2 핵심 기능)
  static Future<List<dynamic>> getCachedRecipesByIngredients(
    List<String> ingredients,
  ) async {
    await _initializeIfNeeded();

    final cacheKey = '${_recipesByIngredientsKey}_${ingredients.join('_')}';
    final cacheJson = _prefs!.getString(cacheKey);

    if (cacheJson == null) return [];

    try {
      final cacheData = jsonDecode(cacheJson) as Map<String, dynamic>;
      final cachedAt = DateTime.parse(cacheData['cached_at']);

      // 24시간 이내의 캐시만 유효
      if (DateTime.now().difference(cachedAt) > _cacheExpiry) {
        await _prefs!.remove(cacheKey);
        return [];
      }

      final List<dynamic> recipesList = cacheData['recipes'];
      return recipesList;
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to parse cached recipes by ingredients: $e');
      }
      return [];
    }
  }

  /// 모든 캐시 삭제
  static Future<void> clearAllCache() async {
    await _initializeIfNeeded();

    await _prefs!.remove(_ingredientsCacheKey);
    await _prefs!.remove(_recipesCacheKey);
    await _prefs!.remove(_lastUpdateKey);
    await _prefs!.remove(_apiConnectionKey);

    // 재료 기반 레시피 캐시들도 모두 삭제
    final keys = _prefs!.getKeys();
    for (final key in keys) {
      if (key.startsWith(_recipesByIngredientsKey)) {
        await _prefs!.remove(key);
      }
    }

    if (kDebugMode) {
      print('🗑️ All cache cleared');
    }
  }
  
  /// 특정 캐시 삭제
  static Future<void> clearCache(String key) async {
    await _initializeIfNeeded();
    await _prefs!.remove(key);
    
    if (kDebugMode) {
      print('🗑️ Cache cleared for key: $key');
    }
  }
  
  /// 캐시 크기 정보
  static Future<Map<String, int>> getCacheInfo() async {
    await _initializeIfNeeded();
    
    final ingredientsJson = _prefs!.getString(_ingredientsCacheKey);
    final recipesJson = _prefs!.getString(_recipesCacheKey);
    
    return {
      'ingredients_size': ingredientsJson?.length ?? 0,
      'recipes_size': recipesJson?.length ?? 0,
      'total_size': (ingredientsJson?.length ?? 0) + (recipesJson?.length ?? 0),
    };
  }
  
  // ===========================================
  // 헬퍼 메서드
  // ===========================================
  
  /// SharedPreferences 초기화 확인
  static Future<void> _initializeIfNeeded() async {
    if (_prefs == null) {
      await initialize();
    }
  }
  
  /// 디버그용 캐시 상태 출력
  static Future<void> printCacheStatus() async {
    if (!kDebugMode) return;
    
    await _initializeIfNeeded();
    
    final isValid = await isCacheValid();
    final lastUpdate = await getLastCacheUpdateTime();
    final cacheInfo = await getCacheInfo();
    final connectionStatus = await getLastApiConnectionStatus();
    
    print('=== Cache Status ===');
    print('Valid: $isValid');
    print('Last Update: $lastUpdate');
    print('Cache Info: $cacheInfo');
    print('Last Connection: $connectionStatus');
    print('==================');
  }
}
