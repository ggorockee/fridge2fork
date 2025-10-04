import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/async_state_manager.dart';
import '../services/api/api_client.dart';

/// 비동기 성능 모니터링 위젯 (개발 전용)
class AsyncPerformanceMonitor extends ConsumerWidget {
  const AsyncPerformanceMonitor({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // 디버그 모드에서만 표시
    if (!kDebugMode) return const SizedBox.shrink();

    final asyncStats = ref.watch(asyncPerformanceStatsProvider);
    final runningTasks = ref.watch(runningTasksProvider);
    final apiRequestStatus = ApiClient.getRequestStatus();

    return Container(
      margin: const EdgeInsets.all(8.0),
      padding: const EdgeInsets.all(12.0),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.8),
        borderRadius: BorderRadius.circular(8.0),
        border: Border.all(color: Colors.green, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            '🔍 비동기 성능 모니터',
            style: TextStyle(
              color: Colors.green,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),

          // API 클라이언트 상태
          _buildSection(
            '📡 API 클라이언트',
            [
              'pending: ${apiRequestStatus['pending_requests']}개',
              'current: ${apiRequestStatus['current_requests']}개',
              'max: ${apiRequestStatus['max_concurrent']}개',
            ],
          ),

          const SizedBox(height: 8),

          // 비동기 작업 상태
          _buildSection(
            '⚡ 비동기 작업',
            [
              'running: ${asyncStats['running_tasks']}개',
              'avg: ${asyncStats['average_duration_ms']}ms',
              'max: ${asyncStats['max_duration_ms']}ms',
              'retries: ${asyncStats['total_retries']}회',
            ],
          ),

          // 실행 중인 작업 목록
          if (runningTasks.isNotEmpty) ...[
            const SizedBox(height: 8),
            _buildSection(
              '🏃 실행 중인 작업',
              runningTasks.entries.map((entry) {
                final taskId = entry.key;
                final taskInfo = entry.value;
                final durationMs = taskInfo['duration_ms'] as int;
                final retryCount = taskInfo['retry_count'] as int;

                return '$taskId: ${durationMs}ms (retry: $retryCount)';
              }).toList(),
            ),
          ],

          const SizedBox(height: 8),

          // 컨트롤 버튼들
          Row(
            children: [
              _buildControlButton(
                '🔄 새로고침',
                () => ref.invalidate(asyncPerformanceStatsProvider),
              ),
              const SizedBox(width: 8),
              _buildControlButton(
                '❌ 모든 작업 취소',
                () => AsyncStateManager.cancelAllTasks(),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSection(String title, List<String> items) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            color: Colors.yellow,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        ...items.map((item) => Text(
          '  • $item',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 11,
          ),
        )),
      ],
    );
  }

  Widget _buildControlButton(String text, VoidCallback onPressed) {
    return SizedBox(
      height: 24,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.green.withValues(alpha: 0.7),
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          minimumSize: Size.zero,
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
        child: Text(
          text,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 10,
          ),
        ),
      ),
    );
  }
}

/// 비동기 성능 모니터 오버레이 (전역 표시)
class AsyncPerformanceOverlay extends StatelessWidget {
  final Widget child;
  final bool showMonitor;

  const AsyncPerformanceOverlay({
    super.key,
    required this.child,
    this.showMonitor = true,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        child,
        if (kDebugMode && showMonitor)
          const Positioned(
            top: 50,
            right: 8,
            child: AsyncPerformanceMonitor(),
          ),
      ],
    );
  }
}

/// 비동기 작업 상태 표시 위젯
class AsyncTaskStatusWidget<T> extends ConsumerWidget {
  final AsyncTaskState<T> state;
  final Widget Function(T data) dataBuilder;
  final Widget? loadingWidget;
  final Widget Function(String error)? errorBuilder;
  final String? loadingMessage;

  const AsyncTaskStatusWidget({
    super.key,
    required this.state,
    required this.dataBuilder,
    this.loadingWidget,
    this.errorBuilder,
    this.loadingMessage,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      child: _buildStateWidget(context),
    );
  }

  Widget _buildStateWidget(BuildContext context) {
    switch (state.status) {
      case AsyncTaskStatus.loading:
        return loadingWidget ?? _buildDefaultLoading();

      case AsyncTaskStatus.success:
        if (state.hasData) {
          return dataBuilder(state.data as T);
        }
        return _buildDefaultEmpty();

      case AsyncTaskStatus.error:
        return errorBuilder?.call(state.error ?? 'Unknown error') ??
               _buildDefaultError(state.error ?? 'Unknown error');

      case AsyncTaskStatus.cancelled:
        return _buildDefaultCancelled();

      case AsyncTaskStatus.idle:
        return _buildDefaultIdle();
    }
  }

  Widget _buildDefaultLoading() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(),
          if (loadingMessage != null) ...[
            const SizedBox(height: 8),
            Text(
              loadingMessage!,
              style: const TextStyle(fontSize: 14),
            ),
          ],
          if (state.retryCount > 0) ...[
            const SizedBox(height: 4),
            Text(
              '재시도 중... (${state.retryCount}회)',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDefaultError(String error) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.error_outline,
            color: Colors.red,
            size: 48,
          ),
          const SizedBox(height: 8),
          Text(
            '오류가 발생했습니다',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            error,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
            ),
          ),
          if (state.retryCount > 0) ...[
            const SizedBox(height: 4),
            Text(
              '${state.retryCount}회 재시도 후 실패',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDefaultEmpty() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: const Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.inbox_outlined,
            color: Colors.grey,
            size: 48,
          ),
          SizedBox(height: 8),
          Text(
            '데이터가 없습니다',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDefaultCancelled() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: const Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.cancel_outlined,
            color: Colors.orange,
            size: 48,
          ),
          SizedBox(height: 8),
          Text(
            '작업이 취소되었습니다',
            style: TextStyle(
              fontSize: 16,
              color: Colors.orange,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDefaultIdle() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: const Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.play_circle_outline,
            color: Colors.grey,
            size: 48,
          ),
          SizedBox(height: 8),
          Text(
            '시작 대기 중',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
}