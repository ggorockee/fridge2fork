import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:showcaseview/showcaseview.dart';
import 'package:url_launcher/url_launcher.dart';
import '../widgets/widgets.dart';
import '../widgets/ad_banner_widget.dart';
import '../providers/fridge_provider.dart';
import '../providers/api/ingredient_api_provider.dart';
import '../providers/api/api_connection_provider.dart';
import '../providers/recipe_recommendations_provider.dart';
import '../providers/async_state_manager.dart';
import '../providers/app_state_provider.dart';
import '../models/api/api_ingredient.dart';
import '../models/api/api_fridge.dart';
import '../models/api/api_recipe.dart';
import '../services/interstitial_ad_manager.dart';
import '../services/analytics_service.dart';
import 'add_ingredient_screen.dart';

// HomeScreen의 Showcase Key를 MainScreen에서 참조할 수 있도록 전역 변수로 선언
final homeScreenAddButtonKey = GlobalKey();

/// 홈 화면 - 냉장고 빈 상태 화면
/// 사용자가 식재료를 추가할 수 있도록 유도하는 화면
class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  @override
  void initState() {
    super.initState();
    // API 클라이언트 초기화 및 연결 상태 확인
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await _initializeWithRetry();
    });
  }

  /// 재시도 로직이 포함된 초기화 함수
  Future<void> _initializeWithRetry({int maxRetries = 3}) async {
    if (kDebugMode) debugPrint('🏠 [Home Screen] Starting initialization with retry...');

    for (int attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        if (kDebugMode) debugPrint('🏠 [Home Screen] Initialization attempt $attempt/$maxRetries');

        // API 클라이언트 초기화
        await initializeApiClient(ref);

        // 초기화 완료 확인
        final isApiClientInitialized = ref.read(apiClientInitializedProvider);
        if (kDebugMode) debugPrint('🏠 [Home Screen] API client initialized: $isApiClientInitialized');

        if (isApiClientInitialized) {
          await _loadInitialData();
          if (kDebugMode) debugPrint('✅ [Home Screen] Initialization completed successfully');
          return; // 성공적으로 초기화 완료
        }
      } catch (e) {
        if (kDebugMode) debugPrint('❌ [Home Screen] Initialization attempt $attempt failed: $e');

        if (attempt < maxRetries) {
          // 재시도 전 대기 시간 (1초, 2초, 3초...)
          final delaySeconds = attempt;
          if (kDebugMode) debugPrint('🔄 [Home Screen] Retrying in ${delaySeconds}s...');
          await Future.delayed(Duration(seconds: delaySeconds));
        }
      }
    }

    // 모든 재시도 실패 시 오프라인 모드로 데이터 로드 시도
    if (kDebugMode) debugPrint('⚠️ [Home Screen] All initialization attempts failed, trying offline mode...');
    await _loadInitialDataOffline();
  }

  /// 초기 데이터 로드 (온라인 - 병렬 처리 최적화)
  Future<void> _loadInitialData() async {
    try {
      if (kDebugMode) debugPrint('🏠 [Home Screen] Loading initial data (online mode)...');

      // 병렬 데이터 로딩 - 모든 요청을 동시에 시작
      final futures = [
        // 식재료 목록 로드
        _loadIngredients(),
        // 연결 상태 확인
        _verifyApiConnection(),
      ];

      // 모든 요청을 병렬로 실행하되, 개별 실패는 무시
      final results = await Future.wait(futures, eagerError: false);

      final successCount = results.where((result) => result == true).length;
      if (kDebugMode) {
        debugPrint('✅ [Home Screen] Initialization completed: $successCount/${results.length} operations successful');
      }

    } catch (e) {
      if (kDebugMode) debugPrint('❌ [Home Screen] Initial data loading failed: $e');
    }
  }


  /// 식재료 목록 로드 (독립적 실행 - 비동기 최적화)
  Future<bool> _loadIngredients() async {
    return await AsyncStateManager.executeTask<bool>(
      'home_ingredients',
      () async {
        if (kDebugMode) debugPrint('🥬 [Home Screen] Loading ingredients for selection...');
        await ref.read(ingredientApiProvider.notifier).loadIngredients(
          filter: const IngredientSearchFilter(
            page: 1,
            size: 200, // 전체 식재료 로드
          ),
        );
        if (kDebugMode) debugPrint('✅ [Home Screen] Ingredients loaded successfully');
        return true;
      },
      timeout: const Duration(seconds: 20),
      maxRetries: 2,
      retryDelay: const Duration(seconds: 1),
    );
  }

  /// API 연결 상태 확인 (독립적 실행)
  Future<bool> _verifyApiConnection() async {
    try {
      if (kDebugMode) debugPrint('📡 [Home Screen] Verifying API connection...');
      await ref.read(apiConnectionProvider.notifier).checkConnection();
      final isOnline = ref.read(apiConnectionProvider).isOnline;
      if (kDebugMode) debugPrint('${isOnline ? "✅" : "❌"} [Home Screen] API connection: $isOnline');
      return isOnline;
    } catch (e) {
      if (kDebugMode) debugPrint('❌ [Home Screen] API connection check failed: $e');
      return false;
    }
  }

  /// 초기 데이터 로드 (오프라인)
  Future<void> _loadInitialDataOffline() async {
    try {
      if (kDebugMode) debugPrint('📱 [Home Screen] Loading initial data (offline mode)...');

      // 오프라인 모드에서 캐시된 데이터 로드 시도
      await ref.read(ingredientApiProvider.notifier).loadIngredients(forceRefresh: false);

      if (kDebugMode) debugPrint('✅ [Home Screen] Offline data loaded');
    } catch (e) {
      if (kDebugMode) debugPrint('❌ [Home Screen] Offline data loading failed: $e');
    }
  }

  Future<void> _onRefresh() async {
    if (kDebugMode) debugPrint('🔄 [Home Screen] Pull to refresh triggered');

    // 식재료 목록 새로고침
    await ref.read(ingredientApiProvider.notifier).refresh();

    if (kDebugMode) debugPrint('✅ [Home Screen] Refresh completed');
  }

  void _onAddButtonPressed() async {
    // 식재료 추가 Modal Bottom Sheet 표시
    final result = await AddIngredientScreen.showModal(context);

    // 선택된 식재료가 있으면 API로 추가
    if (result != null && result.isNotEmpty && mounted) {
      int successCount = 0;
      for (final ingredient in result) {
        final success = await ref.read(fridgeProvider.notifier).addIngredient(ingredient);
        if (success) successCount++;
      }

      if (mounted && successCount > 0) {
        SnackBarHelper.showSnackBar(
          context,
          '$successCount개의 식재료가 추가되었습니다!',
          backgroundColor: AppTheme.primaryOrange,
        );

        //  Firebase Analytics 이벤트 기록
        AnalyticsService().logAddIngredients(result);

        // 🎯 수익성 극대화: 식재료 추가 완료 후 전면 광고 기회
        for (int i = 0; i < successCount; i++) {
          await InterstitialAdManager().onIngredientAdded();
        }
      }
    }
  }

  void _removeIngredient(int ingredientId) async {
    final success = await ref.read(fridgeProvider.notifier).removeIngredient(ingredientId);
    if (mounted && !success) {
      SnackBarHelper.showSnackBar(
        context,
        '재료 제거에 실패했습니다',
        backgroundColor: Colors.red,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final fridgeState = ref.watch(fridgeProvider);
    final selectedIngredients = ref.watch(fridgeIngredientNamesProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        backgroundColor: AppTheme.backgroundWhite,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
        centerTitle: true,
        surfaceTintColor: AppTheme.backgroundWhite, // 스크롤 시 색상 변경 방지
        scrolledUnderElevation: 0, // 스크롤 시 elevation 변경 방지
        title: Text(
          '냉털레시피',
          style: TextStyle(
            fontFamily: 'Brandon Grotesque',
            fontSize: 24.sp,
            fontWeight: FontWeight.w500,
            letterSpacing: -0.24,
            color: AppTheme.textPrimary,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ),
      body: RefreshIndicator(
        onRefresh: _onRefresh,
        color: AppTheme.primaryOrange,
        backgroundColor: Colors.white,
        child: Stack(
          children: [
            // 냉장고 영역 - 나머지 공간 전부 차지
            Positioned.fill(
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                child: Column(
                  children: [
                    const AdBannerWidget(isTop: true),

                    // 냉장고 + 상태
                    ConstrainedBox(
                      constraints: BoxConstraints(
                        minHeight: MediaQuery.of(context).size.height - 320.h,
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          SizedBox(height: 40.h), // 상단 여백

                          // 냉장고 이미지 (중앙 정렬)
                          const _FridgeIcon(),

                          SizedBox(height: 16.h),

                          // 냉장고 상태 내용
                          fridgeState.when(
                            data: (fridge) => fridge.ingredients.isEmpty
                                ? _EmptyStateMessage(onAddPressed: _onAddButtonPressed)
                                : _SelectedIngredientsSection(
                                    ingredients: fridge.ingredients,
                                    onRemove: _removeIngredient,
                                    onAddPressed: _onAddButtonPressed,
                                  ),
                            loading: () => const CircularProgressIndicator(
                              valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primaryOrange),
                            ),
                            error: (_, __) => _EmptyStateMessage(onAddPressed: _onAddButtonPressed),
                          ),
                        ],
                      ),
                    ),
                    SizedBox(height: 320.h), // 레시피 영역 차지할 공간 확보 (여백 증가)
                  ],
                ),
              ),
            ),

            // 하단 레시피 영역 고정 (바텀 네비게이션 바 위로)
            Positioned(
              left: 0,
              right: 0,
              bottom: 0.h, // 바텀 네비게이션 바와 16px 간격
              child: Container(
                height: 300.h, // 레시피 영역 높이 약간 증가
                color: AppTheme.backgroundWhite,
                child: selectedIngredients.isEmpty
                    ? const _RecipeRecommendationSection()
                    : _RecipeRecommendationsSection(ingredients: selectedIngredients),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 냉장고 아이콘 위젯 - 앱 로고 이미지 사용
class _FridgeIcon extends StatelessWidget {
  const _FridgeIcon();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 120.w,
      height: 120.h,
      decoration: const BoxDecoration(
        color: AppTheme.backgroundWhite,
        borderRadius: BorderRadius.all(Radius.circular(AppTheme.radiusMedium)),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
        child: Image.asset(
          'assets/logos/app_logo.png',
          width: 120.w,
          height: 120.h,
          fit: BoxFit.contain,
        ),
      ),
    );
  }
}

/// 빈 상태 메시지 위젯 - 재빌드 시에도 안정적인 렌더링을 위한 정적 위젯
class _EmptyStateMessage extends StatelessWidget {
  final VoidCallback onAddPressed;

  const _EmptyStateMessage({required this.onAddPressed});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // 메인 메시지
        Text(
          '냉장고가 비어있어요',
          style: TextStyle(
            fontSize: 20.sp,
            fontWeight: FontWeight.w600,
            color: AppTheme.textPrimary,
          ),
          textAlign: TextAlign.center,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),

        SizedBox(height: 8.h),

        // 서브 메시지
        Text(
          '식재료를 추가해 보세요',
          style: TextStyle(
            fontSize: 14.sp,
            color: AppTheme.textPrimary,
          ),
          textAlign: TextAlign.center,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),

        const SizedBox(height: AppTheme.spacingL),

        // [+] 버튼
        Showcase(
          key: homeScreenAddButtonKey,
          description: '냉장고에 식재료를 추가하려면 이 버튼을 누르세요!',
          onTargetClick: onAddPressed,
          disposeOnTap: true,
          child: SizedBox(
            width: 56.w,
            height: 56.h,
            child: Material(
              color: Colors.white,
              shape: CircleBorder(
                side: BorderSide(
                  color: AppTheme.primaryOrange,
                  width: 2.w,
                ),
              ),
              child: InkWell(
                onTap: onAddPressed,
                customBorder: const CircleBorder(),
                child: Icon(
                  Icons.add,
                  color: AppTheme.primaryOrange,
                  size: 32.sp,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/// 레시피 추천 섹션 - 가로 스크롤 가능한 레시피 카드들
class _RecipeRecommendationSection extends ConsumerWidget {
  const _RecipeRecommendationSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: EdgeInsets.only(top: 16.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // 섹션 제목
          Padding(
            padding: EdgeInsets.only(left: 16.w, bottom: 16.h),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                '추천 레시피',
                style: TextStyle(
                  fontSize: 18.sp,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),

          // 가로 스크롤 레시피 카드들
          SizedBox(
            height: 160.h, // 카드 높이와 동일하게 고정
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.restaurant_menu,
                    size: 48.sp,
                    color: AppTheme.primaryOrange.withValues(alpha: 0.5),
                  ),
                  SizedBox(height: 8.h),
                  Text(
                    '냉장고에 재료를 추가하면\n맛있는 레시피를 추천해드려요!',
                    style: TextStyle(
                      fontSize: 12.sp,
                      color: AppTheme.textSecondary,
                    ),
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// 선택된 식재료 표시 섹션
class _SelectedIngredientsSection extends ConsumerWidget {
  final List<ApiFridgeIngredient> ingredients;
  final Function(int) onRemove;
  final VoidCallback onAddPressed;

  const _SelectedIngredientsSection({
    required this.ingredients,
    required this.onRemove,
    required this.onAddPressed,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // 2줄까지만 표시 (3개씩 2줄 = 6개)
    final displayIngredients = ingredients.take(6).toList();
    final hasMore = ingredients.length > 6;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppTheme.spacingM),
      child: Column(
        children: [
          // "냉장고 현황" 텍스트만 중앙 정렬, (+) 버튼은 오른쪽에
          SizedBox(
            height: 28.h, // 버튼 높이와 동일
            child: Stack(
              children: [
                // "냉장고 현황" 텍스트를 정확히 중앙에
                Center(
                  child: Text(
                    '냉장고 현황',
                    style: TextStyle(
                      fontSize: 18.sp,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),

                // (+) 버튼을 텍스트 오른쪽에 배치
                Center(
                  child: Transform.translate(
                    offset: Offset(70.w, 0), // 텍스트 너비의 절반 + 간격 + 버튼 중심
                    child: Showcase(
                      key: homeScreenAddButtonKey,
                      description: '냉장고에 식재료를 추가하려면 이 버튼을 누르세요!',
                      onTargetClick: onAddPressed,
                      disposeOnTap: true,
                      child: SizedBox(
                        width: 28.w,
                        height: 28.h,
                        child: Material(
                          color: Colors.white,
                          shape: CircleBorder(
                            side: BorderSide(
                              color: AppTheme.primaryOrange,
                              width: 2.w,
                            ),
                          ),
                          child: InkWell(
                            onTap: onAddPressed,
                            customBorder: const CircleBorder(),
                            child: Icon(
                              Icons.add,
                              color: AppTheme.primaryOrange,
                              size: 18.sp,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          SizedBox(height: 12.h),

          // 선택된 재료 개수
          Text(
            '총 ${ingredients.length}개의 식재료',
            style: TextStyle(
              fontSize: 14.sp,
              color: AppTheme.textSecondary,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),

          SizedBox(height: 12.h),

          // 재료 칩들 (중앙 정렬) - 3줄만 표시
          Wrap(
            alignment: WrapAlignment.center,
            spacing: AppTheme.spacingS,
            runSpacing: AppTheme.spacingS,
            children: displayIngredients.map((ingredient) => _IngredientChip(
              ingredient: ingredient.name,
              onRemove: () => onRemove(ingredient.id),
            )).toList(),
          ),

          // 3번째 줄: 더보기 버튼 (중앙 정렬)
          if (hasMore) ...[
            SizedBox(height: 8.h),
            Center(
              child: GestureDetector(
                onTap: () {
                  // "나의 냉장고" 탭으로 이동 (탭 인덱스 1)
                  ref.read(selectedTabIndexProvider.notifier).state = 1;
                },
                child: Container(
                  padding: EdgeInsets.symmetric(
                    horizontal: 12.w,
                    vertical: AppTheme.spacingS,
                  ),
                  decoration: BoxDecoration(
                    color: AppTheme.lightOrange,
                    borderRadius: BorderRadius.circular(50.r),
                    border: Border.all(
                      color: AppTheme.primaryOrange,
                      width: 1.w,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        '더보기 +${ingredients.length - 6}',
                        style: TextStyle(
                          fontSize: 14.sp,
                          color: AppTheme.primaryOrange,
                          fontWeight: FontWeight.w600,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      SizedBox(width: 4.w),
                      Icon(
                        Icons.arrow_forward_ios,
                        size: 14.sp,
                        color: AppTheme.primaryOrange,
                      ),
                    ],
                  ),
                ),
              ),
            ),
            SizedBox(height: 24.h), // 레시피 추천 섹션과의 간격 확보
          ],
        ],
      ),
    );
  }
}

/// 개별 식재료 칩 위젯
class _IngredientChip extends StatelessWidget {
  final String ingredient;
  final VoidCallback onRemove;

  const _IngredientChip({
    required this.ingredient,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: 12.w,
        vertical: AppTheme.spacingS,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(50.r),
        border: Border.all(
          color: const Color(0xFFD7D7D7),
          width: 1.w,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            ingredient,
            style: TextStyle(
              fontSize: 14.sp,
              color: AppTheme.iconPrimary,
              fontWeight: FontWeight.w600,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          SizedBox(width: 12.w),
          GestureDetector(
            onTap: onRemove,
            child: Icon(
              Icons.close,
              size: 14.sp,
              color: const Color(0xFF999999),
            ),
          ),
        ],
      ),
    );
  }
}

/// 레시피 추천 섹션 위젯
class _RecipeRecommendationsSection extends ConsumerStatefulWidget {
  final List<String> ingredients;

  const _RecipeRecommendationsSection({
    required this.ingredients,
  });

  @override
  ConsumerState<_RecipeRecommendationsSection> createState() => _RecipeRecommendationsSectionState();
}

class _RecipeRecommendationsSectionState extends ConsumerState<_RecipeRecommendationsSection> {
  @override
  void initState() {
    super.initState();
    // 초기 로드
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadRecommendations();
    });
  }

  @override
  void didUpdateWidget(_RecipeRecommendationsSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    // 재료가 변경되면 추천 다시 로드 (빌드 사이클 이후로 지연)
    if (oldWidget.ingredients != widget.ingredients && widget.ingredients.isNotEmpty) {
      Future.microtask(() => _loadRecommendations());
    }
  }

  void _loadRecommendations() {
    if (widget.ingredients.isEmpty) return;

    ref.read(recipeRecommendationsProvider.notifier).loadRecommendations(
      ingredients: widget.ingredients,
      limit: 10,
      algorithm: 'jaccard',
      excludeSeasonings: true,
      // minMatchRate는 서버의 관리자 설정을 사용 (기본값: 0.15)
    );
  }

  @override
  Widget build(BuildContext context) {
    final recommendationsState = ref.watch(recipeRecommendationsProvider);

    return recommendationsState.when(
      data: (response) {
        if (response.recipes.isEmpty) {
          return const SizedBox.shrink();
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 추천 제목 (왼쪽 패딩만)
            Padding(
              padding: EdgeInsets.only(left: 16.w, top: 64.h, bottom: 8.h), // 상단 여백 증가 (AppTheme.spacingM → 48.h)
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '맞춤 레시피 추천',
                    style: TextStyle(
                      fontSize: 18.sp,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  GestureDetector(
                    onTap: () {
                      // "나의 냉장고" 탭으로 이동 (탭 인덱스 1)
                      ref.read(selectedTabIndexProvider.notifier).state = 1;
                    },
                    child: Padding(
                      padding: EdgeInsets.only(right: 16.w),
                      child: Row(
                        children: [
                          Text(
                            '더보기',
                            style: TextStyle(
                              fontSize: 14.sp,
                              color: AppTheme.primaryOrange,
                              fontWeight: FontWeight.w600,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          SizedBox(width: 4.w),
                          Icon(
                            Icons.arrow_forward_ios,
                            size: 12.sp,
                            color: AppTheme.primaryOrange,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            // 레시피 가로 스크롤 리스트
            SizedBox(
              height: 200.h,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                padding: EdgeInsets.only(left: 16.w, right: 16.w),
                itemCount: response.recipes.take(10).length,
                itemBuilder: (context, index) {
                  final recipe = response.recipes[index];
                  return Padding(
                    padding: EdgeInsets.only(right: index < response.recipes.take(10).length - 1 ? 8.w : 0),
                    child: SizedBox(
                      width: 140.w,
                      child: _RecommendedRecipeCard(recipe: recipe),
                    ),
                  );
                },
              ),
            ),
          ],
        );
      },
      loading: () => const Padding(
        padding: EdgeInsets.all(AppTheme.spacingM),
        child: Center(
          child: CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primaryOrange),
          ),
        ),
      ),
      error: (_, __) => const SizedBox.shrink(),
    );
  }
}

/// 추천 레시피 카드 위젯
class _RecommendedRecipeCard extends StatelessWidget {
  final RecipeRecommendation recipe;

  const _RecommendedRecipeCard({
    required this.recipe,
  });

  Future<void> _openRecipeUrl(BuildContext context) async {
    final url = recipe.recipeUrl;

    if (url == null || url.isEmpty) {
      if (context.mounted) {
        SnackBarHelper.showSnackBar(
          context,
          '레시피 링크가 없습니다.',
          backgroundColor: Colors.orange,
        );
      }
      return;
    }

    try {
      final uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } else {
        if (context.mounted) {
          SnackBarHelper.showSnackBar(
            context,
            '링크를 열 수 없습니다.',
            backgroundColor: Colors.red,
          );
        }
      }
    } catch (e) {
      if (context.mounted) {
        SnackBarHelper.showSnackBar(
          context,
          '링크를 열 수 없습니다: $e',
          backgroundColor: Colors.red,
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => _openRecipeUrl(context),
      child: MediaQuery.withClampedTextScaling(
        minScaleFactor: 1.0,
        maxScaleFactor: 1.0, // 시스템 폰트 크기 변경 무시
        child: Padding(
          padding: EdgeInsets.all(8.w),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 이미지 영역 (고정 크기)
              SizedBox(
                width: double.infinity,
                height: 120.h,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8.r),
                  child: Container(
                    color: Colors.grey[200],
                    child: recipe.imageUrl != null && recipe.imageUrl!.isNotEmpty
                        ? Image.network(
                            recipe.imageUrl!,
                            width: double.infinity,
                            height: 120.h,
                            fit: BoxFit.cover,
                            errorBuilder: (context, error, stackTrace) => Center(
                              child: Icon(Icons.restaurant, size: 32.sp, color: Colors.grey),
                            ),
                          )
                        : Center(
                            child: Icon(Icons.restaurant, size: 32.sp, color: Colors.grey),
                          ),
                  ),
                ),
              ),
              SizedBox(height: 4.h),
              // 매칭 퍼센트 배지 (왼쪽 정렬, 고정 높이)
              SizedBox(
                height: 20.h,
                child: recipe.matchPercentage != null && recipe.matchPercentage! > 0
                    ? Align(
                        alignment: Alignment.centerLeft,
                        child: Container(
                          padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 3.h),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryOrange,
                            borderRadius: BorderRadius.circular(12.r),
                          ),
                          child: Text(
                            '${recipe.matchPercentage}% 일치',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 9.sp,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      )
                    : const SizedBox.shrink(),
              ),
              SizedBox(height: 4.h),
              // 제목 (고정 높이)
              SizedBox(
                height: 32.h,
                child: Text(
                  recipe.title,
                  style: TextStyle(
                    fontSize: 11.sp,
                    fontWeight: FontWeight.w600,
                    height: 1.2,
                    color: AppTheme.textPrimary,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
