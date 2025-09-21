import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:showcaseview/showcaseview.dart';
import '../theme/app_theme.dart';
import '../widgets/widgets.dart';
import '../providers/ingredients_provider.dart';
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
      appBar: const CustomAppBar(
        title: '냉털레시피',
        hasSearch: false,
      ),
      body: Stack(
        children: [
          Column(
            children: [
              // 냉장고 부분 - 전체 화면의 2/3
              Expanded(
                flex: 2,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(0, 0, 0, 20), // 상단 여백, 하단 여백
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
              
              // 남은 공간 채우기
              const SizedBox(height: 30),
              
            ],
          ),
          
          // 플로팅 액션 버튼 - 냉장고 영역 우하단에 위치
          Positioned(
            right: 16, // body 전체 기준 우측에서 16px 마진
            bottom: 220 + 80 + 16, // 추천 레시피 높이(220) + 하단 네비(80) + 마진(16)
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
      
    );
  }

}

/// 냉장고 아이콘 위젯 - 재빌드 시에도 안정적인 렌더링을 위한 정적 위젯
class _FridgeIcon extends StatelessWidget {
  const _FridgeIcon();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 120,
      height: 120,
      decoration: const BoxDecoration(
        color: AppTheme.primaryOrange,
        borderRadius: BorderRadius.all(Radius.circular(AppTheme.radiusMedium)),
      ),
      child: const Icon(
        Icons.kitchen,
        size: 60,
        color: Colors.white,
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
class _RecipeRecommendationSection extends StatelessWidget {
  const _RecipeRecommendationSection();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.only(left: AppTheme.spacingM, top: AppTheme.spacingM),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 섹션 제목
          const Padding(
            padding: EdgeInsets.only(bottom: AppTheme.spacingM),
            child: Text(
              '추천 레시피',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
          ),
          
          // 가로 스크롤 레시피 카드들
          SizedBox(
            height: 160, // 카드 높이와 동일하게 고정
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: 5, // 샘플 데이터
              itemBuilder: (context, index) {
                final recipes = [
                  {'title': '제육볶음', 'time': '25분'},
                  {'title': '김치찌개', 'time': '30분'},
                  {'title': '불고기', 'time': '20분'},
                  {'title': '된장찌개', 'time': '15분'},
                  {'title': '비빔밥', 'time': '10분'},
                ];
                
                return _RecipeCard(
                  title: recipes[index]['title']!,
                  cookingTime: recipes[index]['time']!,
                  isLast: index == 4, // 마지막 아이템인지 확인
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

/// 레시피 카드 위젯
class _RecipeCard extends StatelessWidget {
  final String title;
  final String cookingTime;
  final bool isLast;

  const _RecipeCard({
    required this.title,
    required this.cookingTime,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 140,
      height: 160, // 카드 높이를 160으로 고정
      margin: EdgeInsets.only(
        right: isLast ? 0 : AppTheme.spacingM, // 마지막 아이템은 우측 마진 없음
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(AppTheme.radiusCard),
        border: Border.all(
          color: Colors.grey.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 레시피 이미지 (placeholder)
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
                'https://picsum.photos/300/200?random=${title.hashCode.abs() % 1000}',
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
                  title,
                  style: const TextStyle(
                    fontSize: 14, // 폰트 크기를 카드에 맞게 조정
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                
                const SizedBox(height: 4), // 간격을 카드에 맞게 조정
                
                Row(
                  children: [
                    const Icon(
                      Icons.access_time,
                      size: 12, // 아이콘 크기를 카드에 맞게 조정
                      color: AppTheme.textSecondary,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      cookingTime,
                      style: const TextStyle(
                        fontSize: 12, // 폰트 크기를 카드에 맞게 조정
                        color: AppTheme.textPrimary,
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
          Text(
            '냉장고 현황',
            style: const TextStyle(
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
