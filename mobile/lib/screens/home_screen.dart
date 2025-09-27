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
import '../models/api/api_recipe.dart';
import '../models/api/api_ingredient.dart';
import '../services/interstitial_ad_manager.dart';
import '../services/analytics_service.dart';
import 'add_ingredient_screen.dart';
import 'my_fridge_screen.dart';
import 'recipe_detail_screen.dart';

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
      if (kDebugMode) debugPrint('🏠 [Home Screen] Initializing API client...');
      await initializeApiClient(ref);
      if (kDebugMode) debugPrint('🏠 [Home Screen] API client initialization completed');

      // API 클라이언트 초기화 완료 후 기본 데이터 로드
      final isApiClientInitialized = ref.read(apiClientInitializedProvider);
      if (isApiClientInitialized) {
        if (kDebugMode) debugPrint('🏠 [Home Screen] Loading default recommended recipes...');
        ref.read(recipeApiProvider.notifier).loadPopularRecipes(size: 6);

        if (kDebugMode) debugPrint('🏠 [Home Screen] Loading ingredients for selection...');
        ref.read(ingredientApiProvider.notifier).loadIngredients(
          filter: const IngredientSearchFilter(
            page: 1,
            size: 200, // 전체 식재료 로드
          ),
        );
      } else {
        if (kDebugMode) debugPrint('⚠️ [Home Screen] API client not initialized, skipping data load');
      }
    });
  }

  Future<void> _onRefresh() async {
    if (kDebugMode) debugPrint('🔄 [Home Screen] Pull to refresh triggered');

    // 인기 레시피 새로고침
    await ref.read(recipeApiProvider.notifier).refresh();

    // 식재료 목록도 새로고침 (옵션)
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
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: SizedBox(
            height: MediaQuery.of(context).size.height -
                   (AppBar().preferredSize.height + MediaQuery.of(context).padding.top),
            child: Stack(
              children: [
                Column(
                  children: [
                // 상단 배너 광고 (수익성 극대화 - 첫 화면 최상단)
                const AdBannerWidget(isTop: true),
              
              // 냉장고 부분 - 높이 제한
              SizedBox(
                height: 400, // 고정 높이로 설정 (551에서 400으로 줄임)
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(0, 0, 0, 16), // 하단 여백을 20에서 16으로 줄임 (20% 감소)
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // 냉장고 아이콘 - 주황색 둥근 사각형
                      const _FridgeIcon(),
                      
                      const SizedBox(height: AppTheme.spacingM),
                      
                      // 메시지 영역 또는 선택된 재료 표시
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
              ),
              
              // 추천 레시피 부분 - 고정 높이
              const SizedBox(
                height: 220, // 제목 + 카드(160px) + 패딩을 고려한 고정 높이
                child: _RecipeRecommendationSection(),
              ),
              
              // 남은 공간 채우기 (15px로 줄임)
              const SizedBox(height: 15),
              
            ],
          ),
          
          // 플로팅 액션 버튼 - 냉장고 영역 우하단에 위치
          Positioned(
            right: 16, // body 전체 기준 우측에서 16px 마진
            bottom: 220 + 80 + 15, // 추천 레시피 높이(220) + 하단 네비(80) + 마진(15)
            child: Showcase(
              key: homeScreenAddButtonKey,
              description: '냉장고에 식재료를 추가하려면 이 버튼을 누르세요!',
              onTargetClick: _onAddButtonPressed,
              disposeOnTap: true,
              child: FloatingActionButton(
                onPressed: _onAddButtonPressed,
                backgroundColor: Colors.white,
                elevation: 0, // 그림자 제거
                heroTag: "home_fab", // Hero 애니메이션 방지
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: const BorderSide(
                    color: AppTheme.primaryOrange,
                    width: 2,
                  ),
                ),
                child: const Padding(
                  padding: EdgeInsets.all(4),
                  child: Icon(
                    Icons.add,
                    color: AppTheme.primaryOrange,
                    size: 32,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
            ),
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
    final recipesState = ref.watch(recipeApiProvider);
    final isApiOnline = ref.watch(isApiOnlineProvider);
    final isApiClientInitialized = ref.watch(apiClientInitializedProvider);

    // API 클라이언트가 초기화되고 보유 재료가 있을 때 API 호출
    if (kDebugMode) debugPrint('🏠 [Home Screen] API Client Initialized: $isApiClientInitialized, Selected Ingredients: ${selectedIngredients.length}');

    // API 클라이언트 초기화 상태 변화 감지
    ref.listen(apiClientInitializedProvider, (previous, next) {
      if (kDebugMode) debugPrint('🏠 [Home Screen] API Client initialization changed: $previous → $next');
      if (next && selectedIngredients.isNotEmpty) {
        if (kDebugMode) debugPrint('🚀 [Home Screen] API initialized, triggering recipe call');
        ref.read(recipeApiProvider.notifier).loadRecipesByIngredients(selectedIngredients);
      }
    });

    if (isApiClientInitialized && selectedIngredients.isNotEmpty) {
      ref.listen(selectedIngredientsProvider, (previous, next) {
        if (kDebugMode) debugPrint('👂 [Home Screen] Ingredients changed from ${previous?.length ?? 0} to ${next.length}');
        if (next.isNotEmpty && (previous == null || previous.isEmpty || previous.length != next.length)) {
          // 재료가 새로 추가되거나 변경되었을 때 API 호출
          if (kDebugMode) debugPrint('🚀 [Home Screen] Triggering recipe API call with ingredients: $next');
          ref.read(recipeApiProvider.notifier).loadRecipesByIngredients(next);
        }
      });
    } else {
      if (kDebugMode) debugPrint('⚠️ [Home Screen] API call conditions not met - API Initialized: $isApiClientInitialized, Has Ingredients: ${selectedIngredients.isNotEmpty}');
    }

    return Container(
      padding: const EdgeInsets.only(left: AppTheme.spacingM, top: AppTheme.spacingM),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 섹션 제목 - 식재료 유무에 따라 동적 변경
          Padding(
            padding: const EdgeInsets.only(bottom: AppTheme.spacingM),
            child: Text(
              selectedIngredients.isNotEmpty ? '맞춤 레시피' : '인기 레시피',
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
            child: recipesState.when(
              data: (recipes) {
                if (recipes.isEmpty) {
                  // 식재료가 있는데 레시피가 없는 경우와 식재료가 없는 경우 구분
                  if (selectedIngredients.isNotEmpty) {
                    return Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.search_off,
                            size: 48,
                            color: AppTheme.textSecondary,
                          ),
                          const SizedBox(height: AppTheme.spacingS),
                          Text(
                            '조건에 맞는 레시피가 없습니다',
                            style: AppTheme.bodySmall.copyWith(
                              color: AppTheme.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    );
                  } else {
                    return Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.restaurant_menu,
                            size: 48,
                            color: AppTheme.textSecondary,
                          ),
                          const SizedBox(height: AppTheme.spacingS),
                          Text(
                            '레시피를 불러오고 있습니다...',
                            style: AppTheme.bodySmall.copyWith(
                              color: AppTheme.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    );
                  }
                }

                return ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: recipes.length,
                  itemBuilder: (context, index) {
                    final recipe = recipes[index];

                    return _RecipeCard(
                      recipe: recipe,
                      isLast: index == recipes.length - 1,
                      onTap: () async {
                        // URL로 이동 (url_launcher 패키지 사용)
                        final url = recipe.url;
                        if (url != null && url.isNotEmpty) {
                          try {
                            final uri = Uri.parse(url);
                            if (await canLaunchUrl(uri)) {
                              await launchUrl(uri, mode: LaunchMode.externalApplication);
                            } else {
                              SnackBarHelper.showSnackBar(
                                context,
                                '링크를 열 수 없습니다.',
                                backgroundColor: Colors.red,
                              );
                            }
                          } catch (e) {
                            SnackBarHelper.showSnackBar(
                              context,
                              '링크를 열 수 없습니다: $e',
                              backgroundColor: Colors.red,
                            );
                          }
                        } else {
                          SnackBarHelper.showSnackBar(
                            context,
                            '레시피 링크가 없습니다.',
                            backgroundColor: Colors.orange,
                          );
                        }
                      },
                    );
                  },
                );
              },
              loading: () {
                // API 클라이언트 초기화 상태에 따른 로딩 메시지
                if (!isApiClientInitialized) {
                  return const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(
                          color: AppTheme.primaryOrange,
                        ),
                        SizedBox(height: AppTheme.spacingS),
                        Text(
                          '맛있는 레시피를 준비하고 있어요!',
                          style: TextStyle(
                            fontSize: 12,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  );
                } else if (selectedIngredients.isNotEmpty) {
                  return const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(
                          color: AppTheme.primaryOrange,
                        ),
                        SizedBox(height: AppTheme.spacingS),
                        Text(
                          '당신만을 위한 레시피를 찾고 있어요!',
                          style: TextStyle(
                            fontSize: 12,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  );
                } else {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(
                          Icons.restaurant_menu,
                          size: 48,
                          color: AppTheme.textSecondary,
                        ),
                        const SizedBox(height: AppTheme.spacingS),
                        Text(
                          '식재료를 추가하면 레시피를 추천해드립니다',
                          style: AppTheme.bodySmall.copyWith(
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  );
                }
              },
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
                    if (!isApiOnline) ...[
                      const SizedBox(height: AppTheme.spacingS),
                      Text(
                        '오프라인 모드로 제한된 레시피를 제공합니다',
                        style: TextStyle(
                          fontSize: 10,
                          color: AppTheme.textSecondary.withValues(alpha: 0.7),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
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
        width: 140,
        height: 160, // 카드 높이를 160으로 고정
        margin: EdgeInsets.only(
          right: isLast ? 0 : AppTheme.spacingM, // 마지막 아이템은 우측 마진 없음
        ),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(AppTheme.radiusCard),
          border: Border.all(
            color: Colors.grey.withValues(alpha: 0.2),
            width: 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 레시피 이미지
            Container(
              height: 100, // 이미지 높이를 카드에 맞게 조정
              decoration: BoxDecoration(
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(AppTheme.radiusCard),
                  topRight: Radius.circular(AppTheme.radiusCard),
                ),
              ),
              child: ClipRRect(
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(AppTheme.radiusCard),
                  topRight: Radius.circular(AppTheme.radiusCard),
                ),
                child: Image.network(
                  recipe.imageUrl ?? 'https://picsum.photos/300/200?random=${recipe.id.hashCode.abs() % 1000}',
                  width: double.infinity,
                  height: 100,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) {
                    return Container(
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
