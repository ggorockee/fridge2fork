import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';
import '../../config/app_config.dart';
import '../../models/api/api_response.dart';
import '../session_service.dart';

/// API 클라이언트 설정 (비동기 최적화)
class ApiClient {
  static http.Client? _client;
  static String? _baseUrl;
  static Duration? _timeout;
  static Map<String, String>? _defaultHeaders;

  // 비동기 최적화를 위한 추가 필드들
  static final Map<String, Future<dynamic>> _pendingRequests = {};
  static const int _maxConcurrentRequests = 5;
  static int _currentRequestCount = 0;

  /// API 클라이언트 초기화
  static void initialize({
    String? baseUrl,
    Duration? timeout,
    Map<String, String>? defaultHeaders,
  }) {
    _baseUrl = baseUrl ?? AppConfig.apiBaseUrl;
    _timeout = timeout ?? Duration(milliseconds: AppConfig.apiTimeoutMs);
    _defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...?defaultHeaders,
    };

    // HTTP 클라이언트 설정
    _client = http.Client();

    if (kDebugMode && AppConfig.enableNetworkLogging) {
      debugPrint('🔧 API Client initialized');
      debugPrint('Base URL: $_baseUrl');
      debugPrint('Timeout: ${_timeout?.inMilliseconds}ms');
    }
  }

  /// HTTP 클라이언트 가져오기
  static http.Client get client {
    if (_client == null) {
      throw Exception('API Client not initialized. Call ApiClient.initialize() first.');
    }
    return _client!;
  }

  /// 기본 URL 가져오기
  static String get baseUrl {
    if (_baseUrl == null) {
      throw Exception('API Client not initialized. Call ApiClient.initialize() first.');
    }
    return _baseUrl!;
  }

  /// 기본 헤더 가져오기
  static Map<String, String> get defaultHeaders {
    return _defaultHeaders ?? {'Content-Type': 'application/json'};
  }

  /// 타임아웃 가져오기
  static Duration get timeout {
    return _timeout ?? Duration(milliseconds: AppConfig.apiTimeoutMs);
  }

  /// GET 요청
  static Future<ApiResponse<T>> get<T>(
    String endpoint, {
    Map<String, dynamic>? queryParams,
    Map<String, String>? headers,
    T Function(dynamic)? fromJson,
  }) async {
    return _makeRequest<T>(
      'GET',
      endpoint,
      queryParams: queryParams,
      headers: headers,
      fromJson: fromJson,
    );
  }

  /// POST 요청
  static Future<ApiResponse<T>> post<T>(
    String endpoint, {
    Map<String, dynamic>? body,
    Map<String, String>? headers,
    T Function(dynamic)? fromJson,
  }) async {
    return _makeRequest<T>(
      'POST',
      endpoint,
      body: body,
      headers: headers,
      fromJson: fromJson,
    );
  }

  /// PUT 요청
  static Future<ApiResponse<T>> put<T>(
    String endpoint, {
    Map<String, dynamic>? body,
    Map<String, String>? headers,
    T Function(dynamic)? fromJson,
  }) async {
    return _makeRequest<T>(
      'PUT',
      endpoint,
      body: body,
      headers: headers,
      fromJson: fromJson,
    );
  }

  /// DELETE 요청
  static Future<ApiResponse<T>> delete<T>(
    String endpoint, {
    Map<String, String>? headers,
    T Function(dynamic)? fromJson,
  }) async {
    return _makeRequest<T>(
      'DELETE',
      endpoint,
      headers: headers,
      fromJson: fromJson,
    );
  }

  /// 비동기 최적화된 공통 요청 처리
  static Future<ApiResponse<T>> _makeRequest<T>(
    String method,
    String endpoint, {
    Map<String, dynamic>? queryParams,
    Map<String, dynamic>? body,
    Map<String, String>? headers,
    T Function(dynamic)? fromJson,
  }) async {
    // Request deduplication: 동일한 요청이 진행 중이면 기존 요청 결과 반환
    final requestKey = _generateRequestKey(method, endpoint, queryParams, body);

    if (_pendingRequests.containsKey(requestKey)) {
      if (kDebugMode && AppConfig.enableNetworkLogging) {
        debugPrint('🔄 Request deduplication: Using pending request for $method $endpoint');
      }
      return await _pendingRequests[requestKey] as Future<ApiResponse<T>>;
    }

    // 동시 요청 수 제한
    if (_currentRequestCount >= _maxConcurrentRequests) {
      if (kDebugMode && AppConfig.enableNetworkLogging) {
        debugPrint('⏳ Request queued: Max concurrent requests reached ($method $endpoint)');
      }
      await _waitForAvailableSlot();
    }

    // 요청 시작
    _currentRequestCount++;

    final requestFuture = _executeRequest<T>(
      method, endpoint,
      queryParams: queryParams,
      body: body,
      headers: headers,
      fromJson: fromJson
    );

    _pendingRequests[requestKey] = requestFuture;

    try {
      final result = await requestFuture;
      return result;
    } finally {
      // 요청 완료 후 정리
      _currentRequestCount--;
      _pendingRequests.remove(requestKey);
    }
  }

  /// 요청 키 생성 (중복 방지)
  static String _generateRequestKey(
    String method,
    String endpoint,
    Map<String, dynamic>? queryParams,
    Map<String, dynamic>? body
  ) {
    final queryString = queryParams?.entries.map((e) => '${e.key}=${e.value}').join('&') ?? '';
    final bodyString = body != null ? jsonEncode(body) : '';
    return '$method:$endpoint:$queryString:$bodyString';
  }

  /// 사용 가능한 슬롯 대기
  static Future<void> _waitForAvailableSlot() async {
    while (_currentRequestCount >= _maxConcurrentRequests) {
      await Future.delayed(const Duration(milliseconds: 50));
    }
  }

  /// 실제 요청 실행
  static Future<ApiResponse<T>> _executeRequest<T>(
    String method,
    String endpoint, {
    Map<String, dynamic>? queryParams,
    Map<String, dynamic>? body,
    Map<String, String>? headers,
    T Function(dynamic)? fromJson,
  }) async {
    try {
      // URL 구성
      final uri = _buildUri(endpoint, queryParams);

      // 세션 ID 헤더 자동 추가
      final sessionId = await SessionService.instance.getSessionId();

      // 헤더 구성
      final requestHeaders = {
        ...defaultHeaders,
        'X-Session-ID': sessionId,
        ...?headers,
      };

      // 요청 로깅
      if (kDebugMode && AppConfig.enableNetworkLogging) {
        debugPrint('🌐 $method $uri');
        if (body != null) {
          debugPrint('📤 Request Body: ${jsonEncode(body)}');
        }
      }

      // HTTP 요청 생성
      http.Request request;
      switch (method.toUpperCase()) {
        case 'GET':
          request = http.Request('GET', uri);
          break;
        case 'POST':
          request = http.Request('POST', uri);
          if (body != null) {
            request.body = jsonEncode(body);
          }
          break;
        case 'PUT':
          request = http.Request('PUT', uri);
          if (body != null) {
            request.body = jsonEncode(body);
          }
          break;
        case 'DELETE':
          request = http.Request('DELETE', uri);
          break;
        default:
          throw Exception('Unsupported HTTP method: $method');
      }

      request.headers.addAll(requestHeaders);

      // 요청 실행
      final streamedResponse = await client.send(request).timeout(timeout);
      var response = await http.Response.fromStream(streamedResponse);

      // 응답 로깅
      if (kDebugMode && AppConfig.enableNetworkLogging) {
        debugPrint('📥 Response ${response.statusCode}: ${response.body}');
      }

      // UTF-8 인코딩 확인 및 수정
      if (response.headers['content-type']?.contains('charset') != true) {
        // Content-Type에 charset이 명시되지 않은 경우 UTF-8로 가정하고 디코딩
        final originalBody = response.body;
        if (originalBody.contains('�')) {
          // 깨진 문자가 있으면 UTF-8로 다시 디코딩 시도
          try {
            final bytes = response.bodyBytes;
            final decodedBody = utf8.decode(bytes, allowMalformed: false);
            response = http.Response(decodedBody, response.statusCode,
              headers: response.headers, request: response.request);
            if (kDebugMode) {
              debugPrint('🔧 Re-decoded response body with UTF-8');
            }
          } catch (e) {
            if (kDebugMode) {
              debugPrint('⚠️ UTF-8 re-decoding failed: $e');
            }
          }
        }
      }

      // 응답 처리
      return _handleResponse<T>(response, fromJson);

    } on SocketException {
      // 네트워크 오류
      return ApiResponse.error(
        message: '네트워크 연결을 확인해주세요.',
        errorCode: 'NETWORK_ERROR',
        statusCode: 0,
      );
    } on HttpException catch (e) {
      // HTTP 오류
      return ApiResponse.error(
        message: 'HTTP 오류가 발생했습니다: ${e.message}',
        errorCode: 'HTTP_ERROR',
        statusCode: 500,
      );
    } on FormatException catch (e) {
      // JSON 파싱 오류
      return ApiResponse.error(
        message: '응답 데이터 형식 오류: ${e.message}',
        errorCode: 'FORMAT_ERROR',
        statusCode: 422,
      );
    } catch (e) {
      // 기타 오류
      return ApiResponse.error(
        message: '알 수 없는 오류가 발생했습니다: $e',
        errorCode: 'UNKNOWN_ERROR',
        statusCode: 500,
      );
    }
  }

  /// URI 구성 (한글 파라미터 인코딩 지원)
  static Uri _buildUri(String endpoint, Map<String, dynamic>? queryParams) {
    final baseUri = Uri.parse('$baseUrl$endpoint');

    if (queryParams != null && queryParams.isNotEmpty) {
      // 한글 및 특수문자를 올바르게 인코딩
      final encodedParams = <String, String>{};
      for (final entry in queryParams.entries) {
        final value = entry.value.toString();
        encodedParams[entry.key] = Uri.encodeComponent(value);
      }

      return baseUri.replace(
        queryParameters: {
          ...baseUri.queryParameters,
          ...encodedParams,
        },
      );
    }

    return baseUri;
  }

  /// 응답 처리
  static ApiResponse<T> _handleResponse<T>(
    http.Response response,
    T Function(dynamic)? fromJson,
  ) {
    final statusCode = response.statusCode;
    
    try {
      final Map<String, dynamic> jsonResponse = jsonDecode(response.body);

      if (kDebugMode && AppConfig.enableNetworkLogging) {
        debugPrint('🔍 Parsed JSON keys: ${jsonResponse.keys.toList()}');
      }

      if (statusCode >= 200 && statusCode < 300) {
        // 성공 응답 - 다양한 API 응답 구조 지원
        var data = jsonResponse['data'];

        // data 필드가 없으면 다른 가능한 필드들 확인
        if (data == null) {
          if (jsonResponse.containsKey('ingredients')) {
            // RecipeIngredientsResponse의 경우 전체 응답 구조 유지
            if (jsonResponse.containsKey('categories') || jsonResponse.containsKey('total')) {
              data = jsonResponse; // ingredients, categories, total을 모두 포함한 전체 응답
              if (kDebugMode && AppConfig.enableNetworkLogging) {
                debugPrint('🥬 Using RecipeIngredientsResponse structure: ${jsonResponse['ingredients'].length} ingredients, ${jsonResponse['categories']?.length ?? 0} categories');
              }
            } else {
              // 기존 PaginatedResponse 형식
              data = {'items': jsonResponse['ingredients']};
              if (kDebugMode && AppConfig.enableNetworkLogging) {
                debugPrint('🥬 Using ingredients field: ${jsonResponse['ingredients'].length} items');
              }
            }
          } else if (jsonResponse.containsKey('recipes')) {
            data = jsonResponse; // 전체 응답을 그대로 전달
            if (kDebugMode && AppConfig.enableNetworkLogging) {
              debugPrint('🍳 Using recipes field: ${jsonResponse['recipes'].length} items');
            }
          } else {
            // 전체 응답을 data로 사용 (meta 필드 제외)
            data = Map<String, dynamic>.from(jsonResponse)
              ..remove('message')
              ..remove('metadata')
              ..remove('timestamp');
            if (kDebugMode && AppConfig.enableNetworkLogging) {
              debugPrint('📦 Using full response as data: ${data.keys.toList()}');
            }
          }
        } else {
          if (kDebugMode && AppConfig.enableNetworkLogging) {
            debugPrint('📄 Using data field from response');
          }
        }

        if (fromJson != null && data != null) {
          return ApiResponse.success(
            data: fromJson(data),
            message: jsonResponse['message'] ?? 'Success',
            statusCode: statusCode,
            metadata: jsonResponse['metadata'],
          );
        } else {
          if (data != null) {
            return ApiResponse.success(
              data: data as T,
              message: jsonResponse['message'] ?? 'Success',
              statusCode: statusCode,
              metadata: jsonResponse['metadata'],
            );
          } else {
            return ApiResponse.error(
              message: jsonResponse['message'] ?? 'No data received',
              statusCode: statusCode,
              metadata: jsonResponse['metadata'],
            );
          }
        }
      } else {
        // 에러 응답
        return ApiResponse.error(
          message: jsonResponse['message'] ?? 'Request failed',
          errorCode: jsonResponse['error_code'] ?? jsonResponse['errorCode'],
          statusCode: statusCode,
          metadata: jsonResponse['metadata'],
        );
      }
    } catch (e) {
      // JSON 파싱 실패
      return ApiResponse.error(
        message: 'Invalid response format',
        errorCode: 'INVALID_RESPONSE',
        statusCode: statusCode,
      );
    }
  }

  /// 병렬 요청 실행 (최적화된 배치 처리)
  static Future<List<ApiResponse<T>>> batchRequests<T>(
    List<Future<ApiResponse<T>>> requests, {
    int? concurrencyLimit,
  }) async {
    final limit = concurrencyLimit ?? _maxConcurrentRequests;
    final results = <ApiResponse<T>>[];

    for (int i = 0; i < requests.length; i += limit) {
      final batch = requests.skip(i).take(limit);
      final batchResults = await Future.wait(batch, eagerError: false);
      results.addAll(batchResults);

      if (kDebugMode && AppConfig.enableNetworkLogging) {
        debugPrint('🚀 Batch ${(i ~/ limit) + 1} completed: ${batchResults.length} requests');
      }
    }

    return results;
  }

  /// 진행 중인 요청 상태 조회
  static Map<String, dynamic> getRequestStatus() {
    return {
      'pending_requests': _pendingRequests.length,
      'current_requests': _currentRequestCount,
      'max_concurrent': _maxConcurrentRequests,
    };
  }

  /// 모든 진행 중인 요청 취소
  static void cancelAllRequests() {
    _pendingRequests.clear();
    _currentRequestCount = 0;
    if (kDebugMode) debugPrint('❌ All pending requests cancelled');
  }

  /// 클라이언트 종료
  static void close() {
    cancelAllRequests();
    _client?.close();
    _client = null;
  }

  /// API 연결 테스트 (향상된 버전)
  static Future<bool> testConnection() async {
    try {
      // 시스템 health check 엔드포인트 먼저 시도
      var response = await get(ApiEndpoints.systemHealth);

      if (!response.success) {
        // 시스템 헬스체크 실패시 시스템 버전 엔드포인트 시도
        response = await get(ApiEndpoints.systemVersion);
      }

      if (kDebugMode && AppConfig.enableNetworkLogging) {
        debugPrint('🔍 API Connection Test: ${response.success ? "SUCCESS" : "FAILED"}');
        if (response.success) {
          debugPrint('📡 API Status: ${response.data}');
        } else {
          debugPrint('❌ API Connection Failed: ${response.message}');
        }
      }
      return response.success;
    } catch (e) {
      if (kDebugMode && AppConfig.enableNetworkLogging) {
        debugPrint('❌ API Connection Test Failed: $e');
      }
      return false;
    }
  }

  /// 시스템 헬스체크
  static Future<ApiResponse<Map<String, dynamic>>> getSystemHealth() async {
    return await get<Map<String, dynamic>>(
      '/system/health',
      fromJson: (json) => Map<String, dynamic>.from(json),
    );
  }

  /// API 버전 정보
  static Future<ApiResponse<Map<String, dynamic>>> getSystemVersion() async {
    return await get<Map<String, dynamic>>(
      '/system/version',
      fromJson: (json) => Map<String, dynamic>.from(json),
    );
  }
}

/// API 엔드포인트 상수 - OpenAPI 스펙 기반
class ApiEndpoints {
  // 시스템
  static const String health = '/health';
  static const String systemHealth = '/fridge2fork/v1/system/health';
  static const String systemVersion = '/fridge2fork/v1/system/version';
  static const String systemPlatforms = '/fridge2fork/v1/system/platforms';
  static const String systemStats = '/fridge2fork/v1/system/stats';

  // 냉장고 재료 관리
  static const String ingredients = '/fridge2fork/v1/fridge/ingredients';
  static const String myIngredients = '/fridge2fork/v1/fridge/my-ingredients';
  static const String categories = '/fridge2fork/v1/fridge/categories';
  static const String recipesByIngredients = '/fridge2fork/v1/fridge/recipes/by-ingredients';

  // 레시피
  static const String recipes = '/fridge2fork/v1/recipes/';
  static const String recipeIngredients = '/fridge2fork/v1/recipes/ingredients'; // 레시피에 사용된 모든 재료 목록
  static const String recipeCategories = '/fridge2fork/v1/recipes/categories'; // 레시피 카테고리 목록
  static const String randomRecommendations = '/fridge2fork/v1/recipes/random-recommendations';
  static const String recipesByFridge = '/fridge2fork/v1/recipes/by-fridge';
  static const String recipeStats = '/fridge2fork/v1/recipes/stats/summary';

  /// 특정 레시피 상세 조회
  static String recipeById(String rcpSno) => '/fridge2fork/v1/recipes/$rcpSno';

  /// 엔드포인트에서 ID 치환
  static String replaceId(String endpoint, String id) {
    return endpoint.replaceAll('{id}', id).replaceAll('{rcp_sno}', id);
  }
}
