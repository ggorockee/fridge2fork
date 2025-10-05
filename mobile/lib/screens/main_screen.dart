import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:showcaseview/showcaseview.dart';
import '../providers/app_state_provider.dart';
import '../theme/app_theme.dart';
import 'home_screen.dart';
import 'my_fridge_screen.dart';
import 'recipe_screen.dart';
import 'feedback_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../widgets/widgets.dart';
import '../services/analytics_service.dart';

/// 메인 화면 - 탭 기반 네비게이션
/// 하단 네비게이션 바가 항상 표시되는 메인 컨테이너 화면
class MainScreen extends ConsumerStatefulWidget {
  const MainScreen({super.key});

  @override
  ConsumerState<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends ConsumerState<MainScreen> {
  late PageController _pageController;

  // Showcase를 위한 GlobalKey 선언
  final GlobalKey _fridgeTabKey = GlobalKey();

  // 각 탭에 해당하는 화면 이름 (애널리틱스용)
  static const List<String> _screenNames = <String>[
    'home',
    'my_fridge', // Changed from 'recipe' to 'my_fridge'
    'recipe',
    'feedback',
  ];

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    // 첫 화면 진입 기록
    final selectedIndex = ref.read(selectedTabIndexProvider);
    AnalyticsService().logScreenView(_screenNames[selectedIndex]);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _onBottomNavTapped(int index) {
    ref.read(selectedTabIndexProvider.notifier).state = index;
    _pageController.animateToPage(
      index,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
    // 화면 전환 시 애널리틱스 이벤트 기록
    AnalyticsService().logScreenView(_screenNames[index]);
  }

  void _onPageChanged(int index) {
    ref.read(selectedTabIndexProvider.notifier).state = index;
  }

  @override
  Widget build(BuildContext context) {
    final selectedIndex = ref.watch(selectedTabIndexProvider);

    // Provider 변경 시 PageController도 업데이트
    ref.listen(selectedTabIndexProvider, (previous, next) {
      if (previous != next && _pageController.hasClients) {
        _pageController.animateToPage(
          next,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
        );
        // 화면 전환 시 애널리틱스 이벤트 기록
        AnalyticsService().logScreenView(_screenNames[next]);
      }
    });

    return ShowCaseWidget(
      onFinish: () async {
        // 온보딩 완료 후 isFirstLaunch 상태를 false로 변경
        ref.read(isFirstLaunchProvider.notifier).state = false;

        // SharedPreferences에 온보딩 완료 상태 저장
        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool('isFirstLaunch', false);
      },
      builder: (context) {
        // 온보딩 시작을 위해 context를 전달
        WidgetsBinding.instance.addPostFrameCallback((_) {
          final isFirstLaunch = ref.read(isFirstLaunchProvider);
          if (isFirstLaunch) {
            ShowCaseWidget.of(context).startShowCase([
              homeScreenAddButtonKey,
              _fridgeTabKey,
            ]);
          }
        });

        return Scaffold(
          backgroundColor: AppTheme.backgroundWhite,
          body: SafeArea(
            // 시스템 UI 영역(상태 표시줄 등)을 피해서 콘텐츠 렌더링
            child: PageView(
              controller: _pageController,
              onPageChanged: _onPageChanged,
              children: [
                // 홈 화면
                const HomeScreen(),

                // 나의냉장고 화면
                const MyFridgeScreen(),

                // 요리하기 화면
                const RecipeScreen(),

                // 의견보내기 화면
                const FeedbackScreen(),
              ],
            ),
          ),

          // 하단 네비게이션 바 (항상 표시)
          bottomNavigationBar: Container(
            height: 80.h,
            decoration: const BoxDecoration(
              color: Colors.white,
              border: Border(
                top: BorderSide(
                  color: const Color(0xFFF0F0F0),
                  width: 1,
                ),
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildBottomNavItem(
                  icon: Icons.home,
                  label: '홈',
                  isSelected: selectedIndex == 0,
                  onTap: () => _onBottomNavTapped(0),
                ),
                _buildBottomNavItem(
                  key: _fridgeTabKey, // Showcase 아이템에 GlobalKey 전달
                  icon: Icons.kitchen,
                  label: '나의냉장고',
                  description: '추가한 식재료들을 이곳에서 확인하고 관리할 수 있어요.',
                  isSelected: selectedIndex == 1,
                  onTap: () => _onBottomNavTapped(1),
                ),
                _buildBottomNavItem(
                  icon: Icons.restaurant_menu,
                  label: '요리하기',
                  isSelected: selectedIndex == 2,
                  onTap: () => _onBottomNavTapped(2),
                ),
                _buildBottomNavItem(
                  icon: Icons.feedback,
                  label: '의견보내기',
                  isSelected: selectedIndex == 3,
                  onTap: () => _onBottomNavTapped(3),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  /// 하단 네비게이션 아이템 위젯
  Widget _buildBottomNavItem({
    GlobalKey? key, // Showcase를 위해 Key 타입 수정
    required IconData icon,
    required String label,
    String? description, // Showcase 설명
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    Widget content = GestureDetector(
      onTap: onTap,
      child: Container(
        padding: EdgeInsets.symmetric(vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 24.sp,
              color: isSelected ? AppTheme.primaryOrange : AppTheme.iconPrimary,
            ),
            SizedBox(height: 4.h),
            Text(
              label,
              style: TextStyle(
                fontSize: 12.sp,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                color: isSelected ? AppTheme.primaryOrange : AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );

    if (description != null) {
      return Showcase(
        key: key!,
        description: description,
        child: content,
      );
    }
    return content;
  }
}
