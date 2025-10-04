import 'package:flutter/foundation.dart';
import 'api_client.dart';
import '../../models/api/api_recipe.dart';
import '../../models/api/api_response.dart';

/// 레시피 API 서비스
class RecipeApiService {
  /// 레시피 목록 조회 (페이지네이션)
  static Future<ApiResponse<PaginatedResponse<ApiRecipe>>> getRecipes({
    RecipeSearchFilter? filter,
  }) async {
    final searchFilter = filter ?? const RecipeSearchFilter();
    final queryParams = searchFilter.toQueryParams();

    return await ApiClient.get<PaginatedResponse<ApiRecipe>>(
      ApiEndpoints.recipes,
      queryParams: queryParams,
      fromJson: (json) => PaginatedResponse.fromJson(
        json,
        (item) => ApiRecipe.fromJson(item),
      ),
    );
  }

  /// 특정 레시피 조회
  static Future<ApiResponse<ApiRecipe>> getRecipeById(String rcpSno) async {
    return await ApiClient.get<ApiRecipe>(
      ApiEndpoints.recipeById(rcpSno),
      fromJson: (json) => ApiRecipe.fromJson(json),
    );
  }

  /// 보유 재료 기반 레시피 추천 (Phase 2 핵심 기능 - 개선됨)
  static Future<ApiResponse<PaginatedResponse<ApiRecipe>>> getRecipesByIngredients(
    List<String> ingredientNames, {
    int page = 1,
    int size = 10,
  }) async {
    if (ingredientNames.isEmpty) {
      return ApiResponse.error(
        message: '재료를 선택해주세요',
        statusCode: 400,
      );
    }

    try {
      // 한글 재료명을 포함한 쿼리 파라미터 (URL 인코딩 자동 처리)
      final queryParams = {
        'ingredients': ingredientNames.join(','),
        'page': page,
        'size': size,
      };

      if (kDebugMode) {
        debugPrint('🔍 Requesting recipes for ingredients: ${ingredientNames.join(", ")}');
      }

      final response = await ApiClient.get<PaginatedResponse<ApiRecipe>>(
        ApiEndpoints.recipeRecommendations,
        queryParams: queryParams,
        fromJson: (json) => PaginatedResponse.fromJson(
          json,
          (item) => ApiRecipe.fromJson(item),
        ),
      );

      if (kDebugMode && response.success && response.data != null) {
        debugPrint('✅ Found ${response.data!.items.length} recipes for ingredients');
      }

      return response;
    } catch (e) {
      if (kDebugMode) {
        debugPrint('❌ Error in getRecipesByIngredients: $e');
      }

      // 에러 발생 시 빈 결과 반환 (앱이 중단되지 않도록)
      return ApiResponse.error(
        message: '레시피 추천 중 오류가 발생했습니다',
        statusCode: 500,
      );
    }
  }

  /// 레시피 검색
  static Future<ApiResponse<PaginatedResponse<ApiRecipe>>> searchRecipes(
    String searchQuery, {
    String? category,
    String? difficulty,
    int? maxCookingTime,
    int page = 1,
    int size = 10,
  }) async {
    final filter = RecipeSearchFilter(
      search: searchQuery,
      category: category,
      difficulty: difficulty,
      maxCookingTime: maxCookingTime,
      page: page,
      size: size,
    );

    return await getRecipes(filter: filter);
  }

  /// 카테고리별 레시피 조회
  static Future<ApiResponse<PaginatedResponse<ApiRecipe>>> getRecipesByCategory(
    String category, {
    int page = 1,
    int size = 10,
  }) async {
    final filter = RecipeSearchFilter(
      category: category,
      page: page,
      size: size,
    );

    return await getRecipes(filter: filter);
  }

  /// 인기 레시피 조회
  static Future<ApiResponse<PaginatedResponse<ApiRecipe>>> getPopularRecipes({
    int page = 1,
    int size = 10,
  }) async {
    final filter = RecipeSearchFilter(
      isPopular: true,
      page: page,
      size: size,
    );

    return await getRecipes(filter: filter);
  }

  /// 활성 레시피만 조회
  static Future<ApiResponse<PaginatedResponse<ApiRecipe>>> getActiveRecipes({
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

    return await getRecipes(filter: filter);
  }

  /// 조리 시간별 레시피 조회
  static Future<ApiResponse<PaginatedResponse<ApiRecipe>>> getRecipesByCookingTime(
    int maxCookingTimeMinutes, {
    String? category,
    int page = 1,
    int size = 10,
  }) async {
    final filter = RecipeSearchFilter(
      category: category,
      maxCookingTime: maxCookingTimeMinutes,
      page: page,
      size: size,
    );

    return await getRecipes(filter: filter);
  }

  /// 난이도별 레시피 조회
  static Future<ApiResponse<PaginatedResponse<ApiRecipe>>> getRecipesByDifficulty(
    String difficulty, {
    String? category,
    int page = 1,
    int size = 10,
  }) async {
    final filter = RecipeSearchFilter(
      category: category,
      difficulty: difficulty,
      page: page,
      size: size,
    );

    return await getRecipes(filter: filter);
  }

  /// 레시피 통계 정보 조회
  static Future<ApiResponse<Map<String, dynamic>>> getRecipeStats() async {
    return await ApiClient.get<Map<String, dynamic>>(
      ApiEndpoints.recipeStats,
      fromJson: (json) => Map<String, dynamic>.from(json),
    );
  }

  /// 모든 레시피 조회 (페이지네이션 없음)
  static Future<ApiResponse<List<ApiRecipe>>> getAllRecipes({
    String? category,
    bool? isActive,
  }) async {
    final response = await getRecipes(
      filter: RecipeSearchFilter(
        category: category,
        isActive: isActive,
        page: 1,
        size: 1000, // 큰 사이즈로 설정하여 모든 데이터 가져오기
      ),
    );

    if (response.success && response.data != null) {
      return ApiResponse.success(
        data: response.data!.items,
        message: response.message,
        statusCode: response.statusCode ?? 200,
        metadata: response.metadata,
      );
    } else {
      return ApiResponse.error(
        message: response.message,
        errorCode: response.errorCode,
        statusCode: response.statusCode ?? 500,
      );
    }
  }

  /// 관련 레시피 추천 (같은 카테고리 또는 유사한 재료)
  static Future<ApiResponse<List<ApiRecipe>>> getRelatedRecipes(
    String recipeId, {
    int limit = 3,
  }) async {
    // 먼저 해당 레시피 정보를 가져옴
    final recipeResponse = await getRecipeById(recipeId);
    if (!recipeResponse.success || recipeResponse.data == null) {
      return ApiResponse.error(
        message: '레시피를 찾을 수 없습니다.',
        errorCode: 'RECIPE_NOT_FOUND',
        statusCode: 404,
      );
    }

    final targetRecipe = recipeResponse.data!;
    
    // 같은 카테고리의 다른 레시피들을 가져옴
    final relatedResponse = await getRecipesByCategory(
      targetRecipe.category,
      size: limit + 1, // 자기 자신 제외를 위해 +1
    );

    if (!relatedResponse.success || relatedResponse.data == null) {
      return ApiResponse.error(
        message: '관련 레시피를 찾을 수 없습니다.',
        errorCode: 'RELATED_RECIPES_NOT_FOUND',
        statusCode: 404,
      );
    }

    // 자기 자신을 제외하고 제한된 개수만 반환
    final relatedRecipes = relatedResponse.data!.items
        .where((recipe) => recipe.id != recipeId)
        .take(limit)
        .toList();

    return ApiResponse.success(
      data: relatedRecipes,
      message: '관련 레시피를 조회했습니다.',
      statusCode: 200,
    );
  }

  /// 레시피 ID 목록으로 여러 레시피 조회
  static Future<ApiResponse<List<ApiRecipe>>> getRecipesByIds(
    List<String> recipeIds,
  ) async {
    final List<ApiRecipe> recipes = [];
    
    for (final id in recipeIds) {
      final response = await getRecipeById(id);
      if (response.success && response.data != null) {
        recipes.add(response.data!);
      }
    }
    
    return ApiResponse.success(
      data: recipes,
      message: '${recipes.length}개의 레시피를 조회했습니다.',
      statusCode: 200,
    );
  }

  /// 레시피 검색 (고급 필터)
  static Future<ApiResponse<PaginatedResponse<ApiRecipe>>> searchRecipesAdvanced({
    String? search,
    String? category,
    String? difficulty,
    int? minCookingTime,
    int? maxCookingTime,
    int? minServings,
    int? maxServings,
    double? minRating,
    bool? isPopular,
    bool? isActive,
    int page = 1,
    int size = 10,
  }) async {
    final filter = RecipeSearchFilter(
      search: search,
      category: category,
      difficulty: difficulty,
      maxCookingTime: maxCookingTime,
      isPopular: isPopular,
      isActive: isActive,
      page: page,
      size: size,
    );

    final response = await getRecipes(filter: filter);
    
    if (!response.success || response.data == null) {
      return response;
    }

    // 클라이언트 사이드에서 추가 필터링
    var filteredRecipes = response.data!.items;

    // 최소 조리 시간 필터링
    if (minCookingTime != null) {
      filteredRecipes = filteredRecipes
          .where((recipe) => recipe.cookingTimeMinutes >= minCookingTime)
          .toList();
    }

    // 최소 서빙 수 필터링
    if (minServings != null) {
      filteredRecipes = filteredRecipes
          .where((recipe) => recipe.servings >= minServings)
          .toList();
    }

    // 최대 서빙 수 필터링
    if (maxServings != null) {
      filteredRecipes = filteredRecipes
          .where((recipe) => recipe.servings <= maxServings)
          .toList();
    }

    // 최소 평점 필터링
    if (minRating != null) {
      filteredRecipes = filteredRecipes
          .where((recipe) => recipe.rating >= minRating)
          .toList();
    }

    // 페이지네이션 적용
    final startIndex = (page - 1) * size;
    final endIndex = (startIndex + size).clamp(0, filteredRecipes.length);
    final pagedRecipes = filteredRecipes.sublist(
      startIndex.clamp(0, filteredRecipes.length),
      endIndex,
    );

    final paginatedResponse = PaginatedResponse<ApiRecipe>(
      items: pagedRecipes,
      currentPage: page,
      totalPages: (filteredRecipes.length / size).ceil(),
      totalItems: filteredRecipes.length,
      pageSize: size,
      hasNextPage: endIndex < filteredRecipes.length,
      hasPreviousPage: page > 1,
    );

    return ApiResponse.success(
      data: paginatedResponse,
      message: response.message,
      statusCode: response.statusCode ?? 200,
      metadata: response.metadata,
    );
  }

  /// 레시피 추천 (유사도 알고리즘)
  static Future<ApiResponse<RecipeRecommendationsResponse>> getRecommendations({
    required List<String> ingredients,
    int limit = 20,
    String algorithm = 'jaccard',
    bool excludeSeasonings = true,
    double? minMatchRate, // null이면 서버의 관리자 설정 사용 (기본값: 0.15)
  }) async {
    final queryParams = <String, dynamic>{
      'ingredients': ingredients.join(','),
      'limit': limit,
      'algorithm': algorithm,
      'exclude_seasonings': excludeSeasonings,
    };

    // minMatchRate가 명시적으로 제공된 경우에만 추가
    if (minMatchRate != null) {
      queryParams['min_match_rate'] = minMatchRate;
    }

    return await ApiClient.get<RecipeRecommendationsResponse>(
      ApiEndpoints.recipeRecommendations,
      queryParams: queryParams,
      fromJson: (json) => RecipeRecommendationsResponse.fromJson(json),
    );
  }
}
