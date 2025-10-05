import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
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
      margin: EdgeInsets.all(8.0.w),
      padding: EdgeInsets.all(12.0.w),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.8),
        borderRadius: BorderRadius.circular(8.0.r),
        border: Border.all(color: Colors.green, width: 1.w),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '🔍 비동기 성능 모니터',
            style: TextStyle(
              color: Colors.green,
              fontSize: 14.sp,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 8.h),

          // API 클라이언트 상태
          _buildSection(
            '📡 API 클라이언트',
            [
              'pending: ${apiRequestStatus['pending_requests']}개',
              'current: ${apiRequestStatus['current_requests']}개',
              'max: ${apiRequestStatus['max_concurrent']}개',
            ],
          ),

          SizedBox(height: 8.h),

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
            SizedBox(height: 8.h),
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

          SizedBox(height: 8.h),

          // 컨트롤 버튼들
          Row(
            children: [
              _buildControlButton(
                '🔄 새로고침',
                () => ref.invalidate(asyncPerformanceStatsProvider),
              ),
              SizedBox(width: 8.w),
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
          style: TextStyle(
            color: Colors.yellow,
            fontSize: 12.sp,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 4.h),
        ...items.map((item) => Text(
          '  • $item',
          style: TextStyle(
            color: Colors.white,
            fontSize: 11.sp,
          ),
        )),
      ],
    );
  }

  Widget _buildControlButton(String text, VoidCallback onPressed) {
    return SizedBox(
      height: 24.h,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.green.withValues(alpha: 0.7),
          padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 2.h),
          minimumSize: Size.zero,
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
        child: Text(
          text,
          style: TextStyle(
            color: Colors.white,
            fontSize: 10.sp,
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
      padding: EdgeInsets.all(16.w),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(),
          if (loadingMessage != null) ...[
            SizedBox(height: 8.h),
            Text(
              loadingMessage!,
              style: TextStyle(fontSize: 14.sp),
            ),
          ],
          if (state.retryCount > 0) ...[
            SizedBox(height: 4.h),
            Text(
              '재시도 중... (${state.retryCount}회)',
              style: TextStyle(
                fontSize: 12.sp,
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
      padding: EdgeInsets.all(16.w),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.error_outline,
            color: Colors.red,
            size: 48.sp,
          ),
          SizedBox(height: 8.h),
          Text(
            '오류가 발생했습니다',
            style: TextStyle(
              fontSize: 16.sp,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 4.h),
          Text(
            error,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14.sp,
              color: Colors.grey[600],
            ),
          ),
          if (state.retryCount > 0) ...[
            SizedBox(height: 4.h),
            Text(
              '${state.retryCount}회 재시도 후 실패',
              style: TextStyle(
                fontSize: 12.sp,
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
      padding: EdgeInsets.all(16.w),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.inbox_outlined,
            color: Colors.grey,
            size: 48.sp,
          ),
          SizedBox(height: 8.h),
          Text(
            '데이터가 없습니다',
            style: TextStyle(
              fontSize: 16.sp,
              color: Colors.grey,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDefaultCancelled() {
    return Container(
      padding: EdgeInsets.all(16.w),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.cancel_outlined,
            color: Colors.orange,
            size: 48.sp,
          ),
          SizedBox(height: 8.h),
          Text(
            '작업이 취소되었습니다',
            style: TextStyle(
              fontSize: 16.sp,
              color: Colors.orange,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDefaultIdle() {
    return Container(
      padding: EdgeInsets.all(16.w),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.play_circle_outline,
            color: Colors.grey,
            size: 48.sp,
          ),
          SizedBox(height: 8.h),
          Text(
            '시작 대기 중',
            style: TextStyle(
              fontSize: 16.sp,
              color: Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
}