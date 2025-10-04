import 'api_client.dart';
import '../../models/api/api_response.dart';

/// 시스템 API 서비스
class SystemApiService {
  /// 헬스체크 (시스템용)
  static Future<ApiResponse<Map<String, dynamic>>> getHealth() async {
    return await ApiClient.get<Map<String, dynamic>>(
      ApiEndpoints.systemHealth,
      fromJson: (json) => Map<String, dynamic>.from(json),
    );
  }

  /// 간단한 헬스체크
  static Future<ApiResponse<Map<String, dynamic>>> getSimpleHealth() async {
    return await ApiClient.get<Map<String, dynamic>>(
      ApiEndpoints.health,
      fromJson: (json) => Map<String, dynamic>.from(json),
    );
  }

  /// 시스템 버전 정보 조회
  static Future<ApiResponse<Map<String, dynamic>>> getVersion() async {
    return await ApiClient.get<Map<String, dynamic>>(
      ApiEndpoints.systemVersion,
      fromJson: (json) => Map<String, dynamic>.from(json),
    );
  }

  /// 지원 플랫폼 정보 조회
  static Future<ApiResponse<Map<String, dynamic>>> getPlatforms() async {
    return await ApiClient.get<Map<String, dynamic>>(
      ApiEndpoints.systemPlatforms,
      fromJson: (json) => Map<String, dynamic>.from(json),
    );
  }

  /// 시스템 통계 정보 조회
  static Future<ApiResponse<Map<String, dynamic>>> getStats() async {
    return await ApiClient.get<Map<String, dynamic>>(
      ApiEndpoints.systemStats,
      fromJson: (json) => Map<String, dynamic>.from(json),
    );
  }

  /// API 서버 연결 상태 확인
  static Future<bool> isServerOnline() async {
    try {
      final response = await getHealth();
      return response.success;
    } catch (e) {
      return false;
    }
  }

  /// API 서버 응답 시간 측정
  static Future<Duration?> getResponseTime() async {
    final stopwatch = Stopwatch()..start();
    
    try {
      final response = await getHealth();
      stopwatch.stop();
      
      if (response.success) {
        return stopwatch.elapsed;
      } else {
        return null;
      }
    } catch (e) {
      stopwatch.stop();
      return null;
    }
  }

  /// 시스템 정보 요약 조회
  static Future<ApiResponse<Map<String, dynamic>>> getSystemSummary() async {
    try {
      // 여러 API를 병렬로 호출
      final results = await Future.wait([
        getHealth(),
        getVersion(),
        getStats(),
      ]);

      final healthResponse = results[0];
      final versionResponse = results[1];
      final statsResponse = results[2];

      // 모든 응답이 성공한 경우에만 성공으로 처리
      if (healthResponse.success && versionResponse.success && statsResponse.success) {
        final summary = <String, dynamic>{
          'health': healthResponse.data,
          'version': versionResponse.data,
          'stats': statsResponse.data,
          'timestamp': DateTime.now().toIso8601String(),
        };

        return ApiResponse.success(
          data: summary,
          message: '시스템 정보를 성공적으로 조회했습니다.',
          statusCode: 200,
        );
      } else {
        return ApiResponse.error(
          message: '일부 시스템 정보를 가져올 수 없습니다.',
          errorCode: 'PARTIAL_FAILURE',
          statusCode: 206, // Partial Content
        );
      }
    } catch (e) {
      return ApiResponse.error(
        message: '시스템 정보 조회 중 오류가 발생했습니다: $e',
        errorCode: 'SYSTEM_ERROR',
        statusCode: 500,
      );
    }
  }

  /// API 서버 상태 모니터링
  static Future<ApiResponse<Map<String, dynamic>>> monitorServerStatus() async {
    final stopwatch = Stopwatch()..start();
    
    try {
      final healthResponse = await getHealth();
      stopwatch.stop();
      
      final status = <String, dynamic>{
        'is_online': healthResponse.success,
        'response_time_ms': stopwatch.elapsedMilliseconds,
        'timestamp': DateTime.now().toIso8601String(),
        'status_code': healthResponse.statusCode,
        'error_message': healthResponse.success ? null : healthResponse.message,
      };

      if (healthResponse.success && healthResponse.data != null) {
        status.addAll(healthResponse.data!);
      }

      return ApiResponse.success(
        data: status,
        message: healthResponse.success 
            ? '서버가 정상적으로 작동 중입니다.'
            : '서버 연결에 문제가 있습니다.',
        statusCode: healthResponse.success ? 200 : 503,
      );
    } catch (e) {
      stopwatch.stop();
      
      return ApiResponse.error(
        message: '서버 상태 확인 중 오류가 발생했습니다: $e',
        errorCode: 'MONITORING_ERROR',
        statusCode: 500,
        metadata: {
          'response_time_ms': stopwatch.elapsedMilliseconds,
          'timestamp': DateTime.now().toIso8601String(),
        },
      );
    }
  }

  /// API 서버 연결 테스트 (재시도 포함)
  static Future<ApiResponse<Map<String, dynamic>>> testConnection({
    int maxRetries = 3,
    Duration retryDelay = const Duration(seconds: 1),
  }) async {
    int attempt = 0;
    final results = <Map<String, dynamic>>[];

    while (attempt < maxRetries) {
      attempt++;
      
      final stopwatch = Stopwatch()..start();
      try {
        final response = await getHealth();
        stopwatch.stop();

        final result = {
          'attempt': attempt,
          'success': response.success,
          'response_time_ms': stopwatch.elapsedMilliseconds,
          'status_code': response.statusCode,
          'timestamp': DateTime.now().toIso8601String(),
        };

        results.add(result);

        if (response.success) {
          // 성공한 경우 즉시 반환
          return ApiResponse.success(
            data: {
              'connection_test': 'passed',
              'attempts': results,
              'total_attempts': attempt,
              'average_response_time_ms': results
                  .map((r) => r['response_time_ms'] as int)
                  .reduce((a, b) => a + b) ~/ results.length,
            },
            message: '연결 테스트가 성공했습니다.',
            statusCode: 200,
          );
        }

        // 마지막 시도가 아니면 잠시 대기
        if (attempt < maxRetries) {
          await Future.delayed(retryDelay);
        }
      } catch (e) {
        stopwatch.stop();
        
        results.add({
          'attempt': attempt,
          'success': false,
          'response_time_ms': stopwatch.elapsedMilliseconds,
          'error': e.toString(),
          'timestamp': DateTime.now().toIso8601String(),
        });

        if (attempt < maxRetries) {
          await Future.delayed(retryDelay);
        }
      }
    }

    // 모든 시도가 실패한 경우
    return ApiResponse.error(
      message: '연결 테스트가 실패했습니다. $maxRetries회 시도 후에도 연결할 수 없습니다.',
      errorCode: 'CONNECTION_TEST_FAILED',
      statusCode: 503,
      metadata: {
        'attempts': results,
        'total_attempts': maxRetries,
      },
    );
  }
}
