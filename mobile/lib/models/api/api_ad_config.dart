/// AdMob 광고 설정 API 모델
///
/// 서버 API: GET /system/ads/config?platform={android|ios}
class AdConfigResponse {
  final String? bannerTop;
  final String? bannerBottom;
  final String? interstitial1;
  final String? interstitial2;
  final String? native1;
  final String? native2;

  AdConfigResponse({
    this.bannerTop,
    this.bannerBottom,
    this.interstitial1,
    this.interstitial2,
    this.native1,
    this.native2,
  });

  /// JSON에서 객체 생성
  factory AdConfigResponse.fromJson(Map<String, dynamic> json) {
    return AdConfigResponse(
      bannerTop: json['banner_top'] as String?,
      bannerBottom: json['banner_bottom'] as String?,
      interstitial1: json['interstitial_1'] as String?,
      interstitial2: json['interstitial_2'] as String?,
      native1: json['native_1'] as String?,
      native2: json['native_2'] as String?,
    );
  }

  /// 객체를 JSON으로 변환
  Map<String, dynamic> toJson() {
    return {
      'banner_top': bannerTop,
      'banner_bottom': bannerBottom,
      'interstitial_1': interstitial1,
      'interstitial_2': interstitial2,
      'native_1': native1,
      'native_2': native2,
    };
  }

  /// 모든 광고 ID가 null인지 확인
  bool get isEmpty =>
      bannerTop == null &&
      bannerBottom == null &&
      interstitial1 == null &&
      interstitial2 == null &&
      native1 == null &&
      native2 == null;

  /// 최소 하나 이상의 광고 ID가 있는지 확인
  bool get isNotEmpty => !isEmpty;

  @override
  String toString() {
    return 'AdConfigResponse('
        'bannerTop: $bannerTop, '
        'bannerBottom: $bannerBottom, '
        'interstitial1: $interstitial1, '
        'interstitial2: $interstitial2, '
        'native1: $native1, '
        'native2: $native2'
        ')';
  }

  /// 복사본 생성 (일부 필드만 변경)
  AdConfigResponse copyWith({
    String? bannerTop,
    String? bannerBottom,
    String? interstitial1,
    String? interstitial2,
    String? native1,
    String? native2,
  }) {
    return AdConfigResponse(
      bannerTop: bannerTop ?? this.bannerTop,
      bannerBottom: bannerBottom ?? this.bannerBottom,
      interstitial1: interstitial1 ?? this.interstitial1,
      interstitial2: interstitial2 ?? this.interstitial2,
      native1: native1 ?? this.native1,
      native2: native2 ?? this.native2,
    );
  }
}
