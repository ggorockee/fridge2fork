import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';
import '../providers/ingredients_provider.dart';
import 'add_ingredient_screen.dart';

/// 나의냉장고 화면
/// 사용자가 보유한 모든 식재료를 카테고리별로 관리할 수 있는 화면
class MyFridgeScreen extends ConsumerStatefulWidget {
  const MyFridgeScreen({super.key});

  @override
  ConsumerState<MyFridgeScreen> createState() => _MyFridgeScreenState();
}

class _MyFridgeScreenState extends ConsumerState<MyFridgeScreen> {

  void _onAddButtonPressed() async {
    // 식재료 추가 Modal Bottom Sheet 표시
    final result = await AddIngredientScreen.showModal(context);
    
    // 선택된 식재료가 있으면 처리
    if (result != null && result.isNotEmpty) {
      ref.read(selectedIngredientsProvider.notifier).addIngredients(result);
      SnackBarHelper.showSnackBar(
        context,
        '${result.length}개의 식재료가 추가되었습니다!',
        backgroundColor: AppTheme.primaryOrange,
      );
    }
  }

  void _removeIngredient(String ingredient) {
    ref.read(selectedIngredientsProvider.notifier).removeIngredient(ingredient);
    SnackBarHelper.showSnackBar(
      context,
      '$ingredient이(가) 제거되었습니다',
      backgroundColor: AppTheme.textPrimary.withOpacity(0.85),
    );
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
            onPressed: () {
              ref.read(selectedIngredientsProvider.notifier).clearAllIngredients();
              Navigator.of(context).pop();
              SnackBarHelper.showSnackBar(
                context,
                '모든 식재료가 삭제되었습니다',
                backgroundColor: AppTheme.textPrimary.withOpacity(0.85),
              );
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
    final selectedIngredients = ref.watch(selectedIngredientsProvider);
    final categories = ref.watch(categoriesProvider);
    

    // 카테고리별로 식재료 그룹화
    Map<String, List<String>> categorizedIngredients = {};
    for (final category in categories.skip(1)) { // '전체' 제외
      final categoryIngredients = selectedIngredients
          .where((ingredient) {
            final ingredientsData = ref.read(ingredientsDataProvider);
            return ingredientsData[category]?.contains(ingredient) ?? false;
          })
          .where((ingredient) {
            final searchText = ref.watch(searchTextProvider);
            return searchText.isEmpty || ingredient.contains(searchText);
          })
          .toList();
      
      if (categoryIngredients.isNotEmpty) {
        categorizedIngredients[category] = categoryIngredients;
      }
    }

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
          if (selectedIngredients.isNotEmpty)
            IconButton(
              onPressed: _clearAllIngredients,
              icon: const Icon(
                Icons.delete_outline,
                color: AppTheme.textSecondary,
              ),
              tooltip: '모든 식재료 삭제',
            ),
        ],
      ),
      body: selectedIngredients.isEmpty 
        ? _buildEmptyState()
        : _buildBodyWithSearch(categorizedIngredients),
      floatingActionButton: selectedIngredients.isEmpty
        ? null
        : FloatingActionButton(
            onPressed: _onAddButtonPressed,
            backgroundColor: Colors.white,
            elevation: 0,
            heroTag: "fridge_fab", // Hero 애니메이션 방지
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
            // 빈 냉장고 아이콘 - 앱 로고 사용
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
            
            // 메시지
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
            
            // 추가 버튼
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
  Widget _buildBodyWithSearch(Map<String, List<String>> categorizedIngredients) {
    return Column(
      children: [
        // 검색바
        Container(
          padding: const EdgeInsets.all(AppTheme.spacingM),
          child: SearchTextField(
            hintText: '식재료 검색...',
            onChanged: (value) {
              ref.read(searchTextProvider.notifier).state = value;
            },
          ),
        ),
        
        // 구분선
        Container(
          height: 1,
          color: AppTheme.borderGray,
        ),
        
        // 냉장고 콘텐츠
        Expanded(
          child: _buildFridgeContent(categorizedIngredients),
        ),
      ],
    );
  }

  /// 냉장고 콘텐츠 위젯
  Widget _buildFridgeContent(Map<String, List<String>> categorizedIngredients) {
    final selectedIngredients = ref.watch(selectedIngredientsProvider);
    
    return Column(
      children: [
        // 상단 통계 및 검색
        Padding(
          padding: const EdgeInsets.all(AppTheme.spacingM),
          child: Column(
            children: [
              // 통계 카드
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(AppTheme.spacingM),
                decoration: BoxDecoration(
                  color: AppTheme.lightOrange,
                  borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
                  border: Border.all(
                    color: AppTheme.primaryOrange.withOpacity(0.2),
                    width: 1,
                  ),
                ),
                child: Row(
                  children: [
                    // 아이콘
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
                    
                    // 통계 정보
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '총 ${selectedIngredients.length}개의 식재료',
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
              
            ],
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
  Widget _buildCategoryList(Map<String, List<String>> categorizedIngredients) {
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
  final List<String> ingredients;
  final Function(String) onRemoveIngredient;

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
            color: Colors.black.withOpacity(0.05),
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
                // 카테고리 아이콘
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
                
                // 카테고리 이름
                Text(
                  category,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                ),
                
                const SizedBox(width: AppTheme.spacingS),
                
                // 개수 뱃지
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
              AppTheme.spacingM
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
    switch (category) {
      case '정육/계란':
        return Colors.red.shade400;
      case '수산물':
        return Colors.blue.shade400;
      case '채소':
        return Colors.green.shade400;
      case '장/양념/오일':
        return Colors.orange.shade400;
      default:
        return AppTheme.primaryOrange;
    }
  }

  IconData _getCategoryIcon(String category) {
    switch (category) {
      case '정육/계란':
        return Icons.egg;
      case '수산물':
        return Icons.set_meal;
      case '채소':
        return Icons.grass;
      case '장/양념/오일':
        return Icons.local_dining;
      default:
        return Icons.category;
    }
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
    return Tooltip(
      message: ingredient,
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
                ingredient,
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
