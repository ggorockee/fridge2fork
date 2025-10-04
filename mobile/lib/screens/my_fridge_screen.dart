import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../widgets/widgets.dart';
import '../providers/fridge_provider.dart';
import '../models/api/api_fridge.dart';
import 'add_ingredient_screen.dart';
import '../services/analytics_service.dart';

/// 나의냉장고 화면 (API 기반)
class MyFridgeScreen extends ConsumerStatefulWidget {
  const MyFridgeScreen({super.key});

  @override
  ConsumerState<MyFridgeScreen> createState() => _MyFridgeScreenState();
}

class _MyFridgeScreenState extends ConsumerState<MyFridgeScreen> {
  String _searchText = '';

  @override
  void initState() {
    super.initState();
    AnalyticsService().logScreenView('my_fridge');
  }

  void _onAddButtonPressed() async {
    // 식재료 추가 Modal Bottom Sheet 표시
    final result = await AddIngredientScreen.showModal(context);

    // 선택된 식재료가 있으면 API로 추가
    if (result != null && result.isNotEmpty) {
      int successCount = 0;
      for (final ingredient in result) {
        final success = await ref.read(fridgeProvider.notifier).addIngredient(ingredient);
        if (success) successCount++;
      }

      if (mounted) {
        SnackBarHelper.showSnackBar(
          context,
          '$successCount개의 식재료가 추가되었습니다!',
          backgroundColor: AppTheme.primaryOrange,
        );
      }
    }
  }

  void _removeIngredient(ApiFridgeIngredient ingredient) async {
    final success = await ref.read(fridgeProvider.notifier).removeIngredient(ingredient.id);

    if (mounted) {
      if (success) {
        SnackBarHelper.showSnackBar(
          context,
          '${ingredient.name}이(가) 제거되었습니다',
          backgroundColor: AppTheme.textPrimary.withValues(alpha: 0.85),
        );
      } else {
        SnackBarHelper.showSnackBar(
          context,
          '재료 제거에 실패했습니다',
          backgroundColor: Colors.red,
        );
      }
    }
  }

  void _clearAllIngredients() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('모든 식재료 삭제'),
        content: const Text('냉장고의 모든 식재료를 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () async {
              final navigator = Navigator.of(context);
              final messenger = ScaffoldMessenger.of(context);
              navigator.pop();
              final success = await ref.read(fridgeProvider.notifier).clearFridge();

              if (mounted) {
                if (success) {
                  messenger.showSnackBar(
                    const SnackBar(
                      content: Text('모든 식재료가 삭제되었습니다'),
                      backgroundColor: Color(0xD9333333),
                    ),
                  );
                } else {
                  messenger.showSnackBar(
                    const SnackBar(
                      content: Text('삭제에 실패했습니다'),
                      backgroundColor: Colors.red,
                    ),
                  );
                }
              }
            },
            child: const Text(
              '삭제',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final fridgeState = ref.watch(fridgeProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        backgroundColor: AppTheme.backgroundWhite,
        elevation: 0,
        automaticallyImplyLeading: false,
        title: const Text(
          '나의 냉장고',
          style: TextStyle(
            color: AppTheme.textPrimary,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
        ),
        actions: [
          fridgeState.when(
            data: (fridge) => fridge.ingredients.isNotEmpty
                ? IconButton(
                    onPressed: _clearAllIngredients,
                    icon: const Icon(
                      Icons.delete_outline,
                      color: AppTheme.textSecondary,
                    ),
                    tooltip: '모든 식재료 삭제',
                  )
                : const SizedBox.shrink(),
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
      body: fridgeState.when(
        data: (fridge) => fridge.ingredients.isEmpty
            ? _buildEmptyState()
            : _buildBodyWithSearch(fridge),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => _buildErrorState(error.toString()),
      ),
      floatingActionButton: fridgeState.when(
        data: (fridge) => fridge.ingredients.isEmpty
            ? null
            : SizedBox(
                width: 45,
                height: 45,
                child: FloatingActionButton(
                  onPressed: _onAddButtonPressed,
                  backgroundColor: Colors.white,
                  elevation: 0,
                  heroTag: "fridge_fab",
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
        loading: () => null,
        error: (_, __) => null,
      ),
    );
  }

  /// 에러 상태 위젯
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
              color: Colors.red,
            ),
            const SizedBox(height: AppTheme.spacingM),
            const Text(
              '냉장고를 불러올 수 없습니다',
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
              onPressed: () => ref.read(fridgeProvider.notifier).loadFridge(),
              type: ButtonType.primary,
            ),
          ],
        ),
      ),
    );
  }

  /// 빈 냉장고 상태 위젯
  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppTheme.spacingXL),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
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
            ),
            const SizedBox(height: AppTheme.spacingL),
            const Text(
              '냉장고가 비어있어요',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: AppTheme.spacingS),
            const Text(
              '식재료를 추가해서 냉장고를 채워보세요!',
              style: TextStyle(
                fontSize: 14,
                color: AppTheme.textPrimary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppTheme.spacingXL),
            SizedBox(
              width: double.infinity,
              child: CustomButton(
                text: '식재료 추가하기',
                onPressed: _onAddButtonPressed,
                type: ButtonType.primary,
                height: 56,
                icon: Icons.add,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 검색바를 포함한 Body 위젯
  Widget _buildBodyWithSearch(ApiFridge fridge) {
    // 카테고리별로 그룹화
    final categorizedIngredients = <String, List<ApiFridgeIngredient>>{};
    for (final ingredient in fridge.ingredients) {
      if (_searchText.isNotEmpty && !ingredient.name.contains(_searchText)) {
        continue;
      }
      if (!categorizedIngredients.containsKey(ingredient.category)) {
        categorizedIngredients[ingredient.category] = [];
      }
      categorizedIngredients[ingredient.category]!.add(ingredient);
    }

    return Column(
      children: [
        // 검색바
        Container(
          padding: const EdgeInsets.all(AppTheme.spacingM),
          child: SearchTextField(
            hintText: '식재료 검색...',
            onChanged: (value) {
              setState(() {
                _searchText = value;
              });
            },
          ),
        ),
        Container(
          height: 1,
          color: AppTheme.borderGray,
        ),
        // 냉장고 콘텐츠
        Expanded(
          child: _buildFridgeContent(fridge, categorizedIngredients),
        ),
      ],
    );
  }

  /// 냉장고 콘텐츠 위젯
  Widget _buildFridgeContent(ApiFridge fridge, Map<String, List<ApiFridgeIngredient>> categorizedIngredients) {
    return Column(
      children: [
        // 상단 통계
        Padding(
          padding: const EdgeInsets.all(AppTheme.spacingM),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.all(AppTheme.spacingM),
            decoration: BoxDecoration(
              color: AppTheme.lightOrange,
              borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
              border: Border.all(
                color: AppTheme.primaryOrange.withValues(alpha: 0.2),
                width: 1,
              ),
            ),
            child: Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: AppTheme.primaryOrange,
                    borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                  ),
                  child: const Icon(
                    Icons.inventory_2,
                    color: Colors.white,
                    size: 24,
                  ),
                ),
                const SizedBox(width: AppTheme.spacingM),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '총 ${fridge.ingredients.length}개의 식재료',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${categorizedIngredients.length}개 카테고리',
                        style: const TextStyle(
                          fontSize: 14,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        // 카테고리별 식재료 목록
        Expanded(
          child: categorizedIngredients.isEmpty
              ? _buildNoResultsState()
              : _buildCategoryList(categorizedIngredients),
        ),
      ],
    );
  }

  /// 검색 결과 없음 상태
  Widget _buildNoResultsState() {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(AppTheme.spacingXL),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.search_off,
              size: 64,
              color: AppTheme.textSecondary,
            ),
            SizedBox(height: AppTheme.spacingM),
            Text(
              '검색 결과가 없습니다',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            SizedBox(height: AppTheme.spacingS),
            Text(
              '다른 검색어로 시도해보세요',
              style: TextStyle(
                fontSize: 14,
                color: AppTheme.textPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 카테고리별 목록
  Widget _buildCategoryList(Map<String, List<ApiFridgeIngredient>> categorizedIngredients) {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: AppTheme.spacingM),
      itemCount: categorizedIngredients.length,
      itemBuilder: (context, index) {
        final category = categorizedIngredients.keys.elementAt(index);
        final ingredients = categorizedIngredients[category]!;

        return _CategorySection(
          category: category,
          ingredients: ingredients,
          onRemoveIngredient: _removeIngredient,
        );
      },
    );
  }
}

/// 카테고리 섹션 위젯
class _CategorySection extends StatelessWidget {
  final String category;
  final List<ApiFridgeIngredient> ingredients;
  final Function(ApiFridgeIngredient) onRemoveIngredient;

  const _CategorySection({
    required this.category,
    required this.ingredients,
    required this.onRemoveIngredient,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: AppTheme.spacingL),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 카테고리 헤더
          Padding(
            padding: const EdgeInsets.all(AppTheme.spacingM),
            child: Row(
              children: [
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: _getCategoryColor(category),
                    borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                  ),
                  child: Icon(
                    _getCategoryIcon(category),
                    color: Colors.white,
                    size: 18,
                  ),
                ),
                const SizedBox(width: AppTheme.spacingS),
                Text(
                  category,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const SizedBox(width: AppTheme.spacingS),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppTheme.spacingS,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: AppTheme.backgroundGray,
                    borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                  ),
                  child: Text(
                    '${ingredients.length}개',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ),
              ],
            ),
          ),
          // 식재료 그리드
          Padding(
            padding: const EdgeInsets.fromLTRB(
              AppTheme.spacingM,
              0,
              AppTheme.spacingM,
              AppTheme.spacingM,
            ),
            child: GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                childAspectRatio: 2.5,
                crossAxisSpacing: AppTheme.spacingS,
                mainAxisSpacing: AppTheme.spacingS,
              ),
              itemCount: ingredients.length,
              itemBuilder: (context, index) {
                final ingredient = ingredients[index];
                return _IngredientChip(
                  ingredient: ingredient,
                  onRemove: () => onRemoveIngredient(ingredient),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Color _getCategoryColor(String category) {
    // 서버에서 오는 카테고리명에 맞게 조정
    if (category.contains('육') || category.contains('계란')) {
      return Colors.red.shade400;
    } else if (category.contains('수산') || category.contains('해산')) {
      return Colors.blue.shade400;
    } else if (category.contains('채소')) {
      return Colors.green.shade400;
    } else if (category.contains('양념') || category.contains('조미')) {
      return Colors.orange.shade400;
    }
    return AppTheme.primaryOrange;
  }

  IconData _getCategoryIcon(String category) {
    if (category.contains('육') || category.contains('계란')) {
      return Icons.egg;
    } else if (category.contains('수산') || category.contains('해산')) {
      return Icons.set_meal;
    } else if (category.contains('채소')) {
      return Icons.grass;
    } else if (category.contains('양념') || category.contains('조미')) {
      return Icons.local_dining;
    }
    return Icons.category;
  }
}

/// 개별 식재료 칩 위젯
class _IngredientChip extends StatelessWidget {
  final ApiFridgeIngredient ingredient;
  final VoidCallback onRemove;

  const _IngredientChip({
    required this.ingredient,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: ingredient.name,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: 12,
          vertical: AppTheme.spacingS,
        ),
        decoration: BoxDecoration(
          color: AppTheme.backgroundGray,
          borderRadius: BorderRadius.circular(AppTheme.radiusButton),
          border: Border.all(
            color: AppTheme.borderGray,
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Expanded(
              child: Text(
                ingredient.name,
                style: const TextStyle(
                  fontSize: 14,
                  color: AppTheme.textPrimary,
                  fontWeight: FontWeight.w500,
                ),
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
            ),
            const SizedBox(width: 8),
            GestureDetector(
              onTap: onRemove,
              child: const Icon(
                Icons.close,
                size: 14,
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
