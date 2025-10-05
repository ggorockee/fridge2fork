import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/feedback.dart';
import '../services/api/feedback_api_service.dart';

/// 피드백 전송 상태
class FeedbackState {
  final bool isSubmitting;
  final bool isSuccess;
  final String? errorMessage;
  final Feedback? submittedFeedback;

  const FeedbackState({
    this.isSubmitting = false,
    this.isSuccess = false,
    this.errorMessage,
    this.submittedFeedback,
  });

  FeedbackState copyWith({
    bool? isSubmitting,
    bool? isSuccess,
    String? errorMessage,
    Feedback? submittedFeedback,
  }) {
    return FeedbackState(
      isSubmitting: isSubmitting ?? this.isSubmitting,
      isSuccess: isSuccess ?? this.isSuccess,
      errorMessage: errorMessage,
      submittedFeedback: submittedFeedback ?? this.submittedFeedback,
    );
  }
}

/// 피드백 상태 관리 Notifier
class FeedbackNotifier extends StateNotifier<FeedbackState> {
  FeedbackNotifier() : super(const FeedbackState());

  /// 피드백 전송
  Future<bool> submitFeedback(Feedback feedback) async {
    state = state.copyWith(isSubmitting: true, isSuccess: false, errorMessage: null);

    try {
      final response = await FeedbackApiService.submitFeedback(feedback);

      if (response.success && response.data != null) {
        state = state.copyWith(
          isSubmitting: false,
          isSuccess: true,
          submittedFeedback: response.data,
        );
        return true;
      } else {
        state = state.copyWith(
          isSubmitting: false,
          isSuccess: false,
          errorMessage: response.message,
        );
        return false;
      }
    } catch (e) {
      state = state.copyWith(
        isSubmitting: false,
        isSuccess: false,
        errorMessage: '피드백 전송 중 오류가 발생했습니다: $e',
      );
      return false;
    }
  }

  /// 상태 초기화
  void reset() {
    state = const FeedbackState();
  }
}

/// 피드백 Provider
final feedbackProvider = StateNotifierProvider<FeedbackNotifier, FeedbackState>((ref) {
  return FeedbackNotifier();
});
