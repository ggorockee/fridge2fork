/// 상품 데이터 모델
/// Figma 디자인의 과일 샐러드 상품들을 위한 데이터 구조
class Product {
  final String id;
  final String name;
  final String description;
  final double price;
  final String? imageUrl;
  final ProductCategory category;
  final List<String> ingredients;
  final double rating;
  final int reviewCount;
  final bool isRecommended;
  final bool isPopular;
  final bool isNew;
  final ProductColor backgroundColor;

  const Product({
    required this.id,
    required this.name,
    required this.description,
    required this.price,
    this.imageUrl,
    required this.category,
    this.ingredients = const [],
    this.rating = 0.0,
    this.reviewCount = 0,
    this.isRecommended = false,
    this.isPopular = false,
    this.isNew = false,
    this.backgroundColor = ProductColor.white,
  });

  /// 가격을 형식화된 문자열로 반환
  String get formattedPrice => price.toInt().toString();

  /// 재료 목록을 쉼표로 구분된 문자열로 반환
  String get ingredientsString => ingredients.join(', ');

  /// JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'price': price,
      'imageUrl': imageUrl,
      'category': category.name,
      'ingredients': ingredients,
      'rating': rating,
      'reviewCount': reviewCount,
      'isRecommended': isRecommended,
      'isPopular': isPopular,
      'isNew': isNew,
      'backgroundColor': backgroundColor.name,
    };
  }

  /// JSON에서 생성
  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      price: json['price'].toDouble(),
      imageUrl: json['imageUrl'],
      category: ProductCategory.values.firstWhere(
        (e) => e.name == json['category'],
        orElse: () => ProductCategory.salad,
      ),
      ingredients: List<String>.from(json['ingredients'] ?? []),
      rating: json['rating']?.toDouble() ?? 0.0,
      reviewCount: json['reviewCount'] ?? 0,
      isRecommended: json['isRecommended'] ?? false,
      isPopular: json['isPopular'] ?? false,
      isNew: json['isNew'] ?? false,
      backgroundColor: ProductColor.values.firstWhere(
        (e) => e.name == json['backgroundColor'],
        orElse: () => ProductColor.white,
      ),
    );
  }

  /// 복사본 생성
  Product copyWith({
    String? id,
    String? name,
    String? description,
    double? price,
    String? imageUrl,
    ProductCategory? category,
    List<String>? ingredients,
    double? rating,
    int? reviewCount,
    bool? isRecommended,
    bool? isPopular,
    bool? isNew,
    ProductColor? backgroundColor,
  }) {
    return Product(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      price: price ?? this.price,
      imageUrl: imageUrl ?? this.imageUrl,
      category: category ?? this.category,
      ingredients: ingredients ?? this.ingredients,
      rating: rating ?? this.rating,
      reviewCount: reviewCount ?? this.reviewCount,
      isRecommended: isRecommended ?? this.isRecommended,
      isPopular: isPopular ?? this.isPopular,
      isNew: isNew ?? this.isNew,
      backgroundColor: backgroundColor ?? this.backgroundColor,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Product && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;
}

/// 상품 카테고리
enum ProductCategory {
  salad('샐러드'),
  juice('주스'),
  smoothie('스무디'),
  combo('콤보');

  const ProductCategory(this.displayName);
  final String displayName;
}

/// 상품 배경색 (Figma 디자인 기반)
enum ProductColor {
  white('흰색'),
  yellow('노란색'),
  pink('분홍색'),
  purple('보라색'),
  green('초록색'),
  mint('민트색');

  const ProductColor(this.displayName);
  final String displayName;
}

/// 장바구니 아이템 모델
class CartItem {
  final Product product;
  final int quantity;
  final DateTime addedAt;

  const CartItem({
    required this.product,
    required this.quantity,
    required this.addedAt,
  });

  /// 총 가격 계산
  double get totalPrice => product.price * quantity;

  /// 형식화된 총 가격
  String get formattedTotalPrice => totalPrice.toInt().toString();

  /// JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'product': product.toJson(),
      'quantity': quantity,
      'addedAt': addedAt.toIso8601String(),
    };
  }

  /// JSON에서 생성
  factory CartItem.fromJson(Map<String, dynamic> json) {
    return CartItem(
      product: Product.fromJson(json['product']),
      quantity: json['quantity'],
      addedAt: DateTime.parse(json['addedAt']),
    );
  }

  /// 복사본 생성
  CartItem copyWith({
    Product? product,
    int? quantity,
    DateTime? addedAt,
  }) {
    return CartItem(
      product: product ?? this.product,
      quantity: quantity ?? this.quantity,
      addedAt: addedAt ?? this.addedAt,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is CartItem && other.product.id == product.id;
  }

  @override
  int get hashCode => product.id.hashCode;
}
