import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../theme/app_theme.dart';

/// 커스텀 상태 바 위젯
/// Figma 디자인의 상단 상태 바 (시간, 배터리, 신호 등) 스타일 구현
class CustomStatusBar extends StatelessWidget implements PreferredSizeWidget {
  final Color backgroundColor;
  final Color textColor;
  final bool showBackButton;
  final String? title;
  final VoidCallback? onBackPressed;
  final List<Widget>? actions;

  const CustomStatusBar({
    super.key,
    this.backgroundColor = AppTheme.primaryOrange,
    this.textColor = Colors.white,
    this.showBackButton = false,
    this.title,
    this.onBackPressed,
    this.actions,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: backgroundColor,
      padding: EdgeInsets.only(top: 44.h), // 상태바 높이 고려
      child: Container(
        height: 44.h,
        padding: EdgeInsets.symmetric(horizontal: AppTheme.spacingM),
        child: Row(
          children: [
            // 뒤로가기 버튼
            if (showBackButton)
              GestureDetector(
                onTap: onBackPressed ?? () => Navigator.of(context).pop(),
                child: Container(
                  width: 80.w,
                  height: 32.h,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(AppTheme.radiusCircle),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.arrow_back_ios,
                        size: 16.sp,
                        color: AppTheme.iconPrimary,
                      ),
                      Text(
                        'Go back',
                        style: TextStyle(
                          fontFamily: 'Brandon Grotesque',
                          fontSize: 16.sp,
                          fontWeight: FontWeight.w400,
                          letterSpacing: 0,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            
            // 제목
            if (title != null) ...[
              if (showBackButton) SizedBox(width: AppTheme.spacingM),
              Expanded(
                child: Text(
                  title!,
                  style: TextStyle(
                    fontFamily: 'Brandon Grotesque',
                    fontSize: 24.sp,
                    fontWeight: FontWeight.w500,
                    letterSpacing: -0.24,
                    color: textColor,
                  ),
                  textAlign: showBackButton ? TextAlign.left : TextAlign.center,
                ),
              ),
            ],
            
            // 액션 버튼들
            if (actions != null) ...actions!,
          ],
        ),
      ),
    );
  }

  @override
  Size get preferredSize => Size.fromHeight(88.h); // 44 + 44 (상태바 + 앱바)
}

/// 배송 상태 표시 위젯
/// Figma 디자인의 "Order Taken", "Order Is Being Prepared" 등의 상태 표시 구현
class DeliveryStatusItem extends StatelessWidget {
  final String title;
  final String? subtitle;
  final DeliveryStatus status;
  final IconData? icon;
  final Widget? customIcon;
  final bool showLine;

  const DeliveryStatusItem({
    super.key,
    required this.title,
    this.subtitle,
    required this.status,
    this.icon,
    this.customIcon,
    this.showLine = true,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 64.h,
      child: Row(
        children: [
          // 상태 아이콘
          Container(
            width: 65.w,
            height: 64.h,
            decoration: BoxDecoration(
              color: _getBackgroundColor(),
              borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
            ),
            child: Center(
              child: customIcon ??
                Icon(
                  icon ?? _getDefaultIcon(),
                  size: 24.sp,
                  color: status == DeliveryStatus.completed
                      ? Colors.white
                      : AppTheme.primaryOrange,
                ),
            ),
          ),

          SizedBox(width: AppTheme.spacingM),

          // 상태 텍스트
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  title,
                  style: AppTheme.bodyMedium,
                ),
                if (subtitle != null) ...[
                  SizedBox(height: 4.h),
                  Text(
                    subtitle!,
                    style: AppTheme.bodySmall,
                  ),
                ],
              ],
            ),
          ),

          // 완료 체크마크
          if (status == DeliveryStatus.completed)
            Container(
              width: 24.w,
              height: 24.h,
              decoration: BoxDecoration(
                color: AppTheme.successGreen,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.check,
                size: 16.sp,
                color: Colors.white,
              ),
            ),
        ],
      ),
    );
  }

  Color _getBackgroundColor() {
    switch (status) {
      case DeliveryStatus.completed:
        return AppTheme.successGreen;
      case DeliveryStatus.inProgress:
        return AppTheme.primaryOrange;
      case DeliveryStatus.pending:
        return AppTheme.backgroundGray;
    }
  }

  IconData _getDefaultIcon() {
    switch (status) {
      case DeliveryStatus.completed:
        return Icons.check;
      case DeliveryStatus.inProgress:
        return Icons.local_shipping;
      case DeliveryStatus.pending:
        return Icons.access_time;
    }
  }
}

enum DeliveryStatus {
  pending,    // 대기중
  inProgress, // 진행중
  completed,  // 완료
}
