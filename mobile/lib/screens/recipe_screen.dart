import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';
import '../providers/recipe_provider.dart';
import '../providers/ingredients_provider.dart';
import '../models/recipe.dart';
import '../widgets/custom_toggle_switch.dart';

class RecipeScreen extends ConsumerStatefulWidget {
  const RecipeScreen({super.key});

  @override
  ConsumerState<RecipeScreen> createState() => _RecipeScreenState();
}

class _RecipeScreenState extends ConsumerState<RecipeScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    // 스크롤 리스너 추가
    _scrollController.addListener(_onScroll);
    // 첫 페이지 로드
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(paginatedRecipeProvider.notifier).loadFirstPage();
    });
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    super.dispose();
  }

  /// 스크롤 이벤트 처리
  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      // 하단에서 200px 전에 다음 페이지 로드
      ref.read(paginatedRecipeProvider.notifier).loadNextPage();
    }
  }

  @override
  Widget build(BuildContext context) {
    final recipeState = ref.watch(paginatedRecipeProvider);
    final showOnlyFavorites = ref.watch(showOnlyFavoritesProvider);

    // 즐겨찾기 필터 변경 시 새로고침
    ref.listen(showOnlyFavoritesProvider, (previous, next) {
      ref.read(paginatedRecipeProvider.notifier).refresh();
    });

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        backgroundColor: AppTheme.backgroundWhite,
        elevation: 0,
        automaticallyImplyLeading: false,
        title: const Text(
          '요리하기',
          style: TextStyle(
            color: AppTheme.textPrimary,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
        ),
        actions: [
          // 즐겨찾기 토글 버튼
          Consumer(
            builder: (context, ref, child) {
              final showOnlyFavorites = ref.watch(showOnlyFavoritesProvider);
              return Row(
                children: [
                  const Text(
                    '즐겨찾기',
                    style: TextStyle(
                      fontSize: 14,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(width: AppTheme.spacingM),
                  CustomToggleSwitch(
                    value: showOnlyFavorites,
                    onChanged: (value) {
                      ref.read(showOnlyFavoritesProvider.notifier).state = value;
                    },
                  ),
                ],
              );
            },
          ),
          const SizedBox(width: AppTheme.spacingS),
        ],
      ),
      body: _buildBody(recipeState, showOnlyFavorites),
    );
  }


  /// Body 구현 (무한스크롤 지원)
  Widget _buildBody(RecipeListState recipeState, bool showOnlyFavorites) {
    return Column(
      children: [
        // 검색바
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: Container(
            height: 56,
            decoration: BoxDecoration(
              color: const Color(0xFFF3F4F9),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: Icon(
                    Icons.search,
                    color: Color(0xFF5D577E),
                    size: 20,
                  ),
                ),
                Expanded(
                  child: TextFormField(
                    onChanged: (value) {
                      ref.read(recipeSearchQueryProvider.notifier).state = value;
                      ref.read(paginatedRecipeProvider.notifier).refresh();
                    },
                    style: const TextStyle(
                      fontSize: 14,
                      color: Color(0xFF27214D),
                    ),
                    decoration: const InputDecoration(
                      hintText: '레시피 검색',
                      border: InputBorder.none,
                      enabledBorder: InputBorder.none,
                      focusedBorder: InputBorder.none,
                      contentPadding: EdgeInsets.symmetric(vertical: 16),
                      hintStyle: TextStyle(
                        fontSize: 14,
                        color: Color(0xFFC2BDBD),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        
        // 구분선
        Container(
          height: 1,
          color: AppTheme.borderGray,
        ),
        
        // 콘텐츠
        Expanded(
          child: _buildContent(recipeState, showOnlyFavorites),
        ),
      ],
    );
  }

  /// 콘텐츠 구현
  Widget _buildContent(RecipeListState recipeState, bool showOnlyFavorites) {
    // 에러 상태
    if (recipeState.error != null) {
      return _buildErrorState(recipeState.error!);
    }

    // 빈 즐겨찾기 상태
    if (recipeState.recipes.isEmpty && showOnlyFavorites && !recipeState.isLoading) {
      return _buildEmptyFavoritesState();
    }

    // 검색 결과 없음
    if (recipeState.recipes.isEmpty && !recipeState.isLoading) {
      return _buildEmptySearchState();
    }

    // 레시피 그리드
    return _buildRecipeGrid(recipeState);
  }

  /// 레시피 그리드 구현 (무한스크롤 지원)
  Widget _buildRecipeGrid(RecipeListState recipeState) {
    return ListView.separated(
      controller: _scrollController,
      padding: const EdgeInsets.all(AppTheme.spacingM),
      itemCount: recipeState.recipes.length + (recipeState.hasMore ? 1 : 0),
      separatorBuilder: (context, index) {
        // 광고 영역을 특정 위치에 삽입
        if (index == 2) {
          return _buildAdBanner();
        }
        return const SizedBox(height: AppTheme.spacingM);
      },
      itemBuilder: (context, index) {
        // 로딩 인디케이터 표시
        if (index >= recipeState.recipes.length) {
          return _buildLoadingItem();
        }

        final recipe = recipeState.recipes[index];
        return GestureDetector(
          onTap: () {
            Navigator.of(context).pushNamed(
              '/recipe-detail',
              arguments: recipe,
            );
          },
          child: RecipeListCard(recipe: recipe),
        );
      },
    );
  }

  /// 광고 배너
  Widget _buildAdBanner() {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: AppTheme.spacingM),
      height: 120,
      decoration: BoxDecoration(
        color: const Color(0xFFFFF2E7),
        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
        border: Border.all(
          color: AppTheme.primaryOrange.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(AppTheme.spacingM),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    '앗! 재료가 부족한가요? 😱 😱',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: AppTheme.spacingS),
                  const Row(
                    children: [
                      Text(
                        '🛍️ ',
                        style: TextStyle(fontSize: 16),
                      ),
                      Text(
                        '쿠팡으로 재료사러 가기 ',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.primaryOrange,
                        ),
                      ),
                      Text(
                        '🛒',
                        style: TextStyle(fontSize: 16),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  const Text(
                    '지금 바로 주문하면 내일 바로 받아볼 수 있어요!',
                    style: TextStyle(
                      fontSize: 11,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
          ),
          Container(
            width: 60,
            height: 60,
            margin: const EdgeInsets.all(AppTheme.spacingM),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  '🍎🥝',
                  style: TextStyle(fontSize: 20),
                ),
                Container(
                  width: 20,
                  height: 20,
                  decoration: const BoxDecoration(
                    color: AppTheme.primaryOrange,
                    shape: BoxShape.circle,
                  ),
                  child: const Center(
                    child: Text(
                      '2',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 로딩 아이템
  Widget _buildLoadingItem() {
    return Container(
      height: 120,
      decoration: BoxDecoration(
        color: Colors.grey.withOpacity(0.1),
        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
      ),
      child: const Center(
        child: CircularProgressIndicator(
          valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primaryOrange),
        ),
      ),
    );
  }

  /// 에러 상태
  Widget _buildErrorState(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppTheme.spacingXL),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              size: 64,
              color: AppTheme.textSecondary,
            ),
            const SizedBox(height: AppTheme.spacingM),
            const Text(
              '오류가 발생했습니다',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: AppTheme.spacingS),
            Text(
              error,
              style: const TextStyle(
                fontSize: 14,
                color: AppTheme.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppTheme.spacingL),
            CustomButton(
              text: '다시 시도',
              onPressed: () {
                ref.read(paginatedRecipeProvider.notifier).refresh();
              },
              type: ButtonType.primary,
            ),
          ],
        ),
      ),
    );
  }

  /// 빈 검색 결과 상태
  Widget _buildEmptySearchState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppTheme.spacingXL),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.search_off,
              size: 64,
              color: AppTheme.textSecondary,
            ),
            const SizedBox(height: AppTheme.spacingM),
            const Text(
              '검색 결과가 없습니다',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: AppTheme.spacingS),
            const Text(
              '다른 검색어로 시도해보세요',
              style: TextStyle(
                fontSize: 14,
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 즐겨찾기 빈 상태 화면
  Widget _buildEmptyFavoritesState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppTheme.spacingXL),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                color: AppTheme.lightOrange,
                borderRadius: BorderRadius.circular(AppTheme.radiusLarge),
              ),
              child: const Icon(
                Icons.favorite_border,
                size: 60,
                color: AppTheme.primaryOrange,
              ),
            ),
            const SizedBox(height: AppTheme.spacingXL),
            const Text(
              '즐겨찾기한 레시피가 없어요',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: AppTheme.spacingM),
            const Text(
              '마음에 드는 레시피에 하트를 눌러\n즐겨찾기에 추가해보세요!',
              style: TextStyle(
                fontSize: 16,
                color: AppTheme.textSecondary,
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppTheme.spacingXL),
            CustomButton(
              text: '모든 레시피 보기',
              onPressed: () {
                ref.read(showOnlyFavoritesProvider.notifier).state = false;
              },
              type: ButtonType.secondary,
              height: 48,
            ),
          ],
        ),
      ),
    );
  }
}

/// 레시피 카드 위젯
class RecipeCard extends ConsumerWidget {
  final Recipe recipe;

  const RecipeCard({
    super.key,
    required this.recipe,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favoriteRecipeIds = ref.watch(favoriteRecipesProvider);
    final isFavorite = favoriteRecipeIds.contains(recipe.id);
    final userIngredients = ref.watch(selectedIngredientsProvider);
    final availableCount = recipe.getAvailableIngredients(userIngredients).length;
    final totalCount = recipe.ingredients.length;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 이미지와 즐겨찾기 버튼
          Expanded(
            flex: 3,
            child: Stack(
              children: [
                // 레시피 이미지
                Container(
                  width: double.infinity,
                  decoration: const BoxDecoration(
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(AppTheme.radiusMedium),
                      topRight: Radius.circular(AppTheme.radiusMedium),
                    ),
                  ),
                  child: ClipRRect(
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(AppTheme.radiusMedium),
                      topRight: Radius.circular(AppTheme.radiusMedium),
                    ),
                    child: Image.network(
                      'https://picsum.photos/400/250?random=${recipe.id.hashCode.abs() % 1000}',
                      fit: BoxFit.cover,
                      width: double.infinity,
                      height: double.infinity,
                      errorBuilder: (context, error, stackTrace) {
                        return Container(
                          color: AppTheme.lightOrange,
                          child: const Center(
                            child: Icon(
                              Icons.restaurant,
                              size: 40,
                              color: AppTheme.primaryOrange,
                            ),
                          ),
                        );
                      },
                      loadingBuilder: (context, child, loadingProgress) {
                        if (loadingProgress == null) return child;
                        return Container(
                          color: AppTheme.lightOrange,
                          child: const Center(
                            child: CircularProgressIndicator(
                              valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primaryOrange),
                              strokeWidth: 2,
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ),
                // 즐겨찾기 버튼
                Positioned(
                  top: 8,
                  right: 8,
                  child: GestureDetector(
                    onTap: () {
                      ref.read(favoriteRecipesProvider.notifier).toggleFavorite(recipe.id);
                    },
                    child: Container(
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.9),
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.1),
                            blurRadius: 4,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Icon(
                        isFavorite ? Icons.favorite : Icons.favorite_border,
                        size: 18,
                        color: isFavorite ? AppTheme.primaryOrange : AppTheme.textSecondary,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          // 레시피 정보
          Container(
            height: 100,
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 레시피 이름
                Text(
                  recipe.name,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                // 레시피 설명
                Expanded(
                  child: Text(
                    recipe.description,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppTheme.textSecondary,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(height: 8),
                // 재료 현황 및 조리 시간
                Row(
                  children: [
                    const Icon(
                      Icons.kitchen,
                      size: 14,
                      color: AppTheme.textSecondary,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '$availableCount/$totalCount개',
                      style: TextStyle(
                        fontSize: 12,
                        color: availableCount == totalCount
                            ? AppTheme.primaryOrange
                            : AppTheme.textSecondary,
                        fontWeight: availableCount == totalCount
                            ? FontWeight.w600
                            : FontWeight.normal,
                      ),
                    ),
                    const Spacer(),
                    // 조리 시간
                    const Icon(
                      Icons.access_time,
                      size: 14,
                      color: AppTheme.textSecondary,
                    ),
                    const SizedBox(width: 2),
                    Text(
                      '${recipe.cookingTimeMinutes}분',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// 새로운 리스트 형태 레시피 카드 위젯
class RecipeListCard extends ConsumerWidget {
  final Recipe recipe;

  const RecipeListCard({
    super.key,
    required this.recipe,
  });

  /// 재료 보유 상태에 따른 색상 반환
  Color _getIngredientStatusColor(int availableCount, int totalCount) {
    final percentage = availableCount / totalCount;
    if (percentage >= 1.0) {
      return const Color(0xFF4CAF50); // 녹색 - 모든 재료 보유
    } else if (percentage >= 0.7) {
      return AppTheme.primaryOrange; // 주황색 - 대부분 재료 보유
    } else {
      return const Color(0xFFF44336); // 빨간색 - 재료 부족
    }
  }

  /// 재료 보유 상태 텍스트
  String _getIngredientStatusText(int availableCount, int totalCount) {
    if (availableCount == totalCount) {
      return '$totalCount개 재료 모두 보유';
    } else {
      return '$availableCount개 재료 보유 | 재료 총 ${totalCount}개';
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favoriteRecipeIds = ref.watch(favoriteRecipesProvider);
    final isFavorite = favoriteRecipeIds.contains(recipe.id);
    final userIngredients = ref.watch(selectedIngredientsProvider);
    final availableIngredients = recipe.getAvailableIngredients(userIngredients);
    final unavailableIngredients = recipe.getUnavailableIngredients(userIngredients);
    final availableCount = availableIngredients.length;
    final totalCount = recipe.ingredients.length;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppTheme.spacingM),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 레시피 제목과 즐겨찾기 버튼
            Row(
              children: [
                Expanded(
                  child: Text(
                    recipe.name,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                GestureDetector(
                  onTap: () {
                    ref.read(favoriteRecipesProvider.notifier).toggleFavorite(recipe.id);
                  },
                  child: Icon(
                    isFavorite ? Icons.favorite : Icons.favorite_border,
                    color: isFavorite ? AppTheme.primaryOrange : AppTheme.textSecondary,
                    size: 20,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppTheme.spacingS),
            
            // 재료 보유 상태
            Text(
              _getIngredientStatusText(availableCount, totalCount),
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: _getIngredientStatusColor(availableCount, totalCount),
              ),
            ),
            const SizedBox(height: AppTheme.spacingS),
            
            // 없는 재료 (있을 경우에만 표시)
            if (unavailableIngredients.isNotEmpty) ...[
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '없는 재료',
                    style: TextStyle(
                      fontSize: 12,
                      color: AppTheme.textSecondary,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(width: AppTheme.spacingM),
                  Expanded(
                    child: Text(
                      unavailableIngredients.map((ing) => ing.name).join(', '),
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppTheme.textPrimary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
            ],
            
            // 보유 재료
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '보유 재료',
                  style: TextStyle(
                    fontSize: 12,
                    color: AppTheme.textSecondary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(width: AppTheme.spacingM),
                Expanded(
                  child: Text(
                    availableIngredients.isNotEmpty 
                        ? availableIngredients.map((ing) => ing.name).join(', ')
                        : '보유한 재료가 없습니다',
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppTheme.textPrimary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
