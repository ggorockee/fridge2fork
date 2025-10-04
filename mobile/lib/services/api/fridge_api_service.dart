import 'package:flutter/foundation.dart';
import 'api_client.dart';
import '../../models/api/api_fridge.dart';
import '../../models/api/api_response.dart';

/// 냉장고 관리 API 서비스 (서버 스펙 준수)
class FridgeApiService {
  /// 냉장고 조회
  /// GET /fridge
  static Future<ApiResponse<ApiFridge>> getFridge() async {
    try {
      final response = await ApiClient.get<ApiFridge>(
        ApiEndpoints.fridge,
        fromJson: (json) => ApiFridge.fromJson(json),
      );

      if (kDebugMode && response.success) {
        debugPrint('🥬 냉장고 조회 성공: ${response.data?.ingredients.length}개 재료');
      }

      return response;
    } catch (e) {
      if (kDebugMode) {
        debugPrint('❌ 냉장고 조회 실패: $e');
      }
      return ApiResponse.error(
        message: '냉장고를 불러오는 중 오류가 발생했습니다',
        statusCode: 500,
      );
    }
  }

  /// 냉장고에 재료 추가
  /// POST /fridge/ingredients
  /// body: {ingredient_name: str}
  static Future<ApiResponse<ApiFridge>> addIngredient(String ingredientName) async {
    try {
      final response = await ApiClient.post<ApiFridge>(
        ApiEndpoints.fridgeIngredients,
        body: {'ingredient_name': ingredientName},
        fromJson: (json) => ApiFridge.fromJson(json),
      );

      if (kDebugMode && response.success) {
        debugPrint('✅ 재료 추가 성공: $ingredientName');
      }

      return response;
    } catch (e) {
      if (kDebugMode) {
        debugPrint('❌ 재료 추가 실패: $e');
      }
      return ApiResponse.error(
        message: '재료 추가 중 오류가 발생했습니다',
        statusCode: 500,
      );
    }
  }

  /// 냉장고에서 재료 제거
  /// DELETE /fridge/ingredients/{ingredient_id}
  static Future<ApiResponse<Map<String, dynamic>>> removeIngredient(int ingredientId) async {
    try {
      final response = await ApiClient.delete<Map<String, dynamic>>(
        '${ApiEndpoints.fridgeIngredients}/$ingredientId',
        fromJson: (json) => json,
      );

      if (kDebugMode && response.success) {
        debugPrint('🗑️ 재료 제거 성공: ID $ingredientId');
      }

      return response;
    } catch (e) {
      if (kDebugMode) {
        debugPrint('❌ 재료 제거 실패: $e');
      }
      return ApiResponse.error(
        message: '재료 제거 중 오류가 발생했습니다',
        statusCode: 500,
      );
    }
  }

  /// 냉장고 전체 비우기
  /// DELETE /fridge/clear
  static Future<ApiResponse<Map<String, dynamic>>> clearFridge() async {
    try {
      final response = await ApiClient.delete<Map<String, dynamic>>(
        ApiEndpoints.fridgeClear,
        fromJson: (json) => json,
      );

      if (kDebugMode && response.success) {
        debugPrint('🗑️ 냉장고 전체 삭제 성공');
      }

      return response;
    } catch (e) {
      if (kDebugMode) {
        debugPrint('❌ 냉장고 전체 삭제 실패: $e');
      }
      return ApiResponse.error(
        message: '냉장고 비우기 중 오류가 발생했습니다',
        statusCode: 500,
      );
    }
  }
}
