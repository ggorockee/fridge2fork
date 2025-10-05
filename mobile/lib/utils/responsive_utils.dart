import 'package:flutter/material.dart';

/// 디바이스 타입 enum
enum DeviceType {
  mobile,
  tablet,
}

/// 반응형 유틸리티 클래스
/// Flutter 앱의 태블릿 대응을 위한 화면 크기 감지 및 반응형 값 계산
class ResponsiveUtils {
  /// 태블릿 브레이크포인트 (600dp)
  /// iOS: iPad Mini 이상
  /// Android: 600dp 이상의 태블릿
  static const double tabletBreakpoint = 600.0;

  /// 컨텐츠 최대 너비 (태블릿용)
  static const double maxContentWidth = 800.0;

  /// 현재 디바이스 타입 감지
  static DeviceType getDeviceType(BuildContext context) {
    final shortestSide = MediaQuery.of(context).size.shortestSide;
    return shortestSide >= tabletBreakpoint ? DeviceType.tablet : DeviceType.mobile;
  }

  /// 현재 디바이스가 태블릿인지 확인
  static bool isTablet(BuildContext context) {
    return getDeviceType(context) == DeviceType.tablet;
  }

  /// 현재 디바이스가 모바일인지 확인
  static bool isMobile(BuildContext context) {
    return getDeviceType(context) == DeviceType.mobile;
  }

  /// 디바이스 타입에 따른 그리드 열 수 반환
  /// [mobileColumns] 모바일에서 표시할 열 수 (기본: 3)
  /// [tabletColumns] 태블릿에서 표시할 열 수 (기본: 4)
  static int getGridColumns(
    BuildContext context, {
    int mobileColumns = 3,
    int tabletColumns = 4,
  }) {
    return isTablet(context) ? tabletColumns : mobileColumns;
  }

  /// 디바이스 타입에 따른 패딩 값 반환
  /// [mobilePadding] 모바일에서 사용할 패딩
  /// [tabletPadding] 태블릿에서 사용할 패딩
  static double getResponsivePadding(
    BuildContext context, {
    required double mobilePadding,
    required double tabletPadding,
  }) {
    return isTablet(context) ? tabletPadding : mobilePadding;
  }

  /// 디바이스 타입에 따른 값 반환 (범용)
  /// [mobileValue] 모바일에서 사용할 값
  /// [tabletValue] 태블릿에서 사용할 값
  static T getValue<T>(
    BuildContext context, {
    required T mobileValue,
    required T tabletValue,
  }) {
    return isTablet(context) ? tabletValue : mobileValue;
  }

  /// 태블릿에서 중앙 정렬을 위한 최대 너비 제한 위젯
  /// [child] 제한할 자식 위젯
  /// [maxWidth] 최대 너비 (기본: 800)
  static Widget constrainWidth(
    BuildContext context, {
    required Widget child,
    double maxWidth = maxContentWidth,
  }) {
    if (isTablet(context)) {
      return Center(
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxWidth),
          child: child,
        ),
      );
    }
    return child;
  }

  /// 화면 너비 반환
  static double getScreenWidth(BuildContext context) {
    return MediaQuery.of(context).size.width;
  }

  /// 화면 높이 반환
  static double getScreenHeight(BuildContext context) {
    return MediaQuery.of(context).size.height;
  }

  /// 화면의 짧은 쪽 길이 반환
  static double getShortestSide(BuildContext context) {
    return MediaQuery.of(context).size.shortestSide;
  }

  /// 화면의 긴 쪽 길이 반환
  static double getLongestSide(BuildContext context) {
    return MediaQuery.of(context).size.longestSide;
  }

  /// 디바이스 타입에 따른 폰트 크기 조정
  /// [baseFontSize] 기본 폰트 크기
  /// [scaleFactor] 태블릿에서의 스케일 팩터 (기본: 1.1)
  static double getResponsiveFontSize(
    BuildContext context, {
    required double baseFontSize,
    double scaleFactor = 1.1,
  }) {
    return isTablet(context) ? baseFontSize * scaleFactor : baseFontSize;
  }

  /// 디바이스 타입에 따른 아이콘 크기 조정
  /// [baseIconSize] 기본 아이콘 크기
  /// [scaleFactor] 태블릿에서의 스케일 팩터 (기본: 1.2)
  static double getResponsiveIconSize(
    BuildContext context, {
    required double baseIconSize,
    double scaleFactor = 1.2,
  }) {
    return isTablet(context) ? baseIconSize * scaleFactor : baseIconSize;
  }
}

/// 반응형 Builder 위젯
/// 디바이스 타입에 따라 다른 위젯을 빌드
class ResponsiveBuilder extends StatelessWidget {
  final Widget Function(BuildContext context, DeviceType deviceType) builder;

  const ResponsiveBuilder({
    super.key,
    required this.builder,
  });

  @override
  Widget build(BuildContext context) {
    final deviceType = ResponsiveUtils.getDeviceType(context);
    return builder(context, deviceType);
  }
}

/// 반응형 레이아웃 위젯
/// 디바이스 타입에 따라 모바일 또는 태블릿 레이아웃 선택
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget? tablet;

  const ResponsiveLayout({
    super.key,
    required this.mobile,
    this.tablet,
  });

  @override
  Widget build(BuildContext context) {
    if (ResponsiveUtils.isTablet(context) && tablet != null) {
      return tablet!;
    }
    return mobile;
  }
}
