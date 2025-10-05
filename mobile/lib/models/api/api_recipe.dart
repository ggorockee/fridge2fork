import '../recipe.dart';

/// API 레시피 모델 (API 응답용)
class ApiRecipe {
  final String id;
  final String name;
  final String description;
  final String? imageUrl;
  final String? url;
  final List<ApiRecipeIngredient> ingredients;
  final List<ApiCookingStep> steps;
  final int cookingTimeMinutes;
  final int servings;
  final String difficulty;
  final String category;
  final double rating;
  final int reviewCount;
  final bool isPopular;
  final bool isActive;
  final DateTime createdAt;
  final DateTime updatedAt;

  const ApiRecipe({
    required this.id,
    required this.name,
    required this.description,
    this.imageUrl,
    this.url,
    required this.ingredients,
    required this.steps,
    required this.cookingTimeMinutes,
    required this.servings,
    required this.difficulty,
    required this.category,
    required this.rating,
    required this.reviewCount,
    required this.isPopular,
    required this.isActive,
    required this.createdAt,
    required this.updatedAt,
  });

  /// JSON에서 생성
  factory ApiRecipe.fromJson(Map<String, dynamic> json) {
    return ApiRecipe(
      id: json['recipe_id']?.toString() ?? json['id'] ?? '',
      name: json['title'] ?? json['name'] ?? '',
      description: json['description'] ?? '',
      imageUrl: json['image_url'] ?? json['imageUrl'],
      url: json['url'],
      ingredients: (json['ingredients'] as List?)
          ?.map((e) => ApiRecipeIngredient.fromJson(e))
          .toList() ?? [],
      steps: (json['steps'] as List?)
          ?.map((e) => ApiCookingStep.fromJson(e))
          .toList() ?? [],
      cookingTimeMinutes: json['cooking_time_minutes'] ?? json['cookingTimeMinutes'] ?? 0,
      servings: json['servings'] ?? 1,
      difficulty: json['difficulty'] ?? 'easy',
      category: json['category'] ?? 'stew',
      rating: (json['rating'] ?? 0.0).toDouble(),
      reviewCount: json['review_count'] ?? json['reviewCount'] ?? 0,
      isPopular: json['is_popular'] ?? json['isPopular'] ?? false,
      isActive: json['is_active'] ?? json['isActive'] ?? true,
      createdAt: DateTime.tryParse(json['created_at'] ?? json['createdAt'] ?? '') ?? DateTime.now(),
      updatedAt: DateTime.tryParse(json['updated_at'] ?? json['updatedAt'] ?? '') ?? DateTime.now(),
    );
  }

  /// JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'image_url': imageUrl,
      'url': url,
      'ingredients': ingredients.map((e) => e.toJson()).toList(),
      'steps': steps.map((e) => e.toJson()).toList(),
      'cooking_time_minutes': cookingTimeMinutes,
      'servings': servings,
      'difficulty': difficulty,
      'category': category,
      'rating': rating,
      'review_count': reviewCount,
      'is_popular': isPopular,
      'is_active': isActive,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  /// 기존 Recipe 모델로 변환 (호환성)
  Recipe toRecipe() {
    return Recipe(
      id: id,
      name: name,
      description: description,
      imageUrl: imageUrl ?? 'https://picsum.photos/400/300?random=$id',
      ingredients: ingredients.map((e) => e.toIngredient()).toList(),
      steps: steps.map((e) => e.toCookingStep()).toList(),
      cookingTimeMinutes: cookingTimeMinutes,
      servings: servings,
      difficulty: _parseDifficulty(difficulty),
      category: _parseCategory(category),
      rating: rating,
      reviewCount: reviewCount,
      isPopular: isPopular,
    );
  }

  /// Difficulty 열거형 파싱
  Difficulty _parseDifficulty(String difficulty) {
    switch (difficulty.toLowerCase()) {
      case 'easy':
      case '쉬움':
        return Difficulty.easy;
      case 'medium':
      case '보통':
        return Difficulty.medium;
      case 'hard':
      case '어려움':
        return Difficulty.hard;
      default:
        return Difficulty.easy;
    }
  }

  /// RecipeCategory 열거형 파싱
  RecipeCategory _parseCategory(String category) {
    switch (category.toLowerCase()) {
      case 'stew':
      case '찌개':
      case '국':
        return RecipeCategory.stew;
      case 'stirfry':
      case '볶음':
      case '구이':
        return RecipeCategory.stirFry;
      case 'sidedish':
      case '밑반찬':
        return RecipeCategory.sideDish;
      case 'rice':
      case '밥':
      case '덮밥':
        return RecipeCategory.rice;
      case 'kimchi':
      case '김치':
      case '젓갈':
        return RecipeCategory.kimchi;
      case 'soup':
      case '탕':
      case '전골':
        return RecipeCategory.soup;
      case 'noodles':
      case '면':
      case '국수':
        return RecipeCategory.noodles;
      default:
        return RecipeCategory.stew;
    }
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is ApiRecipe && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() {
    return 'ApiRecipe(id: $id, name: $name, category: $category)';
  }
}

/// API 레시피 재료 모델
class ApiRecipeIngredient {
  final String ingredientId;
  final String name;
  final String amount;
  final String? unit;
  final bool isEssential;

  const ApiRecipeIngredient({
    required this.ingredientId,
    required this.name,
    required this.amount,
    this.unit,
    required this.isEssential,
  });

  /// JSON에서 생성
  factory ApiRecipeIngredient.fromJson(Map<String, dynamic> json) {
    return ApiRecipeIngredient(
      ingredientId: json['ingredient_id'] ?? json['ingredientId'] ?? '',
      name: json['name'] ?? '',
      amount: json['amount'] ?? '',
      unit: json['unit'],
      isEssential: json['is_essential'] ?? json['isEssential'] ?? true,
    );
  }

  /// JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'ingredient_id': ingredientId,
      'name': name,
      'amount': amount,
      'unit': unit,
      'is_essential': isEssential,
    };
  }

  /// 기존 Ingredient 모델로 변환
  Ingredient toIngredient() {
    return Ingredient(
      name: name,
      amount: unit != null ? '$amount $unit' : amount,
      isEssential: isEssential,
    );
  }
}

/// API 조리 단계 모델
class ApiCookingStep {
  final int stepNumber;
  final String description;
  final String? imageUrl;
  final int? durationMinutes;

  const ApiCookingStep({
    required this.stepNumber,
    required this.description,
    this.imageUrl,
    this.durationMinutes,
  });

  /// JSON에서 생성
  factory ApiCookingStep.fromJson(Map<String, dynamic> json) {
    return ApiCookingStep(
      stepNumber: json['step_number'] ?? json['stepNumber'] ?? 0,
      description: json['description'] ?? '',
      imageUrl: json['image_url'] ?? json['imageUrl'],
      durationMinutes: json['duration_minutes'] ?? json['durationMinutes'],
    );
  }

  /// JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'step_number': stepNumber,
      'description': description,
      'image_url': imageUrl,
      'duration_minutes': durationMinutes,
    };
  }

  /// 기존 CookingStep 모델로 변환
  CookingStep toCookingStep() {
    return CookingStep(
      stepNumber: stepNumber,
      description: description,
      imageUrl: imageUrl,
      durationMinutes: durationMinutes,
    );
  }
}

/// 레시피 검색 필터
class RecipeSearchFilter {
  final String? search;
  final String? category;
  final String? difficulty;
  final int? maxCookingTime;
  final int? maxServings;
  final bool? isPopular;
  final bool? isActive;
  final int page;
  final int size;

  const RecipeSearchFilter({
    this.search,
    this.category,
    this.difficulty,
    this.maxCookingTime,
    this.maxServings,
    this.isPopular,
    this.isActive,
    this.page = 1,
    this.size = 10,
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
      params['category'] = category;
    }

    if (difficulty != null) {
      params['difficulty'] = difficulty;
    }

    if (maxCookingTime != null) {
      params['max_cooking_time'] = maxCookingTime;
    }

    if (maxServings != null) {
      params['max_servings'] = maxServings;
    }

    if (isPopular != null) {
      params['is_popular'] = isPopular;
    }

    if (isActive != null) {
      params['is_active'] = isActive;
    }

    return params;
  }

  /// 복사본 생성
  RecipeSearchFilter copyWith({
    String? search,
    String? category,
    String? difficulty,
    int? maxCookingTime,
    int? maxServings,
    bool? isPopular,
    bool? isActive,
    int? page,
    int? size,
  }) {
    return RecipeSearchFilter(
      search: search ?? this.search,
      category: category ?? this.category,
      difficulty: difficulty ?? this.difficulty,
      maxCookingTime: maxCookingTime ?? this.maxCookingTime,
      maxServings: maxServings ?? this.maxServings,
      isPopular: isPopular ?? this.isPopular,
      isActive: isActive ?? this.isActive,
      page: page ?? this.page,
      size: size ?? this.size,
    );
  }

  @override
  String toString() {
    return 'RecipeSearchFilter(search: $search, category: $category, page: $page, size: $size)';
  }
}

/// 레시피 추천 응답 모델
class RecipeRecommendation {
  final String recipeSno;
  final String name;
  final String title;
  final String? servings;
  final String? difficulty;
  final String? cookingTime;
  final String? imageUrl;
  final String? recipeUrl;
  final String? introduction;
  final double matchScore;
  final int matchedCount;
  final int totalCount;
  final String algorithm;

  const RecipeRecommendation({
    required this.recipeSno,
    required this.name,
    required this.title,
    this.servings,
    this.difficulty,
    this.cookingTime,
    this.imageUrl,
    this.recipeUrl,
    this.introduction,
    required this.matchScore,
    required this.matchedCount,
    required this.totalCount,
    required this.algorithm,
  });

  /// 매칭 퍼센트 계산 (matchScore를 퍼센트로 변환)
  int? get matchPercentage {
    if (matchScore <= 0) return null;
    return (matchScore * 100).round();
  }

  factory RecipeRecommendation.fromJson(Map<String, dynamic> json) {
    return RecipeRecommendation(
      recipeSno: json['recipe_sno']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      servings: json['servings']?.toString(),
      difficulty: json['difficulty']?.toString(),
      cookingTime: json['cooking_time']?.toString(),
      imageUrl: json['image_url']?.toString(),
      recipeUrl: json['recipe_url']?.toString(),
      introduction: json['introduction']?.toString(),
      matchScore: (json['match_score'] as num?)?.toDouble() ?? 0.0,
      matchedCount: json['matched_count'] as int? ?? 0,
      totalCount: json['total_count'] as int? ?? 0,
      algorithm: json['algorithm']?.toString() ?? 'jaccard',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'recipe_sno': recipeSno,
      'name': name,
      'title': title,
      'servings': servings,
      'difficulty': difficulty,
      'cooking_time': cookingTime,
      'image_url': imageUrl,
      'recipe_url': recipeUrl,
      'introduction': introduction,
      'match_score': matchScore,
      'matched_count': matchedCount,
      'total_count': totalCount,
      'algorithm': algorithm,
    };
  }
}

/// 레시피 추천 응답 모델
class RecipeRecommendationsResponse {
  final List<RecipeRecommendation> recipes;
  final int total;
  final String algorithm;
  final String summary;

  const RecipeRecommendationsResponse({
    required this.recipes,
    required this.total,
    required this.algorithm,
    required this.summary,
  });

  factory RecipeRecommendationsResponse.fromJson(Map<String, dynamic> json) {
    return RecipeRecommendationsResponse(
      recipes: (json['recipes'] as List<dynamic>?)
              ?.map((item) => RecipeRecommendation.fromJson(item as Map<String, dynamic>))
              .toList() ??
          [],
      total: json['total'] as int? ?? 0,
      algorithm: json['algorithm']?.toString() ?? 'jaccard',
      summary: json['summary']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'recipes': recipes.map((r) => r.toJson()).toList(),
      'total': total,
      'algorithm': algorithm,
      'summary': summary,
    };
  }
}
