class FeedbackType {
  static const String bug = 'BUG';
  static const String feature = 'FEATURE';
  static const String improvement = 'IMPROVEMENT';
  static const String other = 'OTHER';

  static String getDisplayName(String type) {
    switch (type) {
      case bug:
        return '버그 리포트';
      case feature:
        return '기능 제안';
      case improvement:
        return '개선 제안';
      case other:
        return '기타';
      default:
        return '기타';
    }
  }

  static List<Map<String, String>> getAll() {
    return [
      {'value': bug, 'label': '버그 리포트'},
      {'value': feature, 'label': '기능 제안'},
      {'value': improvement, 'label': '개선 제안'},
      {'value': other, 'label': '기타'},
    ];
  }
}

class Feedback {
  final int? id;
  final String feedbackType;
  final String title;
  final String content;
  final String? contactEmail;
  final DateTime? createdAt;

  Feedback({
    this.id,
    required this.feedbackType,
    required this.title,
    required this.content,
    this.contactEmail,
    this.createdAt,
  });

  factory Feedback.fromJson(Map<String, dynamic> json) {
    return Feedback(
      id: json['id'] as int?,
      feedbackType: json['feedback_type'] as String,
      title: json['title'] as String,
      content: json['content'] as String,
      contactEmail: json['contact_email'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'feedback_type': feedbackType,
      'title': title,
      'content': content,
      if (contactEmail != null && contactEmail!.isNotEmpty)
        'contact_email': contactEmail,
    };
  }
}
