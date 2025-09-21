import '../models/product.dart';
import '../theme/app_theme.dart';
import 'package:flutter/material.dart';

/// 샘플 데이터 서비스
/// Figma 디자인의 상품들을 기반으로 한 더미 데이터 제공
class SampleDataService {
  /// Figma 디자인의 추천 상품들
  static List<Product> get recommendedProducts => [
    const Product(
      id: 'honey_lime_combo',
      name: 'Honey lime combo',
      description: 'Red Quinoa, Lime, Honey, Blueberries, Strawberries, Mango, Fresh mint.',
      price: 2000,
      category: ProductCategory.combo,
      ingredients: ['Red Quinoa', 'Lime', 'Honey', 'Blueberries', 'Strawberries', 'Mango', 'Fresh mint'],
      rating: 4.5,
      reviewCount: 23,
      isRecommended: true,
      backgroundColor: ProductColor.white,
    ),
    const Product(
      id: 'berry_mango_combo',
      name: 'Berry mango combo',
      description: 'Fresh berries mixed with sweet mango pieces for a perfect balance.',
      price: 8000,
      category: ProductCategory.combo,
      ingredients: ['Mixed Berries', 'Mango', 'Yogurt', 'Honey'],
      rating: 4.7,
      reviewCount: 45,
      isRecommended: true,
      backgroundColor: ProductColor.white,
    ),
  ];

  /// Figma 디자인의 인기 상품들
  static List<Product> get popularProducts => [
    const Product(
      id: 'quinoa_fruit_salad',
      name: 'Quinoa fruit salad',
      description: 'If you are looking for a new fruit salad to eat today, quinoa is the perfect brunch for you.',
      price: 10000,
      category: ProductCategory.salad,
      ingredients: ['Red Quinoa', 'Lime', 'Honey', 'Blueberries', 'Strawberries', 'Mango', 'Fresh mint'],
      rating: 4.8,
      reviewCount: 67,
      isPopular: true,
      backgroundColor: ProductColor.yellow,
    ),
    const Product(
      id: 'tropical_fruit_salad',
      name: 'Tropical fruit salad',
      description: 'A refreshing mix of tropical fruits perfect for hot summer days.',
      price: 10000,
      category: ProductCategory.salad,
      ingredients: ['Pineapple', 'Mango', 'Papaya', 'Coconut', 'Lime'],
      rating: 4.6,
      reviewCount: 34,
      isPopular: true,
      backgroundColor: ProductColor.pink,
    ),
    const Product(
      id: 'melon_fruit_salad',
      name: 'Melon fruit salad',
      description: 'Sweet and juicy melon pieces with a hint of mint.',
      price: 10000,
      category: ProductCategory.salad,
      ingredients: ['Watermelon', 'Cantaloupe', 'Honeydew', 'Fresh mint'],
      rating: 4.4,
      reviewCount: 28,
      isPopular: true,
      backgroundColor: ProductColor.purple,
    ),
  ];

  /// 모든 상품 목록
  static List<Product> get allProducts => [
    ...recommendedProducts,
    ...popularProducts,
    // 추가 상품들
    const Product(
      id: 'green_smoothie',
      name: 'Green Smoothie',
      description: 'Healthy green smoothie with spinach, apple, and banana.',
      price: 6500,
      category: ProductCategory.smoothie,
      ingredients: ['Spinach', 'Apple', 'Banana', 'Yogurt', 'Honey'],
      rating: 4.3,
      reviewCount: 19,
      isNew: true,
      backgroundColor: ProductColor.green,
    ),
    const Product(
      id: 'berry_juice',
      name: 'Mixed Berry Juice',
      description: 'Fresh mixed berry juice packed with antioxidants.',
      price: 5500,
      category: ProductCategory.juice,
      ingredients: ['Strawberries', 'Blueberries', 'Raspberries', 'Apple juice'],
      rating: 4.2,
      reviewCount: 12,
      isNew: true,
      backgroundColor: ProductColor.mint,
    ),
  ];

  /// 카테고리 목록
  static List<String> get categories => [
    'Hottest',
    'Popular', 
    'New combo',
    'Top',
  ];

  /// 카테고리별 상품 필터링
  static List<Product> getProductsByCategory(String category) {
    switch (category.toLowerCase()) {
      case 'hottest':
        return allProducts.where((p) => p.isRecommended).toList();
      case 'popular':
        return allProducts.where((p) => p.isPopular).toList();
      case 'new combo':
        return allProducts.where((p) => p.isNew).toList();
      case 'top':
        return allProducts
            .where((p) => p.rating >= 4.5)
            .toList()
            ..sort((a, b) => b.rating.compareTo(a.rating));
      default:
        return allProducts;
    }
  }

  /// 상품 ID로 상품 찾기
  static Product? getProductById(String id) {
    try {
      return allProducts.firstWhere((product) => product.id == id);
    } catch (e) {
      return null;
    }
  }

  /// 상품 검색
  static List<Product> searchProducts(String query) {
    if (query.isEmpty) return allProducts;
    
    final lowercaseQuery = query.toLowerCase();
    return allProducts.where((product) {
      return product.name.toLowerCase().contains(lowercaseQuery) ||
             product.description.toLowerCase().contains(lowercaseQuery) ||
             product.ingredients.any((ingredient) => 
                 ingredient.toLowerCase().contains(lowercaseQuery));
    }).toList();
  }

  /// ProductColor를 Flutter Color로 변환
  static Color getFlutterColor(ProductColor productColor) {
    switch (productColor) {
      case ProductColor.white:
        return Colors.white;
      case ProductColor.yellow:
        return AppTheme.cardYellow;
      case ProductColor.pink:
        return AppTheme.cardPink;
      case ProductColor.purple:
        return AppTheme.cardPurple;
      case ProductColor.green:
        return AppTheme.cardGreen;
      case ProductColor.mint:
        return AppTheme.cardMint;
    }
  }

  /// 장바구니 샘플 데이터
  static List<CartItem> get sampleCartItems => [
    CartItem(
      product: getProductById('quinoa_fruit_salad')!,
      quantity: 2,
      addedAt: DateTime.now().subtract(const Duration(minutes: 5)),
    ),
    CartItem(
      product: getProductById('tropical_fruit_salad')!,
      quantity: 2,
      addedAt: DateTime.now().subtract(const Duration(minutes: 10)),
    ),
    CartItem(
      product: getProductById('melon_fruit_salad')!,
      quantity: 2,
      addedAt: DateTime.now().subtract(const Duration(minutes: 15)),
    ),
  ];

  /// 총 장바구니 금액 계산
  static double calculateCartTotal(List<CartItem> cartItems) {
    return cartItems.fold(0.0, (total, item) => total + item.totalPrice);
  }

  /// 형식화된 총 금액
  static String getFormattedCartTotal(List<CartItem> cartItems) {
    return calculateCartTotal(cartItems).toInt().toString();
  }
}
