import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'config/app_config.dart';
import 'providers/app_state_provider.dart';
import 'screens/splash_screen.dart';
import 'screens/recipe_detail_screen.dart';
import 'models/recipe.dart';
import 'theme/app_theme.dart';

void main() async {
  // Flutter 엔진과 위젯 바인딩 초기화
  WidgetsFlutterBinding.ensureInitialized();
  
  // 환경 설정 초기화
  final environment = kReleaseMode ? AppEnvironment.production : AppEnvironment.development;
  await AppConfig.initialize(environment);
  
  // 디버그 모드에서 설정 정보 출력
  if (AppConfig.debugMode) {
    AppConfig.printConfig();
  }
  
  // SharedPreferences 인스턴스 로드
  final prefs = await SharedPreferences.getInstance();
  
  bool isFirstLaunch;

  if (AppConfig.isProduction) {
    // 운영 모드: SharedPreferences를 확인하여 최초 실행 여부 판단
    isFirstLaunch = prefs.getBool('isFirstLaunch') ?? true;
  } else {
    // 개발 모드: 테스트를 위해 앱을 재시작할 때마다 온보딩 표시
    isFirstLaunch = false; // 온보딩 비활성화
  }

  runApp(
    ProviderScope(
      overrides: [
        // 앱 시작 시 isFirstLaunchProvider의 상태를 SharedPreferences 값으로 설정
        isFirstLaunchProvider.overrideWith((ref) => isFirstLaunch),
      ],
      child: const MyApp(),
    ),
  );
}

/// 냉털레시피 앱의 메인 애플리케이션 클래스
/// 냉장고 털어서 만드는 한식 레시피 추천 앱
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConfig.appName,
      debugShowCheckedModeBanner: !AppConfig.isProduction,
      theme: AppTheme.lightTheme,
      home: const SplashScreen(),
      onGenerateRoute: (settings) {
        switch (settings.name) {
          case '/recipe-detail':
            final recipe = settings.arguments as Recipe;
            return MaterialPageRoute(
              builder: (context) => RecipeDetailScreen(recipe: recipe),
            );
          default:
            return null;
        }
      },
    );
  }
}
