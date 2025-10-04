import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../models/api/api_recipe.dart';
import '../../services/api/recipe_api_service.dart';
import '../fridge_provider.dart';
import '../recipe_provider.dart';

/// 레시피 추천 상태 클래스
class RecipeRecommendationState {
  final List<RecipeRecommendation> recipes;
  final bool isLoading;
  final String? error;
  final int total;
  final String algorithm;
  final String summary;

  const RecipeRecommendationState({
    this.recipes = const [],
    this.isLoading = false,
    this.error,
    this.total = 0,
    this.algorithm = 'jaccard',
    this.summary = '',
  });

  RecipeRecommendationState copyWith({
    List<RecipeRecommendation>? recipes,
    bool? isLoading,
    String? error,
    int? total,
    String? algorithm,
    String? summary,
  }) {
    return RecipeRecommendationState(
      recipes: recipes ?? this.recipes,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      total: total ?? this.total,
      algorithm: algorithm ?? this.algorithm,
      summary: summary ?? this.summary,
    );
  }
}

/// 냉장고 기반 레시피 추천 StateNotifier
class RecipeRecommendationNotifier
    extends StateNotifier<RecipeRecommendationState> {
  RecipeRecommendationNotifier(this.ref)
      : super(const RecipeRecommendationState());

  final Ref ref;

  /// 냉장고 재료 기반 레시피 추천 로드
  Future<void> loadRecommendations({
    int limit = 50,
    String algorithm = 'jaccard',
    bool excludeSeasonings = true,
    double? minMatchRate,
  }) async {
    if (state.isLoading) return;

    // 냉장고 재료 가져오기
    final ingredientNames = ref.read(fridgeIngredientNamesProvider);

    if (ingredientNames.isEmpty) {
      if (kDebugMode) {
        debugPrint('🍳 No ingredients in fridge, skipping recommendation');
      }
      state = state.copyWith(
        recipes: [],
        isLoading: false,
        error: null,
        total: 0,
      );
      return;
    }

    state = state.copyWith(isLoading: true, error: null);

    try {
      if (kDebugMode) {
        debugPrint(
            '🍳 Loading recipe recommendations for ingredients: ${ingredientNames.join(", ")}');
        debugPrint('🍳 Settings: limit=$limit, algorithm=$algorithm, minMatchRate=${minMatchRate ?? 0.01}');
      }

      final response = await RecipeApiService.getRecommendations(
        ingredients: ingredientNames,
        limit: limit,
        algorithm: algorithm,
        excludeSeasonings: excludeSeasonings,
        minMatchRate: minMatchRate ?? 0.01, // 재료가 1개라도 있으면 표시
      );

      if (response.success && response.data != null) {
        final recommendationsData = response.data!;

        if (kDebugMode) {
          debugPrint(
              '✅ Loaded ${recommendationsData.recipes.length} recipe recommendations');
          debugPrint(
              '📊 Total: ${recommendationsData.total}, Algorithm: ${recommendationsData.algorithm}, Summary: ${recommendationsData.summary}');
        }

        state = state.copyWith(
          recipes: recommendationsData.recipes,
          isLoading: false,
          error: null,
          total: recommendationsData.total,
          algorithm: recommendationsData.algorithm,
          summary: recommendationsData.summary,
        );
      } else {
        if (kDebugMode) {
          debugPrint('❌ Failed to load recommendations: ${response.message}');
        }
        state = state.copyWith(
          isLoading: false,
          error: response.message,
        );
      }
    } catch (e, stackTrace) {
      if (kDebugMode) {
        debugPrint('❌ Error loading recommendations: $e');
        debugPrint('Stack trace: $stackTrace');
      }
      state = state.copyWith(
        isLoading: false,
        error: '레시피 추천을 불러오는 중 오류가 발생했습니다: $e',
      );
    }
  }

  /// 새로고침
  Future<void> refresh() async {
    state = const RecipeRecommendationState();
    await loadRecommendations();
  }

  /// 검색어로 필터링
  List<RecipeRecommendation> filterBySearchQuery(String query) {
    if (query.isEmpty) {
      return state.recipes;
    }

    final lowerQuery = query.toLowerCase();
    return state.recipes
        .where((recipe) =>
            recipe.name.toLowerCase().contains(lowerQuery) ||
            recipe.title.toLowerCase().contains(lowerQuery) ||
            (recipe.introduction?.toLowerCase().contains(lowerQuery) ?? false))
        .toList();
  }
}

/// 냉장고 기반 레시피 추천 Provider
final recipeRecommendationProvider = StateNotifierProvider<
    RecipeRecommendationNotifier, RecipeRecommendationState>((ref) {
  return RecipeRecommendationNotifier(ref);
});

/// 검색어로 필터링된 추천 레시피 Provider
final filteredRecommendationProvider = Provider<List<RecipeRecommendation>>((ref) {
  final recommendationState = ref.watch(recipeRecommendationProvider);
  // recipe_provider.dart에서 정의된 recipeSearchQueryProvider 사용
  final searchQuery = ref.watch(recipeSearchQueryProvider);

  if (searchQuery.isEmpty) {
    return recommendationState.recipes;
  }

  final lowerQuery = searchQuery.toLowerCase();
  return recommendationState.recipes
      .where((recipe) =>
          recipe.name.toLowerCase().contains(lowerQuery) ||
          recipe.title.toLowerCase().contains(lowerQuery) ||
          (recipe.introduction?.toLowerCase().contains(lowerQuery) ?? false))
      .toList();
});
