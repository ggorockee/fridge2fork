import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../theme/app_theme.dart';
import '../providers/ingredients_provider.dart';
import 'package:another_flushbar/flushbar.dart';

/// 커스텀 앱바 위젯
/// 검색 기능이 통합된 앱바
class CustomAppBar extends ConsumerStatefulWidget implements PreferredSizeWidget {
  final String title;
  final bool hasSearch;
  final String searchHint;
  final List<Widget>? actions;
  final VoidCallback? onBackPressed;

  const CustomAppBar({
    super.key,
    required this.title,
    this.hasSearch = false,
    this.searchHint = '검색...',
    this.actions,
    this.onBackPressed,
  });

  @override
  ConsumerState<CustomAppBar> createState() => _CustomAppBarState();

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}

class _CustomAppBarState extends ConsumerState<CustomAppBar> {
  late TextEditingController _searchController;

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _startSearch() {
    ref.read(isSearchingProvider.notifier).state = true;
    _searchController.text = ref.read(searchTextProvider);
  }

  void _stopSearch() {
    ref.read(isSearchingProvider.notifier).state = false;
    ref.read(searchTextProvider.notifier).state = '';
    _searchController.clear();
  }

  @override
  Widget build(BuildContext context) {
    final isSearching = ref.watch(isSearchingProvider);

    return AppBar(
      backgroundColor: AppTheme.backgroundWhite,
      elevation: 0,
      automaticallyImplyLeading: false,
      
      // 검색 모드에 따른 제목/검색창 표시
      title: isSearching && widget.hasSearch
          ? _buildSearchField()
          : Row(
              children: [
                // 뒤로가기 버튼 (필요한 경우)
                if (widget.onBackPressed != null) ...[
                  GestureDetector(
                    onTap: widget.onBackPressed,
                    child: Container(
                      width: 40.w,
                      height: 40.h,
                      decoration: BoxDecoration(
                        color: AppTheme.backgroundGray,
                        borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
                      ),
                      child: Icon(
                        Icons.arrow_back,
                        color: AppTheme.iconPrimary,
                        size: 20.sp,
                      ),
                    ),
                  ),
                  SizedBox(width: AppTheme.spacingM),
                ],

                // 제목
                Expanded(
                  child: Text(
                    widget.title,
                    style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 20.sp,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
      
      // 액션 버튼들
      actions: isSearching && widget.hasSearch
          ? [
              // 검색 취소 버튼
              IconButton(
                onPressed: _stopSearch,
                icon: const Icon(
                  Icons.close,
                  color: AppTheme.iconPrimary,
                ),
              ),
            ]
          : [
              // 검색 시작 버튼 (검색 기능이 있는 경우)
              if (widget.hasSearch)
                IconButton(
                  onPressed: _startSearch,
                  icon: const Icon(
                    Icons.search,
                    color: AppTheme.iconPrimary,
                  ),
                ),
              
              // 추가 액션 버튼들
              if (widget.actions != null) ...widget.actions!,
            ],
    );
  }

  /// 검색 입력 필드
  Widget _buildSearchField() {
    return TextField(
      controller: _searchController,
      autofocus: true,
      style: TextStyle(
        color: AppTheme.textPrimary,
        fontSize: 16.sp,
      ),
      decoration: InputDecoration(
        hintText: widget.searchHint,
        hintStyle: TextStyle(
          color: AppTheme.textPlaceholder,
          fontSize: 16.sp,
        ),
        border: InputBorder.none,
        contentPadding: EdgeInsets.zero,
      ),
      onChanged: (value) {
        ref.read(searchTextProvider.notifier).state = value;
      },
    );
  }
}

/// 앱 전체에서 일관된 스타일의 알림 메시지(Flushbar)를 표시하기 위한 헬퍼 클래스
class SnackBarHelper {
  static void showSnackBar(
    BuildContext context,
    String message, {
    Color backgroundColor = AppTheme.primaryOrange,
    Duration duration = const Duration(seconds: 3),
  }) {
    Flushbar(
      messageText: Text(
        message,
        textAlign: TextAlign.center,
        style: TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w600,
          fontSize: 15.sp,
        ),
      ),
      backgroundColor: backgroundColor,
      duration: duration,
      flushbarPosition: FlushbarPosition.TOP, // 상단에 표시
      margin: EdgeInsets.all(12.w),
      borderRadius: BorderRadius.circular(AppTheme.radiusButton),
      animationDuration: const Duration(milliseconds: 400),
      boxShadows: [
        BoxShadow(
          color: Colors.black.withOpacity(0.1),
          offset: Offset(0, 2.h),
          blurRadius: 5.r,
        ),
      ],
    ).show(context);
  }
}
