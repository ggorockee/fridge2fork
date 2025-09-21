import 'package:flutter_riverpod/flutter_riverpod.dart';

/// 앱 최초 실행 여부를 관리하는 Provider
final isFirstLaunchProvider = StateProvider<bool>((ref) => false);
