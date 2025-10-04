import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/api/api_recipe.dart';
import '../services/api/recipe_api_service.dart';

/// 레시피 추천 상태 관리 Notifier
class RecipeRecommendationsNotifier extends StateNotifier<AsyncValue<RecipeRecommendationsResponse>> {
  RecipeRecommendationsNotifier() : super(const AsyncValue.loading());

  /// 레시피 추천 로드
  Future<void> loadRecommendations({
    required List<String> ingredients,
    int limit = 20,
    String algorithm = 'jaccard',
    bool excludeSeasonings = true,
    double? minMatchRate, // null이면 서버의 관리자 설정 사용
  }) async {
    if (ingredients.isEmpty) {
      state = const AsyncValue.data(RecipeRecommendationsResponse(
        recipes: [],
        total: 0,
        algorithm: 'jaccard',
        summary: '냉장고에 식재료를 추가하면 맞춤 레시피를 추천해드려요!',
      ));
      return;
    }

    state = const AsyncValue.loading();

    try {
      final response = await RecipeApiService.getRecommendations(
        ingredients: ingredients,
        limit: limit,
        algorithm: algorithm,
        excludeSeasonings: excludeSeasonings,
        minMatchRate: minMatchRate,
      );

      if (response.success && response.data != null) {
        state = AsyncValue.data(response.data!);
      } else {
        state = AsyncValue.error(
          response.message,
          StackTrace.current,
        );
      }
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  /// 추천 초기화
  void clearRecommendations() {
    state = const AsyncValue.data(RecipeRecommendationsResponse(
      recipes: [],
      total: 0,
      algorithm: 'jaccard',
      summary: '',
    ));
  }
}

/// 레시피 추천 Provider
final recipeRecommendationsProvider =
    StateNotifierProvider<RecipeRecommendationsNotifier, AsyncValue<RecipeRecommendationsResponse>>((ref) {
  return RecipeRecommendationsNotifier();
});

/// 추천 레시피 목록 Provider
final recommendedRecipesProvider = Provider<List<RecipeRecommendation>>((ref) {
  final state = ref.watch(recipeRecommendationsProvider);
  return state.when(
    data: (response) => response.recipes,
    loading: () => [],
    error: (_, __) => [],
  );
});

/// 추천 레시피 개수 Provider
final recommendedRecipesCountProvider = Provider<int>((ref) {
  final recipes = ref.watch(recommendedRecipesProvider);
  return recipes.length;
});

/// 추천 요약 Provider
final recommendationSummaryProvider = Provider<String>((ref) {
  final state = ref.watch(recipeRecommendationsProvider);
  return state.when(
    data: (response) => response.summary,
    loading: () => '레시피를 추천하고 있습니다...',
    error: (_, __) => '레시피 추천에 실패했습니다',
  );
});
