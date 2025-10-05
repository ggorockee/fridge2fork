import 'api_client.dart';
import '../../models/api/api_ingredient.dart';
import '../../models/api/api_response.dart';

/// 식재료 API 서비스
class IngredientApiService {
  /// 카테고리 목록 조회
  static Future<ApiResponse<CategoriesResponse>> getCategories({
    String categoryType = 'normalized',
  }) async {
    final queryParams = <String, dynamic>{
      'category_type': categoryType,
    };

    return await ApiClient.get<CategoriesResponse>(
      ApiEndpoints.categories,
      queryParams: queryParams,
      fromJson: (json) => CategoriesResponse.fromJson(json),
    );
  }

  /// 레시피에 사용된 모든 재료 목록 조회 (새 API)
  static Future<ApiResponse<RecipeIngredientsResponse>> getRecipeIngredients({
    bool excludeSeasonings = true,
    int? limit,
  }) async {
    final queryParams = <String, dynamic>{
      'exclude_seasonings': excludeSeasonings,
    };

    if (limit != null) {
      queryParams['limit'] = limit;
    }

    return await ApiClient.get<RecipeIngredientsResponse>(
      ApiEndpoints.ingredients,
      queryParams: queryParams,
      fromJson: (json) => RecipeIngredientsResponse.fromJson(json),
    );
  }
  /// 식재료 목록 조회 (페이지네이션)
  static Future<ApiResponse<PaginatedResponse<ApiIngredient>>> getIngredients({
    IngredientSearchFilter? filter,
  }) async {
    final searchFilter = filter ?? const IngredientSearchFilter();
    final queryParams = searchFilter.toQueryParams();

    return await ApiClient.get<PaginatedResponse<ApiIngredient>>(
      ApiEndpoints.ingredients,
      queryParams: queryParams,
      fromJson: (json) => PaginatedResponse.fromJson(
        json,
        (item) => ApiIngredient.fromJson(item),
      ),
    );
  }

  /// 특정 식재료 조회 (현재 API에서 지원하지 않음)
  static Future<ApiResponse<ApiIngredient>> getIngredientById(String id) async {
    // TODO: API 스펙에 없는 엔드포인트 - 필요시 백엔드에 요청
    return await ApiClient.get<ApiIngredient>(
      '/fridge2fork/v1/fridge/ingredients/$id',
      fromJson: (json) => ApiIngredient.fromJson(json),
    );
  }

  /// 식재료 검색
  static Future<ApiResponse<PaginatedResponse<ApiIngredient>>> searchIngredients(
    String searchQuery, {
    IngredientCategory? category,
    int page = 1,
    int size = 20,
  }) async {
    final filter = IngredientSearchFilter(
      search: searchQuery,
      category: category,
      page: page,
      size: size,
    );

    return await getIngredients(filter: filter);
  }

  /// 카테고리별 식재료 조회
  static Future<ApiResponse<PaginatedResponse<ApiIngredient>>> getIngredientsByCategory(
    IngredientCategory category, {
    int page = 1,
    int size = 20,
  }) async {
    final filter = IngredientSearchFilter(
      category: category,
      page: page,
      size: size,
    );

    return await getIngredients(filter: filter);
  }

  /// 활성 식재료만 조회
  static Future<ApiResponse<PaginatedResponse<ApiIngredient>>> getActiveIngredients({
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

    return await getIngredients(filter: filter);
  }

  /// 모든 식재료 조회 (페이지네이션 없음)
  static Future<ApiResponse<List<ApiIngredient>>> getAllIngredients({
    IngredientCategory? category,
    bool? isActive,
  }) async {
    final response = await getIngredients(
      filter: IngredientSearchFilter(
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

  /// 식재료 이름으로 검색 (정확한 매칭)
  static Future<ApiResponse<ApiIngredient?>> findIngredientByName(String name) async {
    final response = await searchIngredients(name, size: 1);
    
    if (response.success && response.data != null && response.data!.items.isNotEmpty) {
      final ingredients = response.data!.items;
      final exactMatch = ingredients.firstWhere(
        (ingredient) => ingredient.name.toLowerCase() == name.toLowerCase(),
        orElse: () => ingredients.first, // 정확한 매칭이 없으면 첫 번째 결과 반환
      );
      
      return ApiResponse.success(
        data: exactMatch,
        message: response.message,
        statusCode: response.statusCode ?? 200,
      );
    } else {
      return ApiResponse.success(
        data: null,
        message: '식재료를 찾을 수 없습니다.',
        statusCode: 404,
      );
    }
  }

  /// 식재료 ID 목록으로 여러 식재료 조회
  static Future<ApiResponse<List<ApiIngredient>>> getIngredientsByIds(
    List<String> ingredientIds,
  ) async {
    final List<ApiIngredient> ingredients = [];
    
    for (final id in ingredientIds) {
      final response = await getIngredientById(id);
      if (response.success && response.data != null) {
        ingredients.add(response.data!);
      }
    }
    
    return ApiResponse.success(
      data: ingredients,
      message: '${ingredients.length}개의 식재료를 조회했습니다.',
      statusCode: 200,
    );
  }

  /// 식재료 통계 정보 조회
  static Future<ApiResponse<Map<String, dynamic>>> getIngredientStats() async {
    // 현재 API 명세에 식재료 통계 엔드포인트가 없으므로
    // 전체 식재료를 조회하여 클라이언트에서 계산
    final response = await getAllIngredients();
    
    if (!response.success || response.data == null) {
      return ApiResponse.error(
        message: '식재료 통계를 가져올 수 없습니다.',
        errorCode: 'STATS_ERROR',
        statusCode: 500,
      );
    }

    final ingredients = response.data!;
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

    return ApiResponse.success(
      data: stats,
      message: '식재료 통계를 조회했습니다.',
      statusCode: 200,
    );
  }
}
