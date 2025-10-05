import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../widgets/widgets.dart';
import '../models/feedback.dart' as feedback_model;
import '../providers/feedback_provider.dart';

/// 의견보내기 화면
class FeedbackScreen extends ConsumerStatefulWidget {
  const FeedbackScreen({super.key});

  @override
  ConsumerState<FeedbackScreen> createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends ConsumerState<FeedbackScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        backgroundColor: AppTheme.backgroundWhite,
        elevation: 0,
        automaticallyImplyLeading: false,
        title: Text(
          '의견보내기',
          style: TextStyle(
            color: AppTheme.textPrimary,
            fontSize: 20.sp,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(AppTheme.spacingM),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 피드백 카테고리 목록
            _buildFeedbackItem(
              icon: Icons.add_box,
              iconColor: AppTheme.primaryOrange,
              title: '식재료 추가 요청',
              onTap: () => _showFeedbackForm('식재료 추가 요청'),
            ),
            SizedBox(height: AppTheme.spacingM),
            
            _buildFeedbackItem(
              icon: Icons.restaurant_menu,
              iconColor: AppTheme.primaryOrange,
              title: '레시피 추가 요청',
              onTap: () => _showFeedbackForm('레시피 추가 요청'),
            ),
            SizedBox(height: AppTheme.spacingM),
            
            _buildFeedbackItem(
              icon: Icons.bug_report,
              iconColor: AppTheme.primaryOrange,
              title: '의견 보내기',
              onTap: () => _showFeedbackForm('의견 보내기'),
            ),
            
            SizedBox(height: AppTheme.spacingXL),
            
            // 하단 안내 메시지
            SizedBox(
              width: double.infinity,
              child: Container(
                padding: EdgeInsets.all(AppTheme.spacingL),
                decoration: BoxDecoration(
                  color: AppTheme.lightOrange,
                  borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
                  border: Border.all(
                    color: AppTheme.primaryOrange.withValues(alpha: 0.3),
                    width: 1.w,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '어떤 의견이든 환영해요! 😊',
                      style: TextStyle(
                        fontSize: 16.sp,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    SizedBox(height: AppTheme.spacingS),
                    Text(
                      '냉장고 털기 앱이 처음이라 서툴 수 있어요.',
                      style: TextStyle(
                        fontSize: 14.sp,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    Text(
                      '여러분의 따뜻한 응원과 조언으로 더 나아질게요! 💪',
                      style: TextStyle(
                        fontSize: 14.sp,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 피드백 아이템 위젯
  Widget _buildFeedbackItem({
    required IconData icon,
    required Color iconColor,
    required String title,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: EdgeInsets.all(AppTheme.spacingM),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 10.r,
              offset: Offset(0.w, 2.h),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 48.w,
              height: 48.h,
              decoration: BoxDecoration(
                color: AppTheme.backgroundGray,
                borderRadius: BorderRadius.circular(AppTheme.radiusSmall),
              ),
              child: Icon(
                icon,
                color: iconColor,
                size: 24.sp,
              ),
            ),
            SizedBox(width: AppTheme.spacingM),
            Expanded(
              child: Text(
                title,
                style: TextStyle(
                  fontSize: 16.sp,
                  fontWeight: FontWeight.w500,
                  color: AppTheme.textPrimary,
                ),
              ),
            ),
            Icon(
              Icons.arrow_forward_ios,
              color: AppTheme.textSecondary,
              size: 16.sp,
            ),
          ],
        ),
      ),
    );
  }

  /// 피드백 폼 모달 표시
  void _showFeedbackForm(String category) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => FeedbackFormModal(category: category),
    );
  }
}

/// 피드백 폼 모달
class FeedbackFormModal extends ConsumerStatefulWidget {
  final String category;

  const FeedbackFormModal({
    super.key,
    required this.category,
  });

  @override
  ConsumerState<FeedbackFormModal> createState() => _FeedbackFormModalState();
}

class _FeedbackFormModalState extends ConsumerState<FeedbackFormModal> {
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _feedbackController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();

  @override
  void dispose() {
    _titleController.dispose();
    _feedbackController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  /// 카테고리를 피드백 타입으로 변환
  String _getFeedbackType() {
    switch (widget.category) {
      case '식재료 추가 요청':
        return feedback_model.FeedbackType.feature;
      case '레시피 추가 요청':
        return feedback_model.FeedbackType.feature;
      case '의견 보내기':
        return feedback_model.FeedbackType.improvement;
      default:
        return feedback_model.FeedbackType.other;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.8,
      decoration: const BoxDecoration(
        color: AppTheme.backgroundWhite,
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(AppTheme.radiusLarge),
          topRight: Radius.circular(AppTheme.radiusLarge),
        ),
      ),
      child: Column(
        children: [
          // Modal 상단 핸들 바
          Container(
            width: 40.w,
            height: 4.h,
            margin: EdgeInsets.symmetric(vertical: AppTheme.spacingM),
            decoration: BoxDecoration(
              color: AppTheme.textSecondary.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(2.r),
            ),
          ),
          
          // 헤더
          Padding(
            padding: EdgeInsets.symmetric(horizontal: AppTheme.spacingM),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    widget.category,
                    style: TextStyle(
                      fontSize: 20.sp,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: Icon(
                    Icons.close,
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: AppTheme.spacingL),
          
          // 폼 내용
          Expanded(
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: AppTheme.spacingM),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 제목 입력 필드
                  Text(
                    '제목',
                    style: TextStyle(
                      fontSize: 16.sp,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  SizedBox(height: AppTheme.spacingS),
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: AppTheme.spacingM),
                    decoration: BoxDecoration(
                      color: AppTheme.backgroundGray,
                      borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
                      border: Border.all(
                        color: AppTheme.textPlaceholder.withValues(alpha: 0.3),
                        width: 1.w,
                      ),
                    ),
                    child: TextField(
                      controller: _titleController,
                      style: TextStyle(
                        fontSize: 14.sp,
                        color: AppTheme.textPrimary,
                      ),
                      decoration: const InputDecoration(
                        hintText: '제목을 입력해주세요',
                        hintStyle: TextStyle(
                          color: AppTheme.textPlaceholder,
                        ),
                        border: InputBorder.none,
                      ),
                    ),
                  ),

                  SizedBox(height: AppTheme.spacingL),

                  // 내용 입력 필드
                  Text(
                    '내용',
                    style: TextStyle(
                      fontSize: 16.sp,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  SizedBox(height: AppTheme.spacingS),
                  Expanded(
                    child: Container(
                      padding: EdgeInsets.all(AppTheme.spacingM),
                      decoration: BoxDecoration(
                        color: AppTheme.backgroundGray,
                        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
                        border: Border.all(
                          color: AppTheme.textPlaceholder.withValues(alpha: 0.3),
                          width: 1.w,
                        ),
                      ),
                      child: TextField(
                        controller: _feedbackController,
                        maxLines: null,
                        expands: true,
                        textAlignVertical: TextAlignVertical.top,
                        style: TextStyle(
                          fontSize: 14.sp,
                          color: AppTheme.textPrimary,
                        ),
                        decoration: const InputDecoration(
                          hintText: '의견을 자세히 적어주세요...',
                          hintStyle: TextStyle(
                            color: AppTheme.textPlaceholder,
                          ),
                          border: InputBorder.none,
                        ),
                      ),
                    ),
                  ),

                  SizedBox(height: AppTheme.spacingL),

                  // 이메일 입력 필드 (선택사항)
                  Text(
                    '답변 받을 이메일 (선택)',
                    style: TextStyle(
                      fontSize: 16.sp,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  SizedBox(height: AppTheme.spacingS),
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: AppTheme.spacingM),
                    decoration: BoxDecoration(
                      color: AppTheme.backgroundGray,
                      borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
                      border: Border.all(
                        color: AppTheme.textPlaceholder.withValues(alpha: 0.3),
                        width: 1.w,
                      ),
                    ),
                    child: TextField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      style: TextStyle(
                        fontSize: 14.sp,
                        color: AppTheme.textPrimary,
                      ),
                      decoration: const InputDecoration(
                        hintText: 'example@email.com',
                        hintStyle: TextStyle(
                          color: AppTheme.textPlaceholder,
                        ),
                        border: InputBorder.none,
                      ),
                    ),
                  ),
                  
                  SizedBox(height: AppTheme.spacingL),
                  
                  // 제출 버튼
                  Consumer(
                    builder: (context, ref, child) {
                      final feedbackState = ref.watch(feedbackProvider);
                      final isSubmitting = feedbackState.isSubmitting;

                      return SizedBox(
                        width: double.infinity,
                        child: CustomButton(
                          text: isSubmitting ? '전송 중...' : '의견 보내기',
                          onPressed: isSubmitting ? null : _submitFeedback,
                          type: ButtonType.primary,
                          height: 56.h,
                          icon: Icons.send,
                        ),
                      );
                    },
                  ),

                  // 하단 안전 영역
                  SizedBox(height: MediaQuery.of(context).padding.bottom + AppTheme.spacingM),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 피드백 제출
  Future<void> _submitFeedback() async {
    // 제목 유효성 검사
    if (_titleController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('제목을 입력해주세요.'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    // 내용 유효성 검사
    if (_feedbackController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('의견을 입력해주세요.'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    // Feedback 객체 생성
    final feedback = feedback_model.Feedback(
      feedbackType: _getFeedbackType(),
      title: _titleController.text.trim(),
      content: _feedbackController.text.trim(),
      contactEmail: _emailController.text.trim().isEmpty ? null : _emailController.text.trim(),
    );

    // API 호출
    final success = await ref.read(feedbackProvider.notifier).submitFeedback(feedback);

    if (mounted) {
      if (success) {
        // 성공 시 모달 닫고 성공 메시지 표시
        Navigator.of(context).pop();

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('소중한 의견 감사합니다! 🙏'),
            backgroundColor: AppTheme.primaryOrange,
          ),
        );
      } else {
        // 실패 시 에러 메시지 표시
        final feedbackState = ref.read(feedbackProvider);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(feedbackState.errorMessage ?? '피드백 전송에 실패했습니다.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
}
