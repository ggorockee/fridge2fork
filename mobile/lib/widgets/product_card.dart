import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../theme/app_theme.dart';

/// 상품 카드 위젯
/// Figma 디자인의 "Honey lime combo", "Berry mango combo" 등의 상품 카드 스타일 구현
class ProductCard extends StatelessWidget {
  final String name;
  final String price;
  final String? imageUrl;
  final Color backgroundColor;
  final VoidCallback? onTap;
  final VoidCallback? onAddToCart;
  final bool isRecommended;
  final double? width;
  final double? height;

  const ProductCard({
    super.key,
    required this.name,
    required this.price,
    this.imageUrl,
    this.backgroundColor = Colors.white,
    this.onTap,
    this.onAddToCart,
    this.isRecommended = false,
    this.width,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: width?.w ?? 152.w,
        height: height?.h ?? 183.h,
        decoration: AppTheme.cardDecoration(
          backgroundColor: backgroundColor,
          radius: AppTheme.radiusCard,
        ),
        child: Padding(
          padding: const EdgeInsets.all(AppTheme.spacingM),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 상품 이미지
              Expanded(
                child: Center(
                  child: Container(
                    width: 80.w,
                    height: 80.h,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                      color: AppTheme.backgroundGray,
                    ),
                    child: imageUrl != null
                        ? ClipRRect(
                            borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                            child: Image.network(
                              imageUrl!,
                              fit: BoxFit.cover,
                              errorBuilder: (context, error, stackTrace) {
                                return Image.network(
                                  'https://picsum.photos/200/200?random=${name.hashCode.abs() % 1000}',
                                  fit: BoxFit.cover,
                                );
                              },
                            ),
                          )
                        : ClipRRect(
                            borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                            child: Image.network(
                              'https://picsum.photos/200/200?random=${name.hashCode.abs() % 1000}',
                              fit: BoxFit.cover,
                            ),
                          ),
                  ),
                ),
              ),
              
              const SizedBox(height: AppTheme.spacingS),
              
              // 상품명
              Text(
                name,
                style: AppTheme.bodyMedium,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              
              const SizedBox(height: AppTheme.spacingXS),
              
              // 가격과 장바구니 버튼
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // 가격
                  Row(
                    children: [
                      Icon(
                        Icons.currency_exchange,
                        size: 16.sp,
                        color: AppTheme.darkOrange,
                      ),
                      SizedBox(width: 4.w),
                      Text(
                        price,
                        style: AppTheme.bodySmall.copyWith(
                          color: AppTheme.darkOrange,
                        ),
                      ),
                    ],
                  ),
                  
                  // 장바구니 추가 버튼
                  GestureDetector(
                    onTap: onAddToCart,
                    child: Container(
                      width: 24.w,
                      height: 24.h,
                      decoration: const BoxDecoration(
                        color: AppTheme.lightOrange,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        Icons.add,
                        size: 16.sp,
                        color: AppTheme.primaryOrange,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// 가로형 상품 카드 위젯
/// Figma 디자인의 "Quinoa fruit salad", "Tropical fruit salad" 등의 가로형 카드 스타일 구현
class HorizontalProductCard extends StatelessWidget {
  final String name;
  final String price;
  final String? subtitle;
  final String? imageUrl;
  final Color backgroundColor;
  final VoidCallback? onTap;
  final VoidCallback? onAddToCart;
  final VoidCallback? onRemove;
  final int quantity;

  const HorizontalProductCard({
    super.key,
    required this.name,
    required this.price,
    this.subtitle,
    this.imageUrl,
    this.backgroundColor = Colors.white,
    this.onTap,
    this.onAddToCart,
    this.onRemove,
    this.quantity = 1,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 80.h,
        decoration: AppTheme.cardDecoration(
          backgroundColor: backgroundColor,
          radius: AppTheme.radiusSmall,
        ),
        child: Padding(
          padding: const EdgeInsets.all(AppTheme.spacingM),
          child: Row(
            children: [
              // 상품 이미지
              Container(
                width: 64.w,
                height: 64.h,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                  color: AppTheme.backgroundGray,
                ),
                child: imageUrl != null
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                        child: Image.network(
                          imageUrl!,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) {
                            return Image.network(
                              'https://picsum.photos/300/200?random=${name.hashCode.abs() % 1000}',
                              fit: BoxFit.cover,
                            );
                          },
                        ),
                      )
                    : Icon(
                        Icons.fastfood,
                        color: AppTheme.textGray,
                        size: 24.sp,
                      ),
              ),
              
              const SizedBox(width: AppTheme.spacingM),
              
              // 상품 정보
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      name,
                      style: AppTheme.bodyMedium,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (subtitle != null) ...[
                      SizedBox(height: 2.h),
                      Text(
                        subtitle!,
                        style: AppTheme.bodySmall,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ],
                ),
              ),
              
              const SizedBox(width: AppTheme.spacingM),
              
              // 가격
              Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.currency_exchange,
                        size: 16.sp,
                        color: AppTheme.iconPrimary,
                      ),
                      SizedBox(width: 4.w),
                      Text(
                        price,
                        style: AppTheme.bodyMedium,
                      ),
                    ],
                  ),
                  if (quantity > 1) ...[
                    SizedBox(height: 2.h),
                    Text(
                      '수량: $quantity',
                      style: AppTheme.bodySmall.copyWith(
                        color: AppTheme.textPrimary,
                      ),
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// 큰 상품 카드 위젯
/// Figma 디자인의 "Quinoa fruit salad", "Tropical fruit salad" 등의 큰 카드 스타일 구현
class LargeProductCard extends StatelessWidget {
  final String name;
  final String price;
  final String? imageUrl;
  final Color backgroundColor;
  final VoidCallback? onTap;
  final double? width;
  final double? height;

  const LargeProductCard({
    super.key,
    required this.name,
    required this.price,
    this.imageUrl,
    this.backgroundColor = Colors.white,
    this.onTap,
    this.width,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: width?.w ?? 140.w,
        height: height?.h ?? 150.h,
        decoration: AppTheme.cardDecoration(
          backgroundColor: backgroundColor,
          radius: AppTheme.radiusSmall,
        ),
        child: Padding(
          padding: const EdgeInsets.all(AppTheme.spacingM),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 상품 이미지
              Expanded(
                child: Center(
                  child: Container(
                    width: 64.w,
                    height: 64.h,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                      color: AppTheme.backgroundGray,
                    ),
                    child: imageUrl != null
                        ? ClipRRect(
                            borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                            child: Image.network(
                              imageUrl!,
                              fit: BoxFit.cover,
                              errorBuilder: (context, error, stackTrace) {
                                return Image.network(
                                  'https://picsum.photos/400/300?random=${name.hashCode.abs() % 1000}',
                                  fit: BoxFit.cover,
                                );
                              },
                            ),
                          )
                        : Icon(
                            Icons.fastfood,
                            color: AppTheme.textGray,
                            size: 32.sp,
                          ),
                  ),
                ),
              ),
              
              const SizedBox(height: AppTheme.spacingS),
              
              // 상품명
              Text(
                name,
                style: AppTheme.bodyMedium,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              
              const SizedBox(height: AppTheme.spacingXS),
              
              // 가격
              Row(
                children: [
                  Icon(
                    Icons.currency_exchange,
                    size: 16.sp,
                    color: AppTheme.darkOrange,
                  ),
                  SizedBox(width: 4.w),
                  Text(
                    price,
                    style: AppTheme.bodyMedium.copyWith(
                      color: AppTheme.darkOrange,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
