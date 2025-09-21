/// 한식 레시피 데이터 모델
class Recipe {
  final String id;
  final String name;
  final String description;
  final String imageUrl;
  final List<Ingredient> ingredients;
  final List<CookingStep> steps;
  final int cookingTimeMinutes;
  final int servings;
  final Difficulty difficulty;
  final RecipeCategory category;
  final double rating;
  final int reviewCount;
  final bool isPopular;

  const Recipe({
    required this.id,
    required this.name,
    required this.description,
    required this.imageUrl,
    required this.ingredients,
    required this.steps,
    required this.cookingTimeMinutes,
    required this.servings,
    required this.difficulty,
    required this.category,
    this.rating = 0.0,
    this.reviewCount = 0,
    this.isPopular = false,
  });

  /// 사용자가 보유한 재료와의 매칭율 계산
  double calculateMatchingRate(List<String> userIngredients) {
    if (ingredients.isEmpty) return 0.0;
    
    int matchCount = 0;
    for (final ingredient in ingredients) {
      if (userIngredients.any((userIngredient) => 
          userIngredient.toLowerCase().contains(ingredient.name.toLowerCase()) ||
          ingredient.name.toLowerCase().contains(userIngredient.toLowerCase()))) {
        matchCount++;
      }
    }
    
    return (matchCount / ingredients.length) * 100;
  }

  /// 부족한 재료 목록 반환
  List<Ingredient> getMissingIngredients(List<String> userIngredients) {
    return ingredients.where((ingredient) {
      return !userIngredients.any((userIngredient) => 
          userIngredient.toLowerCase().contains(ingredient.name.toLowerCase()) ||
          ingredient.name.toLowerCase().contains(userIngredient.toLowerCase()));
    }).toList();
  }

  /// 보유한 재료 목록 반환
  List<Ingredient> getAvailableIngredients(List<String> userIngredients) {
    return ingredients.where((ingredient) {
      return userIngredients.any((userIngredient) => 
          userIngredient.toLowerCase().contains(ingredient.name.toLowerCase()) ||
          ingredient.name.toLowerCase().contains(userIngredient.toLowerCase()));
    }).toList();
  }

  /// 보유하지 않은 재료 목록 반환
  List<Ingredient> getUnavailableIngredients(List<String> userIngredients) {
    return ingredients.where((ingredient) {
      return !userIngredients.any((userIngredient) => 
          userIngredient.toLowerCase().contains(ingredient.name.toLowerCase()) ||
          ingredient.name.toLowerCase().contains(userIngredient.toLowerCase()));
    }).toList();
  }

  /// JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'imageUrl': imageUrl,
      'ingredients': ingredients.map((e) => e.toJson()).toList(),
      'steps': steps.map((e) => e.toJson()).toList(),
      'cookingTimeMinutes': cookingTimeMinutes,
      'servings': servings,
      'difficulty': difficulty.name,
      'category': category.name,
      'rating': rating,
      'reviewCount': reviewCount,
      'isPopular': isPopular,
    };
  }

  /// JSON에서 생성
  factory Recipe.fromJson(Map<String, dynamic> json) {
    return Recipe(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      imageUrl: json['imageUrl'],
      ingredients: (json['ingredients'] as List)
          .map((e) => Ingredient.fromJson(e))
          .toList(),
      steps: (json['steps'] as List)
          .map((e) => CookingStep.fromJson(e))
          .toList(),
      cookingTimeMinutes: json['cookingTimeMinutes'],
      servings: json['servings'],
      difficulty: Difficulty.values.firstWhere(
        (e) => e.name == json['difficulty'],
        orElse: () => Difficulty.easy,
      ),
      category: RecipeCategory.values.firstWhere(
        (e) => e.name == json['category'],
        orElse: () => RecipeCategory.stew,
      ),
      rating: json['rating']?.toDouble() ?? 0.0,
      reviewCount: json['reviewCount'] ?? 0,
      isPopular: json['isPopular'] ?? false,
    );
  }
}

/// 재료 모델
class Ingredient {
  final String name;
  final String amount;
  final bool isEssential;

  const Ingredient({
    required this.name,
    required this.amount,
    this.isEssential = true,
  });

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'amount': amount,
      'isEssential': isEssential,
    };
  }

  factory Ingredient.fromJson(Map<String, dynamic> json) {
    return Ingredient(
      name: json['name'],
      amount: json['amount'],
      isEssential: json['isEssential'] ?? true,
    );
  }
}

/// 조리 단계 모델
class CookingStep {
  final int stepNumber;
  final String description;
  final String? imageUrl;
  final int? durationMinutes;

  const CookingStep({
    required this.stepNumber,
    required this.description,
    this.imageUrl,
    this.durationMinutes,
  });

  Map<String, dynamic> toJson() {
    return {
      'stepNumber': stepNumber,
      'description': description,
      'imageUrl': imageUrl,
      'durationMinutes': durationMinutes,
    };
  }

  factory CookingStep.fromJson(Map<String, dynamic> json) {
    return CookingStep(
      stepNumber: json['stepNumber'],
      description: json['description'],
      imageUrl: json['imageUrl'],
      durationMinutes: json['durationMinutes'],
    );
  }
}

/// 난이도 열거형
enum Difficulty {
  easy('하'),
  medium('중'),
  hard('상');

  const Difficulty(this.displayName);
  final String displayName;
}

/// 레시피 카테고리 열거형
enum RecipeCategory {
  stew('찌개/국'),
  stirFry('볶음/구이'),
  sideDish('밑반찬'),
  rice('밥/덮밥'),
  kimchi('김치/젓갈'),
  soup('탕/전골'),
  noodles('면/국수');

  const RecipeCategory(this.displayName);
  final String displayName;
}

/// 정렬 옵션 열거형
enum SortOption {
  matchingRate('매칭율 높은 순'),
  popularity('인기순'),
  cookingTime('조리시간 짧은 순'),
  rating('평점 높은 순');

  const SortOption(this.displayName);
  final String displayName;
}
