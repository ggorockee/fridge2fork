/// 냉장고 API 모델
class ApiFridge {
  final int id;
  final List<ApiFridgeIngredient> ingredients;
  final DateTime updatedAt;

  const ApiFridge({
    required this.id,
    required this.ingredients,
    required this.updatedAt,
  });

  /// JSON에서 생성
  factory ApiFridge.fromJson(Map<String, dynamic> json) {
    return ApiFridge(
      id: json['id'] as int? ?? 0,
      ingredients: (json['ingredients'] as List?)
              ?.map((e) => ApiFridgeIngredient.fromJson(e))
              .toList() ??
          [],
      updatedAt: DateTime.tryParse(json['updated_at'] ?? '') ?? DateTime.now(),
    );
  }

  /// JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'ingredients': ingredients.map((e) => e.toJson()).toList(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  /// 재료명 목록 반환
  List<String> get ingredientNames =>
      ingredients.map((e) => e.name).toList();

  /// 복사 생성자 (Optimistic UI를 위해 필요)
  ApiFridge copyWith({
    int? id,
    List<ApiFridgeIngredient>? ingredients,
    DateTime? updatedAt,
  }) {
    return ApiFridge(
      id: id ?? this.id,
      ingredients: ingredients ?? this.ingredients,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

/// 냉장고 재료 모델
class ApiFridgeIngredient {
  final int id;
  final String name;
  final String category;
  final DateTime addedAt;

  const ApiFridgeIngredient({
    required this.id,
    required this.name,
    required this.category,
    required this.addedAt,
  });

  /// JSON에서 생성
  factory ApiFridgeIngredient.fromJson(Map<String, dynamic> json) {
    return ApiFridgeIngredient(
      id: json['id'] as int? ?? 0,
      name: json['name'] as String? ?? '',
      category: json['category'] as String? ?? '',
      addedAt: DateTime.tryParse(json['added_at'] ?? '') ?? DateTime.now(),
    );
  }

  /// JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'category': category,
      'added_at': addedAt.toIso8601String(),
    };
  }
}
