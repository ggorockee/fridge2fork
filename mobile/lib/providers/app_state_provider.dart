import 'package:flutter_riverpod/flutter_riverpod.dart';

/// 앱 최초 실행 여부를 관리하는 Provider
final isFirstLaunchProvider = StateProvider<bool>((ref) => false);

/// 선택된 탭 인덱스를 관리하는 Provider
/// 0: 홈, 1: 나의 냉장고, 2: 요리하기, 3: 의견보내기
final selectedTabIndexProvider = StateProvider<int>((ref) => 0);
