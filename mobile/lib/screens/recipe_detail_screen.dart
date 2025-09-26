import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';
import '../models/recipe.dart';
import '../services/recipe_data.dart';
import '../services/analytics_service.dart';

/// 레시피 상세 화면 (DETAIL-01)
/// 레시피의 모든 정보를 상세하게 보여주며, 사용자 인터랙션을 처리합니다.
class RecipeDetailScreen extends StatefulWidget {
  final Recipe recipe;
  final List<String> userIngredients;

  const RecipeDetailScreen({
    super.key,
    required this.recipe,
    this.userIngredients = const [],
  });

  @override
  State<RecipeDetailScreen> createState() => _RecipeDetailScreenState();
}

class _RecipeDetailScreenState extends State<RecipeDetailScreen> {
  late PageController _stepPageController;
  int _currentStepIndex = 0;

  @override
  void initState() {
    super.initState();
    _stepPageController = PageController();
    AnalyticsService().logScreenView('recipe_detail');
  }

  @override
  void dispose() {
    _stepPageController.dispose();
    super.dispose();
  }

  void _showMissingIngredientsGuide() {
    final missingIngredients = widget.recipe.getMissingIngredients(widget.userIngredients);
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _buildMissingIngredientsBottomSheet(missingIngredients),
    );
  }

  void _navigateToRelatedRecipe(Recipe recipe) {
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (context) => RecipeDetailScreen(
          recipe: recipe,
          userIngredients: widget.userIngredients,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final availableIngredients = widget.recipe.getAvailableIngredients(widget.userIngredients);
    final missingIngredients = widget.recipe.getMissingIngredients(widget.userIngredients);

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      body: CustomScrollView(
        slivers: [
          // 상단 이미지와 앱바
          SliverAppBar(
            expandedHeight: 300,
            pinned: true,
            backgroundColor: AppTheme.primaryOrange,
            flexibleSpace: FlexibleSpaceBar(
              background: Image.network(
                'https://picsum.photos/400/300?random=${widget.recipe.id.hashCode.abs() % 1000}',
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) {
                  return Container(
                    decoration: const BoxDecoration(
                      color: AppTheme.backgroundGray,
                    ),
                    child: const Icon(
                      Icons.restaurant_menu,
                      size: 80,
                      color: AppTheme.textGray,
                    ),
                  );
                },
              ),
            ),
            actions: [
              IconButton(
                onPressed: () {
                  // TODO: 공유 기능 구현 (예: dynamic links, share_plus 패키지)
                  AnalyticsService().logShare('recipe', widget.recipe.id);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('공유 기능은 현재 준비 중입니다.')),
                  );
                },
                icon: const Icon(Icons.share_outlined),
                tooltip: '공유하기',
              ),
            ],
          ),
          
          // 메인 콘텐츠
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(AppTheme.spacingM),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 레시피 기본 정보
                  Text(
                    widget.recipe.name,
                    style: AppTheme.headingLarge,
                  ),
                  
                  const SizedBox(height: AppTheme.spacingS),
                  
                  Text(
                    widget.recipe.description,
                    style: AppTheme.bodyMedium.copyWith(
                      color: AppTheme.textSecondary,
                    ),
                  ),
                  
                  const SizedBox(height: AppTheme.spacingL),
                  
                  // 요리 기본 정보 카드
                  Container(
                    padding: const EdgeInsets.all(AppTheme.spacingM),
                    decoration: AppTheme.cardDecoration(
                      backgroundColor: AppTheme.backgroundGray,
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildInfoItem(
                          Icons.person,
                          '${widget.recipe.servings}인분',
                        ),
                        _buildInfoItem(
                          Icons.timer,
                          '${widget.recipe.cookingTimeMinutes}분',
                        ),
                        _buildInfoItem(
                          Icons.star,
                          widget.recipe.difficulty.displayName,
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: AppTheme.spacingXL),
                  
                  // 재료 리스트
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        '준비할 재료',
                        style: AppTheme.headingSmall,
                      ),
                      if (widget.userIngredients.isNotEmpty && missingIngredients.isNotEmpty)
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: AppTheme.spacingM,
                            vertical: AppTheme.spacingS,
                          ),
                          decoration: BoxDecoration(
                            color: AppTheme.cardPink,
                            borderRadius: BorderRadius.circular(AppTheme.radiusButton),
                          ),
                          child: Text(
                            '부족한 재료 ${missingIngredients.length}개',
                            style: AppTheme.bodySmall.copyWith(
                              color: Colors.red,
                            ),
                          ),
                        ),
                    ],
                  ),
                  
                  const SizedBox(height: AppTheme.spacingM),
                  
                  // 재료 목록
                  ...widget.recipe.ingredients.map((ingredient) {
                    final isAvailable = widget.userIngredients.isNotEmpty &&
                        availableIngredients.contains(ingredient);
                    final isMissing = widget.userIngredients.isNotEmpty &&
                        missingIngredients.contains(ingredient);
                    
                    return Container(
                      margin: const EdgeInsets.only(bottom: AppTheme.spacingS),
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppTheme.spacingM,
                        vertical: AppTheme.spacingM,
                      ),
                      decoration: BoxDecoration(
                        color: isAvailable 
                            ? AppTheme.cardGreen.withOpacity(0.3)
                            : isMissing 
                                ? AppTheme.cardPink.withOpacity(0.3)
                                : AppTheme.backgroundGray,
                        borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                        border: Border.all(
                          color: isAvailable 
                              ? AppTheme.successGreen
                              : isMissing 
                                  ? Colors.red.withOpacity(0.3)
                                  : Colors.transparent,
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            isAvailable 
                                ? Icons.check_circle
                                : isMissing 
                                    ? Icons.cancel
                                    : Icons.circle_outlined,
                            size: 20,
                            color: isAvailable 
                                ? AppTheme.successGreen
                                : isMissing 
                                    ? Colors.red
                                    : AppTheme.textGray,
                          ),
                          const SizedBox(width: AppTheme.spacingM),
                          Expanded(
                            child: Text(
                              '${ingredient.name} ${ingredient.amount}',
                              style: AppTheme.bodyMedium.copyWith(
                                color: isMissing ? Colors.red : AppTheme.textPrimary,
                                decoration: isAvailable 
                                    ? null 
                                    : isMissing 
                                        ? TextDecoration.lineThrough 
                                        : null,
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                  
                  // 부족 재료 가이드 버튼
                  if (widget.userIngredients.isNotEmpty && missingIngredients.isNotEmpty) ...[
                    const SizedBox(height: AppTheme.spacingM),
                    CustomButton(
                      text: '부족한 재료만 모아보기',
                      type: ButtonType.secondary,
                      onPressed: _showMissingIngredientsGuide,
                      width: double.infinity,
                    ),
                  ],
                  
                  const SizedBox(height: AppTheme.spacingXL),
                  
                  // 조리법
                  const Text(
                    '따라해보세요',
                    style: AppTheme.headingSmall,
                  ),
                  
                  const SizedBox(height: AppTheme.spacingM),
                  
                  // 조리 단계 페이지뷰
                  SizedBox(
                    height: 300,
                    child: PageView.builder(
                      controller: _stepPageController,
                      onPageChanged: (index) {
                        setState(() {
                          _currentStepIndex = index;
                        });
                      },
                      itemCount: widget.recipe.steps.length,
                      itemBuilder: (context, index) {
                        final step = widget.recipe.steps[index];
                        return Container(
                          margin: const EdgeInsets.symmetric(horizontal: AppTheme.spacingS),
                          decoration: AppTheme.cardDecoration(),
                          child: Column(
                            children: [
                              // 단계 이미지 영역
                              Container(
                                height: 180,
                                width: double.infinity,
                                decoration: BoxDecoration(
                                  color: AppTheme.backgroundGray,
                                  borderRadius: const BorderRadius.only(
                                    topLeft: Radius.circular(AppTheme.radiusCard),
                                    topRight: Radius.circular(AppTheme.radiusCard),
                                  ),
                                ),
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Text(
                                      'Step ${step.stepNumber}',
                                      style: AppTheme.headingMedium.copyWith(
                                        color: AppTheme.primaryOrange,
                                      ),
                                    ),
                                    const SizedBox(height: AppTheme.spacingS),
                                    const Icon(
                                      Icons.restaurant,
                                      size: 40,
                                      color: AppTheme.textGray,
                                    ),
                                    if (step.durationMinutes != null) ...[
                                      const SizedBox(height: AppTheme.spacingS),
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                          const Icon(
                                            Icons.timer,
                                            size: 16,
                                            color: AppTheme.textGray,
                                          ),
                                          const SizedBox(width: 4),
                                          Text(
                                            '${step.durationMinutes}분',
                                            style: AppTheme.bodySmall.copyWith(
                                              color: AppTheme.textGray,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                              
                              // 단계 설명
                              Expanded(
                                child: Padding(
                                  padding: const EdgeInsets.all(AppTheme.spacingM),
                                  child: Center(
                                    child: Text(
                                      step.description,
                                      style: AppTheme.bodyMedium,
                                      textAlign: TextAlign.center,
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                  
                  // 페이지 인디케이터
                  const SizedBox(height: AppTheme.spacingM),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(
                      widget.recipe.steps.length,
                      (index) => Container(
                        margin: const EdgeInsets.symmetric(horizontal: 4),
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: index == _currentStepIndex
                              ? AppTheme.primaryOrange
                              : AppTheme.textGray.withOpacity(0.3),
                        ),
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: AppTheme.spacingXL),
                  
                  // 관련 레시피 추천
                  FutureBuilder<List<Recipe>>(
                    future: getRelatedRecipes(widget.recipe),
                    builder: (context, snapshot) {
                      if (!snapshot.hasData || snapshot.data!.isEmpty) {
                        return const SizedBox.shrink();
                      }
                      
                      final relatedRecipes = snapshot.data!;
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            '비슷한 재료로 만들 수 있는 다른 요리',
                            style: AppTheme.headingSmall,
                          ),
                          
                          const SizedBox(height: AppTheme.spacingM),
                          
                          SizedBox(
                            height: 200,
                            child: ListView.builder(
                              scrollDirection: Axis.horizontal,
                              itemCount: relatedRecipes.length,
                              itemBuilder: (context, index) {
                                final relatedRecipe = relatedRecipes[index];
                                return Container(
                                  width: 160,
                                  margin: EdgeInsets.only(
                                    right: index < relatedRecipes.length - 1 
                                        ? AppTheme.spacingM 
                                        : 0,
                                  ),
                                  child: GestureDetector(
                                    onTap: () => _navigateToRelatedRecipe(relatedRecipe),
                                    child: Container(
                                      decoration: AppTheme.cardDecoration(),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          // 이미지 영역
                                          Container(
                                            height: 100,
                                            width: double.infinity,
                                            decoration: const BoxDecoration(
                                              borderRadius: BorderRadius.only(
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
                                                'https://picsum.photos/160/100?random=${relatedRecipe.id.hashCode.abs() % 1000}',
                                                fit: BoxFit.cover,
                                                errorBuilder: (context, error, stackTrace) {
                                                  return Container(
                                                    color: AppTheme.backgroundGray,
                                                    child: const Icon(
                                                      Icons.restaurant,
                                                      size: 40,
                                                      color: AppTheme.textGray,
                                                    ),
                                                  );
                                                },
                                              ),
                                            ),
                                          ),
                                          
                                          // 레시피 정보
                                          Expanded(
                                            child: Padding(
                                              padding: const EdgeInsets.all(AppTheme.spacingM),
                                              child: Column(
                                                crossAxisAlignment: CrossAxisAlignment.start,
                                                children: [
                                                  Text(
                                                    relatedRecipe.name,
                                                    style: AppTheme.bodyMedium,
                                                    maxLines: 2,
                                                    overflow: TextOverflow.ellipsis,
                                                  ),
                                                  
                                                  const Spacer(),
                                                  
                                                  Row(
                                                    children: [
                                                      const Icon(
                                                        Icons.timer,
                                                        size: 14,
                                                        color: AppTheme.textGray,
                                                      ),
                                                      const SizedBox(width: 4),
                                                      Text(
                                                        '${relatedRecipe.cookingTimeMinutes}분',
                                                        style: AppTheme.bodySmall.copyWith(
                                                          color: AppTheme.textGray,
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                ],
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
                        ],
                      );
                    },
                  ),
                  
                  const SizedBox(height: AppTheme.spacingXXL),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoItem(IconData icon, String text) {
    return Column(
      children: [
        Icon(
          icon,
          size: 24,
          color: AppTheme.primaryOrange,
        ),
        const SizedBox(height: AppTheme.spacingS),
        Text(
          text,
          style: AppTheme.bodyMedium,
        ),
      ],
    );
  }

  Widget _buildMissingIngredientsBottomSheet(List<Ingredient> missingIngredients) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(AppTheme.radiusLarge),
          topRight: Radius.circular(AppTheme.radiusLarge),
        ),
      ),
      child: Padding(
        padding: EdgeInsets.fromLTRB(
          AppTheme.spacingL,
          AppTheme.spacingL,
          AppTheme.spacingL,
          MediaQuery.of(context).viewInsets.bottom + AppTheme.spacingL,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 핸들
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppTheme.textGray,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            
            const SizedBox(height: AppTheme.spacingL),
            
            // 제목
            Text(
              '이 재료만 채우면, 레시피가 더 많아져요! 🛒',
              style: AppTheme.headingSmall,
            ),
            
            const SizedBox(height: AppTheme.spacingM),
            
            // 부족한 재료 목록
            ...missingIngredients.map((ingredient) {
              return Container(
                margin: const EdgeInsets.only(bottom: AppTheme.spacingS),
                padding: const EdgeInsets.all(AppTheme.spacingM),
                decoration: BoxDecoration(
                  color: AppTheme.backgroundGray,
                  borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.shopping_cart,
                      size: 20,
                      color: AppTheme.primaryOrange,
                    ),
                    const SizedBox(width: AppTheme.spacingM),
                    Text(
                      '${ingredient.name} ${ingredient.amount}',
                      style: AppTheme.bodyMedium,
                    ),
                  ],
                ),
              );
            }).toList(),
            
            const SizedBox(height: AppTheme.spacingM),
            
            // 설명 텍스트
            Text(
              '위 재료들은 다양한 한식 요리에 활용되는 필수 아이템이에요.\n냉장고에 채워두고 더 많은 요리를 즐겨보세요!',
              style: AppTheme.bodyMedium.copyWith(
                color: AppTheme.textSecondary,
              ),
            ),
            
            const SizedBox(height: AppTheme.spacingL),
            
            // 닫기 버튼
            CustomButton(
              text: '확인했어요',
              type: ButtonType.primary,
              onPressed: () => Navigator.of(context).pop(),
              width: double.infinity,
            ),
          ],
        ),
      ),
    );
  }
}
