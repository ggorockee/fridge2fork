import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/recipe.dart';

/// 레시피 페이지네이션 결과
class RecipePage {
  final List<Recipe> recipes;
  final bool hasMore;
  final int currentPage;
  final int totalCount;

  RecipePage({
    required this.recipes,
    required this.hasMore,
    required this.currentPage,
    required this.totalCount,
  });
}

/// 레시피 데이터 서비스
class RecipeDataService {
  static List<Recipe>? _allRecipes;
  static const int _pageSize = 10; // 한 페이지당 10개 아이템

  /// JSON에서 모든 레시피 로드
  static Future<List<Recipe>> _loadAllRecipes() async {
    if (_allRecipes != null) return _allRecipes!;

    try {
      final String jsonString = await rootBundle.loadString('assets/data/recipes.json');
      final List<dynamic> jsonList = json.decode(jsonString);
      
      _allRecipes = jsonList.map((json) => Recipe.fromJson(json)).toList();
      return _allRecipes!;
    } catch (e) {
      print('Error loading recipes: $e');
      return [];
    }
  }

  /// 페이지네이션된 레시피 목록 가져오기
  static Future<RecipePage> getRecipePage({
    int page = 1,
    String? searchQuery,
    List<String>? userIngredients,
    bool showOnlyFavorites = false,
    List<String>? favoriteIds,
  }) async {
    final allRecipes = await _loadAllRecipes();
    List<Recipe> filteredRecipes = List.from(allRecipes);

    // 검색 필터링
    if (searchQuery != null && searchQuery.isNotEmpty) {
      filteredRecipes = filteredRecipes.where((recipe) =>
          recipe.name.toLowerCase().contains(searchQuery.toLowerCase()) ||
          recipe.description.toLowerCase().contains(searchQuery.toLowerCase()) ||
          recipe.ingredients.any((ingredient) => 
              ingredient.name.toLowerCase().contains(searchQuery.toLowerCase()))).toList();
    }

    // 즐겨찾기 필터링
    if (showOnlyFavorites && favoriteIds != null) {
      filteredRecipes = filteredRecipes.where((recipe) => 
          favoriteIds.contains(recipe.id)).toList();
    }

    // 재료 기반 정렬 (재료가 있는 경우)
    if (userIngredients != null && userIngredients.isNotEmpty) {
      filteredRecipes.sort((a, b) =>
          b.calculateMatchingRate(userIngredients).compareTo(a.calculateMatchingRate(userIngredients)));
    }

    final totalCount = filteredRecipes.length;
    final startIndex = (page - 1) * _pageSize;
    final endIndex = (startIndex + _pageSize).clamp(0, totalCount);
    
    final pageRecipes = filteredRecipes.sublist(
      startIndex.clamp(0, totalCount),
      endIndex,
    );

    final hasMore = endIndex < totalCount;

    return RecipePage(
      recipes: pageRecipes,
      hasMore: hasMore,
      currentPage: page,
      totalCount: totalCount,
    );
  }

  /// 전체 레시피 목록 (기존 호환성을 위해)
  static Future<List<Recipe>> getAllRecipes() async {
    return await _loadAllRecipes();
  }
}

// 기존 호환성을 위한 변수들
List<Recipe> sampleRecipes = [];

/// 관련 레시피 추천 (같은 카테고리 또는 유사한 재료)
Future<List<Recipe>> getRelatedRecipes(Recipe targetRecipe, {int limit = 3}) async {
  final allRecipes = await RecipeDataService.getAllRecipes();
  final related = allRecipes
      .where((recipe) =>
          recipe.id != targetRecipe.id &&
          (recipe.category == targetRecipe.category ||
              recipe.ingredients.any((ingredient) => targetRecipe.ingredients
                  .any((target) => target.name == ingredient.name))))
      .take(limit)
      .toList();
  return related;
}

/// 카테고리별 레시피 필터링
Future<List<Recipe>> getRecipesByCategory(RecipeCategory category) async {
  final allRecipes = await RecipeDataService.getAllRecipes();
  return allRecipes.where((recipe) => recipe.category == category).toList();
}

/// 재료 기반 레시피 검색
Future<List<Recipe>> searchRecipesByIngredients(List<String> userIngredients) async {
  final allRecipes = await RecipeDataService.getAllRecipes();
  if (userIngredients.isEmpty) return allRecipes;

  var results = allRecipes.map((recipe) {
    final matchingRate = recipe.calculateMatchingRate(userIngredients);
    return MapEntry(recipe, matchingRate);
  }).where((entry) => entry.value > 0).toList();

  // 매칭율 순으로 정렬
  results.sort((a, b) => b.value.compareTo(a.value));

  return results.map((entry) => entry.key).toList();
}

/// 인기 레시피
Future<List<Recipe>> get popularRecipes async {
  final allRecipes = await RecipeDataService.getAllRecipes();
  return allRecipes.where((recipe) => recipe.isPopular).toList();
}

/// 레시피 정렬
List<Recipe> sortRecipes(List<Recipe> recipes, SortOption sortOption, [List<String>? userIngredients]) {
  final sortedRecipes = List<Recipe>.from(recipes);

  switch (sortOption) {
    case SortOption.matchingRate:
      if (userIngredients != null && userIngredients.isNotEmpty) {
        sortedRecipes.sort((a, b) =>
            b.calculateMatchingRate(userIngredients).compareTo(a.calculateMatchingRate(userIngredients)));
      }
      break;
    case SortOption.popularity:
      sortedRecipes.sort((a, b) => b.reviewCount.compareTo(a.reviewCount));
      break;
    case SortOption.cookingTime:
      sortedRecipes.sort((a, b) => a.cookingTimeMinutes.compareTo(b.cookingTimeMinutes));
      break;
    case SortOption.rating:
      sortedRecipes.sort((a, b) => b.rating.compareTo(a.rating));
      break;
  }

  return sortedRecipes;
}
