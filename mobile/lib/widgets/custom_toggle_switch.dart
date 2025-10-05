import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../theme/app_theme.dart';

class CustomToggleSwitch extends StatefulWidget {
  final bool value;
  final ValueChanged<bool> onChanged;
  final double width;
  final double height;

  const CustomToggleSwitch({
    super.key,
    required this.value,
    required this.onChanged,
    this.width = 44.0,
    this.height = 24.0,
  });

  @override
  State<CustomToggleSwitch> createState() => _CustomToggleSwitchState();
}

class _CustomToggleSwitchState extends State<CustomToggleSwitch> {
  @override
  Widget build(BuildContext context) {
    final thumbSize = widget.height - 4;

    return GestureDetector(
      onTap: () {
        widget.onChanged(!widget.value);
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: widget.width.w,
        height: widget.height.h,
        decoration: BoxDecoration(
          color: widget.value ? AppTheme.lightOrange : AppTheme.backgroundGray,
          borderRadius: BorderRadius.circular((widget.height / 2).r),
        ),
        child: Stack(
          children: [
            AnimatedAlign(
              duration: const Duration(milliseconds: 200),
              curve: Curves.easeIn,
              alignment: widget.value ? Alignment.centerRight : Alignment.centerLeft,
              child: Container(
                width: thumbSize.w,
                height: thumbSize.h,
                margin: EdgeInsets.all(2.0.w),
                decoration: BoxDecoration(
                  color: AppTheme.primaryOrange,
                  shape: BoxShape.circle,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
