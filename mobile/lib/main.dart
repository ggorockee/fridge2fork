import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:firebase_core/firebase_core.dart'; // Firebase Core 패키지 임포트
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'config/app_config.dart';
import 'providers/app_state_provider.dart';
import 'providers/api/api_connection_provider.dart';
import 'screens/splash_screen.dart';
import 'screens/recipe_detail_screen.dart';
import 'models/recipe.dart';
import 'theme/app_theme.dart';
import 'services/ad_service.dart';
import 'services/interstitial_ad_manager.dart';
import 'services/cache_service.dart';
import 'services/offline_service.dart';
import 'services/session_service.dart';
import 'widgets/async_performance_monitor.dart';

void main() async {
  // Flutter 엔진과 위젯 바인딩 초기화
  WidgetsFlutterBinding.ensureInitialized();

  // 🔧 환경 설정 초기화 (.env 파일의 ENVIRONMENT 값에 따라 자동 결정)
  try {
    await AppConfig.initialize();
    debugPrint('✅ AppConfig initialized successfully');
    if (AppConfig.debugMode) {
      AppConfig.printConfig();
    }
  } catch (e) {
    debugPrint('⚠️ AppConfig initialization failed: $e');
    debugPrint('ℹ️ Using default configuration');
  }

  // 🔥 Firebase 초기화 (네이티브 설정 파일 사용: GoogleService-Info.plist, google-services.json)
  try {
    await Firebase.initializeApp();
    debugPrint('✅ Firebase initialized successfully');
  } catch (e) {
    debugPrint('⚠️ Firebase initialization failed: $e');
    debugPrint('ℹ️ App will run without Firebase features');
  }

  // 📱 AdMob 초기화 및 전면 광고 프리로드 (수익성 극대화)
  try {
    final adService = AdService();
    await adService.initialize();
    await adService.preloadInterstitialAd();
    debugPrint('✅ AdMob initialized successfully');

    // 전면 광고 관리자 초기화 (앱 시작 후 광고 기회 제공)
    InterstitialAdManager().onAppLaunched();
  } catch (e) {
    debugPrint('⚠️ AdMob initialization failed: $e');
    debugPrint('ℹ️ App will run without ads');
  }

  // 🗄️ 캐시 서비스 초기화
  try {
    await CacheService.initialize();
    debugPrint('✅ CacheService initialized successfully');
  } catch (e) {
    debugPrint('⚠️ CacheService initialization failed: $e');
  }

  // 📴 오프라인 서비스 초기화
  try {
    await OfflineService.initialize();
    debugPrint('✅ OfflineService initialized successfully');
  } catch (e) {
    debugPrint('⚠️ OfflineService initialization failed: $e');
  }

  // 🔐 세션 서비스 초기화 (API 호출을 위한 세션 관리)
  try {
    await SessionService.initialize();
    debugPrint('✅ SessionService initialized successfully');
  } catch (e) {
    debugPrint('⚠️ SessionService initialization failed: $e');
  }

  // 💾 SharedPreferences 인스턴스 로드
  final prefs = await SharedPreferences.getInstance();

  bool isFirstLaunch;

  if (AppConfig.isProduction) {
    // 운영 모드: SharedPreferences를 확인하여 최초 실행 여부 판단
    isFirstLaunch = prefs.getBool('isFirstLaunch') ?? true;
  } else {
    // 개발 모드: 테스트를 위해 앱을 재시작할 때마다 온보딩 표시
    isFirstLaunch = false; // 온보딩 비활성화
  }

  debugPrint('🚀 App initialization completed');

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
class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // API 클라이언트 초기화
    ref.listen(apiClientInitializedProvider, (previous, next) {
      if (!next) {
        // API 클라이언트가 초기화되지 않았다면 초기화
        initializeApiClient(ref);
      }
    });

    // ScreenUtil을 사용하여 반응형 디자인 구현
    return ScreenUtilInit(
      // 디자인 기준 사이즈 (일반적인 모바일 디자인 기준)
      designSize: const Size(375, 812),
      // 최소 텍스트 크기 배율 (접근성 고려)
      minTextAdapt: true,
      // 분할 화면 모드 지원
      splitScreenMode: true,
      builder: (context, child) {
        return MaterialApp(
          title: AppConfig.appName,
          debugShowCheckedModeBanner: false,
          theme: AppTheme.lightTheme,
          home: const AsyncPerformanceOverlay(
            showMonitor: kDebugMode,
            child: SplashScreen(),
          ),
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
      },
    );
  }
}
