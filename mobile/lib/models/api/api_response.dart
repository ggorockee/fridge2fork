/// API 공통 응답 모델
class ApiResponse<T> {
  final bool success;
  final String message;
  final T? data;
  final Map<String, dynamic>? metadata;
  final int? statusCode;
  final String? errorCode;

  const ApiResponse({
    required this.success,
    required this.message,
    this.data,
    this.metadata,
    this.statusCode,
    this.errorCode,
  });

  /// 성공 응답 생성
  factory ApiResponse.success({
    required T data,
    String message = 'Success',
    Map<String, dynamic>? metadata,
    int statusCode = 200,
  }) {
    return ApiResponse<T>(
      success: true,
      message: message,
      data: data,
      metadata: metadata,
      statusCode: statusCode,
    );
  }

  /// 실패 응답 생성
  factory ApiResponse.error({
    required String message,
    String? errorCode,
    int statusCode = 400,
    Map<String, dynamic>? metadata,
  }) {
    return ApiResponse<T>(
      success: false,
      message: message,
      errorCode: errorCode,
      statusCode: statusCode,
      metadata: metadata,
    );
  }

  /// JSON에서 생성
  factory ApiResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic) fromJsonT,
  ) {
    return ApiResponse<T>(
      success: json['success'] ?? false,
      message: json['message'] ?? '',
      data: json['data'] != null ? fromJsonT(json['data']) : null,
      metadata: json['metadata'] != null ? Map<String, dynamic>.from(json['metadata']) : null,
      statusCode: json['status_code'] ?? json['statusCode'],
      errorCode: json['error_code'] ?? json['errorCode'],
    );
  }

  /// JSON으로 변환
  Map<String, dynamic> toJson([dynamic Function(T)? toJsonT]) {
    return {
      'success': success,
      'message': message,
      'data': data != null && toJsonT != null ? toJsonT(data!) : data,
      'metadata': metadata,
      'status_code': statusCode,
      'error_code': errorCode,
    };
  }
}

/// 페이지네이션 응답 모델
class PaginatedResponse<T> {
  final List<T> items;
  final int currentPage;
  final int totalPages;
  final int totalItems;
  final int pageSize;
  final bool hasNextPage;
  final bool hasPreviousPage;

  const PaginatedResponse({
    required this.items,
    required this.currentPage,
    required this.totalPages,
    required this.totalItems,
    required this.pageSize,
    required this.hasNextPage,
    required this.hasPreviousPage,
  });

  /// JSON에서 생성
  factory PaginatedResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic) fromJsonT,
  ) {
    final items = (json['items'] as List?)
        ?.map((item) => fromJsonT(item))
        .toList() ?? [];

    return PaginatedResponse<T>(
      items: items,
      currentPage: json['current_page'] ?? json['currentPage'] ?? 1,
      totalPages: json['total_pages'] ?? json['totalPages'] ?? 1,
      totalItems: json['total_items'] ?? json['totalItems'] ?? 0,
      pageSize: json['page_size'] ?? json['pageSize'] ?? 10,
      hasNextPage: json['has_next_page'] ?? json['hasNextPage'] ?? false,
      hasPreviousPage: json['has_previous_page'] ?? json['hasPreviousPage'] ?? false,
    );
  }

  /// JSON으로 변환
  Map<String, dynamic> toJson([dynamic Function(T)? toJsonT]) {
    return {
      'items': toJsonT != null ? items.map((item) => toJsonT(item)).toList() : items,
      'current_page': currentPage,
      'total_pages': totalPages,
      'total_items': totalItems,
      'page_size': pageSize,
      'has_next_page': hasNextPage,
      'has_previous_page': hasPreviousPage,
    };
  }
}

/// API 에러 모델
class ApiError {
  final String code;
  final String message;
  final String? details;
  final Map<String, dynamic>? context;

  const ApiError({
    required this.code,
    required this.message,
    this.details,
    this.context,
  });

  /// JSON에서 생성
  factory ApiError.fromJson(Map<String, dynamic> json) {
    return ApiError(
      code: json['code'] ?? 'UNKNOWN_ERROR',
      message: json['message'] ?? 'An unknown error occurred',
      details: json['details'],
      context: json['context'] != null ? Map<String, dynamic>.from(json['context']) : null,
    );
  }

  /// JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'code': code,
      'message': message,
      'details': details,
      'context': context,
    };
  }

  @override
  String toString() {
    return 'ApiError(code: $code, message: $message, details: $details)';
  }
}

/// API 요청 상태
enum ApiStatus {
  idle,      // 초기 상태
  loading,   // 로딩 중
  success,   // 성공
  error,     // 에러
  offline,   // 오프라인
}

/// API 요청 결과
class ApiResult<T> {
  final ApiStatus status;
  final T? data;
  final ApiError? error;
  final DateTime timestamp;

  const ApiResult({
    required this.status,
    this.data,
    this.error,
    required this.timestamp,
  });

  /// 로딩 상태 생성
  factory ApiResult.loading() {
    return ApiResult<T>(
      status: ApiStatus.loading,
      timestamp: DateTime.now(),
    );
  }

  /// 성공 상태 생성
  factory ApiResult.success(T data) {
    return ApiResult<T>(
      status: ApiStatus.success,
      data: data,
      timestamp: DateTime.now(),
    );
  }

  /// 에러 상태 생성
  factory ApiResult.error(ApiError error) {
    return ApiResult<T>(
      status: ApiStatus.error,
      error: error,
      timestamp: DateTime.now(),
    );
  }

  /// 오프라인 상태 생성
  factory ApiResult.offline() {
    return ApiResult<T>(
      status: ApiStatus.offline,
      timestamp: DateTime.now(),
    );
  }

  /// 로딩 중인지 확인
  bool get isLoading => status == ApiStatus.loading;

  /// 성공했는지 확인
  bool get isSuccess => status == ApiStatus.success && data != null;

  /// 에러가 발생했는지 확인
  bool get isError => status == ApiStatus.error;

  /// 오프라인 상태인지 확인
  bool get isOffline => status == ApiStatus.offline;

  /// 데이터가 있는지 확인
  bool get hasData => data != null;
}
