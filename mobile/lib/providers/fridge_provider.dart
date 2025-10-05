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

  /// 재료 추가 (백그라운드 처리)
  Future<bool> addIngredient(String ingredientName) async {
    if (kDebugMode) {
      debugPrint('🥬 [FridgeProvider] Adding ingredient: $ingredientName');
    }

    // 백그라운드에서 API 호출 (UI 블로킹 없음)
    FridgeApiService.addIngredient(ingredientName).then((response) async {
      if (kDebugMode) {
        final sessionAfter = await SessionService.instance.getSessionId();
        debugPrint('🔍 [DEBUG] Session AFTER add: ${sessionAfter ?? "null"}');
        debugPrint('🥬 [FridgeProvider] Response: success=${response.success}, hasData=${response.data != null}');
      }

      if (response.success && response.data != null) {
        state = AsyncValue.data(response.data!);
        if (kDebugMode) {
          debugPrint('✅ [FridgeProvider] State updated with ${response.data!.ingredients.length} ingredients');
          debugPrint('🔍 [DEBUG] Fridge ID: ${response.data!.id}');
          debugPrint('🔍 [DEBUG] Ingredients: ${response.data!.ingredients.map((e) => e.name).join(", ")}');
        }
      } else {
        if (kDebugMode) {
          debugPrint('❌ [FridgeProvider] Failed to add ingredient: ${response.message}');
        }
      }
    }).catchError((error) {
      if (kDebugMode) {
        debugPrint('❌ [FridgeProvider] Error adding ingredient: $error');
      }
    });

    return true; // 즉시 반환 (UI 블로킹 없음)
  }

  /// 여러 재료를 한번에 추가 (병렬 처리 + Loading State)
  Future<int> addIngredients(List<String> ingredientNames) async {
    if (ingredientNames.isEmpty) return 0;

    if (kDebugMode) {
      debugPrint('🥬 [FridgeProvider] Adding ${ingredientNames.length} ingredients in batch');
    }

    // Loading 상태로 전환 (사용자에게 처리 중임을 표시)
    state = const AsyncValue.loading();

    try {
      // 병렬로 모든 재료 추가 API 호출
      final futures = ingredientNames.map((name) =>
        FridgeApiService.addIngredient(name)
      ).toList();

      final responses = await Future.wait(futures);

      // 성공한 재료 개수 계산
      final successCount = responses.where((r) => r.success).length;

      if (kDebugMode) {
        debugPrint('✅ [FridgeProvider] Batch add completed: $successCount/${ingredientNames.length} succeeded');
      }

      // 냉장고 재조회로 최종 상태 갱신 (한번만 re-render)
      await loadFridge();

      return successCount;
    } catch (e) {
      if (kDebugMode) {
        debugPrint('❌ [FridgeProvider] Batch add error: $e');
      }

      // 에러 발생 시에도 냉장고 재조회
      await loadFridge();
      return 0;
    }
  }

  /// 재료 제거 (Optimistic UI)
  Future<bool> removeIngredient(int ingredientId) async {
    // 1. 현재 상태 백업 (롤백용)
    final currentFridge = state.value;

    if (currentFridge == null) {
      if (kDebugMode) {
        debugPrint('❌ [FridgeProvider] Cannot remove: fridge is null');
      }
      return false;
    }

    // 2. Optimistic Update: 로컬에서 즉시 제거 (UI 즉시 반영)
    final updatedIngredients = currentFridge.ingredients
        .where((ing) => ing.id != ingredientId)
        .toList();

    state = AsyncValue.data(currentFridge.copyWith(
      ingredients: updatedIngredients,
      updatedAt: DateTime.now(),
    ));

    if (kDebugMode) {
      debugPrint('🗑️ [FridgeProvider] Optimistically removed ingredient $ingredientId');
      debugPrint('📊 [FridgeProvider] UI updated with ${updatedIngredients.length} ingredients');
    }

    // 3. 백그라운드에서 API 호출 (unawaited)
    FridgeApiService.removeIngredient(ingredientId).then((response) {
      if (!response.success) {
        // 실패 시 롤백
        if (kDebugMode) {
          debugPrint('❌ [FridgeProvider] API failed, rolling back');
        }
        state = AsyncValue.data(currentFridge);
      } else {
        if (kDebugMode) {
          debugPrint('✅ [FridgeProvider] API confirmed removal');
        }
      }
    }).catchError((error) {
      // 에러 발생 시에도 롤백
      if (kDebugMode) {
        debugPrint('❌ [FridgeProvider] Error occurred, rolling back: $error');
      }
      state = AsyncValue.data(currentFridge);
    });

    return true; // 즉시 반환 (UI 블로킹 없음)
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
