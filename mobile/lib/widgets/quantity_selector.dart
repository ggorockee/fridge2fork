import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../theme/app_theme.dart';

/// 수량 선택 위젯
/// Figma 디자인의 수량 증가/감소 버튼 스타일 구현
class QuantitySelector extends StatelessWidget {
  final int quantity;
  final Function(int) onChanged;
  final int minQuantity;
  final int maxQuantity;
  final double size;

  const QuantitySelector({
    super.key,
    required this.quantity,
    required this.onChanged,
    this.minQuantity = 1,
    this.maxQuantity = 99,
    this.size = 32,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        // 감소 버튼
        GestureDetector(
          onTap: quantity > minQuantity
              ? () => onChanged(quantity - 1)
              : null,
          child: Container(
            width: size.w,
            height: size.h,
            decoration: BoxDecoration(
              color: quantity > minQuantity
                  ? Colors.transparent
                  : AppTheme.backgroundGray,
              border: Border.all(
                color: quantity > minQuantity
                    ? AppTheme.textPrimary
                    : AppTheme.textGray,
                width: 1.w,
              ),
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.remove,
              size: (size * 0.5).sp,
              color: quantity > minQuantity
                  ? AppTheme.textPrimary
                  : AppTheme.textGray,
            ),
          ),
        ),

        SizedBox(width: AppTheme.spacingM),

        // 수량 표시
        SizedBox(
          width: size.w,
          child: Text(
            quantity.toString(),
            style: TextStyle(
              fontFamily: 'Brandon Grotesque',
              fontSize: (size * 0.75).sp,
              fontWeight: FontWeight.w400,
              letterSpacing: -0.24,
              color: AppTheme.textPrimary,
            ),
            textAlign: TextAlign.center,
          ),
        ),

        SizedBox(width: AppTheme.spacingM),

        // 증가 버튼
        GestureDetector(
          onTap: quantity < maxQuantity
              ? () => onChanged(quantity + 1)
              : null,
          child: Container(
            width: size.w,
            height: size.h,
            decoration: BoxDecoration(
              color: quantity < maxQuantity
                  ? AppTheme.lightOrange
                  : AppTheme.backgroundGray,
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.add,
              size: (size * 0.5).sp,
              color: quantity < maxQuantity
                  ? AppTheme.primaryOrange
                  : AppTheme.textGray,
            ),
          ),
        ),
      ],
    );
  }
}

/// 가격 표시 위젯
/// Figma 디자인의 가격 표시 스타일 구현 (통화 아이콘 + 가격)
class PriceDisplay extends StatelessWidget {
  final String price;
  final TextStyle? textStyle;
  final Color? iconColor;
  final double iconSize;

  const PriceDisplay({
    super.key,
    required this.price,
    this.textStyle,
    this.iconColor,
    this.iconSize = 16,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          Icons.currency_exchange,
          size: iconSize.sp,
          color: iconColor ?? AppTheme.darkOrange,
        ),
        SizedBox(width: 4.w),
        Text(
          price,
          style: textStyle ?? AppTheme.bodySmall.copyWith(
            color: AppTheme.darkOrange,
          ),
        ),
      ],
    );
  }
}

/// 평점 표시 위젯
/// 별점과 평점을 표시하는 위젯
class RatingDisplay extends StatelessWidget {
  final double rating;
  final int reviewCount;
  final double starSize;
  final Color? starColor;

  const RatingDisplay({
    super.key,
    required this.rating,
    this.reviewCount = 0,
    this.starSize = 16,
    this.starColor,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        // 별점 표시
        Row(
          children: List.generate(5, (index) {
            return Icon(
              index < rating.floor()
                  ? Icons.star
                  : index < rating
                      ? Icons.star_half
                      : Icons.star_border,
              size: starSize.sp,
              color: starColor ?? AppTheme.primaryOrange,
            );
          }),
        ),

        SizedBox(width: AppTheme.spacingXS),

        // 평점 숫자
        Text(
          rating.toStringAsFixed(1),
          style: AppTheme.bodySmall,
        ),

        // 리뷰 수
        if (reviewCount > 0) ...[
          SizedBox(width: AppTheme.spacingXS),
          Text(
            '($reviewCount)',
            style: AppTheme.bodySmall.copyWith(
              color: AppTheme.textGray,
            ),
          ),
        ],
      ],
    );
  }
}
