import '../product.dart';

/// 카테고리 정보 모델 (API 응답용)
class ApiCategory {
  final int id;
  final String name;
  final String code;
  final String? icon;
  final int displayOrder;

  const ApiCategory({
    required this.id,
    required this.name,
    required this.code,
    this.icon,
    required this.displayOrder,
  });

  factory ApiCategory.fromJson(Map<String, dynamic> json) {
    return ApiCategory(
      id: json['id'] as int,
      name: json['name'] as String,
      code: json['code'] as String,
      icon: json['icon'] as String?,
      displayOrder: json['display_order'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'code': code,
      'icon': icon,
      'display_order': displayOrder,
    };
  }
}

/// API 식재료 모델 (API 응답용)
class ApiIngredient {
  final int id; // API에서는 int 타입의 id
  final String name;
  final String? description;
  final String? imageUrl;
  final ApiCategory category; // category 객체
  final bool isCommonSeasoning; // 공통 양념 여부
  final String? unit;
  final bool isActive;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const ApiIngredient({
    required this.id,
    required this.name,
    this.description,
    this.imageUrl,
    required this.category,
    this.isCommonSeasoning = false,
    this.unit,
    this.isActive = true,
    this.createdAt,
    this.updatedAt,
  });

  /// JSON에서 생성
  factory ApiIngredient.fromJson(Map<String, dynamic> json) {
    final ingredientName = json['name']?.toString().trim() ?? '';

    // 카테고리 정보 파싱
    final ApiCategory categoryObj;
    if (json['category'] is Map<String, dynamic>) {
      categoryObj = ApiCategory.fromJson(json['category']);
    } else {
      // category가 문자열인 경우 기본 카테고리 생성
      categoryObj = ApiCategory(
        id: 0,
        name: json['category']?.toString() ?? '기타',
        code: 'others',
        displayOrder: 999,
      );
    }

    // 빈 이름이나 이상한 이름들은 필터링
    if (ingredientName.isEmpty ||
        ingredientName.length < 2 ||
        ingredientName.contains('null') ||
        ingredientName.contains('undefined')) {
      // 빈 이름인 경우 기본값 설정
      return ApiIngredient(
        id: json['id'] as int? ?? 0,
        name: '알 수 없는 재료',
        description: json['description'],
        imageUrl: json['image_url'] ?? json['imageUrl'],
        category: categoryObj,
        isCommonSeasoning: json['is_common_seasoning'] as bool? ?? false,
        unit: json['unit'],
        isActive: false, // 빈 이름은 비활성화
        createdAt: DateTime.tryParse(json['created_at'] ?? json['createdAt'] ?? ''),
        updatedAt: DateTime.tryParse(json['updated_at'] ?? json['updatedAt'] ?? ''),
      );
    }

    return ApiIngredient(
      id: json['id'] as int? ?? 0,
      name: ingredientName,
      description: json['description'],
      imageUrl: json['image_url'] ?? json['imageUrl'],
      category: categoryObj,
      isCommonSeasoning: json['is_common_seasoning'] as bool? ?? false,
      unit: json['unit'],
      isActive: json['is_active'] ?? json['isActive'] ?? true,
      createdAt: DateTime.tryParse(json['created_at'] ?? json['createdAt'] ?? ''),
      updatedAt: DateTime.tryParse(json['updated_at'] ?? json['updatedAt'] ?? ''),
    );
  }

  /// JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'image_url': imageUrl,
      'category': category.toJson(),
      'is_common_seasoning': isCommonSeasoning,
      'unit': unit,
      'is_active': isActive,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  /// 기존 Product 모델로 변환 (호환성)
  Product toProduct() {
    return Product(
      id: id.toString(),
      name: name,
      description: description ?? '',
      price: 0.0, // API 식재료는 가격이 없음
      imageUrl: imageUrl,
      category: _convertToProductCategory(category.code),
      ingredients: [name],
    );
  }

  /// ProductCategory로 변환
  ProductCategory _convertToProductCategory(String categoryCode) {
    // 모든 경우 salad로 반환 (기존 Product 모델의 제한)
    return ProductCategory.salad;
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is ApiIngredient && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() {
    return 'ApiIngredient(id: $id, name: $name, category: ${category.name})';
  }
}

/// 레시피 재료 목록 API 응답 모델
class RecipeIngredientsResponse {
  final List<ApiIngredient> ingredients;
  final int total;
  final List<ApiCategory> categories;

  const RecipeIngredientsResponse({
    required this.ingredients,
    required this.total,
    required this.categories,
  });

  factory RecipeIngredientsResponse.fromJson(Map<String, dynamic> json) {
    return RecipeIngredientsResponse(
      ingredients: (json['ingredients'] as List<dynamic>?)
              ?.map((item) => ApiIngredient.fromJson(item as Map<String, dynamic>))
              .toList() ??
          [],
      total: json['total'] as int? ?? 0,
      categories: (json['categories'] as List<dynamic>?)
              ?.map((item) => ApiCategory.fromJson(item as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'ingredients': ingredients.map((i) => i.toJson()).toList(),
      'total': total,
      'categories': categories.map((c) => c.toJson()).toList(),
    };
  }
}

/// 카테고리 목록 API 응답 모델
class CategoriesResponse {
  final List<ApiCategory> categories;
  final int total;

  const CategoriesResponse({
    required this.categories,
    required this.total,
  });

  factory CategoriesResponse.fromJson(Map<String, dynamic> json) {
    return CategoriesResponse(
      categories: (json['categories'] as List<dynamic>?)
              ?.map((item) => ApiCategory.fromJson(item as Map<String, dynamic>))
              .toList() ??
          [],
      total: json['total'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'categories': categories.map((c) => c.toJson()).toList(),
      'total': total,
    };
  }
}

/// 식재료 카테고리 (API용)
enum IngredientCategory {
  vegetables('채소'),
  fruits('과일'),
  meat('육류'),
  seafood('해산물'),
  dairy('유제품'),
  grains('곡물'),
  spices('양념'),
  others('기타');

  const IngredientCategory(this.displayName);
  final String displayName;
}

/// 식재료 검색 필터
class IngredientSearchFilter {
  final String? search;
  final IngredientCategory? category;
  final bool? isActive;
  final int page;
  final int size;

  const IngredientSearchFilter({
    this.search,
    this.category,
    this.isActive,
    this.page = 1,
    this.size = 20,
  });

  /// 쿼리 파라미터로 변환
  Map<String, dynamic> toQueryParams() {
    final params = <String, dynamic>{
      'page': page,
      'size': size,
    };

    if (search != null && search!.isNotEmpty) {
      params['search'] = search;
    }

    if (category != null) {
      params['category'] = category!.name;
    }

    if (isActive != null) {
      params['is_active'] = isActive;
    }

    return params;
  }

  /// 복사본 생성
  IngredientSearchFilter copyWith({
    String? search,
    IngredientCategory? category,
    bool? isActive,
    int? page,
    int? size,
  }) {
    return IngredientSearchFilter(
      search: search ?? this.search,
      category: category ?? this.category,
      isActive: isActive ?? this.isActive,
      page: page ?? this.page,
      size: size ?? this.size,
    );
  }

  @override
  String toString() {
    return 'IngredientSearchFilter(search: $search, category: $category, page: $page, size: $size)';
  }
}
