import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:showcaseview/showcaseview.dart';
import 'package:url_launcher/url_launcher.dart';
import '../widgets/widgets.dart';
import '../widgets/ad_banner_widget.dart';
import '../providers/ingredients_provider.dart';
import '../providers/api/recipe_api_provider.dart';
import '../providers/api/ingredient_api_provider.dart';
import '../providers/api/api_connection_provider.dart';
import '../providers/recipe_recommendations_provider.dart';
import '../providers/async_state_manager.dart';
import '../models/api/api_recipe.dart';
import '../models/api/api_ingredient.dart';
import '../services/interstitial_ad_manager.dart';
import '../services/analytics_service.dart';
import 'add_ingredient_screen.dart';
import 'my_fridge_screen.dart';

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

    // 선택된 식재료가 있으면 처리
    if (result != null && result.isNotEmpty && mounted) {
      ref.read(selectedIngredientsProvider.notifier).addIngredients(result);
      SnackBarHelper.showSnackBar(
        context,
        '${result.length}개의 식재료가 추가되었습니다!',
        backgroundColor: AppTheme.primaryOrange,
      );

      //  Firebase Analytics 이벤트 기록
      AnalyticsService().logAddIngredients(result);

      // 🎯 수익성 극대화: 식재료 추가 완료 후 전면 광고 기회
      for (int i = 0; i < result.length; i++) {
        await InterstitialAdManager().onIngredientAdded();
      }
    }
  }

  void _removeIngredient(String ingredient) {
    ref.read(selectedIngredientsProvider.notifier).removeIngredient(ingredient);
  }

  void _toggleShowAllIngredients() {
    // 더보기 버튼을 누르면 나의냉장고 화면으로 이동
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => const MyFridgeScreen(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final selectedIngredients = ref.watch(selectedIngredientsProvider);
    final showAllIngredients = ref.watch(showAllIngredientsProvider);
    
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        backgroundColor: AppTheme.backgroundWhite,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
        centerTitle: true,
        surfaceTintColor: AppTheme.backgroundWhite, // 스크롤 시 색상 변경 방지
        scrolledUnderElevation: 0, // 스크롤 시 elevation 변경 방지
        title: const Text(
          '냉털레시피',
          style: TextStyle(
            fontFamily: 'Brandon Grotesque',
            fontSize: 24,
            fontWeight: FontWeight.w500,
            letterSpacing: -0.24,
            color: AppTheme.textPrimary,
          ),
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
                        minHeight: MediaQuery.of(context).size.height - 350,
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const SizedBox(height: AppTheme.spacingXL),
                          const _FridgeIcon(),
                          const SizedBox(height: AppTheme.spacingM),
                          selectedIngredients.isEmpty
                              ? const _EmptyStateMessage()
                              : _SelectedIngredientsSection(
                                  ingredients: selectedIngredients,
                                  showAll: showAllIngredients,
                                  onRemove: _removeIngredient,
                                  onToggleShowAll: _toggleShowAllIngredients,
                                ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 295), // 레시피 영역 차지할 공간 확보
                  ],
                ),
              ),
            ),

            // 하단 레시피 영역 고정 (바텀 네비게이션 바 위로 16px)
            Positioned(
              left: 0,
              right: 0,
              bottom: 16, // 바텀 네비게이션 바와 16px 간격
              child: Container(
                height: 295,
                color: AppTheme.backgroundWhite,
                child: selectedIngredients.isEmpty
                    ? _RecipeRecommendationSection()
                    : _RecipeRecommendationsSection(ingredients: selectedIngredients),
              ),
            ),

            // 플로팅 액션 버튼 - 냉장고 영역 하단에 위치
            Positioned(
              right: 16,
              bottom: 295 + 16 + 16, // 레시피 영역 높이 + 바텀 간격 + 버튼 여백
              child: Showcase(
                key: homeScreenAddButtonKey,
                description: '냉장고에 식재료를 추가하려면 이 버튼을 누르세요!',
                onTargetClick: _onAddButtonPressed,
                disposeOnTap: true,
                child: SizedBox(
                  width: 45,
                  height: 45,
                  child: FloatingActionButton(
                    onPressed: _onAddButtonPressed,
                    backgroundColor: Colors.white,
                    elevation: 0,
                    heroTag: "home_fab",
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(13),
                      side: const BorderSide(
                        color: AppTheme.primaryOrange,
                        width: 2,
                      ),
                    ),
                    child: const Icon(
                      Icons.add,
                      color: AppTheme.primaryOrange,
                      size: 26,
                    ),
                  ),
                ),
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
      width: 120,
      height: 120,
      decoration: const BoxDecoration(
        color: AppTheme.backgroundWhite,
        borderRadius: BorderRadius.all(Radius.circular(AppTheme.radiusMedium)),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
        child: Image.asset(
          'assets/logos/app_logo.png',
          width: 120,
          height: 120,
          fit: BoxFit.contain,
        ),
      ),
    );
  }
}

/// 빈 상태 메시지 위젯 - 재빌드 시에도 안정적인 렌더링을 위한 정적 위젯
class _EmptyStateMessage extends StatelessWidget {
  const _EmptyStateMessage();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        // 메인 메시지
        Text(
          '냉장고가 비어있어요',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w600,
            color: AppTheme.textPrimary,
          ),
        ),
        
        SizedBox(height: AppTheme.spacingS),
        
        // 서브 메시지
        Text(
          '[+] 버튼을 눌러 식재료를 추가해보세요!',
          style: TextStyle(
            fontSize: 14,
            color: AppTheme.textPrimary,
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
    final selectedIngredients = ref.watch(selectedIngredientsProvider);
    final recipesState = selectedIngredients.isNotEmpty
        ? ref.watch(recipeApiProvider)
        : null;
    final isApiOnline = ref.watch(isApiOnlineProvider);
    final isApiClientInitialized = ref.watch(apiClientInitializedProvider);

    // API 클라이언트가 초기화되고 보유 재료가 있을 때 API 호출
    if (kDebugMode) debugPrint('🏠 [Home Screen] API Client Initialized: $isApiClientInitialized, Selected Ingredients: ${selectedIngredients.length}');

    return Container(
      padding: const EdgeInsets.only(left: AppTheme.spacingM, top: AppTheme.spacingM),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 섹션 제목 - 식재료 유무에 따라 동적 변경
          Padding(
            padding: const EdgeInsets.only(bottom: AppTheme.spacingM),
            child: Text(
              selectedIngredients.isNotEmpty ? '맞춤 레시피' : '추천 레시피',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
          ),

          // 가로 스크롤 레시피 카드들
          SizedBox(
            height: 160, // 카드 높이와 동일하게 고정
            child: selectedIngredients.isEmpty
                // 식재료가 없는 경우: 친근한 메시지 바로 표시
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.restaurant_menu,
                          size: 48,
                          color: AppTheme.primaryOrange.withValues(alpha: 0.5),
                        ),
                        const SizedBox(height: AppTheme.spacingS),
                        const Text(
                          '냉장고에 재료를 추가하면\n맛있는 레시피를 추천해드려요!',
                          style: TextStyle(
                            fontSize: 12,
                            color: AppTheme.textSecondary,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  )
                // 식재료가 있는 경우: 맞춤 레시피 표시
                : _buildCustomRecipeList(context, recipesState!, selectedIngredients, isApiOnline, isApiClientInitialized),
          ),
        ],
      ),
    );
  }

  /// 맞춤 레시피 목록 위젯 빌드
  Widget _buildCustomRecipeList(
    BuildContext context,
    AsyncValue<List<ApiRecipe>> recipesState,
    List<String> selectedIngredients,
    bool isApiOnline,
    bool isApiClientInitialized,
  ) {
    return recipesState.when(
      data: (recipes) {
        if (recipes.isEmpty) {
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.search_off,
                  size: 48,
                  color: AppTheme.textSecondary,
                ),
                SizedBox(height: AppTheme.spacingS),
                Text(
                  '조건에 맞는 레시피가 없습니다',
                  style: TextStyle(
                    fontSize: 12,
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          );
        }

        return ListView.builder(
          scrollDirection: Axis.horizontal,
          itemCount: recipes.length,
          itemBuilder: (context, index) {
            final recipe = recipes[index];
            return _RecipeCard(
              recipe: recipe,
              isLast: index == recipes.length - 1,
              onTap: () => _handleRecipeTap(context, recipe),
            );
          },
        );
      },
      loading: () => const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(
              color: AppTheme.primaryOrange,
            ),
            SizedBox(height: AppTheme.spacingS),
            Text(
              '맛있는 레시피를 찾고 있어요!',
              style: TextStyle(
                fontSize: 12,
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      ),
      error: (error, stack) => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              isApiOnline ? Icons.error_outline : Icons.wifi_off,
              size: 48,
              color: AppTheme.textSecondary,
            ),
            const SizedBox(height: AppTheme.spacingS),
            Text(
              isApiOnline
                  ? '레시피를 불러올 수 없습니다'
                  : '네트워크 연결을 확인해주세요',
              style: AppTheme.bodySmall.copyWith(
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 레시피 탭 이벤트 처리
  void _handleRecipeTap(BuildContext context, ApiRecipe recipe) async {
    final url = recipe.url;
    if (url != null && url.isNotEmpty) {
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
    } else {
      if (context.mounted) {
        SnackBarHelper.showSnackBar(
          context,
          '레시피 링크가 없습니다.',
          backgroundColor: Colors.orange,
        );
      }
    }
  }
}

/// 레시피 카드 위젯
class _RecipeCard extends StatelessWidget {
  final ApiRecipe recipe;
  final bool isLast;
  final VoidCallback? onTap;

  const _RecipeCard({
    required this.recipe,
    this.isLast = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 160,
        height: 160,
        margin: EdgeInsets.only(
          right: isLast ? 0 : AppTheme.spacingM,
        ),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 레시피 이미지
            ClipRRect(
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(12),
                topRight: Radius.circular(12),
              ),
              child: Image.network(
                recipe.imageUrl ?? 'https://picsum.photos/300/200?random=${recipe.id.hashCode.abs() % 1000}',
                width: double.infinity,
                height: 110,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) {
                  return Container(
                    height: 110,
                    color: AppTheme.backgroundGray,
                    child: const Center(
                      child: Icon(
                        Icons.restaurant,
                        size: 36,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  );
                },
              ),
            ),

            // 레시피 정보
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppTheme.spacingS,
                vertical: 8, // 세로 패딩을 카드에 맞게 조정
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    recipe.name,
                    style: const TextStyle(
                      fontSize: 14, // 폰트 크기를 카드에 맞게 조정
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),

                  const SizedBox(height: 4), // 간격을 카드에 맞게 조정

                  // 조리시간이 0보다 클 때만 표시
                  if (recipe.cookingTimeMinutes > 0) ...[
                    Row(
                      children: [
                        const Icon(
                          Icons.access_time,
                          size: 12, // 아이콘 크기를 카드에 맞게 조정
                          color: AppTheme.textSecondary,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${recipe.cookingTimeMinutes}분',
                          style: const TextStyle(
                            fontSize: 12, // 폰트 크기를 카드에 맞게 조정
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 선택된 식재료 표시 섹션
class _SelectedIngredientsSection extends StatelessWidget {
  final List<String> ingredients;
  final bool showAll;
  final Function(String) onRemove;
  final VoidCallback onToggleShowAll;

  const _SelectedIngredientsSection({
    required this.ingredients,
    required this.showAll,
    required this.onRemove,
    required this.onToggleShowAll,
  });

  @override
  Widget build(BuildContext context) {
    // 4줄까지만 표시 (3개씩 4줄 = 12개)
    final displayIngredients = showAll ? ingredients : ingredients.take(12).toList();
    final hasMore = ingredients.length > 12;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppTheme.spacingM),
      child: Column(
        children: [
          // 냉장고 상태 제목
          const Text(
            '냉장고 현황',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: AppTheme.textPrimary,
            ),
          ),
          
          const SizedBox(height: AppTheme.spacingM),
          
          // 선택된 재료 개수
          Text(
            '총 ${ingredients.length}개의 식재료',
            style: const TextStyle(
              fontSize: 14,
              color: AppTheme.textSecondary,
            ),
          ),
          
          const SizedBox(height: AppTheme.spacingM),
          
          // 재료 칩들
          Wrap(
            spacing: AppTheme.spacingS,
            runSpacing: AppTheme.spacingS,
            children: [
              ...displayIngredients.map((ingredient) => _IngredientChip(
                ingredient: ingredient,
                onRemove: () => onRemove(ingredient),
              )),
              
              // 더보기/접기 버튼
              if (hasMore)
                GestureDetector(
                  onTap: onToggleShowAll,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: AppTheme.spacingS,
                    ),
                    decoration: BoxDecoration(
                      color: AppTheme.lightOrange,
                      borderRadius: BorderRadius.circular(50),
                      border: Border.all(
                        color: AppTheme.primaryOrange,
                        width: 1,
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          showAll ? '접기' : '더보기 +${ingredients.length - 12}',
                          style: const TextStyle(
                            fontSize: 14,
                            color: AppTheme.primaryOrange,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(
                          showAll ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                          size: 16,
                          color: AppTheme.primaryOrange,
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
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
      padding: const EdgeInsets.symmetric(
        horizontal: 12,
        vertical: AppTheme.spacingS,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(50),
        border: Border.all(
          color: const Color(0xFFD7D7D7),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            ingredient,
            style: const TextStyle(
              fontSize: 14,
              color: AppTheme.iconPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(width: 12),
          GestureDetector(
            onTap: onRemove,
            child: const Icon(
              Icons.close,
              size: 14,
              color: Color(0xFF999999),
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

        return Padding(
          padding: const EdgeInsets.all(AppTheme.spacingM),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 추천 제목
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    '맞춤 레시피 추천',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  Text(
                    '${response.total}개',
                    style: const TextStyle(
                      fontSize: 14,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              // 요약
              Text(
                response.summary,
                style: const TextStyle(
                  fontSize: 12,
                  color: AppTheme.textSecondary,
                ),
              ),
              const SizedBox(height: AppTheme.spacingM),
              // 레시피 카드 리스트 (가로 스크롤)
              SizedBox(
                height: 195,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: response.recipes.take(10).length,
                  itemBuilder: (context, index) {
                    final recipe = response.recipes[index];
                    return _RecommendedRecipeCard(recipe: recipe);
                  },
                ),
              ),
            ],
          ),
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
    const double cardHeight = 195.0;
    const double imageHeight = cardHeight * 2 / 3; // 130px (2/3)
    const double textHeight = cardHeight - imageHeight;  // 65px (나머지)

    return GestureDetector(
      onTap: () => _openRecipeUrl(context),
      child: MediaQuery.withClampedTextScaling(
        minScaleFactor: 1.0,
        maxScaleFactor: 1.0, // 시스템 폰트 크기 변경 무시
        child: Container(
          width: 160,
          height: cardHeight,
          margin: const EdgeInsets.only(right: AppTheme.spacingM),
          clipBehavior: Clip.hardEdge, // 하드 클리핑으로 변경
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.1),
                blurRadius: 4,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            children: [
              // 이미지 영역 (2/3 = 130px)
              SizedBox(
                height: imageHeight,
                width: 160,
                child: recipe.imageUrl != null && recipe.imageUrl!.isNotEmpty
                    ? Image.network(
                        recipe.imageUrl!,
                        height: imageHeight,
                        width: 160,
                        fit: BoxFit.cover,
                        errorBuilder: (context, error, stackTrace) => Container(
                          height: imageHeight,
                          width: 160,
                          color: Colors.grey[200],
                          child: const Icon(Icons.restaurant, size: 40, color: Colors.grey),
                        ),
                      )
                    : Container(
                        height: imageHeight,
                        width: 160,
                        color: Colors.grey[200],
                        child: const Icon(Icons.restaurant, size: 40, color: Colors.grey),
                      ),
              ),
              // 텍스트 영역 (나머지 = 65px)
              Container(
                height: textHeight,
                padding: const EdgeInsets.fromLTRB(8, 6, 8, 6),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 제목 (남은 공간 사용)
                    Expanded(
                      child: Text(
                        recipe.title,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          height: 1.2,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    // 매칭률 (하단 고정)
                    SizedBox(
                      height: 18,
                      child: Align(
                        alignment: Alignment.centerRight,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppTheme.lightOrange,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            '${(recipe.matchScore * 100).toInt()}% 일치',
                            style: const TextStyle(
                              fontSize: 9,
                              color: AppTheme.primaryOrange,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
