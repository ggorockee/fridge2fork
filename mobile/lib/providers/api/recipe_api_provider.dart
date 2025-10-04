import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../models/api/api_recipe.dart';
import '../../models/api/api_response.dart';
import '../../services/api/recipe_api_service.dart';
import '../../services/cache_service.dart';
import '../../services/offline_service.dart';
import '../api/api_connection_provider.dart';

/// 레시피 API 상태 관리 Notifier
class RecipeApiNotifier extends StateNotifier<AsyncValue<List<ApiRecipe>>> {
  RecipeApiNotifier(this._ref) : super(const AsyncValue.loading());

  final Ref _ref;
  List<ApiRecipe> _cachedRecipes = [];
  RecipeSearchFilter? _lastFilter;

  /// 보유 재료 기반 레시피 추천 로드 (Phase 2 핵심 기능)
  Future<void> loadRecipesByIngredients(
    List<String> ingredients, {
    int page = 1,
    int size = 10,
    bool forceRefresh = false,
  }) async {
    print('🔍 [Recipe API] loadRecipesByIngredients called with ingredients: $ingredients');

    if (ingredients.isEmpty) {
      print('❌ [Recipe API] No ingredients provided, returning empty data');
      state = const AsyncValue.data([]);
      return;
    }

    // API가 오프라인이면 오프라인 서비스에서 데이터 반환
    final isOnline = _ref.read(isApiOnlineProvider);
    print('📡 [Recipe API] API Online Status: $isOnline');

    if (!isOnline) {
      print('🔄 [Recipe API] API is offline, using offline service');
      try {
        final offlineRecipes = await OfflineService.getRecipesByIngredients(ingredients);
        print('✅ [Recipe API] Offline recipes loaded: ${offlineRecipes.length} recipes');
        state = AsyncValue.data(offlineRecipes);
        return;
      } catch (e) {
        print('❌ [Recipe API] Offline service failed: $e');
        state = AsyncValue.error('오프라인 상태에서 레시피를 불러올 수 없습니다', StackTrace.current);
        return;
      }
    }

    print('⏳ [Recipe API] Setting loading state and calling API');
    state = const AsyncValue.loading();

    try {
      final response = await RecipeApiService.getRecipesByIngredients(
        ingredients,
        page: page,
        size: size,
      );

      print('📥 [Recipe API] API Response: success=${response.success}, message=${response.message}');
      if (response.data != null) {
        print('📊 [Recipe API] API Response data: ${response.data!.items.length} recipes found');
      }

      if (response.success && response.data != null) {
        final recipes = response.data!.items;
        _cachedRecipes = recipes;
        state = AsyncValue.data(recipes);

        // 성공한 데이터를 캐시에 저장
        await CacheService.cacheRecipesByIngredients(ingredients, recipes);

        // Firebase Analytics 이벤트 로깅
        _logAnalyticsEvent('recipes_by_ingredients_loaded', {
          'ingredients_count': ingredients.length,
          'recipes_found': recipes.length,
          'ingredients': ingredients.take(5).join(','), // 최대 5개만 로깅
        });
      } else {
        // API 호출 실패 시 캐시된 데이터 시도
        try {
          final cachedRecipes = await CacheService.getCachedRecipesByIngredients(ingredients);
          if (cachedRecipes.isNotEmpty) {
            final apiRecipes = cachedRecipes.map((json) => ApiRecipe.fromJson(json)).toList();
            state = AsyncValue.data(apiRecipes);
            _logAnalyticsEvent('recipes_by_ingredients_cached', {
              'ingredients_count': ingredients.length,
              'cached_recipes': cachedRecipes.length,
            });
          } else {
            throw Exception(response.message);
          }
        } catch (cacheError) {
          state = AsyncValue.error(response.message, StackTrace.current);
        }
      }
    } catch (e) {
      // 모든 API 및 캐시 시도 실패 시 오프라인 데이터 시도
      try {
        final offlineRecipes = await OfflineService.getRecipesByIngredients(ingredients);
        state = AsyncValue.data(offlineRecipes);
        _logAnalyticsEvent('recipes_by_ingredients_offline', {
          'ingredients_count': ingredients.length,
          'offline_recipes': offlineRecipes.length,
        });
      } catch (offlineError) {
        state = AsyncValue.error('레시피를 불러올 수 없습니다: $e', StackTrace.current);
      }
    }
  }

  /// 레시피 목록 로드
  Future<void> loadRecipes({
    RecipeSearchFilter? filter,
    bool forceRefresh = false,
  }) async {
    print('📋 [Recipe API] loadRecipes called with filter: ${filter?.toQueryParams()}');

    // API가 오프라인이면 캐시된 데이터 반환
    final isOnline = _ref.read(isApiOnlineProvider);
    print('📡 [Recipe API] API Online Status for loadRecipes: $isOnline');

    if (!isOnline && _cachedRecipes.isNotEmpty) {
      print('🔄 [Recipe API] Using cached data (offline mode)');
      state = AsyncValue.data(_cachedRecipes);
      return;
    }

    // 같은 필터로 이미 로드했고 강제 새로고침이 아닌 경우 캐시된 데이터 반환
    if (!forceRefresh && 
        _lastFilter != null && 
        _lastFilter == filter && 
        _cachedRecipes.isNotEmpty) {
      state = AsyncValue.data(_cachedRecipes);
      return;
    }

    state = const AsyncValue.loading();

    try {
      final response = await RecipeApiService.getRecipes(filter: filter);
      
      if (response.success && response.data != null) {
        _cachedRecipes = response.data!.items;
        _lastFilter = filter;
        state = AsyncValue.data(_cachedRecipes);
        
        // Firebase Analytics 이벤트 로깅
        _logAnalyticsEvent('recipes_loaded', {
          'count': _cachedRecipes.length,
          'filter_applied': filter != null,
        });
      } else {
        // API 실패 시 캐시된 데이터가 있으면 사용
        if (_cachedRecipes.isNotEmpty) {
          state = AsyncValue.data(_cachedRecipes);
        } else {
          state = AsyncValue.error(
            response.message,
            StackTrace.current,
          );
        }
      }
    } catch (error, stackTrace) {
      // 네트워크 오류 시 캐시된 데이터가 있으면 사용
      if (_cachedRecipes.isNotEmpty) {
        state = AsyncValue.data(_cachedRecipes);
      } else {
        state = AsyncValue.error(error, stackTrace);
      }
    }
  }



  /// 레시피 검색
  Future<void> searchRecipes(
    String searchQuery, {
    String? category,
    String? difficulty,
    int? maxCookingTime,
    int page = 1,
    int size = 10,
  }) async {
    final filter = RecipeSearchFilter(
      search: searchQuery.isNotEmpty ? searchQuery : null,
      category: category,
      difficulty: difficulty,
      maxCookingTime: maxCookingTime,
      page: page,
      size: size,
    );

    await loadRecipes(filter: filter);
  }

  /// 카테고리별 레시피 로드
  Future<void> loadRecipesByCategory(
    String category, {
    int page = 1,
    int size = 10,
  }) async {
    final filter = RecipeSearchFilter(
      category: category,
      page: page,
      size: size,
    );

    await loadRecipes(filter: filter);
  }

  /// 인기 레시피 로드
  Future<void> loadPopularRecipes({
    int page = 1,
    int size = 10,
  }) async {
    print('🔥 [Recipe API] Loading popular recipes (page: $page, size: $size)');

    // API 연결 상태 확인
    final isOnline = _ref.read(isApiOnlineProvider);
    print('📡 [Recipe API] API Online Status: $isOnline');

    if (!isOnline) {
      print('🔄 [Recipe API] API is offline, trying to load from cache or offline data');
      // 오프라인 상태에서는 캐시된 데이터나 기본 데이터 사용
      if (_cachedRecipes.isNotEmpty) {
        state = AsyncValue.data(_cachedRecipes);
        return;
      }
    }

    final filter = RecipeSearchFilter(
      isPopular: true,
      page: page,
      size: size,
    );

    await loadRecipes(filter: filter);
  }

  /// 활성 레시피만 로드
  Future<void> loadActiveRecipes({
    String? category,
    int page = 1,
    int size = 10,
  }) async {
    final filter = RecipeSearchFilter(
      category: category,
      isActive: true,
      page: page,
      size: size,
    );

    await loadRecipes(filter: filter);
  }

  /// 특정 레시피 조회
  Future<ApiRecipe?> getRecipeById(String id) async {
    try {
      final response = await RecipeApiService.getRecipeById(id);
      
      if (response.success && response.data != null) {
        // 캐시 업데이트
        final index = _cachedRecipes.indexWhere((recipe) => recipe.id == id);
        if (index != -1) {
          _cachedRecipes[index] = response.data!;
        } else {
          _cachedRecipes.add(response.data!);
        }
        
        return response.data;
      }
      
      return null;
    } catch (e) {
      // 캐시에서 찾기
      try {
        return _cachedRecipes.firstWhere(
          (recipe) => recipe.id == id,
        );
      } catch (_) {
        return null;
      }
    }
  }

  /// 관련 레시피 추천
  Future<List<ApiRecipe>> getRelatedRecipes(
    String recipeId, {
    int limit = 3,
  }) async {
    try {
      final response = await RecipeApiService.getRelatedRecipes(recipeId, limit: limit);
      
      if (response.success && response.data != null) {
        return response.data!;
      }
      
      return [];
    } catch (e) {
      return [];
    }
  }

  /// 캐시 초기화
  void clearCache() {
    _cachedRecipes.clear();
    _lastFilter = null;
    state = const AsyncValue.loading();
  }

  /// 새로고침
  Future<void> refresh() async {
    print('🔄 [Recipe API] Refreshing recipes...');

    // 현재 상태에 따라 적절한 새로고침 수행
    if (_lastFilter != null) {
      // 필터가 있으면 해당 필터로 새로고침
      await loadRecipes(filter: _lastFilter, forceRefresh: true);
    } else {
      // 기본적으로 인기 레시피 새로고침
      await loadPopularRecipes(size: 6);
    }

    print('✅ [Recipe API] Refresh completed');
  }

  /// Firebase Analytics 이벤트 로깅
  void _logAnalyticsEvent(String eventName, Map<String, dynamic> parameters) {
    // TODO: Firebase Analytics 이벤트 로깅 구현
    print('📊 Analytics Event: $eventName - $parameters');
  }
}

/// 레시피 API 상태 Provider
final recipeApiProvider = StateNotifierProvider<RecipeApiNotifier, AsyncValue<List<ApiRecipe>>>((ref) {
  return RecipeApiNotifier(ref);
});

/// 레시피 목록 간편 접근 Provider
final recipesProvider = Provider<List<ApiRecipe>>((ref) {
  final state = ref.watch(recipeApiProvider);
  return state.when(
    data: (recipes) => recipes,
    loading: () => [],
    error: (_, __) => [],
  );
});

/// 레시피 로딩 상태 Provider
final recipesLoadingProvider = Provider<bool>((ref) {
  final state = ref.watch(recipeApiProvider);
  return state.isLoading;
});

/// 레시피 에러 상태 Provider
final recipesErrorProvider = Provider<String?>((ref) {
  final state = ref.watch(recipeApiProvider);
  return state.hasError ? state.error.toString() : null;
});

/// 카테고리별 레시피 Provider
final recipesByCategoryProvider = Provider.family<List<ApiRecipe>, String>((ref, category) {
  final recipes = ref.watch(recipesProvider);
  return recipes.where((recipe) => recipe.category == category).toList();
});

/// 인기 레시피 Provider
final popularRecipesProvider = Provider<List<ApiRecipe>>((ref) {
  final recipes = ref.watch(recipesProvider);
  return recipes.where((recipe) => recipe.isPopular).toList();
});

/// 레시피 검색 Provider
final recipeSearchProvider = StateProvider<String>((ref) => '');

/// 검색된 레시피 Provider
final searchedRecipesProvider = Provider<List<ApiRecipe>>((ref) {
  final recipes = ref.watch(recipesProvider);
  final searchQuery = ref.watch(recipeSearchProvider);
  
  if (searchQuery.isEmpty) return recipes;
  
  return recipes.where((recipe) =>
      recipe.name.toLowerCase().contains(searchQuery.toLowerCase()) ||
      recipe.description.toLowerCase().contains(searchQuery.toLowerCase()) ||
      recipe.ingredients.any((ingredient) => 
          ingredient.name.toLowerCase().contains(searchQuery.toLowerCase()))
  ).toList();
});

/// 레시피 통계 Provider
final recipeStatsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  try {
    final response = await RecipeApiService.getRecipeStats();
    
    if (response.success && response.data != null) {
      return response.data!;
    } else {
      throw Exception(response.message);
    }
  } catch (e) {
    // API 실패 시 로컬 계산
    final recipes = ref.watch(recipesProvider);
    
    final stats = <String, dynamic>{
      'total_count': recipes.length,
      'active_count': recipes.where((r) => r.isActive).length,
      'popular_count': recipes.where((r) => r.isPopular).length,
      'category_counts': {},
      'difficulty_counts': {},
    };

    // 카테고리별 개수 계산
    final categories = recipes.map((r) => r.category).toSet();
    for (final category in categories) {
      final count = recipes.where((r) => r.category == category).length;
      stats['category_counts'][category] = count;
    }

    // 난이도별 개수 계산
    final difficulties = recipes.map((r) => r.difficulty).toSet();
    for (final difficulty in difficulties) {
      final count = recipes.where((r) => r.difficulty == difficulty).length;
      stats['difficulty_counts'][difficulty] = count;
    }

    return stats;
  }
});

/// 특정 레시피 Provider
final recipeByIdProvider = FutureProvider.family<ApiRecipe?, String>((ref, id) async {
  final notifier = ref.read(recipeApiProvider.notifier);
  return await notifier.getRecipeById(id);
});

/// 관련 레시피 Provider
final relatedRecipesProvider = FutureProvider.family<List<ApiRecipe>, String>((ref, recipeId) async {
  final notifier = ref.read(recipeApiProvider.notifier);
  return await notifier.getRelatedRecipes(recipeId);
});
