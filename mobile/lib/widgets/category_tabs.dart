import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../theme/app_theme.dart';

/// 카테고리 탭 위젯
/// Figma 디자인의 "Hottest", "Popular", "New combo", "Top" 등의 탭 스타일 구현
class CategoryTabs extends StatelessWidget {
  final List<String> categories;
  final int selectedIndex;
  final Function(int) onTap;
  final ScrollController? scrollController;

  const CategoryTabs({
    super.key,
    required this.categories,
    required this.selectedIndex,
    required this.onTap,
    this.scrollController,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 34.h,
      child: ListView.builder(
        controller: scrollController,
        scrollDirection: Axis.horizontal,
        padding: EdgeInsets.symmetric(horizontal: 16.w), // 고정값으로 변경 (AppTheme.spacingM=64.0으로 인한 과도한 패딩 문제 해결)
        itemCount: categories.length,
        itemBuilder: (context, index) {
          final isSelected = index == selectedIndex;
          return Padding(
            padding: EdgeInsets.only(
              right: index < categories.length - 1 ? AppTheme.spacingL : 0,
            ),
            child: GestureDetector(
              onTap: () => onTap(index),
              child: IntrinsicWidth(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      categories[index],
                      style: TextStyle(
                        fontFamily: 'Brandon Grotesque',
                        fontSize: 16.sp, // 모든 탭 동일한 크기
                        fontWeight: FontWeight.w500,
                        letterSpacing: -0.16,
                      color: isSelected
                          ? AppTheme.primaryOrange // 선택된 항목은 오렌지 색상
                          : AppTheme.textPrimary, // 비선택 항목은 진한 색상으로 시인성 향상
                      ),
                    ),
                    SizedBox(height: 4.h),
                    if (isSelected)
                      Container(
                        width: double.infinity, // 텍스트 전체 너비에 맞춤
                        height: 2.h,
                        color: AppTheme.primaryOrange,
                      ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

/// 필터 칩 위젯
/// 카테고리나 필터 옵션을 표시하는 작은 칩 스타일 구현
class CustomFilterChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback? onTap;
  final Color? selectedColor;
  final Color? unselectedColor;

  const CustomFilterChip({
    super.key,
    required this.label,
    this.isSelected = false,
    this.onTap,
    this.selectedColor,
    this.unselectedColor,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 38.h, // 고정 높이 38px로 수정
        padding: EdgeInsets.symmetric(
          horizontal: AppTheme.spacingM,
          // vertical 패딩 제거
        ),
        decoration: BoxDecoration(
          color: isSelected
              ? AppTheme.primaryOrange // 선택된 항목 primaryOrange 색상 사용
              : AppTheme.backgroundGray, // 모든 비선택 항목 통일된 회색 배경
          borderRadius: BorderRadius.circular(AppTheme.radiusButton),
          border: isSelected
              ? null
              : Border.all(
                  color: AppTheme.borderGray,
                  width: 1.w,
                ),
        ),
        child: Center( // 고정 높이 내에서 텍스트 세로 중앙정렬
          child: Text(
            label,
            style: TextStyle(
              fontFamily: 'Brandon Grotesque',
              fontSize: 16.sp, // 텍스트 크기 증가 (14 → 16)
              fontWeight: FontWeight.w600, // 폰트 굵기 증가
              letterSpacing: -0.16,
              color: isSelected
                  ? Colors.white // 선택된 텍스트 색상 #fff
                  : AppTheme.textPrimary, // 비선택 항목 시인성 향상
            ),
            textAlign: TextAlign.center, // 텍스트 가운데 정렬
            overflow: TextOverflow.ellipsis, // 텍스트 잘림 방지
            maxLines: 1, // 한 줄로 제한
          ),
        ),
      ),
    );
  }
}
