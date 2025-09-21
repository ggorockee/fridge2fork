import 'package:flutter/material.dart';
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
          const SizedBox(height: AppTheme.spacingS),
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
          style: const TextStyle(
            fontFamily: 'Brandon Grotesque',
            fontSize: 20,
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
              borderSide: const BorderSide(
                color: AppTheme.primaryOrange,
                width: 2,
              ),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AppTheme.radiusButton),
              borderSide: const BorderSide(
                color: Colors.red,
                width: 2,
              ),
            ),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: AppTheme.spacingL,
              vertical: AppTheme.spacingM,
            ),
            prefixIcon: prefixIcon,
            suffixIcon: suffixIcon,
            hintStyle: const TextStyle(
              fontFamily: 'Brandon Grotesque',
              fontSize: 20,
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
      height: 56,
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
              style: const TextStyle(
                fontFamily: 'Brandon Grotesque',
                fontSize: 14,
                fontWeight: FontWeight.w400,
                letterSpacing: 0,
                color: AppTheme.textPrimary,
              ),
              decoration: InputDecoration(
                hintText: hintText ?? 'Search for fruit salad combos',
                border: InputBorder.none,
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: AppTheme.spacingL,
                  vertical: AppTheme.spacingM,
                ),
                prefixIcon: const Icon(
                  Icons.search,
                  color: AppTheme.textGray,
                  size: 16,
                ),
                hintStyle: const TextStyle(
                  fontFamily: 'Brandon Grotesque',
                  fontSize: 14,
                  fontWeight: FontWeight.w400,
                  letterSpacing: 0,
                  color: AppTheme.textSearch,
                ),
              ),
            ),
          ),
          if (onFilterTap != null) ...[
            const SizedBox(width: AppTheme.spacingS),
            GestureDetector(
              onTap: onFilterTap,
              child: Container(
                width: 26,
                height: 17,
                margin: const EdgeInsets.only(right: AppTheme.spacingM),
                child: Column(
                  children: [
                    Container(
                      height: 1,
                      color: AppTheme.textPrimary,
                    ),
                    const SizedBox(height: 7),
                    Container(
                      height: 1,
                      color: AppTheme.textPrimary,
                    ),
                    const SizedBox(height: 7),
                    Row(
                      children: [
                        Container(
                          width: 8,
                          height: 1,
                          color: AppTheme.textPrimary,
                        ),
                        const SizedBox(width: 10),
                        Container(
                          width: 8,
                          height: 1,
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
