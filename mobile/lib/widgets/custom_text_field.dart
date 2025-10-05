import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../theme/app_theme.dart';

/// 커스텀 텍스트 필드 위젯
/// Figma 디자인의 입력 필드들 (이름 입력, 주소 입력, 카드 정보 등) 스타일 구현
class CustomTextField extends StatelessWidget {
  final String? hintText;
  final String? labelText;
  final TextEditingController? controller;
  final TextInputType keyboardType;
  final bool obscureText;
  final Widget? prefixIcon;
  final Widget? suffixIcon;
  final String? Function(String?)? validator;
  final void Function(String)? onChanged;
  final void Function(String)? onSubmitted;
  final int maxLines;
  final bool enabled;
  final Color? backgroundColor;

  const CustomTextField({
    super.key,
    this.hintText,
    this.labelText,
    this.controller,
    this.keyboardType = TextInputType.text,
    this.obscureText = false,
    this.prefixIcon,
    this.suffixIcon,
    this.validator,
    this.onChanged,
    this.onSubmitted,
    this.maxLines = 1,
    this.enabled = true,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (labelText != null) ...[
          Text(
            labelText!,
            style: AppTheme.headingSmall,
          ),
          SizedBox(height: AppTheme.spacingS),
        ],
        TextFormField(
          controller: controller,
          keyboardType: keyboardType,
          obscureText: obscureText,
          validator: validator,
          onChanged: onChanged,
          onFieldSubmitted: onSubmitted,
          maxLines: maxLines,
          enabled: enabled,
          style: TextStyle(
            fontFamily: 'Brandon Grotesque',
            fontSize: 20.sp,
            fontWeight: FontWeight.w400,
            letterSpacing: -0.2,
            color: AppTheme.textPrimary,
          ),
          decoration: InputDecoration(
            hintText: hintText,
            filled: true,
            fillColor: backgroundColor ?? AppTheme.inputBackground,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AppTheme.radiusButton),
              borderSide: BorderSide.none,
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AppTheme.radiusButton),
              borderSide: BorderSide.none,
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AppTheme.radiusButton),
              borderSide: BorderSide(
                color: AppTheme.primaryOrange,
                width: 2.w,
              ),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AppTheme.radiusButton),
              borderSide: BorderSide(
                color: Colors.red,
                width: 2.w,
              ),
            ),
            contentPadding: EdgeInsets.symmetric(
              horizontal: AppTheme.spacingL,
              vertical: AppTheme.spacingM,
            ),
            prefixIcon: prefixIcon,
            suffixIcon: suffixIcon,
            hintStyle: TextStyle(
              fontFamily: 'Brandon Grotesque',
              fontSize: 20.sp,
              fontWeight: FontWeight.w400,
              letterSpacing: -0.2,
              color: AppTheme.textPlaceholder,
            ),
          ),
        ),
      ],
    );
  }
}

/// 검색 텍스트 필드 위젯
/// Figma 디자인의 "Search for fruit salad combos" 스타일 구현
class SearchTextField extends StatelessWidget {
  final String? hintText;
  final TextEditingController? controller;
  final void Function(String)? onChanged;
  final void Function(String)? onSubmitted;
  final VoidCallback? onFilterTap;

  const SearchTextField({
    super.key,
    this.hintText,
    this.controller,
    this.onChanged,
    this.onSubmitted,
    this.onFilterTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 56.h,
      decoration: BoxDecoration(
        color: AppTheme.backgroundGray,
        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              onChanged: onChanged,
              onSubmitted: onSubmitted,
              style: TextStyle(
                fontFamily: 'Brandon Grotesque',
                fontSize: 14.sp,
                fontWeight: FontWeight.w400,
                letterSpacing: 0,
                color: AppTheme.textPrimary,
              ),
              decoration: InputDecoration(
                hintText: hintText ?? 'Search for fruit salad combos',
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(
                  horizontal: AppTheme.spacingL,
                  vertical: AppTheme.spacingM,
                ),
                prefixIcon: Icon(
                  Icons.search,
                  color: AppTheme.textGray,
                  size: 16.sp,
                ),
                hintStyle: TextStyle(
                  fontFamily: 'Brandon Grotesque',
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w400,
                  letterSpacing: 0,
                  color: AppTheme.textSearch,
                ),
              ),
            ),
          ),
          if (onFilterTap != null) ...[
            SizedBox(width: AppTheme.spacingS),
            GestureDetector(
              onTap: onFilterTap,
              child: Container(
                width: 26.w,
                height: 17.h,
                margin: EdgeInsets.only(right: AppTheme.spacingM),
                child: Column(
                  children: [
                    Container(
                      height: 1.h,
                      color: AppTheme.textPrimary,
                    ),
                    SizedBox(height: 7.h),
                    Container(
                      height: 1.h,
                      color: AppTheme.textPrimary,
                    ),
                    SizedBox(height: 7.h),
                    Row(
                      children: [
                        Container(
                          width: 8.w,
                          height: 1.h,
                          color: AppTheme.textPrimary,
                        ),
                        SizedBox(width: 10.w),
                        Container(
                          width: 8.w,
                          height: 1.h,
                          color: AppTheme.textPrimary,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
