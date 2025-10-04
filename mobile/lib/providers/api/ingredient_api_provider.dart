import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../models/api/api_ingredient.dart';
import '../../services/api/ingredient_api_service.dart';
import '../../services/cache_service.dart';
import '../../services/offline_service.dart';
import '../api/api_connection_provider.dart';

/// 식재료 API 상태 관리 Notifier
class IngredientApiNotifier extends StateNotifier<AsyncValue<List<ApiIngredient>>> {
  IngredientApiNotifier(this._ref) : super(const AsyncValue.loading());

  final Ref _ref;
  List<ApiIngredient> _cachedIngredients = [];
  IngredientSearchFilter? _lastFilter;

  /// 레시피 재료 목록 로드 (새 API 사용)
  Future<void> loadRecipeIngredients({
    bool excludeSeasonings = true,
    int? limit,
    bool forceRefresh = false,
  }) async {
    debugPrint('🥬 [Ingredient API] loadRecipeIngredients called (excludeSeasonings: $excludeSeasonings, limit: $limit)');

    // API가 오프라인이면 캐시된 데이터 반환
    final isOnline = _ref.read(isApiOnlineProvider);
    debugPrint('📡 [Ingredient API] API Online Status: $isOnline');

    if (!isOnline && _cachedIngredients.isNotEmpty) {
      debugPrint('🔄 [Ingredient API] Using cached data (offline mode)');
      state = AsyncValue.data(_cachedIngredients);
      return;
    }

    // 강제 새로고침이 아니고 캐시된 데이터가 있으면 반환
    if (!forceRefresh && _cachedIngredients.isNotEmpty) {
      state = AsyncValue.data(_cachedIngredients);
      return;
    }

    debugPrint('⏳ [Ingredient API] Setting loading state and calling API');
    state = const AsyncValue.loading();

    try {
      final response = await IngredientApiService.getRecipeIngredients(
        excludeSeasonings: excludeSeasonings,
        limit: limit,
      );

      debugPrint('📥 [Ingredient API] API Response: success=${response.success}, message=${response.message}');
      if (response.data != null) {
        debugPrint('📊 [Ingredient API] API Response data: ${response.data!.ingredients.length} ingredients found');
        debugPrint('📂 [Ingredient API] Categories: ${response.data!.categories.length} categories');
      }

      if (response.success && response.data != null) {
        // 활성화된 식재료만 필터링 (빈 이름이나 이상한 이름 제외)
        _cachedIngredients = response.data!.ingredients
            .where((ingredient) =>
                ingredient.isActive &&
                ingredient.name.isNotEmpty &&
                ingredient.name.length >= 2 &&
                !ingredient.name.contains('알 수 없는 재료'))
            .toList();
        state = AsyncValue.data(_cachedIngredients);

        // 성공적으로 로드된 데이터를 캐시에 저장
        await _cacheIngredients(_cachedIngredients);

        // Firebase Analytics 이벤트 로깅
        _logAnalyticsEvent('ingredients_loaded', {
          'count': _cachedIngredients.length,
          'exclude_seasonings': excludeSeasonings,
          'source': 'recipe_ingredients_api',
        });
      } else {
        // API 실패 시 오프라인 데이터 시도
        await _loadOfflineIngredients();
      }
    } catch (error) {
      debugPrint('❌ [Ingredient API] Error: $error');
      // 네트워크 오류 시 오프라인 데이터 시도
      await _loadOfflineIngredients();
    }
  }

  /// 식재료 목록 로드 (기존 API - 호환성 유지)
  Future<void> loadIngredients({
    IngredientSearchFilter? filter,
    bool forceRefresh = false,
  }) async {
    debugPrint('🥬 [Ingredient API] loadIngredients called with filter: ${filter?.toQueryParams()}');

    // API가 오프라인이면 캐시된 데이터 반환
    final isOnline = _ref.read(isApiOnlineProvider);
    debugPrint('📡 [Ingredient API] API Online Status: $isOnline');

    if (!isOnline && _cachedIngredients.isNotEmpty) {
      debugPrint('🔄 [Ingredient API] Using cached data (offline mode)');
      state = AsyncValue.data(_cachedIngredients);
      return;
    }

    // 같은 필터로 이미 로드했고 강제 새로고침이 아닌 경우 캐시된 데이터 반환
    if (!forceRefresh &&
        _lastFilter != null &&
        _lastFilter == filter &&
        _cachedIngredients.isNotEmpty) {
      state = AsyncValue.data(_cachedIngredients);
      return;
    }

    debugPrint('⏳ [Ingredient API] Setting loading state and calling API');
    state = const AsyncValue.loading();

    try {
      final response = await IngredientApiService.getIngredients(filter: filter);

      debugPrint('📥 [Ingredient API] API Response: success=${response.success}, message=${response.message}');
      if (response.data != null) {
        debugPrint('📊 [Ingredient API] API Response data: ${response.data!.items.length} ingredients found');
      }

      if (response.success && response.data != null) {
        // 활성화된 식재료만 필터링 (빈 이름이나 이상한 이름 제외)
        _cachedIngredients = response.data!.items
            .where((ingredient) =>
                ingredient.isActive &&
                ingredient.name.isNotEmpty &&
                ingredient.name.length >= 2 &&
                !ingredient.name.contains('알 수 없는 재료'))
            .toList();
        _lastFilter = filter;
        state = AsyncValue.data(_cachedIngredients);

        // 성공적으로 로드된 데이터를 캐시에 저장
        await _cacheIngredients(_cachedIngredients);

        // Firebase Analytics 이벤트 로깅
        _logAnalyticsEvent('ingredients_loaded', {
          'count': _cachedIngredients.length,
          'filter_applied': filter != null,
          'source': 'api',
        });
      } else {
        // API 실패 시 오프라인 데이터 시도
        await _loadOfflineIngredients();
      }
    } catch (error) {
      // 네트워크 오류 시 오프라인 데이터 시도
      await _loadOfflineIngredients();
    }
  }

  /// 오프라인 데이터 로드
  Future<void> _loadOfflineIngredients() async {
    try {
      final offlineResponse = await OfflineService.getOfflineIngredients();
      
      if (offlineResponse.success && offlineResponse.data != null) {
        _cachedIngredients = offlineResponse.data!;
        state = AsyncValue.data(_cachedIngredients);
        
        // Firebase Analytics 이벤트 로깅
        _logAnalyticsEvent('ingredients_loaded', {
          'count': _cachedIngredients.length,
          'source': 'offline',
        });
      } else {
        // 오프라인 데이터도 없으면 에러
        state = AsyncValue.error(
          '식재료를 불러올 수 없습니다. 네트워크 연결을 확인해주세요.',
          StackTrace.current,
        );
      }
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  /// 식재료 데이터 캐시
  Future<void> _cacheIngredients(List<ApiIngredient> ingredients) async {
    try {
      final ingredientsJson = ingredients.map((ingredient) => ingredient.toJson()).toList();
      await CacheService.cacheIngredients(ingredientsJson);
    } catch (e) {
      // 캐시 실패는 로그만 남기고 계속 진행
      if (kDebugMode) {
        print('❌ Failed to cache ingredients: $e');
      }
    }
  }

  /// 식재료 검색
  Future<void> searchIngredients(
    String searchQuery, {
    IngredientCategory? category,
    int page = 1,
    int size = 20,
  }) async {
    final filter = IngredientSearchFilter(
      search: searchQuery.isNotEmpty ? searchQuery : null,
      category: category,
      page: page,
      size: size,
    );

    await loadIngredients(filter: filter);
  }

  /// 카테고리별 식재료 로드
  Future<void> loadIngredientsByCategory(
    IngredientCategory category, {
    int page = 1,
    int size = 20,
  }) async {
    final filter = IngredientSearchFilter(
      category: category,
      page: page,
      size: size,
    );

    await loadIngredients(filter: filter);
  }

  /// 활성 식재료만 로드
  Future<void> loadActiveIngredients({
    IngredientCategory? category,
    int page = 1,
    int size = 20,
  }) async {
    final filter = IngredientSearchFilter(
      category: category,
      isActive: true,
      page: page,
      size: size,
    );

    await loadIngredients(filter: filter);
  }

  /// 특정 식재료 조회
  Future<ApiIngredient?> getIngredientById(int id) async {
    try {
      final response = await IngredientApiService.getIngredientById(id.toString());

      if (response.success && response.data != null) {
        // 캐시 업데이트
        final index = _cachedIngredients.indexWhere((ingredient) => ingredient.id == id);
        if (index != -1) {
          _cachedIngredients[index] = response.data!;
        } else {
          _cachedIngredients.add(response.data!);
        }

        return response.data;
      }

      return null;
    } catch (e) {
      // 캐시에서 찾기
      try {
        return _cachedIngredients.firstWhere(
          (ingredient) => ingredient.id == id,
        );
      } catch (_) {
        return null;
      }
    }
  }

  /// 식재료 이름으로 검색
  Future<ApiIngredient?> findIngredientByName(String name) async {
    try {
      final response = await IngredientApiService.findIngredientByName(name);
      return response.data;
    } catch (e) {
      // 캐시에서 찾기
      try {
        return _cachedIngredients.firstWhere(
          (ingredient) => ingredient.name.toLowerCase() == name.toLowerCase(),
        );
      } catch (_) {
        return null;
      }
    }
  }

  /// 캐시 초기화
  void clearCache() {
    _cachedIngredients.clear();
    _lastFilter = null;
    state = const AsyncValue.loading();
  }

  /// 새로고침
  Future<void> refresh() async {
    await loadIngredients(filter: _lastFilter, forceRefresh: true);
  }

  /// Firebase Analytics 이벤트 로깅
  void _logAnalyticsEvent(String eventName, Map<String, dynamic> parameters) {
    // TODO: Firebase Analytics 이벤트 로깅 구현
    if (kDebugMode) {
      debugPrint('📊 Analytics Event: $eventName - $parameters');
    }
  }
}

/// 식재료 API 상태 Provider
final ingredientApiProvider = StateNotifierProvider<IngredientApiNotifier, AsyncValue<List<ApiIngredient>>>((ref) {
  return IngredientApiNotifier(ref);
});

/// 식재료 목록 간편 접근 Provider
final ingredientsProvider = Provider<List<ApiIngredient>>((ref) {
  final state = ref.watch(ingredientApiProvider);
  return state.when(
    data: (ingredients) => ingredients,
    loading: () => [],
    error: (_, __) => [],
  );
});

/// 식재료 로딩 상태 Provider
final ingredientsLoadingProvider = Provider<bool>((ref) {
  final state = ref.watch(ingredientApiProvider);
  return state.isLoading;
});

/// 식재료 에러 상태 Provider
final ingredientsErrorProvider = Provider<String?>((ref) {
  final state = ref.watch(ingredientApiProvider);
  return state.hasError ? state.error.toString() : null;
});

/// 카테고리별 식재료 Provider (카테고리 이름으로 필터링)
final ingredientsByCategoryProvider = Provider.family<List<ApiIngredient>, String>((ref, categoryName) {
  final ingredients = ref.watch(ingredientsProvider);
  return ingredients.where((ingredient) => ingredient.category.name == categoryName).toList();
});

/// 식재료 검색 Provider
final ingredientSearchProvider = StateProvider<String>((ref) => '');

/// 검색된 식재료 Provider
final searchedIngredientsProvider = Provider<List<ApiIngredient>>((ref) {
  final ingredients = ref.watch(ingredientsProvider);
  final searchQuery = ref.watch(ingredientSearchProvider);
  
  if (searchQuery.isEmpty) return ingredients;
  
  return ingredients.where((ingredient) =>
      ingredient.name.toLowerCase().contains(searchQuery.toLowerCase()) ||
      (ingredient.description?.toLowerCase().contains(searchQuery.toLowerCase()) ?? false)
  ).toList();
});

/// 식재료 통계 Provider
final ingredientStatsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  try {
    final response = await IngredientApiService.getIngredientStats();
    
    if (response.success && response.data != null) {
      return response.data!;
    } else {
      throw Exception(response.message);
    }
  } catch (e) {
    // API 실패 시 로컬 계산
    final ingredients = ref.watch(ingredientsProvider);

    final stats = <String, dynamic>{
      'total_count': ingredients.length,
      'active_count': ingredients.where((i) => i.isActive).length,
      'category_counts': {},
    };

    // 카테고리별 개수 계산 (ApiCategory.code 기준으로 그룹화)
    final categoryGroups = <String, int>{};
    for (final ingredient in ingredients) {
      final categoryCode = ingredient.category.code;
      categoryGroups[categoryCode] = (categoryGroups[categoryCode] ?? 0) + 1;
    }
    stats['category_counts'] = categoryGroups;

    return stats;
  }
});
