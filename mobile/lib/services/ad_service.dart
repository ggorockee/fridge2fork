import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import '../config/app_config.dart';
import 'ad_config_manager.dart';

/// AdMob 광고 서비스
///
/// 🚨 중요: iOS/Android 광고 정책 준수 필수
/// - 사용자 경험을 해치지 않는 광고 배치
/// - 적절한 광고 빈도 유지
/// - 무효 클릭 방지
///
/// 🎯 동적 광고 ID 지원:
/// - 서버에서 광고 ID를 동적으로 로드
/// - 앱 재배포 없이 광고 ID 변경 가능
/// - AdConfigManager를 통한 캐싱 및 fallback 지원
class AdService {
  static final AdService _instance = AdService._internal();
  factory AdService() => _instance;
  AdService._internal();

  final AdConfigManager _adConfigManager = AdConfigManager();

  // 광고 인스턴스 (수익성 극대화: 4가지 타입 모두 활용)
  BannerAd? _bannerTopAd;
  BannerAd? _bannerBottomAd;
  InterstitialAd? _interstitialAd;
  NativeAd? _nativeAd;
  
  // 광고 상태
  bool _isInitialized = false;
  bool _isInterstitialLoaded = false;
  DateTime? _lastInterstitialShown;
  
  // 광고 ID 가져오기 (동적 로드 + Fallback 지원)
  /// 상단 배너 광고 ID (서버 우선, 환경 변수 fallback)
  String get _bannerTopAdUnitId => _adConfigManager.bannerTopId;

  /// 하단 배너 광고 ID (서버 우선, 환경 변수 fallback)
  String get _bannerBottomAdUnitId => _adConfigManager.bannerBottomId;

  /// 전면 광고 ID (서버 우선, 환경 변수 fallback)
  String get _interstitialAdUnitId => _adConfigManager.interstitial1Id;

  /// 네이티브 광고 ID (서버 우선, 환경 변수 fallback)
  String get _nativeAdUnitId => _adConfigManager.native1Id;

  /// AdMob 초기화
  Future<void> initialize() async {
    if (_isInitialized) return;
    
    try {
      await MobileAds.instance.initialize();
      _isInitialized = true;
      
      // 개발 환경에서는 테스트 디바이스 설정
      if (AppConfig.isDevelopment) {
        await MobileAds.instance.updateRequestConfiguration(
          RequestConfiguration(
            testDeviceIds: ['YOUR_TEST_DEVICE_ID'], // 실제 테스트 디바이스 ID로 변경
          ),
        );
      }
      
      debugPrint('🎯 AdMob 초기화 완료');
    } catch (e) {
      debugPrint('❌ AdMob 초기화 실패: $e');
    }
  }

  /// 상단 배너 광고 생성 (홈 화면용 - 높은 가시성)
  BannerAd? createBannerTopAd() {
    if (!_isInitialized || _bannerTopAdUnitId.isEmpty) return null;
    
    _bannerTopAd?.dispose();
    _bannerTopAd = BannerAd(
      adUnitId: _bannerTopAdUnitId,
      size: AdSize.banner,
      request: const AdRequest(),
      listener: BannerAdListener(
        onAdLoaded: (ad) => debugPrint('🎯 상단 배너 광고 로드 완료'),
        onAdFailedToLoad: (ad, error) {
          debugPrint('❌ 상단 배너 광고 로드 실패: $error');
          ad.dispose();
        },
        onAdOpened: (ad) => debugPrint('🎯 상단 배너 광고 열림'),
        onAdClosed: (ad) => debugPrint('🎯 상단 배너 광고 닫힘'),
      ),
    );
    
    _bannerTopAd!.load();
    return _bannerTopAd;
  }

  /// 하단 배너 광고 생성 (목록 화면용 - 지속적 노출)
  BannerAd? createBannerBottomAd() {
    if (!_isInitialized || _bannerBottomAdUnitId.isEmpty) return null;
    
    _bannerBottomAd?.dispose();
    _bannerBottomAd = BannerAd(
      adUnitId: _bannerBottomAdUnitId,
      size: AdSize.banner,
      request: const AdRequest(),
      listener: BannerAdListener(
        onAdLoaded: (ad) => debugPrint('🎯 하단 배너 광고 로드 완료'),
        onAdFailedToLoad: (ad, error) {
          debugPrint('❌ 하단 배너 광고 로드 실패: $error');
          ad.dispose();
        },
        onAdOpened: (ad) => debugPrint('🎯 하단 배너 광고 열림'),
        onAdClosed: (ad) => debugPrint('🎯 하단 배너 광고 닫힘'),
      ),
    );
    
    _bannerBottomAd!.load();
    return _bannerBottomAd;
  }

  /// 적응형 배너 광고 생성 (화면 크기에 맞춤)
  Future<BannerAd?> createAdaptiveBannerAd({
    required double width, 
    bool isTop = false
  }) async {
    final adUnitId = isTop ? _bannerTopAdUnitId : _bannerBottomAdUnitId;
    if (!_isInitialized || adUnitId.isEmpty) return null;
    
    final adaptiveSize = await AdSize.getAnchoredAdaptiveBannerAdSize(
      Orientation.portrait,
      width.truncate(),
    );
    
    if (adaptiveSize == null) return null;
    
    final bannerAd = BannerAd(
      adUnitId: adUnitId,
      size: adaptiveSize,
      request: const AdRequest(),
      listener: BannerAdListener(
        onAdLoaded: (ad) => debugPrint('🎯 적응형 배너 광고 로드 완료'),
        onAdFailedToLoad: (ad, error) {
          debugPrint('❌ 적응형 배너 광고 로드 실패: $error');
          ad.dispose();
        },
      ),
    );
    
    bannerAd.load();
    return bannerAd;
  }

  /// 전면 광고 로드
  Future<void> loadInterstitialAd() async {
    if (!_isInitialized || _interstitialAdUnitId.isEmpty) return;
    
    try {
      await InterstitialAd.load(
        adUnitId: _interstitialAdUnitId,
        request: const AdRequest(),
        adLoadCallback: InterstitialAdLoadCallback(
          onAdLoaded: (ad) {
            _interstitialAd = ad;
            _isInterstitialLoaded = true;
            debugPrint('🎯 전면 광고 로드 완료');
            
            // 전면 광고 이벤트 리스너 설정
            ad.fullScreenContentCallback = FullScreenContentCallback(
              onAdShowedFullScreenContent: (ad) {
                debugPrint('🎯 전면 광고 표시');
                _lastInterstitialShown = DateTime.now();
              },
              onAdDismissedFullScreenContent: (ad) {
                debugPrint('🎯 전면 광고 닫힘');
                ad.dispose();
                _interstitialAd = null;
                _isInterstitialLoaded = false;
                // 다음 광고 미리 로드
                loadInterstitialAd();
              },
              onAdFailedToShowFullScreenContent: (ad, error) {
                debugPrint('❌ 전면 광고 표시 실패: $error');
                ad.dispose();
                _interstitialAd = null;
                _isInterstitialLoaded = false;
              },
            );
          },
          onAdFailedToLoad: (error) {
            debugPrint('❌ 전면 광고 로드 실패: $error');
            _isInterstitialLoaded = false;
          },
        ),
      );
    } catch (e) {
      debugPrint('❌ 전면 광고 로드 중 오류: $e');
    }
  }

  /// 전면 광고 표시 (정책 준수: 최소 간격 유지)
  Future<bool> showInterstitialAd() async {
    if (!_isInitialized || !_isInterstitialLoaded || _interstitialAd == null) {
      return false;
    }
    
    // 🚨 중요: 전면 광고 최소 간격 확인 (정책 준수)
    final minInterval = AppConfig.adInterstitialMinIntervalSeconds;
    if (_lastInterstitialShown != null) {
      final timeSinceLastAd = DateTime.now().difference(_lastInterstitialShown!);
      if (timeSinceLastAd.inSeconds < minInterval) {
        debugPrint('⏰ 전면 광고 최소 간격 미충족: ${timeSinceLastAd.inSeconds}초 < ${minInterval}초');
        return false;
      }
    }
    
    try {
      await _interstitialAd!.show();
      return true;
    } catch (e) {
      debugPrint('❌ 전면 광고 표시 중 오류: $e');
      return false;
    }
  }

  /// 네이티브 광고 생성 (레시피 목록 통합용 - 높은 클릭률)
  NativeAd? createNativeAd() {
    if (!_isInitialized || _nativeAdUnitId.isEmpty) return null;
    
    _nativeAd?.dispose();
    _nativeAd = NativeAd(
      adUnitId: _nativeAdUnitId,
      factoryId: 'listTile', // 네이티브 광고 팩토리 ID
      request: const AdRequest(),
      listener: NativeAdListener(
        onAdLoaded: (ad) => debugPrint('🎯 네이티브 광고 로드 완료'),
        onAdFailedToLoad: (ad, error) {
          debugPrint('❌ 네이티브 광고 로드 실패: $error');
          ad.dispose();
        },
        onAdOpened: (ad) => debugPrint('🎯 네이티브 광고 열림'),
        onAdClosed: (ad) => debugPrint('🎯 네이티브 광고 닫힘'),
        onAdClicked: (ad) => debugPrint('🎯 네이티브 광고 클릭'),
      ),
    );
    
    _nativeAd!.load();
    return _nativeAd;
  }

  /// 전면 광고 자동 프리로드 (앱 시작 시)
  Future<void> preloadInterstitialAd() async {
    await loadInterstitialAd();
  }

  /// 모든 광고 해제
  void dispose() {
    _bannerTopAd?.dispose();
    _bannerBottomAd?.dispose();
    _interstitialAd?.dispose();
    _nativeAd?.dispose();
    
    _bannerTopAd = null;
    _bannerBottomAd = null;
    _interstitialAd = null;
    _nativeAd = null;
    _isInterstitialLoaded = false;
  }

  /// 광고 상태 확인
  bool get isInitialized => _isInitialized;
  bool get isInterstitialReady => _isInterstitialLoaded;
}
