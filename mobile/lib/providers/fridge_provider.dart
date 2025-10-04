import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/api/api_fridge.dart';
import '../services/api/fridge_api_service.dart';
import '../services/session_service.dart';

/// 냉장고 상태 관리 Provider
class FridgeNotifier extends StateNotifier<AsyncValue<ApiFridge>> {
  FridgeNotifier() : super(const AsyncValue.loading()) {
    // 초기 로드
    loadFridge();
  }

  /// 냉장고 조회
  Future<void> loadFridge() async {
    if (kDebugMode) {
      // 🔍 DEBUG: 냉장고 조회 전 세션 ID
      final sessionBefore = await SessionService.instance.getSessionId();
      debugPrint('🔍 [DEBUG] Session BEFORE getFridge: ${sessionBefore ?? "null"}');
    }

    state = const AsyncValue.loading();

    final response = await FridgeApiService.getFridge();

    if (kDebugMode) {
      // 🔍 DEBUG: 냉장고 조회 후 세션 ID
      final sessionAfter = await SessionService.instance.getSessionId();
      debugPrint('🔍 [DEBUG] Session AFTER getFridge: ${sessionAfter ?? "null"}');

      if (response.success && response.data != null) {
        debugPrint('🔍 [DEBUG] Fridge ID from GET: ${response.data!.id}');
        debugPrint('🔍 [DEBUG] Ingredients from GET: ${response.data!.ingredients.map((e) => e.name).join(", ")}');
        debugPrint('🔍 [DEBUG] Total ingredients: ${response.data!.ingredients.length}');
      }
    }

    if (response.success && response.data != null) {
      state = AsyncValue.data(response.data!);
    } else {
      state = AsyncValue.error(
        response.message,
        StackTrace.current,
      );
    }
  }

  /// 재료 추가
  Future<bool> addIngredient(String ingredientName) async {
    if (kDebugMode) {
      debugPrint('🥬 [FridgeProvider] Adding ingredient: $ingredientName');
      // 🔍 DEBUG: 재료 추가 전 세션 ID
      final sessionBefore = await SessionService.instance.getSessionId();
      debugPrint('🔍 [DEBUG] Session BEFORE add: ${sessionBefore ?? "null"}');
    }

    final response = await FridgeApiService.addIngredient(ingredientName);

    if (kDebugMode) {
      // 🔍 DEBUG: 재료 추가 후 세션 ID
      final sessionAfter = await SessionService.instance.getSessionId();
      debugPrint('🔍 [DEBUG] Session AFTER add: ${sessionAfter ?? "null"}');

      debugPrint('🥬 [FridgeProvider] Response: success=${response.success}, hasData=${response.data != null}');
      if (response.data != null) {
        debugPrint('🥬 [FridgeProvider] Fridge after add: ${response.data!.ingredients.length} ingredients');
        debugPrint('🔍 [DEBUG] Fridge ID in response: ${response.data!.id}');
        debugPrint('🔍 [DEBUG] Ingredients in response: ${response.data!.ingredients.map((e) => e.name).join(", ")}');
      }
    }

    if (response.success && response.data != null) {
      state = AsyncValue.data(response.data!);
      if (kDebugMode) {
        debugPrint('✅ [FridgeProvider] State updated with ${response.data!.ingredients.length} ingredients');
      }
      return true;
    } else {
      if (kDebugMode) {
        debugPrint('❌ [FridgeProvider] Failed to add ingredient: ${response.message}');
      }
      // 에러 상태로 변경하지 않고, 실패만 반환
      return false;
    }
  }

  /// 재료 제거
  Future<bool> removeIngredient(int ingredientId) async {
    final response = await FridgeApiService.removeIngredient(ingredientId);

    if (response.success) {
      // 성공 시 냉장고 재조회
      await loadFridge();
      return true;
    } else {
      return false;
    }
  }

  /// 냉장고 전체 비우기
  Future<bool> clearFridge() async {
    final response = await FridgeApiService.clearFridge();

    if (response.success) {
      // 성공 시 냉장고 재조회
      await loadFridge();
      return true;
    } else {
      return false;
    }
  }
}

/// 냉장고 Provider
final fridgeProvider = StateNotifierProvider<FridgeNotifier, AsyncValue<ApiFridge>>((ref) {
  return FridgeNotifier();
});

/// 냉장고 재료명 목록 Provider
final fridgeIngredientNamesProvider = Provider<List<String>>((ref) {
  final fridgeState = ref.watch(fridgeProvider);
  return fridgeState.when(
    data: (fridge) => fridge.ingredientNames,
    loading: () => [],
    error: (_, __) => [],
  );
});

/// 냉장고 재료 개수 Provider
final fridgeIngredientCountProvider = Provider<int>((ref) {
  final ingredientNames = ref.watch(fridgeIngredientNamesProvider);
  return ingredientNames.length;
});
