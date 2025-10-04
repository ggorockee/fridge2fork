import 'package:flutter/foundation.dart';
import '../../models/api/api_response.dart';
import '../../models/feedback.dart';
import 'api_client.dart';

class FeedbackApiService {
  /// 피드백 전송
  static Future<ApiResponse<Feedback>> submitFeedback(Feedback feedback) async {
    try {
      if (kDebugMode) {
        debugPrint('📤 피드백 전송: ${feedback.title}');
      }

      final response = await ApiClient.post(
        ApiEndpoints.submitFeedback,
        body: feedback.toJson(),
      );

      if (kDebugMode) {
        debugPrint('📥 피드백 응답: ${response.statusCode}');
      }

      if (response.success && response.data != null) {
        final feedbackData = Feedback.fromJson(response.data);
        return ApiResponse.success(
          data: feedbackData,
          message: response.message,
        );
      } else {
        return ApiResponse.error(
          message: response.message,
        );
      }
    } catch (e) {
      if (kDebugMode) {
        debugPrint('❌ 피드백 전송 오류: $e');
      }
      return ApiResponse.error(
        message: '피드백 전송 중 오류가 발생했습니다: $e',
      );
    }
  }
}
