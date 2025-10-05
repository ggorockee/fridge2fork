import 'dart:io';

void main() async {
  final files = [
    'lib/screens/recipe_screen.dart',
    'lib/screens/recipe_list_screen.dart',
    'lib/screens/recipe_detail_screen.dart',
    'lib/screens/main_screen.dart',
    'lib/screens/splash_screen.dart',
    'lib/screens/feedback_screen.dart',
  ];

  for (final filePath in files) {
    print('Converting $filePath...');
    await convertFile(filePath);
  }

  print('All files converted successfully!');
}

Future<void> convertFile(String filePath) async {
  final file = File(filePath);
  if (!await file.exists()) {
    print('Warning: $filePath does not exist');
    return;
  }

  // Read content
  String content = await file.readAsString();

  // Check if screenutil import already exists
  if (!content.contains('flutter_screenutil')) {
    // Add import after flutter imports
    content = content.replaceFirst(
      RegExp(r"import 'package:flutter/material.dart';"),
      "import 'package:flutter/material.dart';\nimport 'package:flutter_screenutil/flutter_screenutil.dart';",
    );
  }

  // Convert fontSize
  content = content.replaceAllMapped(
    RegExp(r'fontSize:\s*(\d+)(?!\.sp)'),
    (match) => 'fontSize: ${match.group(1)}.sp',
  );

  // Convert icon/widget size
  content = content.replaceAllMapped(
    RegExp(r'size:\s*(\d+)(?!\.sp)'),
    (match) => 'size: ${match.group(1)}.sp',
  );

  // Convert width (excluding double.infinity)
  content = content.replaceAllMapped(
    RegExp(r'width:\s*(\d+)(?!\.w)'),
    (match) => 'width: ${match.group(1)}.w',
  );

  // Convert height (excluding double.infinity)
  content = content.replaceAllMapped(
    RegExp(r'height:\s*(\d+)(?!\.h)'),
    (match) => 'height: ${match.group(1)}.h',
  );

  // Convert BorderRadius.circular
  content = content.replaceAllMapped(
    RegExp(r'BorderRadius\.circular\((\d+)\)'),
    (match) => 'BorderRadius.circular(${match.group(1)}.r)',
  );

  // Convert blurRadius
  content = content.replaceAllMapped(
    RegExp(r'blurRadius:\s*(\d+)(?!\.r)'),
    (match) => 'blurRadius: ${match.group(1)}.r',
  );

  // Convert Offset
  content = content.replaceAllMapped(
    RegExp(r'Offset\((\d+),\s*(\d+)\)'),
    (match) => 'Offset(${match.group(1)}.w, ${match.group(2)}.h)',
  );

  // Remove const from widgets using .sp/.w/.h
  content = content.replaceAllMapped(
    RegExp(r'const\s+(Text|Icon|SizedBox|Container|Padding|EdgeInsets)[^;{]*?\.(?:sp|w|h|r)', multiLine: true),
    (match) {
      return match.group(0)!.replaceFirst('const ', '');
    },
  );

  // Write back
  await file.writeAsString(content);
  print('✓ $filePath converted');
}
