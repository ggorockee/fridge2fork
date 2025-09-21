import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';
import '../models/recipe.dart';
import '../services/recipe_data.dart';
import 'recipe_detail_screen.dart';

/// 검색 결과 화면 (LIST-01)
/// 사용자가 입력한 재료와 가장 연관성 높은 레시피 목록을 효과적으로 보여주고, 탐색을 돕습니다.
class RecipeListScreen extends StatefulWidget {
  final String title;
  final RecipeCategory? category;
  final List<String> userIngredients;

  const RecipeListScreen({
    super.key,
    required this.title,
    this.category,
    this.userIngredients = const [],
  });

  @override
  State<RecipeListScreen> createState() => _RecipeListScreenState();
}

class _RecipeListScreenState extends State<RecipeListScreen> {
  List<Recipe> _recipes = [];
  List<Recipe> _filteredRecipes = [];
  SortOption _selectedSortOption = SortOption.matchingRate;

  @override
  void initState() {
    super.initState();
    _loadRecipes();
  }

  void _loadRecipes() async {
    List<Recipe> recipes;
    
    if (widget.category != null) {
      // 카테고리별 레시피
      recipes = await getRecipesByCategory(widget.category!);
    } else if (widget.userIngredients.isNotEmpty) {
      // 재료 기반 검색
      recipes = await searchRecipesByIngredients(widget.userIngredients);
    } else {
      // 전체 레시피 또는 인기 레시피
      recipes = widget.title == '인기 레시피' 
          ? await popularRecipes 
          : await RecipeDataService.getAllRecipes();
    }

    setState(() {
      _recipes = recipes;
      _applySort();
    });
  }

  void _applySort() {
    setState(() {
      _filteredRecipes = sortRecipes(
        _recipes, 
        _selectedSortOption, 
        widget.userIngredients.isNotEmpty ? widget.userIngredients : null,
      );
    });
  }

  void _onSortOptionChanged(SortOption option) {
    setState(() {
      _selectedSortOption = option;
      _applySort();
    });
  }

  void _navigateToRecipeDetail(Recipe recipe) {
    Navigator.of(context).push(
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
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      body: SafeArea(
        child: Column(
          children: [
            // 상단 바
            CustomStatusBar(
              backgroundColor: AppTheme.primaryOrange,
              showBackButton: true,
              title: widget.title,
            ),
            
            // 정렬 옵션
            Container(
              padding: const EdgeInsets.all(AppTheme.spacingM),
              decoration: BoxDecoration(
                color: AppTheme.backgroundWhite,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 10,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '${_filteredRecipes.length}개의 레시피',
                        style: AppTheme.bodyMedium.copyWith(
                          color: AppTheme.textGray,
                        ),
                      ),
                      const Icon(
                        Icons.tune,
                        color: AppTheme.textGray,
                        size: 20,
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: AppTheme.spacingM),
                  
                  // 정렬 옵션 칩들
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: SortOption.values.map((option) {
                        final isSelected = option == _selectedSortOption;
                        return Padding(
                          padding: EdgeInsets.only(
                            right: option != SortOption.values.last 
                                ? AppTheme.spacingM 
                                : 0,
                          ),
                          child: CustomFilterChip(
                            label: option.displayName,
                            isSelected: isSelected,
                            onTap: () => _onSortOptionChanged(option),
                            selectedColor: AppTheme.primaryOrange,
                            unselectedColor: AppTheme.backgroundGray,
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
            
            // 레시피 목록
            Expanded(
              child: _filteredRecipes.isEmpty
                  ? _buildEmptyState()
                  : ListView.builder(
                      padding: const EdgeInsets.all(AppTheme.spacingM),
                      itemCount: _filteredRecipes.length,
                      itemBuilder: (context, index) {
                        final recipe = _filteredRecipes[index];
                        return _buildRecipeCard(recipe);
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.search_off,
            size: 64,
            color: AppTheme.textGray,
          ),
          const SizedBox(height: AppTheme.spacingL),
          const Text(
            '레시피를 찾을 수 없습니다',
            style: AppTheme.headingSmall,
          ),
          const SizedBox(height: AppTheme.spacingS),
          Text(
            '다른 재료나 카테고리를 시도해보세요',
            style: AppTheme.bodyMedium.copyWith(
              color: AppTheme.textGray,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecipeCard(Recipe recipe) {
    final matchingRate = widget.userIngredients.isNotEmpty 
        ? recipe.calculateMatchingRate(widget.userIngredients)
        : 0.0;
    final availableIngredients = recipe.getAvailableIngredients(widget.userIngredients);
    final missingIngredients = recipe.getMissingIngredients(widget.userIngredients);

    return Container(
      margin: const EdgeInsets.only(bottom: AppTheme.spacingM),
      child: GestureDetector(
        onTap: () => _navigateToRecipeDetail(recipe),
        child: Container(
          decoration: AppTheme.cardDecoration(),
          child: Padding(
            padding: const EdgeInsets.all(AppTheme.spacingM),
            child: Row(
              children: [
                // 레시피 이미지
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                    child: Image.network(
                      'https://picsum.photos/80/80?random=${recipe.id.hashCode.abs() % 1000}',
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) {
                        return Container(
                          color: AppTheme.backgroundGray,
                          child: const Icon(
                            Icons.restaurant,
                            size: 32,
                            color: AppTheme.textGray,
                          ),
                        );
                      },
                    ),
                  ),
                ),
                
                const SizedBox(width: AppTheme.spacingM),
                
                // 레시피 정보
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // 레시피 이름과 카테고리
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              recipe.name,
                              style: AppTheme.bodyMedium,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: AppTheme.spacingS,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: AppTheme.lightOrange,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              recipe.category.displayName,
                              style: AppTheme.caption.copyWith(
                                color: AppTheme.primaryOrange,
                              ),
                            ),
                          ),
                        ],
                      ),
                      
                      const SizedBox(height: AppTheme.spacingXS),
                      
                      // 재료 매칭 정보
                      if (widget.userIngredients.isNotEmpty) ...[
                        Row(
                          children: [
                            if (availableIngredients.isNotEmpty) ...[
                              const Icon(
                                Icons.check_circle,
                                size: 14,
                                color: AppTheme.successGreen,
                              ),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Text(
                                  availableIngredients.map((i) => i.name).take(2).join(', '),
                                  style: AppTheme.bodySmall.copyWith(
                                    color: AppTheme.successGreen,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ],
                        ),
                        
                        if (missingIngredients.isNotEmpty) ...[
                          const SizedBox(height: 2),
                          Row(
                            children: [
                              const Icon(
                                Icons.cancel,
                                size: 14,
                                color: AppTheme.textGray,
                              ),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Text(
                                  missingIngredients.map((i) => i.name).take(2).join(', '),
                                  style: AppTheme.bodySmall.copyWith(
                                    color: AppTheme.textGray,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                      
                      const SizedBox(height: AppTheme.spacingS),
                      
                      // 부가 정보
                      Row(
                        children: [
                          // 매칭율
                          if (widget.userIngredients.isNotEmpty && matchingRate > 0) ...[
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: AppTheme.spacingS,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: AppTheme.cardGreen,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                '일치율 ${matchingRate.toInt()}%',
                                style: AppTheme.caption.copyWith(
                                  color: AppTheme.successGreen,
                                ),
                              ),
                            ),
                            const SizedBox(width: AppTheme.spacingS),
                          ],
                          
                          // 조리시간
                          const Icon(
                            Icons.timer,
                            size: 14,
                            color: AppTheme.textGray,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            '${recipe.cookingTimeMinutes}분',
                            style: AppTheme.bodySmall.copyWith(
                              color: AppTheme.textGray,
                            ),
                          ),
                          
                          const SizedBox(width: AppTheme.spacingM),
                          
                          // 난이도
                          RatingDisplay(
                            rating: recipe.difficulty.index + 1.0,
                            reviewCount: 0,
                            starSize: 14,
                          ),
                        ],
                      ),
                    ],
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
