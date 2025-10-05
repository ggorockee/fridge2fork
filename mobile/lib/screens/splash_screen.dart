import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../utils/app_assets.dart';
import '../theme/app_theme.dart';
import 'main_screen.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _navigateToHome();
  }

  void _navigateToHome() {
    Future.delayed(const Duration(seconds: 2), () {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const MainScreen()),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // 앱 로고
            Image.asset(
              AppAssets.appLogo,
              width: 120.w,
              height: 120.h,
              errorBuilder: (context, error, stackTrace) {
                // 로고 파일이 없을 경우 기본 아이콘 표시
                return Container(
                  width: 120.w,
                  height: 120.h,
                  decoration: const BoxDecoration(
                    color: AppTheme.primaryOrange,
                    borderRadius: BorderRadius.all(Radius.circular(AppTheme.radiusMedium)),
                  ),
                  child: Icon(
                    Icons.kitchen,
                    size: 60.sp,
                    color: Colors.white,
                  ),
                );
              },
            ),
            SizedBox(height: 24.h),
            // 앱 이름
            Text(
              '냉털레시피',
              style: TextStyle(
                fontSize: 28.sp,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
            ),
            SizedBox(height: 8.h),
            // 앱 설명
            Text(
              '냉장고 털어서 만드는 레시피',
              style: TextStyle(
                fontSize: 16.sp,
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
