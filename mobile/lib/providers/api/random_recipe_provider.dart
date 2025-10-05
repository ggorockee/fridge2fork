import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/foundation.dart';
import '../../models/api/api_recipe.dart';
import '../../services/api/recipe_api_service.dart';

/// 랜덤 레시피 추천 상태
class RandomRecipeState {
  final List<ApiRecipe> recipes;
  final bool isLoading;
  final String? error;
  final DateTime? lastUpdated;

  const RandomRecipeState({
    this.recipes = const [],
    this.isLoading = false,
    this.error,
    this.lastUpdated,
  });

  RandomRecipeState copyWith({
    List<ApiRecipe>? recipes,
    bool? isLoading,
    String? error,
    DateTime? lastUpdated,
  }) {
    return RandomRecipeState(
      recipes: recipes ?? this.recipes,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      lastUpdated: lastUpdated ?? this.lastUpdated,
    );
  }

  bool get hasError => error != null;
  bool get hasData => recipes.isNotEmpty;
  bool get isEmpty => recipes.isEmpty && !isLoading && !hasError;
}

/// 랜덤 레시피 추천 Provider
class RandomRecipeNotifier extends StateNotifier<RandomRecipeState> {
  RandomRecipeNotifier() : super(const RandomRecipeState());

  /// 랜덤 레시피 추천 로드 (재시도 로직 포함)
  Future<void> loadRandomRecipes({
    int count = 10,
    bool forceRefresh = false,
    int maxRetries = 3,
  }) async {
    // 이미 로딩 중이거나, 강제 새로고침이 아닌데 최근에 로드했으면 스킵
    if (state.isLoading) {
      if (kDebugMode) debugPrint('🍳 Random recipe loading already in progress, skipping...');
      return;
    }

    if (!forceRefresh &&
        state.hasData &&
        state.lastUpdated != null &&
        DateTime.now().difference(state.lastUpdated!).inMinutes < 5) {
      if (kDebugMode) {
        debugPrint('🍳 Using cached random recipes (loaded ${DateTime.now().difference(state.lastUpdated!).inMinutes} minutes ago)');
      }
      return;
    }

    state = state.copyWith(
      isLoading: true,
      error: null,
    );

    // 재시도 로직
    for (int attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        if (kDebugMode) {
          debugPrint('🍳 Loading $count random recipe recommendations (attempt $attempt/$maxRetries)...');
        }

        // 인기 레시피 또는 최신 레시피 조회 (랜덤 추천 대체)
        // 서버에 랜덤 추천 API가 없으므로 인기 레시피로 대체
        final response = await RecipeApiService.getPopularRecipes(
          page: 1,
          size: count,
        );

        if (response.success && response.data != null) {
          final recipes = response.data!.items; // PaginatedResponse에서 items 추출

          state = state.copyWith(
            recipes: recipes,
            isLoading: false,
            error: null,
            lastUpdated: DateTime.now(),
          );

          if (kDebugMode) {
            debugPrint('✅ Successfully loaded ${recipes.length} random recipes on attempt $attempt');
          }

          // 레시피가 비어있으면 fallback 로드 (첫 번째 시도에서도)
          if (recipes.isEmpty) {
            if (kDebugMode) debugPrint('📦 No recipes received, loading fallback...');
            await _loadFallbackRecipes();
          }

          return; // 성공시 함수 종료
        } else {
          if (kDebugMode) {
            debugPrint('❌ Failed to load random recipes on attempt $attempt: ${response.message}');
          }

          if (attempt == maxRetries) {
            // 마지막 시도 실패 - 서버 오류 타입별 메시지 처리
            final errorMessage = _getErrorMessage(response);
            state = state.copyWith(
              isLoading: false,
              error: errorMessage,
            );

            // 서버 오류 시 더미 데이터나 오프라인 대응 시도
            if (response.statusCode == 500) {
              if (kDebugMode) debugPrint('🔧 Server error detected, attempting fallback...');
              await _loadFallbackRecipes();
            }
          } else {
            // 재시도 전 대기
            await Future.delayed(Duration(seconds: attempt));
          }
        }
      } catch (e) {
        if (kDebugMode) {
          debugPrint('❌ Random recipe loading error on attempt $attempt: $e');
        }

        if (attempt == maxRetries) {
          // 마지막 시도 실패
          state = state.copyWith(
            isLoading: false,
            error: '랜덤 레시피 로딩 중 오류가 발생했습니다: $e',
          );
        } else {
          // 재시도 전 대기
          await Future.delayed(Duration(seconds: attempt));
        }
      }
    }

    if (kDebugMode) {
      debugPrint('💔 All $maxRetries attempts to load random recipes failed');
    }
  }

  /// 새로고침 (강제 리로드)
  Future<void> refresh() async {
    if (kDebugMode) {
      debugPrint('🔄 Refreshing random recipes...');
    }
    await loadRandomRecipes(forceRefresh: true);
  }

  /// 에러 상태 초기화
  void clearError() {
    if (state.hasError) {
      state = state.copyWith(error: null);
    }
  }

  /// 특정 레시피 제거 (사용자가 관심없음을 표시한 경우)
  void removeRecipe(String recipeId) {
    final updatedRecipes = state.recipes.where((recipe) => recipe.id != recipeId).toList();
    state = state.copyWith(recipes: updatedRecipes);

    if (kDebugMode) {
      debugPrint('🗑️ Removed recipe $recipeId from recommendations');
    }
  }

  /// 레시피 목록이 부족할 때 추가 로드
  Future<void> loadMoreIfNeeded({int threshold = 3}) async {
    if (state.recipes.length <= threshold && !state.isLoading) {
      if (kDebugMode) {
        debugPrint('📈 Loading more recipes (current: ${state.recipes.length})');
      }
      await loadRandomRecipes(count: 10, forceRefresh: true);
    }
  }

  /// 서버 오류 시 폴백 레시피 로드
  Future<void> _loadFallbackRecipes() async {
    try {
      if (kDebugMode) debugPrint('🔧 Loading fallback recipes...');

      // 간단한 더미 레시피 데이터 생성
      final fallbackRecipes = _generateFallbackRecipes();

      state = state.copyWith(
        recipes: fallbackRecipes,
        isLoading: false,
        error: null, // 에러 상태 클리어 (폴백 데이터가 있으므로)
        lastUpdated: DateTime.now(),
      );

      if (kDebugMode) {
        debugPrint('✅ Loaded ${fallbackRecipes.length} fallback recipes');
      }
    } catch (e) {
      if (kDebugMode) {
        debugPrint('❌ Fallback recipe loading failed: $e');
      }
    }
  }

  /// 폴백용 더미 레시피 생성
  List<ApiRecipe> _generateFallbackRecipes() {
    final now = DateTime.now();

    return [
      ApiRecipe(
        id: 'fallback_1',
        name: '김치찌개',
        description: '매콤하고 얼큰한 김치찌개입니다. 냉장고에 있는 재료로 간단히 만들 수 있어요.',
        imageUrl: 'https://picsum.photos/300/200?random=1',
        url: null,
        ingredients: [
          ApiRecipeIngredient(
            ingredientId: 'ing_1',
            name: '김치',
            amount: '2',
            unit: '컵',
            isEssential: true,
          ),
          ApiRecipeIngredient(
            ingredientId: 'ing_2',
            name: '돼지고기',
            amount: '200',
            unit: 'g',
            isEssential: false,
          ),
        ],
        steps: [
          ApiCookingStep(
            stepNumber: 1,
            description: '김치를 먹기 좋은 크기로 썰어주세요.',
            durationMinutes: 5,
          ),
          ApiCookingStep(
            stepNumber: 2,
            description: '돼지고기를 볶아주세요.',
            durationMinutes: 10,
          ),
          ApiCookingStep(
            stepNumber: 3,
            description: '김치를 넣고 볶다가 물을 부어 끓여주세요.',
            durationMinutes: 15,
          ),
        ],
        cookingTimeMinutes: 30,
        servings: 2,
        difficulty: 'easy',
        category: 'stew',
        rating: 4.2,
        reviewCount: 128,
        isPopular: true,
        isActive: true,
        createdAt: now,
        updatedAt: now,
      ),
      ApiRecipe(
        id: 'fallback_2',
        name: '계란볶음밥',
        description: '간단하고 맛있는 계란볶음밥입니다. 남은 밥으로 금방 만들 수 있어요.',
        imageUrl: 'https://picsum.photos/300/200?random=2',
        url: null,
        ingredients: [
          ApiRecipeIngredient(
            ingredientId: 'ing_3',
            name: '밥',
            amount: '1',
            unit: '공기',
            isEssential: true,
          ),
          ApiRecipeIngredient(
            ingredientId: 'ing_4',
            name: '계란',
            amount: '2',
            unit: '개',
            isEssential: true,
          ),
        ],
        steps: [
          ApiCookingStep(
            stepNumber: 1,
            description: '계란을 풀어주세요.',
            durationMinutes: 2,
          ),
          ApiCookingStep(
            stepNumber: 2,
            description: '팬에 기름을 두르고 계란을 볶아주세요.',
            durationMinutes: 3,
          ),
          ApiCookingStep(
            stepNumber: 3,
            description: '밥을 넣고 함께 볶아주세요.',
            durationMinutes: 10,
          ),
        ],
        cookingTimeMinutes: 15,
        servings: 1,
        difficulty: 'easy',
        category: 'rice',
        rating: 4.0,
        reviewCount: 89,
        isPopular: false,
        isActive: true,
        createdAt: now,
        updatedAt: now,
      ),
      ApiRecipe(
        id: 'fallback_3',
        name: '된장찌개',
        description: '구수하고 담백한 된장찌개입니다. 집밥의 대표 메뉴예요.',
        imageUrl: 'https://picsum.photos/300/200?random=3',
        url: null,
        ingredients: [
          ApiRecipeIngredient(
            ingredientId: 'ing_5',
            name: '된장',
            amount: '2',
            unit: '큰술',
            isEssential: true,
          ),
          ApiRecipeIngredient(
            ingredientId: 'ing_6',
            name: '두부',
            amount: '1/2',
            unit: '모',
            isEssential: false,
          ),
        ],
        steps: [
          ApiCookingStep(
            stepNumber: 1,
            description: '물에 된장을 풀어주세요.',
            durationMinutes: 3,
          ),
          ApiCookingStep(
            stepNumber: 2,
            description: '두부와 야채를 넣고 끓여주세요.',
            durationMinutes: 22,
          ),
        ],
        cookingTimeMinutes: 25,
        servings: 3,
        difficulty: 'easy',
        category: 'stew',
        rating: 4.5,
        reviewCount: 156,
        isPopular: true,
        isActive: true,
        createdAt: now,
        updatedAt: now,
      ),
      ApiRecipe(
        id: 'fallback_4',
        name: '라면',
        description: '간단하고 빠른 라면입니다. 언제든 쉽게 만들 수 있어요.',
        imageUrl: 'https://picsum.photos/300/200?random=4',
        url: null,
        ingredients: [
          ApiRecipeIngredient(
            ingredientId: 'ing_7',
            name: '라면',
            amount: '1',
            unit: '개',
            isEssential: true,
          ),
          ApiRecipeIngredient(
            ingredientId: 'ing_8',
            name: '계란',
            amount: '1',
            unit: '개',
            isEssential: false,
          ),
        ],
        steps: [
          ApiCookingStep(
            stepNumber: 1,
            description: '물 550ml를 끓여주세요.',
            durationMinutes: 3,
          ),
          ApiCookingStep(
            stepNumber: 2,
            description: '면과 스프를 넣고 끓여주세요.',
            durationMinutes: 4,
          ),
          ApiCookingStep(
            stepNumber: 3,
            description: '계란을 넣고 살짝 더 끓여주세요.',
            durationMinutes: 3,
          ),
        ],
        cookingTimeMinutes: 10,
        servings: 1,
        difficulty: 'easy',
        category: 'noodles',
        rating: 3.8,
        reviewCount: 67,
        isPopular: false,
        isActive: true,
        createdAt: now,
        updatedAt: now,
      ),
    ];
  }

  /// 에러 타입별 메시지 생성
  String _getErrorMessage(dynamic response) {
    if (response.statusCode == 500) {
      return '서버에 일시적인 문제가 있습니다\n기본 레시피를 표시합니다';
    } else if (response.statusCode == 404) {
      return '레시피 데이터를 찾을 수 없습니다';
    } else if (response.statusCode == 408 || response.message.contains('timeout')) {
      return '서버 응답 시간이 초과되었습니다\n잠시 후 다시 시도해주세요';
    }

    return response.message.isNotEmpty ? response.message : '랜덤 레시피를 불러올 수 없습니다';
  }
}

/// 랜덤 레시피 추천 상태 Provider
final randomRecipeProvider = StateNotifierProvider<RandomRecipeNotifier, RandomRecipeState>(
  (ref) => RandomRecipeNotifier(),
);

/// 랜덤 레시피 자동 로드 Provider
final autoLoadRandomRecipesProvider = Provider<void>((ref) {
  final notifier = ref.read(randomRecipeProvider.notifier);

  // Provider가 생성될 때 자동으로 랜덤 레시피 로드
  Future.microtask(() => notifier.loadRandomRecipes());

  return;
});

/// 랜덤 레시피 새로고침 가능 여부 Provider
final canRefreshRandomRecipesProvider = Provider<bool>((ref) {
  final state = ref.watch(randomRecipeProvider);
  return !state.isLoading;
});