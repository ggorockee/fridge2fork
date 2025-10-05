import 'package:flutter/material.dart';

/// Fridge2Fork 앱의 테마 설정
/// Figma 디자인에서 추출한 컬러 시스템과 타이포그래피를 정의
class AppTheme {
  // 🎨 Primary Colors - Figma에서 추출한 메인 컬러
  static const Color primaryOrange = Color(0xFFFF7F32);
  static const Color secondaryOrange = Color(0xFFFFA451); // 메인 오렌지 컬러
  static const Color darkOrange = Color(0xFFF08626); // 진한 오렌지
  static const Color lightOrange = Color(0xFFFFF2E7); // 연한 오렌지 배경
  
  // 🎨 Background Colors
  static const Color backgroundWhite = Color(0xFFFFFFFF);
  static const Color backgroundGray = Color(0xFFF3F4F9);
  static const Color inputBackground = Color(0xFFF3F1F1);
  
  // 🎨 Icon Colors
  static const Color iconPrimary = Color(0XFF333333);



  // 🎨 Text Colors
  static const Color textPrimary = Color(0XFF333333); // 메인 텍스트
  static const Color textSecondary = Color(0xFF5D577E); // 서브 텍스트
  static const Color textPlaceholder = Color(0xFFC2BDBD); // 플레이스홀더
  static const Color textGray = Color(0xFF938DB5); // 회색 텍스트
  static const Color textSearch = Color(0xFF86869E); // 검색 텍스트
  
  // 🎨 Card Background Colors
  static const Color cardYellow = Color(0xFFFFFAEB); // 노란색 카드
  static const Color cardPink = Color(0xFFFEF0F0); // 분홍색 카드
  static const Color cardPurple = Color(0xFFF1EFF6); // 보라색 카드
  static const Color cardGreen = Color(0xFFE0FFE5); // 초록색 카드
  static const Color cardMint = Color(0xFFF0FEF8); // 민트색 카드
  
  // 🎨 Status Colors
  static const Color successGreen = Color(0xFF4CD964);
  static const Color dividerGray = Color(0xFFF4F4F4);
  static const Color borderGray = Color(0xFFF3F3F3);
  
  // 📱 Corner Radius - Figma 디자인 시스템
  static const double radiusSmall = 10.0;
  static const double radiusMedium = 16.0;
  static const double radiusLarge = 32.0;
  static const double radiusButton = 10.0;
  static const double radiusCard = 16.0;
  static const double radiusCircle = 100.0;

  // 📏 Spacing System
  static const double spacingXS = 4.0;
  static const double spacingS = 8.0;
  static const double spacingM = 16.0;
  static const double spacingL = 24.0;
  static const double spacingXL = 32.0;
  static const double spacingXXL = 48.0;

  // 🔤 Typography - Brandon Grotesque 폰트 시스템
  static const TextStyle headingLarge = TextStyle(
    fontFamily: 'Brandon Grotesque',
    fontSize: 32,
    fontWeight: FontWeight.w500,
    letterSpacing: -0.32,
    color: textPrimary,
  );

  static const TextStyle headingMedium = TextStyle(
    fontFamily: 'Brandon Grotesque',
    fontSize: 24,
    fontWeight: FontWeight.w500,
    letterSpacing: -0.24,
    color: textPrimary,
  );

  static const TextStyle headingSmall = TextStyle(
    fontFamily: 'Brandon Grotesque',
    fontSize: 20,
    fontWeight: FontWeight.w500,
    letterSpacing: -0.2,
    color: textPrimary,
  );

  static const TextStyle bodyLarge = TextStyle(
    fontFamily: 'Brandon Grotesque',
    fontSize: 20,
    fontWeight: FontWeight.w400,
    letterSpacing: -0.2,
    color: textPrimary,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontFamily: 'Brandon Grotesque',
    fontSize: 16,
    fontWeight: FontWeight.w500,
    letterSpacing: -0.16,
    color: textPrimary,
  );

  static const TextStyle bodySmall = TextStyle(
    fontFamily: 'Brandon Grotesque',
    fontSize: 14,
    fontWeight: FontWeight.w400,
    letterSpacing: -0.14,
    color: textPrimary,
  );

  static const TextStyle caption = TextStyle(
    fontFamily: 'Brandon Grotesque',
    fontSize: 10,
    fontWeight: FontWeight.w400,
    letterSpacing: 0,
    color: textPrimary,
  );

  // 🎨 Button Styles
  static final ButtonStyle primaryButtonStyle = ElevatedButton.styleFrom(
    backgroundColor: primaryOrange,
    foregroundColor: Colors.white,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(radiusButton),
    ),
    padding: const EdgeInsets.symmetric(
      horizontal: spacingL,
      vertical: spacingM,
    ),
    textStyle: const TextStyle(
      fontFamily: 'Brandon Grotesque',
      fontSize: 16,
      fontWeight: FontWeight.w500,
      letterSpacing: -0.16,
    ),
  );

  static final ButtonStyle secondaryButtonStyle = ElevatedButton.styleFrom(
    backgroundColor: Colors.white,
    foregroundColor: primaryOrange,
    side: const BorderSide(color: primaryOrange),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(radiusButton),
    ),
    padding: const EdgeInsets.symmetric(
      horizontal: spacingL,
      vertical: spacingM,
    ),
    textStyle: const TextStyle(
      fontFamily: 'Brandon Grotesque',
      fontSize: 16,
      fontWeight: FontWeight.w500,
      letterSpacing: -0.16,
    ),
  );

  // 🎨 Input Decoration
  static final InputDecoration inputDecoration = InputDecoration(
    filled: true,
    fillColor: inputBackground,
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(radiusButton),
      borderSide: BorderSide.none,
    ),
    contentPadding: const EdgeInsets.symmetric(
      horizontal: spacingL,
      vertical: spacingM,
    ),
    hintStyle: const TextStyle(
      fontFamily: 'Brandon Grotesque',
      fontSize: 20,
      fontWeight: FontWeight.w400,
      letterSpacing: -0.2,
      color: textPlaceholder,
    ),
  );

  // 🎨 Card Decoration
  static BoxDecoration cardDecoration({
    Color? backgroundColor,
    double? radius,
  }) {
    return BoxDecoration(
      color: backgroundColor ?? Colors.white,
      borderRadius: BorderRadius.circular(radius ?? radiusCard),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withOpacity(0.05),
          blurRadius: 10,
          offset: const Offset(0, 2),
        ),
      ],
    );
  }

  // 🎨 Flutter ThemeData
  static ThemeData get lightTheme {
    return ThemeData(
      primaryColor: primaryOrange,
      scaffoldBackgroundColor: backgroundWhite,
      fontFamily: 'Brandon Grotesque',
      
      // AppBar 테마
      appBarTheme: const AppBarTheme(
        backgroundColor: primaryOrange,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          fontFamily: 'Brandon Grotesque',
          fontSize: 24,
          fontWeight: FontWeight.w500,
          letterSpacing: -0.24,
          color: Colors.white,
        ),
      ),

      // ElevatedButton 테마
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: primaryButtonStyle,
      ),

      // InputDecoration 테마
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: inputBackground,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(radiusButton),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: spacingL,
          vertical: spacingM,
        ),
        hintStyle: const TextStyle(
          fontFamily: 'Brandon Grotesque',
          fontSize: 20,
          fontWeight: FontWeight.w400,
          letterSpacing: -0.2,
          color: textPlaceholder,
        ),
      ),

      // Card 테마
      cardTheme: CardThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusCard),
        ),
        elevation: 2,
      ),

      // Text 테마
      textTheme: const TextTheme(
        headlineLarge: headingLarge,
        headlineMedium: headingMedium,
        headlineSmall: headingSmall,
        bodyLarge: bodyLarge,
        bodyMedium: bodyMedium,
        bodySmall: bodySmall,
        labelSmall: caption,
      ),

      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryOrange,
        primary: primaryOrange,
        secondary: darkOrange,
        surface: backgroundWhite,
        background: backgroundGray,
      ),
    );
  }
}
