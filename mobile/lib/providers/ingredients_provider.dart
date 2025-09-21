import 'package:flutter_riverpod/flutter_riverpod.dart';

/// 선택된 식재료 목록을 관리하는 StateNotifier
class SelectedIngredientsNotifier extends StateNotifier<List<String>> {
  SelectedIngredientsNotifier() : super([]);

  /// 식재료 추가/제거 토글
  void toggleIngredient(String ingredient) {
    if (state.contains(ingredient)) {
      state = state.where((item) => item != ingredient).toList();
    } else {
      state = [...state, ingredient];
    }
  }

  /// 식재료 제거
  void removeIngredient(String ingredient) {
    state = state.where((item) => item != ingredient).toList();
  }

  /// 여러 식재료 추가
  void addIngredients(List<String> ingredients) {
    final newIngredients = ingredients.where((ingredient) => !state.contains(ingredient));
    state = [...state, ...newIngredients];
  }

  /// 모든 식재료 제거
  void clearAllIngredients() {
    state = [];
  }
}

/// 선택된 식재료 목록 Provider
final selectedIngredientsProvider = StateNotifierProvider<SelectedIngredientsNotifier, List<String>>((ref) {
  return SelectedIngredientsNotifier();
});

/// 검색 텍스트 상태 Provider
final searchTextProvider = StateProvider<String>((ref) => '');

/// 선택된 카테고리 상태 Provider
final selectedCategoryProvider = StateProvider<String>((ref) => '전체');

/// 더보기 상태 Provider (홈 화면에서 모든 재료 표시 여부)
final showAllIngredientsProvider = StateProvider<bool>((ref) => false);

/// 검색 모드 상태 Provider (AppBar 검색 모드 여부)
final isSearchingProvider = StateProvider<bool>((ref) => false);

/// 임시 선택된 식재료 목록을 관리하는 StateNotifier (Modal에서 사용)
class TempSelectedIngredientsNotifier extends StateNotifier<List<String>> {
  TempSelectedIngredientsNotifier() : super([]);

  /// 식재료 추가/제거 토글
  void toggleIngredient(String ingredient) {
    if (state.contains(ingredient)) {
      state = state.where((item) => item != ingredient).toList();
    } else {
      state = [...state, ingredient];
    }
  }

  /// 임시 선택 목록 초기화
  void clearSelection() {
    state = [];
  }

  /// 현재 선택된 목록 반환
  List<String> getSelectedIngredients() {
    return List.from(state);
  }
}

/// 임시 선택된 식재료 목록 Provider (Modal에서 사용)
final tempSelectedIngredientsProvider = StateNotifierProvider<TempSelectedIngredientsNotifier, List<String>>((ref) {
  return TempSelectedIngredientsNotifier();
});

/// 식재료 데이터 Provider (정적 데이터)
final ingredientsDataProvider = Provider<Map<String, List<String>>>((ref) {
  return {
    '정육/계란': [
      '계란', '닭', '닭가슴살', '닭날개', '닭다리살', '돼지갈비', '돼지고기', '돼지고기 다짐육',
      '돼지고기 앞다리살', '돼지고기 저개용', '돼지등뼈', '등갈비', '매추리알', '목살', '베이컨', '삼겹살'
    ],
    '수산물': [
      '고등어', '광어', '김', '낙지', '대구', '멸치', '명태', '바지락', '새우', '연어',
      '오징어', '전복', '조개', '참치', '홍합'
    ],
    '채소': [
      '가지', '감자', '고구마', '고추', '깻잎', '당근', '대파', '마늘', '무', '배추',
      '브로콜리', '상추', '시금치', '양배추', '양파', '오이', '토마토', '파프리카', '호박'
    ],
    '장/양념/오일': [
      '간장', '고추장', '된장', '마요네즈', '미림', '올리브오일', '참기름', '초고추장', '케첩', '후추'
    ],
  };
});

/// 카테고리 목록 Provider
final categoriesProvider = Provider<List<String>>((ref) {
  return ['전체', '정육/계란', '수산물', '채소', '장/양념/오일'];
});

/// 필터링된 식재료 목록 Provider
final filteredIngredientsProvider = Provider<List<String>>((ref) {
  final ingredientsData = ref.watch(ingredientsDataProvider);
  final selectedCategory = ref.watch(selectedCategoryProvider);
  final searchText = ref.watch(searchTextProvider);

  List<String> allIngredients = [];
  
  if (selectedCategory == '전체') {
    for (final ingredients in ingredientsData.values) {
      allIngredients.addAll(ingredients);
    }
  } else {
    allIngredients = ingredientsData[selectedCategory] ?? [];
  }

  if (searchText.isNotEmpty) {
    allIngredients = allIngredients
        .where((ingredient) => ingredient.contains(searchText))
        .toList();
  }

  return allIngredients;
});

/// 카테고리별로 그룹화된 식재료 Provider (전체 선택 시)
final categorizedIngredientsProvider = Provider<Map<String, List<String>>>((ref) {
  final ingredientsData = ref.watch(ingredientsDataProvider);
  final searchText = ref.watch(searchTextProvider);
  
  Map<String, List<String>> categorizedIngredients = {};
  
  for (final category in ingredientsData.keys) {
    List<String> categoryItems = ingredientsData[category] ?? [];
    
    if (searchText.isNotEmpty) {
      categoryItems = categoryItems
          .where((ingredient) => ingredient.contains(searchText))
          .toList();
    }
    
    if (categoryItems.isNotEmpty) {
      categorizedIngredients[category] = categoryItems;
    }
  }
  
  return categorizedIngredients;
});
