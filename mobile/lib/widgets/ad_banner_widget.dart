import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import '../services/ad_service.dart';
import '../theme/app_theme.dart';

/// 배너 광고 위젯
/// 
/// 🚨 정책 준수: 
/// - 광고와 콘텐츠를 명확히 구분
/// - 사용자 경험을 해치지 않는 배치
/// - 적절한 크기 유지
class AdBannerWidget extends StatefulWidget {
  final bool isTop;
  final bool isAdaptive;
  
  const AdBannerWidget({
    super.key,
    this.isTop = false,
    this.isAdaptive = true,
  });

  @override
  State<AdBannerWidget> createState() => _AdBannerWidgetState();
}

class _AdBannerWidgetState extends State<AdBannerWidget> {
  BannerAd? _bannerAd;
  bool _isAdLoaded = false;

  @override
  void initState() {
    super.initState();
    _loadBannerAd();
  }

  void _loadBannerAd() {
    final adService = AdService();
    
    if (widget.isAdaptive) {
      // 적응형 배너 (화면 크기에 맞춤)
      WidgetsBinding.instance.addPostFrameCallback((_) async {
        if (mounted) {
          final width = MediaQuery.of(context).size.width;
          _bannerAd = await adService.createAdaptiveBannerAd(
            width: width,
            isTop: widget.isTop,
          );
          
          if (_bannerAd != null && mounted) {
            setState(() => _isAdLoaded = true);
          }
        }
      });
    } else {
      // 일반 배너 (수익성 극대화: 위치별 구분)
      _bannerAd = widget.isTop 
          ? adService.createBannerTopAd()
          : adService.createBannerBottomAd();
      
      if (_bannerAd != null) {
        setState(() => _isAdLoaded = true);
      }
    }
  }

  @override
  void dispose() {
    _bannerAd?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isAdLoaded || _bannerAd == null) {
      return const SizedBox.shrink();
    }

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: AppTheme.backgroundGray,
        border: Border.all(
          color: AppTheme.textPlaceholder.withOpacity(0.3),
          width: 0.5.w,
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 광고 표시 라벨 (정책 준수)
          Container(
            width: double.infinity,
            padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 2.h),
            color: AppTheme.textPlaceholder.withOpacity(0.1),
            child: Text(
              '광고',
              style: TextStyle(
                fontSize: 10.sp,
                color: AppTheme.textPlaceholder,
                fontWeight: FontWeight.w400,
              ),
              textAlign: TextAlign.center,
            ),
          ),
          // 광고 콘텐츠
          SizedBox(
            width: _bannerAd!.size.width.toDouble(),
            height: _bannerAd!.size.height.toDouble(),
            child: AdWidget(ad: _bannerAd!),
          ),
        ],
      ),
    );
  }
}

/// 네이티브 광고 위젯 (레시피 목록에 자연스럽게 통합)
/// 
/// 🎯 수익성 전략:
/// - 레시피 목록에 자연스럽게 통합하여 높은 클릭률 달성
/// - 사용자 경험을 해치지 않는 디자인으로 광고 거부감 최소화
/// - 스크롤 중간에 배치하여 높은 가시성 확보
class AdNativeWidget extends StatefulWidget {
  final EdgeInsets margin;
  
  const AdNativeWidget({
    super.key,
    this.margin = const EdgeInsets.symmetric(horizontal: AppTheme.spacingM),
  });

  @override
  State<AdNativeWidget> createState() => _AdNativeWidgetState();
}

class _AdNativeWidgetState extends State<AdNativeWidget> {
  NativeAd? _nativeAd;
  bool _isAdLoaded = false;

  @override
  void initState() {
    super.initState();
    _loadNativeAd();
  }

  void _loadNativeAd() {
    final adService = AdService();
    _nativeAd = adService.createNativeAd();
    
    if (_nativeAd != null) {
      setState(() => _isAdLoaded = true);
    }
  }

  @override
  void dispose() {
    _nativeAd?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isAdLoaded || _nativeAd == null) {
      return const AdLoadingPlaceholder(height: 140);
    }

    return Container(
      margin: widget.margin,
      decoration: BoxDecoration(
        color: AppTheme.backgroundWhite,
        borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
        border: Border.all(
          color: AppTheme.textPlaceholder.withOpacity(0.3),
          width: 0.5.w,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4.r,
            offset: Offset(0, 2.h),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 광고 표시 라벨 (정책 준수)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(AppTheme.spacingS),
            decoration: BoxDecoration(
              color: AppTheme.backgroundGray,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(AppTheme.radiusMedium),
                topRight: Radius.circular(AppTheme.radiusMedium),
              ),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.info_outline,
                  size: 12.sp,
                  color: AppTheme.textPlaceholder,
                ),
                SizedBox(width: 4.w),
                Text(
                  '스폰서 콘텐츠',
                  style: TextStyle(
                    fontSize: 10.sp,
                    color: AppTheme.textPlaceholder,
                    fontWeight: FontWeight.w400,
                  ),
                ),
                const Spacer(),
                Text(
                  '광고',
                  style: TextStyle(
                    fontSize: 10.sp,
                    color: AppTheme.textPlaceholder,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
          // 네이티브 광고 콘텐츠
          SizedBox(
            height: 120.h, // 네이티브 광고 높이
            child: AdWidget(ad: _nativeAd!),
          ),
        ],
      ),
    );
  }
}

/// 광고 로딩 플레이스홀더
class AdLoadingPlaceholder extends StatelessWidget {
  final double height;
  
  const AdLoadingPlaceholder({
    super.key,
    this.height = 50,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: height,
      decoration: BoxDecoration(
        color: AppTheme.backgroundGray,
        border: Border.all(
          color: AppTheme.textPlaceholder.withOpacity(0.3),
          width: 0.5.w,
        ),
      ),
      child: Center(
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 12.w,
              height: 12.h,
              child: CircularProgressIndicator(
                strokeWidth: 2.w,
                valueColor: AlwaysStoppedAnimation<Color>(
                  AppTheme.textPlaceholder,
                ),
              ),
            ),
            SizedBox(width: 8.w),
            Text(
              '광고 로딩 중...',
              style: TextStyle(
                fontSize: 12.sp,
                color: AppTheme.textPlaceholder,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
