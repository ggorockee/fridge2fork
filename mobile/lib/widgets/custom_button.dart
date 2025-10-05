import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../theme/app_theme.dart';
import '../utils/responsive_utils.dart';

/// 커스텀 버튼 위젯
/// Figma 디자인의 "Let's Continue", "Start Ordering", "Add to basket" 등의 버튼 스타일 구현
class CustomButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final ButtonType type;
  final double? width;
  final double? height;
  final bool isLoading;
  final IconData? icon;

  const CustomButton({
    super.key,
    required this.text,
    this.onPressed,
    this.type = ButtonType.primary,
    this.width,
    this.height,
    this.isLoading = false,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    // 태블릿 여부에 따른 폰트 크기 조정
    final isTablet = ResponsiveUtils.isTablet(context);
    final buttonFontSize = isTablet ? 20.sp : 16.sp;
    final iconSize = isTablet ? 24.sp : 20.sp;

    return ConstrainedBox(
      constraints: BoxConstraints(
        minWidth: width?.w ?? 0,
        minHeight: height?.h ?? 56.h, // 최소 높이, 폰트 크기에 따라 자동으로 늘어남
      ),
      child: SizedBox(
        width: width?.w,
        child: ElevatedButton(
          onPressed: isLoading ? null : onPressed,
          style: _getButtonStyle(context, buttonFontSize),
          child: isLoading
              ? SizedBox(
                  width: 20.w,
                  height: 20.h,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.w,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                )
              : Row(
                  mainAxisSize: MainAxisSize.min,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (icon != null) ...[
                      Icon(icon, size: iconSize),
                      SizedBox(width: AppTheme.spacingS),
                    ],
                    Flexible(
                      child: Text(
                        text,
                        textAlign: TextAlign.center,
                        overflow: TextOverflow.ellipsis,
                        maxLines: 2, // 최대 2줄까지 허용
                      ),
                    ),
                  ],
                ),
        ),
      ),
    );
  }

  ButtonStyle _getButtonStyle(BuildContext context, double fontSize) {
    final textStyle = TextStyle(
      fontFamily: 'Brandon Grotesque',
      fontSize: fontSize,
      fontWeight: FontWeight.w500,
      letterSpacing: -0.16,
    );

    switch (type) {
      case ButtonType.primary:
        return AppTheme.primaryButtonStyle.copyWith(
          textStyle: WidgetStateProperty.all(textStyle),
        );
      case ButtonType.secondary:
        return AppTheme.secondaryButtonStyle.copyWith(
          textStyle: WidgetStateProperty.all(textStyle),
        );
      case ButtonType.ghost:
        return ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          foregroundColor: AppTheme.primaryOrange,
          elevation: 0,
          side: BorderSide(color: AppTheme.primaryOrange, width: 1.w),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppTheme.radiusButton),
          ),
          padding: EdgeInsets.symmetric(
            horizontal: AppTheme.spacingL,
            vertical: AppTheme.spacingM,
          ),
          textStyle: textStyle,
        );
      case ButtonType.text:
        return TextButton.styleFrom(
          foregroundColor: AppTheme.primaryOrange,
          padding: EdgeInsets.symmetric(
            horizontal: AppTheme.spacingL,
            vertical: AppTheme.spacingM,
          ),
          textStyle: textStyle,
        );
    }
  }
}

enum ButtonType {
  primary,   // 오렌지 배경 버튼
  secondary, // 흰색 배경 + 오렌지 테두리 버튼
  ghost,     // 투명 배경 + 오렌지 테두리 버튼
  text,      // 텍스트만 있는 버튼
}
