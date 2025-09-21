import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

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
    return SizedBox(
      width: width,
      height: height ?? 56, // Figma 디자인의 기본 버튼 높이
      child: ElevatedButton(
        onPressed: isLoading ? null : onPressed,
        style: _getButtonStyle(),
        child: isLoading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : Row(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (icon != null) ...[
                    Icon(icon, size: 20),
                    const SizedBox(width: AppTheme.spacingS),
                  ],
                  Text(text),
                ],
              ),
      ),
    );
  }

  ButtonStyle _getButtonStyle() {
    switch (type) {
      case ButtonType.primary:
        return AppTheme.primaryButtonStyle;
      case ButtonType.secondary:
        return AppTheme.secondaryButtonStyle;
      case ButtonType.ghost:
        return ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          foregroundColor: AppTheme.primaryOrange,
          elevation: 0,
          side: const BorderSide(color: AppTheme.primaryOrange),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppTheme.radiusButton),
          ),
          padding: const EdgeInsets.symmetric(
            horizontal: AppTheme.spacingL,
            vertical: AppTheme.spacingM,
          ),
        );
      case ButtonType.text:
        return TextButton.styleFrom(
          foregroundColor: AppTheme.primaryOrange,
          padding: const EdgeInsets.symmetric(
            horizontal: AppTheme.spacingL,
            vertical: AppTheme.spacingM,
          ),
          textStyle: const TextStyle(
            fontFamily: 'Brandon Grotesque',
            fontSize: 16,
            fontWeight: FontWeight.w500,
            letterSpacing: -0.16,
          ),
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
