import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// 비동기 작업 상태 관리자
class AsyncStateManager {
  static final Map<String, Future<void>> _runningTasks = {};
  static final Map<String, DateTime> _taskStartTimes = {};
  static final Map<String, int> _retryCounters = {};

  /// 작업 실행 (중복 방지 및 성능 모니터링)
  static Future<T> executeTask<T>(
    String taskId,
    Future<T> Function() task, {
    Duration? timeout,
    int maxRetries = 3,
    Duration retryDelay = const Duration(seconds: 1),
    bool allowDuplicates = false,
  }) async {
    // 중복 작업 방지
    if (!allowDuplicates && _runningTasks.containsKey(taskId)) {
      if (kDebugMode) debugPrint('⏭️ [AsyncStateManager] Task already running: $taskId');
      await _runningTasks[taskId];
      throw Exception('Task already running: $taskId');
    }

    final startTime = DateTime.now();
    _taskStartTimes[taskId] = startTime;
    _retryCounters[taskId] = 0;

    if (kDebugMode) debugPrint('🚀 [AsyncStateManager] Starting task: $taskId');

    final taskFuture = _executeWithRetry<T>(
      taskId,
      task,
      timeout: timeout,
      maxRetries: maxRetries,
      retryDelay: retryDelay,
    );

    _runningTasks[taskId] = taskFuture.then((_) => null);

    try {
      final result = await taskFuture;
      final duration = DateTime.now().difference(startTime);

      if (kDebugMode) {
        debugPrint('✅ [AsyncStateManager] Task completed: $taskId (${duration.inMilliseconds}ms)');
      }

      return result;
    } finally {
      _runningTasks.remove(taskId);
      _taskStartTimes.remove(taskId);
      _retryCounters.remove(taskId);
    }
  }

  /// 재시도 로직이 포함된 작업 실행
  static Future<T> _executeWithRetry<T>(
    String taskId,
    Future<T> Function() task, {
    Duration? timeout,
    int maxRetries = 3,
    Duration retryDelay = const Duration(seconds: 1),
  }) async {
    for (int attempt = 1; attempt <= maxRetries; attempt++) {
      _retryCounters[taskId] = attempt;

      try {
        if (timeout != null) {
          return await task().timeout(timeout);
        } else {
          return await task();
        }
      } catch (e) {
        if (kDebugMode) {
          debugPrint('❌ [AsyncStateManager] Task $taskId attempt $attempt/$maxRetries failed: $e');
        }

        if (attempt < maxRetries) {
          final delay = Duration(milliseconds: retryDelay.inMilliseconds * attempt);
          if (kDebugMode) {
            debugPrint('🔄 [AsyncStateManager] Retrying $taskId in ${delay.inMilliseconds}ms');
          }
          await Future.delayed(delay);
        } else {
          rethrow;
        }
      }
    }

    throw Exception('All retries failed for task: $taskId');
  }

  /// 현재 실행 중인 작업 목록
  static Map<String, Map<String, dynamic>> getRunningTasks() {
    final now = DateTime.now();
    final result = <String, Map<String, dynamic>>{};

    for (final entry in _taskStartTimes.entries) {
      final taskId = entry.key;
      final startTime = entry.value;
      final duration = now.difference(startTime);
      final retryCount = _retryCounters[taskId] ?? 0;

      result[taskId] = {
        'start_time': startTime.toIso8601String(),
        'duration_ms': duration.inMilliseconds,
        'retry_count': retryCount,
        'is_running': _runningTasks.containsKey(taskId),
      };
    }

    return result;
  }

  /// 모든 작업 취소
  static void cancelAllTasks() {
    _runningTasks.clear();
    _taskStartTimes.clear();
    _retryCounters.clear();
    if (kDebugMode) debugPrint('❌ [AsyncStateManager] All tasks cancelled');
  }

  /// 특정 작업 취소
  static void cancelTask(String taskId) {
    _runningTasks.remove(taskId);
    _taskStartTimes.remove(taskId);
    _retryCounters.remove(taskId);
    if (kDebugMode) debugPrint('❌ [AsyncStateManager] Task cancelled: $taskId');
  }

  /// 성능 통계
  static Map<String, dynamic> getPerformanceStats() {
    final runningTasks = getRunningTasks();
    final taskCount = runningTasks.length;

    if (taskCount == 0) {
      return {
        'running_tasks': 0,
        'average_duration_ms': 0,
        'max_duration_ms': 0,
        'total_retries': 0,
      };
    }

    final durations = runningTasks.values.map((t) => t['duration_ms'] as int).toList();
    final retries = runningTasks.values.map((t) => t['retry_count'] as int).toList();

    return {
      'running_tasks': taskCount,
      'average_duration_ms': durations.reduce((a, b) => a + b) ~/ taskCount,
      'max_duration_ms': durations.reduce((a, b) => a > b ? a : b),
      'total_retries': retries.reduce((a, b) => a + b),
    };
  }
}

/// 비동기 작업 상태
enum AsyncTaskStatus {
  idle,
  loading,
  success,
  error,
  cancelled,
}

/// 비동기 작업 상태 정보
class AsyncTaskState<T> {
  final AsyncTaskStatus status;
  final T? data;
  final String? error;
  final DateTime? lastUpdated;
  final int retryCount;
  final Duration? duration;

  const AsyncTaskState({
    this.status = AsyncTaskStatus.idle,
    this.data,
    this.error,
    this.lastUpdated,
    this.retryCount = 0,
    this.duration,
  });

  /// 로딩 상태 생성
  factory AsyncTaskState.loading({int retryCount = 0}) {
    return AsyncTaskState<T>(
      status: AsyncTaskStatus.loading,
      retryCount: retryCount,
      lastUpdated: DateTime.now(),
    );
  }

  /// 성공 상태 생성
  factory AsyncTaskState.success(T data, {Duration? duration}) {
    return AsyncTaskState<T>(
      status: AsyncTaskStatus.success,
      data: data,
      lastUpdated: DateTime.now(),
      duration: duration,
    );
  }

  /// 에러 상태 생성
  factory AsyncTaskState.error(String error, {int retryCount = 0}) {
    return AsyncTaskState<T>(
      status: AsyncTaskStatus.error,
      error: error,
      retryCount: retryCount,
      lastUpdated: DateTime.now(),
    );
  }

  /// 취소 상태 생성
  factory AsyncTaskState.cancelled() {
    return AsyncTaskState<T>(
      status: AsyncTaskStatus.cancelled,
      lastUpdated: DateTime.now(),
    );
  }

  /// 상태 복사
  AsyncTaskState<T> copyWith({
    AsyncTaskStatus? status,
    T? data,
    String? error,
    DateTime? lastUpdated,
    int? retryCount,
    Duration? duration,
  }) {
    return AsyncTaskState<T>(
      status: status ?? this.status,
      data: data ?? this.data,
      error: error ?? this.error,
      lastUpdated: lastUpdated ?? this.lastUpdated,
      retryCount: retryCount ?? this.retryCount,
      duration: duration ?? this.duration,
    );
  }

  /// 상태 확인 getter들
  bool get isLoading => status == AsyncTaskStatus.loading;
  bool get isSuccess => status == AsyncTaskStatus.success;
  bool get isError => status == AsyncTaskStatus.error;
  bool get isCancelled => status == AsyncTaskStatus.cancelled;
  bool get hasData => data != null;

  @override
  String toString() {
    return 'AsyncTaskState(status: $status, hasData: $hasData, error: $error, retryCount: $retryCount)';
  }
}

/// 비동기 작업 관리를 위한 StateNotifier
class AsyncTaskNotifier<T> extends StateNotifier<AsyncTaskState<T>> {
  AsyncTaskNotifier() : super(const AsyncTaskState());

  /// 작업 실행
  Future<void> executeTask(
    String taskId,
    Future<T> Function() task, {
    Duration? timeout,
    int maxRetries = 3,
    Duration retryDelay = const Duration(seconds: 1),
  }) async {
    state = AsyncTaskState.loading();

    try {
      final startTime = DateTime.now();

      final result = await AsyncStateManager.executeTask<T>(
        taskId,
        task,
        timeout: timeout,
        maxRetries: maxRetries,
        retryDelay: retryDelay,
      );

      final duration = DateTime.now().difference(startTime);
      state = AsyncTaskState.success(result, duration: duration);
    } catch (e) {
      state = AsyncTaskState.error(e.toString());
    }
  }

  /// 상태 초기화
  void reset() {
    state = const AsyncTaskState();
  }

  /// 취소
  void cancel(String taskId) {
    AsyncStateManager.cancelTask(taskId);
    state = AsyncTaskState.cancelled();
  }
}

/// 글로벌 비동기 상태 관리 Provider
final asyncStateManagerProvider = Provider<AsyncStateManager>((ref) {
  return AsyncStateManager();
});

/// 성능 모니터링 Provider
final asyncPerformanceStatsProvider = Provider<Map<String, dynamic>>((ref) {
  return AsyncStateManager.getPerformanceStats();
});

/// 실행 중인 작업 목록 Provider
final runningTasksProvider = Provider<Map<String, Map<String, dynamic>>>((ref) {
  return AsyncStateManager.getRunningTasks();
});