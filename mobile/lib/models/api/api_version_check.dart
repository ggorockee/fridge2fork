/// 앱 버전 체크 API 모델
///
/// 서버 API: GET /system/version/check?platform={android|ios}&current_version={version}
class VersionCheckResponse {
  final bool updateRequired;
  final bool forceUpdate;
  final String latestVersion;
  final int currentVersionCode;
  final int latestVersionCode;
  final int minSupportedVersionCode;
  final String updateMessage;
  final String downloadUrl;

  VersionCheckResponse({
    required this.updateRequired,
    required this.forceUpdate,
    required this.latestVersion,
    required this.currentVersionCode,
    required this.latestVersionCode,
    required this.minSupportedVersionCode,
    required this.updateMessage,
    required this.downloadUrl,
  });

  /// JSON에서 객체 생성
  factory VersionCheckResponse.fromJson(Map<String, dynamic> json) {
    return VersionCheckResponse(
      updateRequired: json['update_required'] as bool? ?? false,
      forceUpdate: json['force_update'] as bool? ?? false,
      latestVersion: json['latest_version'] as String? ?? '',
      currentVersionCode: json['current_version_code'] as int? ?? 0,
      latestVersionCode: json['latest_version_code'] as int? ?? 0,
      minSupportedVersionCode: json['min_supported_version_code'] as int? ?? 0,
      updateMessage: json['update_message'] as String? ?? '',
      downloadUrl: json['download_url'] as String? ?? '',
    );
  }

  /// 객체를 JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'update_required': updateRequired,
      'force_update': forceUpdate,
      'latest_version': latestVersion,
      'current_version_code': currentVersionCode,
      'latest_version_code': latestVersionCode,
      'min_supported_version_code': minSupportedVersionCode,
      'update_message': updateMessage,
      'download_url': downloadUrl,
    };
  }

  /// 업데이트가 필요하지 않은지 확인
  bool get isLatestVersion => !updateRequired;

  /// 선택적 업데이트인지 확인
  bool get isOptionalUpdate => updateRequired && !forceUpdate;

  /// 강제 업데이트인지 확인
  bool get isForcedUpdate => forceUpdate;

  @override
  String toString() {
    return 'VersionCheckResponse('
        'updateRequired: $updateRequired, '
        'forceUpdate: $forceUpdate, '
        'latestVersion: $latestVersion, '
        'currentVersionCode: $currentVersionCode, '
        'latestVersionCode: $latestVersionCode, '
        'minSupportedVersionCode: $minSupportedVersionCode, '
        'updateMessage: $updateMessage, '
        'downloadUrl: $downloadUrl'
        ')';
  }

  /// 복사본 생성 (일부 필드만 변경)
  VersionCheckResponse copyWith({
    bool? updateRequired,
    bool? forceUpdate,
    String? latestVersion,
    int? currentVersionCode,
    int? latestVersionCode,
    int? minSupportedVersionCode,
    String? updateMessage,
    String? downloadUrl,
  }) {
    return VersionCheckResponse(
      updateRequired: updateRequired ?? this.updateRequired,
      forceUpdate: forceUpdate ?? this.forceUpdate,
      latestVersion: latestVersion ?? this.latestVersion,
      currentVersionCode: currentVersionCode ?? this.currentVersionCode,
      latestVersionCode: latestVersionCode ?? this.latestVersionCode,
      minSupportedVersionCode: minSupportedVersionCode ?? this.minSupportedVersionCode,
      updateMessage: updateMessage ?? this.updateMessage,
      downloadUrl: downloadUrl ?? this.downloadUrl,
    );
  }
}
