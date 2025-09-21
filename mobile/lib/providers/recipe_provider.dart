import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/recipe.dart';
import '../services/recipe_data.dart';
import 'ingredients_provider.dart';

/// 페이지네이션 상태 클래스
class RecipeListState {
  final List<Recipe> recipes;
  final bool isLoading;
  final bool hasMore;
  final int currentPage;
  final String? error;

  const RecipeListState({
    this.recipes = const [],
    this.isLoading = false,
    this.hasMore = true,
    this.currentPage = 1,
    this.error,
  });

  RecipeListState copyWith({
    List<Recipe>? recipes,
    bool? isLoading,
    bool? hasMore,
    int? currentPage,
    String? error,
  }) {
    return RecipeListState(
      recipes: recipes ?? this.recipes,
      isLoading: isLoading ?? this.isLoading,
      hasMore: hasMore ?? this.hasMore,
      currentPage: currentPage ?? this.currentPage,
      error: error ?? this.error,
    );
  }
}

/// 페이지네이션 레시피 목록을 관리하는 StateNotifier
class PaginatedRecipeNotifier extends StateNotifier<RecipeListState> {
  PaginatedRecipeNotifier(this.ref) : super(const RecipeListState());
  
  final Ref ref;

  /// 첫 페이지 로드
  Future<void> loadFirstPage() async {
    if (state.isLoading) return;

    state = state.copyWith(isLoading: true, error: null);

    try {
      final searchQuery = ref.read(recipeSearchQueryProvider);
      final showOnlyFavorites = ref.read(showOnlyFavoritesProvider);
      final favoriteIds = ref.read(favoriteRecipesProvider);
      final userIngredients = ref.read(selectedIngredientsProvider);

      final recipePage = await RecipeDataService.getRecipePage(
        page: 1,
        searchQuery: searchQuery.isEmpty ? null : searchQuery,
        userIngredients: userIngredients.isEmpty ? null : userIngredients,
        showOnlyFavorites: showOnlyFavorites,
        favoriteIds: favoriteIds.toList(),
      );

      state = RecipeListState(
        recipes: recipePage.recipes,
        isLoading: false,
        hasMore: recipePage.hasMore,
        currentPage: 1,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// 다음 페이지 로드
  Future<void> loadNextPage() async {
    if (state.isLoading || !state.hasMore) return;

    state = state.copyWith(isLoading: true);

    try {
      final searchQuery = ref.read(recipeSearchQueryProvider);
      final showOnlyFavorites = ref.read(showOnlyFavoritesProvider);
      final favoriteIds = ref.read(favoriteRecipesProvider);
      final userIngredients = ref.read(selectedIngredientsProvider);

      final recipePage = await RecipeDataService.getRecipePage(
        page: state.currentPage + 1,
        searchQuery: searchQuery.isEmpty ? null : searchQuery,
        userIngredients: userIngredients.isEmpty ? null : userIngredients,
        showOnlyFavorites: showOnlyFavorites,
        favoriteIds: favoriteIds.toList(),
      );

      state = state.copyWith(
        recipes: [...state.recipes, ...recipePage.recipes],
        isLoading: false,
        hasMore: recipePage.hasMore,
        currentPage: state.currentPage + 1,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// 새로고침
  Future<void> refresh() async {
    state = const RecipeListState();
    await loadFirstPage();
  }
}

/// 페이지네이션 레시피 목록 Provider
final paginatedRecipeProvider = StateNotifierProvider<PaginatedRecipeNotifier, RecipeListState>((ref) {
  return PaginatedRecipeNotifier(ref);
});

/// 즐겨찾기 레시피 목록을 관리하는 StateNotifier
class FavoriteRecipesNotifier extends StateNotifier<Set<String>> {
  FavoriteRecipesNotifier() : super({});

  /// 즐겨찾기 토글
  void toggleFavorite(String recipeId) {
    if (state.contains(recipeId)) {
      state = {...state}..remove(recipeId);
    } else {
      state = {...state, recipeId};
    }
  }

  /// 즐겨찾기 여부 확인
  bool isFavorite(String recipeId) {
    return state.contains(recipeId);
  }

  /// 모든 즐겨찾기 제거
  void clearAllFavorites() {
    state = {};
  }
}

/// 즐겨찾기 레시피 목록 Provider
final favoriteRecipesProvider = StateNotifierProvider<FavoriteRecipesNotifier, Set<String>>((ref) {
  return FavoriteRecipesNotifier();
});

/// 레시피 검색어 Provider
final recipeSearchQueryProvider = StateProvider<String>((ref) => '');

/// 즐겨찾기 필터 활성화 상태 Provider
final showOnlyFavoritesProvider = StateProvider<bool>((ref) => false);

/// 기존 호환성을 위한 Provider들
final recipeListProvider = FutureProvider<List<Recipe>>((ref) async {
  return await RecipeDataService.getAllRecipes();
});

/// 필터링된 레시피 목록 Provider (무한스크롤 버전)
final filteredRecipeListProvider = Provider<List<Recipe>>((ref) {
  final recipeState = ref.watch(paginatedRecipeProvider);
  return recipeState.recipes;
});

/// 즐겨찾기된 레시피 목록 Provider
final favoriteRecipeListProvider = FutureProvider<List<Recipe>>((ref) async {
  final allRecipes = await RecipeDataService.getAllRecipes();
  final favoriteRecipeIds = ref.watch(favoriteRecipesProvider);
  
  return allRecipes
      .where((recipe) => favoriteRecipeIds.contains(recipe.id))
      .toList();
});