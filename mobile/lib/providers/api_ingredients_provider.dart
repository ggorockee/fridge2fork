import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/api/api_ingredient.dart';
import '../providers/api/ingredient_api_provider.dart';
import '../providers/ingredients_provider.dart';
import '../services/api/ingredient_api_service.dart';

/// API 기반 카테고리 목록 Provider (정규화 카테고리 API 직접 호출)
final apiCategoriesProvider = FutureProvider<List<String>>((ref) async {
  try {
    // 정규화된 카테고리 목록 조회 API 호출
    final response = await IngredientApiService.getCategories(categoryType: 'normalized');

    if (response.success && response.data != null) {
      final categoryNames = response.data!.categories
          .map((category) => category.name)
          .toList();

      // '전체'를 맨 앞에 추가
      categoryNames.insert(0, '전체');

      return categoryNames;
    } else {
      // API 실패 시 식재료에서 카테고리 추출 (폴백)
      final ingredients = ref.watch(ingredientsProvider);
      final categories = ingredients
          .map((ingredient) => ingredient.category.name)
          .toSet()
          .toList();
      categories.insert(0, '전체');
      return categories;
    }
  } catch (e) {
    // 에러 발생 시 식재료에서 카테고리 추출 (폴백)
    final ingredients = ref.watch(ingredientsProvider);
    final categories = ingredients
        .map((ingredient) => ingredient.category.name)
        .toSet()
        .toList();
    categories.insert(0, '전체');
    return categories;
  }
});

/// API 기반 카테고리별 식재료 Provider
final apiIngredientsByCategoryProvider = Provider.family<List<ApiIngredient>, String>((ref, categoryName) {
  final ingredients = ref.watch(ingredientsProvider);

  if (categoryName == '전체') {
    return ingredients;
  }

  // ApiCategory.name으로 매칭
  return ingredients.where((ingredient) => ingredient.category.name == categoryName).toList();
});

/// API 기반 필터링된 식재료 목록 Provider
final apiFilteredIngredientsProvider = Provider<List<ApiIngredient>>((ref) {
  final selectedCategory = ref.watch(selectedCategoryProvider);
  final searchText = ref.watch(searchTextProvider);
  
  // 카테고리별 식재료 가져오기
  final categoryIngredients = ref.watch(apiIngredientsByCategoryProvider(selectedCategory));
  
  // 검색 필터링
  if (searchText.isEmpty) {
    return categoryIngredients;
  }
  
  return categoryIngredients.where((ingredient) =>
      ingredient.name.toLowerCase().contains(searchText.toLowerCase()) ||
      (ingredient.description?.toLowerCase().contains(searchText.toLowerCase()) ?? false)
  ).toList();
});

/// API 기반 카테고리별로 그룹화된 식재료 Provider (전체 선택 시)
final apiCategorizedIngredientsProvider = Provider<Map<String, List<ApiIngredient>>>((ref) {
  final ingredients = ref.watch(ingredientsProvider);
  final searchText = ref.watch(searchTextProvider);

  Map<String, List<ApiIngredient>> categorizedIngredients = {};

  // 카테고리별로 그룹화 (ApiCategory 기준)
  for (final ingredient in ingredients) {
    final categoryName = ingredient.category.name;

    if (!categorizedIngredients.containsKey(categoryName)) {
      categorizedIngredients[categoryName] = [];
    }

    // 검색 필터링
    if (searchText.isEmpty ||
        ingredient.name.toLowerCase().contains(searchText.toLowerCase()) ||
        (ingredient.description?.toLowerCase().contains(searchText.toLowerCase()) ?? false)) {
      categorizedIngredients[categoryName]!.add(ingredient);
    }
  }

  // 빈 카테고리 제거
  categorizedIngredients.removeWhere((key, value) => value.isEmpty);

  return categorizedIngredients;
});

/// API 식재료 이름 목록 Provider (기존 호환성을 위해)
final apiIngredientNamesProvider = Provider<List<String>>((ref) {
  final ingredients = ref.watch(apiFilteredIngredientsProvider);
  return ingredients.map((ingredient) => ingredient.name).toList();
});

/// API 카테고리별 식재료 이름 목록 Provider (기존 호환성을 위해)
final apiCategorizedIngredientNamesProvider = Provider<Map<String, List<String>>>((ref) {
  final categorizedIngredients = ref.watch(apiCategorizedIngredientsProvider);
  
  return categorizedIngredients.map((category, ingredients) => 
      MapEntry(category, ingredients.map((ingredient) => ingredient.name).toList()));
});
