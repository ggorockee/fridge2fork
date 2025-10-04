import 'package:flutter/foundation.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'cache_service.dart';
import '../models/api/api_ingredient.dart';
import '../models/api/api_recipe.dart';
import '../models/api/api_response.dart';

/// 오프라인 서비스 - 네트워크 상태 감지 및 오프라인 데이터 제공
class OfflineService {
  static final Connectivity _connectivity = Connectivity();
  static bool _isOnline = true;
  static final List<VoidCallback> _connectionListeners = [];
  
  /// 네트워크 연결 상태 초기화
  static Future<void> initialize() async {
    await _checkConnectivity();
    _connectivity.onConnectivityChanged.listen((List<ConnectivityResult> results) {
      _updateConnectionStatus(results.first);
    });
  }
  
  /// 현재 온라인 상태인지 확인
  static bool get isOnline => _isOnline;
  
  /// 현재 오프라인 상태인지 확인
  static bool get isOffline => !_isOnline;
  
  /// 연결 상태 확인
  static Future<void> _checkConnectivity() async {
    try {
      final results = await _connectivity.checkConnectivity();
      _updateConnectionStatus(results.first);
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to check connectivity: $e');
      }
      _isOnline = false;
    }
  }
  
  /// 연결 상태 업데이트
  static void _updateConnectionStatus(ConnectivityResult result) {
    final wasOnline = _isOnline;
    _isOnline = result != ConnectivityResult.none;
    
    // 상태가 변경되었을 때만 알림
    if (wasOnline != _isOnline) {
      if (kDebugMode) {
        print('🌐 Connection status changed: ${_isOnline ? "Online" : "Offline"}');
      }
      
      // 연결 상태를 캐시에 저장
      CacheService.setApiConnectionStatus(_isOnline);
      
      // 리스너들에게 알림
      for (final listener in _connectionListeners) {
        try {
          listener();
        } catch (e) {
          if (kDebugMode) {
            print('❌ Error in connection listener: $e');
          }
        }
      }
    }
  }
  
  /// 연결 상태 변경 리스너 추가
  static void addConnectionListener(VoidCallback listener) {
    _connectionListeners.add(listener);
  }
  
  /// 연결 상태 변경 리스너 제거
  static void removeConnectionListener(VoidCallback listener) {
    _connectionListeners.remove(listener);
  }
  
  // ===========================================
  // 오프라인 데이터 제공
  // ===========================================
  
  /// 오프라인 식재료 데이터 제공
  static Future<ApiResponse<List<ApiIngredient>>> getOfflineIngredients() async {
    try {
      final cachedData = await CacheService.getCachedIngredients();
      
      if (cachedData == null || cachedData.isEmpty) {
        return ApiResponse.error(
          message: '오프라인 식재료 데이터가 없습니다.',
          errorCode: 'NO_OFFLINE_DATA',
          statusCode: 404,
        );
      }
      
      final ingredients = cachedData
          .map((json) => ApiIngredient.fromJson(json))
          .toList();
      
      return ApiResponse.success(
        data: ingredients,
        message: '오프라인 식재료 데이터를 로드했습니다.',
        statusCode: 200,
      );
    } catch (e) {
      return ApiResponse.error(
        message: '오프라인 식재료 데이터 로드 실패: $e',
        errorCode: 'OFFLINE_LOAD_ERROR',
        statusCode: 500,
      );
    }
  }
  
  /// 오프라인 레시피 데이터 제공
  static Future<ApiResponse<List<ApiRecipe>>> getOfflineRecipes() async {
    try {
      final cachedData = await CacheService.getCachedRecipes();
      
      if (cachedData == null || cachedData.isEmpty) {
        return ApiResponse.error(
          message: '오프라인 레시피 데이터가 없습니다.',
          errorCode: 'NO_OFFLINE_DATA',
          statusCode: 404,
        );
      }
      
      final recipes = cachedData
          .map((json) => ApiRecipe.fromJson(json))
          .toList();
      
      return ApiResponse.success(
        data: recipes,
        message: '오프라인 레시피 데이터를 로드했습니다.',
        statusCode: 200,
      );
    } catch (e) {
      return ApiResponse.error(
        message: '오프라인 레시피 데이터 로드 실패: $e',
        errorCode: 'OFFLINE_LOAD_ERROR',
        statusCode: 500,
      );
    }
  }
  
  /// 오프라인 레시피 검색 (재료 기반)
  static Future<ApiResponse<List<ApiRecipe>>> searchOfflineRecipesByIngredients(
    List<String> ingredientNames,
  ) async {
    try {
      final offlineResponse = await getOfflineRecipes();
      
      if (!offlineResponse.success || offlineResponse.data == null) {
        return offlineResponse;
      }
      
      final recipes = offlineResponse.data!;
      
      // 재료 이름으로 필터링 (간단한 문자열 매칭)
      final filteredRecipes = recipes.where((recipe) {
        return recipe.ingredients.any((recipeIngredient) {
          return ingredientNames.any((userIngredient) =>
              recipeIngredient.name.toLowerCase().contains(userIngredient.toLowerCase()) ||
              userIngredient.toLowerCase().contains(recipeIngredient.name.toLowerCase()));
        });
      }).toList();
      
      // 매칭율 계산 및 정렬
      filteredRecipes.sort((a, b) {
        final aMatches = _calculateMatchingRate(a, ingredientNames);
        final bMatches = _calculateMatchingRate(b, ingredientNames);
        return bMatches.compareTo(aMatches);
      });
      
      return ApiResponse.success(
        data: filteredRecipes,
        message: '오프라인에서 ${filteredRecipes.length}개의 레시피를 찾았습니다.',
        statusCode: 200,
      );
    } catch (e) {
      return ApiResponse.error(
        message: '오프라인 레시피 검색 실패: $e',
        errorCode: 'OFFLINE_SEARCH_ERROR',
        statusCode: 500,
      );
    }
  }
  
  /// 레시피와 사용자 재료의 매칭율 계산
  static double _calculateMatchingRate(ApiRecipe recipe, List<String> userIngredients) {
    if (recipe.ingredients.isEmpty) return 0.0;
    
    int matchCount = 0;
    for (final recipeIngredient in recipe.ingredients) {
      if (userIngredients.any((userIngredient) => 
          userIngredient.toLowerCase().contains(recipeIngredient.name.toLowerCase()) ||
          recipeIngredient.name.toLowerCase().contains(userIngredient.toLowerCase()))) {
        matchCount++;
      }
    }
    
    return (matchCount / recipe.ingredients.length) * 100;
  }
  
  // ===========================================
  // 네트워크 상태 체크
  // ===========================================
  
  /// 네트워크 연결 상태 확인
  static Future<bool> checkNetworkConnection() async {
    try {
      final results = await _connectivity.checkConnectivity();
      return results.first != ConnectivityResult.none;
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to check network connection: $e');
      }
      return false;
    }
  }
  
  /// 캐시 유효성 확인
  static Future<bool> hasValidCache() async {
    return await CacheService.isCacheValid();
  }
  
  /// 오프라인 모드에서 사용 가능한 데이터 확인
  static Future<Map<String, bool>> getOfflineDataAvailability() async {
    final ingredientsCache = await CacheService.getCachedIngredients();
    final recipesCache = await CacheService.getCachedRecipes();
    final hasValidCache = await CacheService.isCacheValid();
    
    return {
      'hasIngredients': ingredientsCache != null && ingredientsCache.isNotEmpty,
      'hasRecipes': recipesCache != null && recipesCache.isNotEmpty,
      'hasValidCache': hasValidCache,
      'isOfflineMode': isOffline,
    };
  }
  
  // ===========================================
  // 오프라인 모드 UI 메시지
  // ===========================================
  
  /// 오프라인 상태 메시지
  static String getOfflineMessage() {
    if (isOffline) {
      return '인터넷 연결을 확인해주세요. 오프라인 모드로 작동 중입니다.';
    }
    return '';
  }
  
  /// 오프라인 모드 아이콘
  static String getOfflineIcon() {
    return isOffline ? '📡' : '🌐';
  }
  
  /// 캐시 상태 메시지
  static Future<String> getCacheStatusMessage() async {
    final availability = await getOfflineDataAvailability();
    final lastUpdate = await CacheService.getLastCacheUpdateTime();
    
    if (!availability['hasValidCache']!) {
      return '캐시된 데이터가 없습니다.';
    }
    
    final ingredientsCount = availability['hasIngredients']! ? '식재료' : '';
    final recipesCount = availability['hasRecipes']! ? '레시피' : '';
    final dataTypes = [ingredientsCount, recipesCount].where((s) => s.isNotEmpty).join(', ');
    
    if (lastUpdate != null) {
      final now = DateTime.now();
      final difference = now.difference(lastUpdate);
      final hours = difference.inHours;
      
      if (hours < 1) {
        return '최근 업데이트된 $dataTypes 데이터를 사용 중입니다.';
      } else if (hours < 24) {
        return '$hours시간 전에 업데이트된 $dataTypes 데이터를 사용 중입니다.';
      } else {
        return '${difference.inDays}일 전에 업데이트된 $dataTypes 데이터를 사용 중입니다.';
      }
    }
    
    return '캐시된 $dataTypes 데이터를 사용 중입니다.';
  }

  /// 재료 기반 오프라인 레시피 추천 (Phase 2 핵심 기능)
  static Future<List<ApiRecipe>> getRecipesByIngredients(
    List<String> ingredients,
  ) async {
    try {
      // 먼저 캐시된 재료 기반 레시피 확인
      final cachedRecipes = await CacheService.getCachedRecipesByIngredients(ingredients);
      if (cachedRecipes.isNotEmpty) {
        return cachedRecipes.map((json) => ApiRecipe.fromJson(json)).toList();
      }

      // 캐시된 재료 기반 데이터가 없으면 전체 레시피에서 필터링
      final offlineResponse = await getOfflineRecipes();
      if (!offlineResponse.success || offlineResponse.data == null) {
        return [];
      }

      final allRecipes = offlineResponse.data!;
      final filteredRecipes = allRecipes.where((recipe) {
        // 사용자가 보유한 재료로 만들 수 있는 레시피 찾기
        return ingredients.any((ingredient) =>
            recipe.ingredients.any((recipeIngredient) =>
                recipeIngredient.name.toLowerCase().contains(ingredient.toLowerCase()) ||
                ingredient.toLowerCase().contains(recipeIngredient.name.toLowerCase())
            )
        );
      }).toList();

      if (kDebugMode) {
        print('🔍 Found ${filteredRecipes.length} offline recipes for ${ingredients.length} ingredients');
      }

      return filteredRecipes;
    } catch (e) {
      if (kDebugMode) {
        print('❌ Error getting offline recipes by ingredients: $e');
      }
      return [];
    }
  }
}
